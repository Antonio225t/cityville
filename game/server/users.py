import json
import xmltodict
from pathlib import Path
import math
from datetime import datetime
from os import mkdir
import os.path
import random

import rand

TEMP_ID_START = 16777217
TEMP_ID_END = 16781312

settings = {}
items = {}
users = {}
randomTables = {}

def timestamp():
    return int(datetime.now().timestamp())

def init():
    global settings, items, users, randomTables
    settings = initSettings()
    items = getItems(settings)
    randomTables = getRandomTables(settings)
    users = initUsers()


def getPopulation(userId): # TODO: This gets the segments.
    if userId not in users:
        return 0
    return users[userId]['userInfo']['world']['citySim']

def getGold(userId):
    if userId not in users:
        return 0
    return users[userId]['userInfo']['player']['gold']


def initSettings():
    with open('../client/gameSettings.xml', "r", encoding="UTF-8") as f:
        xml_string = f.read()
    xml_dict = xmltodict.parse(xml_string)
    settings = xml_dict['settings']
    return settings

def initUsers():
    users = {}
    dir = Path('users')
    i = 0
    for subdir in dir.iterdir():
        id = subdir.stem
        filename = str(subdir) + '/user.json'
        if not os.path.isfile(filename):
            continue
        with open(filename) as file:
            data = json.load(file)
        users[id] = data
        i += 1
    print('Users found:',i-1)
    return users

def recalcLevel(userId):
    player = users[userId]['userInfo']['player']
    xp = player['xp']
    player['energyMax'] = getEnergyMax(xp)
    newLevel = getLevel(xp)
    if player['level'] != newLevel:
        print('Level Up!  New Level:',newLevel)
        player['energy'] = player['energyMax']
        player['cash'] += 1
        player['level'] = newLevel

def save(userId):
    recalcLevel(userId)
    if not os.path.exists('users/' + userId):
        mkdir('users/' + userId)
    filename = 'users/' + userId + '/user.json'
    data = users[userId]
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    stats(userId)

def getExpansions(userId):
    print("getExpansions")
    if userId not in users:
        return 0
    return users[userId]['userInfo']['player']['expansionsPurchased']

def remapIds(userId,remapSet=set()):
    print("remapIds")
    worldObjects = users[userId]['userInfo']['world']['objects']
    result = []
    for obj in worldObjects:
        if 'id' not in obj:
            continue
        id = obj['id']
        if len(remapSet) > 0 and id not in remapSet:
            continue
        if id >= TEMP_ID_START and id <= TEMP_ID_END:
            # assign permanent ids
            newId = users[userId]['idCounter']
            users[userId]['idCounter'] += 1
            # print(users[userId]['idCounter'])
            obj['id'] = newId
            result.append({'id': id, 'newId': newId })
    print('Assigned',len(result),'permanent IDs: ',result)
        
    # also need to update crews to point to correct object
    if 'crews' in users[userId]:
        crews = users[userId]['crews']
        for changed in result:
            if str(changed['id']) in crews:
                crews[str(changed['newId'])] = crews.pop(str(changed['id']))
        
    return result
    
    
    
def createMapRect(expandType,pos):
    print("createMapRect")
    width = int(items[expandType]['@width'])
    height = int(items[expandType]['@height'])
    rect = { 'x': pos['x'], 'y': pos['y'], 'width': width, 'height': height}
    # print(rect)
    return rect

def expandCity(userId, data):
    print('Expanding Map')
    itemName = data[0]
    userInfo = users[userId]['userInfo']
    userInfo['player']['expansionsPurchased'] += 1
    userInfo['world']['mapRects'].append(createMapRect(itemName,data[1]))
    
    # NOT USED?: if license[itemName]: delete(ItemName) else
    permits,_,multiplier = getExpansionData(userInfo['player']['expansionsPurchased'])
       
    print(items[itemName])
    cost = int(items[data[0]]['cost'])
    cost = int(cost * multiplier)
    print('Deducting',cost,'gold')
    userInfo['player']['gold'] -= cost
    print('Deducting',permits,'permits')
    inventoryRemove(userId,'permits',permits)

    # remap existing temp IDs first so that only wilderness gets done in next round
    # remapIds(userId)
        
    # TODO: why bother?  just create a new world object, rather than edit these so much
    remapSet = set()
    for item in data[2]:
        item['className'] = 'Wilderness'
        item['direction'] = item['dir']
        item['state'] = 'static'        
        item['position'] = { 'x': item['x'], 'y': item['y'], 'z': 0}
        del item['dir']
        del item['x']
        del item['y']
        remapSet.add(item['id'])
    userInfo['world']['objects'].extend(data[2])
    result = remapIds(userId,remapSet)
    save(userId)
    return result

            
def renameCity(userId,newName):
    print("renameCity")
    if userId not in users:
        return {}
    # TODO: i think the client does some sanitizing, we should probably do it again here
    # i.e. newName = newName.replace("'","").replace('"',"") -- Poor man's sanitizer.
    users[userId]['userInfo']['worldName'] = newName
    return { 'name': newName }
    
def getUser(userId):
    print("getUser")
    if userId == '-1':
        return users['samantha']
    if userId not in users:
        print('User',userId,'not found. Creating new user.')
        data = users['newUser'].copy() # TODO: should be deep copy, not shallow copy !!!
        data['userInfo']['player']['uid'] = int(userId)
        users[userId] = data
        save(userId)
    else:
        if len(remapIds(userId)) > 0:
            save(userId)
    print('Got User',userId)
    
    # partial fix for goods bugs
    player = users[userId]['userInfo']['player']    
    worldObjects = users[userId]['userInfo']['world']['objects']
    maxGoods = calcGoodsCapacity(worldObjects)
    users[userId]['storageMax'] = maxGoods
    if player['commodities']['storage']['goods'] < 0:
        player['commodities']['storage']['goods'] = 0
    if player['commodities']['storage']['goods'] > maxGoods:
        player['commodities']['storage']['goods'] = maxGoods

    if 'socialXp' not in player:
        player['socialXp'] = 0
        player['socialLevel'] = 1

    updateEnergyInternal(userId)
    return users[userId];
      
def updateWorld(id, message):
    print("updateWorld")
    print(id)
    print(message)
    save(id)
    
def updateOptions(userId, options):
    print("updateOptions")
    print('Saving preferences for user',userId)
    if userId in users:
        print(options)
        users[userId]['userInfo']['player']['options'] = options[0]
        save(userId)

def completedTutorial(userId):
    print('User',userId,'completed tutorial.')
    if userId in users:
        users[userId]['userInfo']['is_new'] = False
        save(userId)

def getIndexById(worldObjects, objectId):
    print("getIndexById")
    # TODO: use a faster lookup (dictionary)
    for i in range(len(worldObjects)):
        object = worldObjects[i]
        if 'id' in object and object['id'] == objectId:
            return i
    return -1

def getLevel(xp):
    print("getLevel")
    levels = settings['levels_cv_level_regrade_var_0']
    level = 1 # Base Level
    for levelData in levels['level']:
        if int(levelData['@requiredXP']) > xp:
            return level
        else:
            level = int(levelData['@num'])
    return level

def getEnergyMax(xp):
    print("getEnergyMax")
    levels = settings['levels_cv_level_regrade_var_0']
    energyMax = 12 # Base Energy
    for level in levels['level']:
        if int(level['@requiredXP']) > xp:
            # print('Energy Max:',energyMax)
            return energyMax
        else:
            energyMax = int(level['@energyMax'])
    # print('Energy Max:',energyMax)
    return energyMax
    

def getCost(itemId):
    print("getCost")
    cost = 0
    if itemId in items:
        item = items[itemId]
        if 'cost' in item:
            cost = int(item['cost'])
        # else:
            # print('No cost for item:',item)
    return cost

def getCash(itemId):
    print("getCash")
    cash = 0
    if itemId in items:
        item = items[itemId]
        if 'cash' in item:
            cash = int(item['cash'])
    return cash


def giveRewards(userId, rewards, unknown):
    print("giveRewards")
    if userId not in users:
        return
    player = users[userId]['userInfo']['player']
    for item in rewards.keys():
        match item:
            case '@gold' | '@coins':
                player['gold'] += int(rewards[item])
            case '@cash':
                player['cash'] += int(rewards[item])
            case '@xp':
                player['xp'] += int(rewards[item])
            case '@energy':
                player['energy'] += int(rewards[item])
            case '@goods':
                player['commodities']['storage']['goods'] += int(rewards[item])
                if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
                    player['commodities']['storage']['goods'] = users[userId]['storageMax']
            case '@itemName' | '@item':                
                inventoryAdd(userId,rewards[item],1,True)
            case '@itemUnlock':
                player['seenFlags'][rewards[item]] = 1
            case '@grantHQ':
                if rewards[item] == "true":
                    franchises = getFranchisesByLocation(userId,'-1')
                    for franchise in franchises:
                        print(franchise)
                        franchiseType = franchiseGetHQType(franchise['name'])
                        franchiseGrantHQ(userId,franchiseType)
            case _:
                print(' UNKNOWN REWARD:',item,rewards[item])
    save(userId)

def collectDoobers(userId,itemName,coinMultiplier = 1):
    print("collectDoobers")
    doobers,secureRands = rand.generateDoobers(userId,itemName)
    player = users[userId]['userInfo']['player']

    for doober in doobers:
        if doober[0] == 'coin':
            doober[1] = math.ceil(doober[1] * coinMultiplier)
        elif doober[0] != 'collectable':
            doober[1] = int(doober[1])

    print('Collected reward(s): ',doobers)
    for doober in doobers:
        match doober[0]:
            case 'food' | 'goods':
                player['commodities']['storage']['goods'] += int(doober[1])
                if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
                    player['commodities']['storage']['goods'] = users[userId]['storageMax']
            case 'coin':
                player['gold'] += int(doober[1])
            case 'xp':
                player['xp'] += int(doober[1])
            case 'energy':
                player['energy'] += int(doober[1])
            case 'collectable':
                collectionAdd(userId,doober[1])
            case _:
                print('UNKNOWN DOOBER:', doober)
    return secureRands

def recalcPop(worldObjects):
    print('Recalculating Population...')
    return {
        "citizen": recalcPopSegment(worldObjects, "citizen")
        # TODO: Add the other segments
    }

def recalcPopSegment(worldObjects, segment):
    popMin = 0
    popMax = 120
    popYield = 0
    potential = 0 # TODO: Figure out
    capacity = 0 # TODO: Figure out
    
    for item in worldObjects:
        itemName = item['itemName']
        itm = items[itemName]
        if 'population' in itm:
            if "@min" in itm["population"]:
                popMin += int(itm["population"]["@min"]) # TODO: Figure out "@min" and "@max"
                popYield += int(itm["population"]["@min"])
            
            if "@cap" in itm["population"]:
                capacity += int(itm["population"]["@cap"])
            # popMax = itm["population"]["@max"]
            # pop += random.randint(int(popMin), int(popMax)) # TODO: Add support for random modifiers (No, it's not like that.)
    print('Population:',popMin)
    return {
        "capacity": capacity,
        "id": segment,
        "maximum": popMax,
        "minimum": popMin,
        "potential": potential,
        "yield": popYield
    }

# def recalcPopCap(worldObjects): # This shouldn't be used anymore...
#     print('Recalculating Population Limit...')
#     popCap = int(settings['citysim']['populations']["population"][0]['@baseCap']) * 10 # TODO: Adjust the settings['citysim']['populations']["population"][0]['@baseCap']
#     for item in worldObjects:
#         itemName = item['itemName']
#         if 'populationCapYield' in items[itemName]:
#             popCapYield = items[itemName]['populationCapYield']
#             popCap += 10 * int(popCapYield)
#     print('Population Limit:',popCap)
#     return popCap

def calcGoodsCapacity(worldObjects):
    print("calcGoodsCapacity")
    totalCapacity = 300 # technically should read from settings\commodities\commodity\initCap
    for item in worldObjects:
        itemName = item['itemName']
        if 'commodity' in items[itemName]:
            # print(items[itemName]['commodity'])
            if '@capacity' in items[itemName]['commodity']:
                capacity = items[itemName]['commodity']['@capacity']
                totalCapacity += int(capacity)
    print('Goods Capacity:',totalCapacity)
    return totalCapacity

    
def handleVisits(userId,params):
    print("handleVisits")
    print(params)
    for businessId in params[0].keys():
        # businessId = params[0][i]
        quantity = params[0][businessId]["NPCEnterAction"]["count"] # TODO: Check if there are other NPC<action>Action
        
        business = getObjectById(userId,businessId)
        if business != None:
            if 'visits' not in business:
                business['visits'] = quantity
            else:
                business['visits'] += quantity
            busData = items[business['itemName']]
            if 'commodityReq' in busData:
                if business['visits'] >= int(busData['commodityReq']):
                    business['state'] = 'closedHarvestable'
            save(userId)

def performAction(userId,params):
    print("performAction")
    if userId not in users:
        print('User not found')
        return
    action = params[0]
    resource = params[1]
    worldObjects = users[userId]['userInfo']['world']['objects']
    if action == 'place':
        print('Placing object')
        name = resource['itemName']
        item = items[name]
        # objectId = len(worldObjects) + 54000
        if 'construction' in item:
            construction = item['construction']
            site = createConstructionSite(resource["id"], construction, resource['direction'], name, resource['className'],resource['position'],resource['state'])
            if 'gates' in item:
                site['gates'] = createGates(item)
            worldObjects.append(site)
        else:
            worldObjects.append(resource)
        
        player = users[userId]['userInfo']['player']
        if len(params[3]) > 0:
            instData = params[3][0]
            if 'isGift' in instData and instData['isGift']:
                if inventoryCount(userId,name) > 0:
                    print('Removing from inventory')
                    inventoryRemove(userId,name,1)
                else:
                    print('Item not found in inventory:',name)
            else:
                cost = getCost(name)
                cash = getCash(name)
                print('Purchasing item:',name,' Coins:',str(cost),'Cash:',cash)
                player['gold'] -= cost
                player['cash'] -= cash
        save(userId)            
        # return {'id': int(objectId)}
    elif action == 'build':
        print('Building object')
        objectId = resource['id']
        index = getIndexById(worldObjects,objectId)
        if index != -1 and 'builds' in worldObjects[index]:
            print(worldObjects[index])
            worldObjects[index]['builds'] += 1
            worldObjects[index]['finishedBuilds'] += 1
            worldObjects[index]['stage'] += 1
            stage = worldObjects[index]['stage']
            siteName = worldObjects[index]['itemName']
            totalStages = int(items[siteName]['numberOfStages'])
            player = users[userId]['userInfo']['player']
            player['energy'] -= 1
            print('Current Stage:',stage,'of',totalStages)  
            if stage != totalStages:
                target = worldObjects[index]['itemName']
                doobers,secureRands = rand.generateDoobers(userId,target)
                for i in doobers:
                    if i[0] == 'xp':
                        player = users[userId]['userInfo']['player']
                        player['xp'] += int(i[1])
            elif 'gates' in worldObjects[index]:
                worldObjects[index]['currentState'] = 2 # STATE_AT_GATE
            save(userId)
        else:
            print('Could not find object',objectId)
    elif action == 'finish':
        objectId = resource['id']
        index = getIndexById(worldObjects,objectId)
        print('Finishing object:',index)
        if index != -1:
            oldItem = worldObjects[index]       
            print(oldItem)
            itemName = oldItem["itemName"]
            className = oldItem["className"]
            if "targetBuildingName" in oldItem:
                itemName = oldItem["targetBuildingName"]
            if "targetBuildingClass" in oldItem:
                className = oldItem["targetBuildingClass"]
            worldObjects[index] = {
                'itemName': itemName,
                'className': className,
                'id': oldItem['id'],
                'position': oldItem['position'],
                'direction': oldItem['direction'],
                'state': oldItem['state']
            }
            if oldItem['state'] == 'planted':
                worldObjects[index]['plantTime'] = timestamp() * 1000
            
            users[userId]['userInfo']['world']['citySim']["segments"] = recalcPop(worldObjects)
            # users[userId]['userInfo']['world']['citySim']['populationCap'] = recalcPopCap(worldObjects)//10 
            users[userId]['storageMax'] = calcGoodsCapacity(worldObjects)
            secureRands = collectDoobers(userId, oldItem['itemName'])
            save(userId)
    elif action == 'move':
        print('Moving object')
        objectId = resource['id']
        index = getIndexById(worldObjects,objectId)
        if index != -1:
            print('New Position for Object',objectId,';',resource['position'])
            item = worldObjects[index] 
            item['position'] = resource['position']
            item['direction'] = resource['direction']
            save(userId)
    elif action == 'sell':
        print('Selling object')
        objectId = resource['id']
        index = getIndexById(worldObjects,objectId)
        if index != -1:
            del worldObjects[index]
            name = resource['itemName']
            sellAmount = math.ceil(getCost(name) * 0.05)
            users[userId]['userInfo']['player']['gold'] += sellAmount
            users[userId]['userInfo']['world']['citySim']["segments"] = recalcPop(worldObjects)
            # users[userId]['userInfo']['world']['citySim']['populationCap'] = recalcPopCap(worldObjects)//10
            save(userId)
        else:
            print('Object',objectId,'not found')
    elif action == 'clear':
        print('Clearing object')
        objectId = resource['id']
        index = getIndexById(worldObjects,objectId)
        if index != -1:
            itemName = worldObjects[index]['itemName']
            secureRands = collectDoobers(userId,itemName)
            del worldObjects[index]
            users[userId]['userInfo']['player']['energy'] -= 1
            return { 'secureRands': secureRands }
    elif action == 'harvest':
        print("Harvest")
        className = resource['className']
        coinYield = 0
        energyCost = 0
        itemName = ''
        if className == 'Plot':
            itemName = resource['contractName']
            print('Harvesting',itemName)
            if itemName in items:
                coinYield = items[itemName]['coinYield']
                energyCost = items[itemName]['energyCost']['@harvest']
        else:
            print('Harvesting',className)
            itemName = resource['itemName']
            if itemName in items and 'coinYield' in items[itemName]:
                coinYield = items[itemName]['coinYield']
                energyCost = items[itemName]['energyCost']['@harvest']
        item = getObjectById(userId,resource['id'])      
        if int(energyCost) > 0:
            print('Deducting harvest energy:',energyCost)
            users[userId]['userInfo']['player']['energy'] -= int(energyCost)
        if item != None:
            if item['className'] == 'Plot':
                item['state'] = 'plowed'
                print('Plowed')
            elif item['state'] == 'open':
                item['state'] = 'closed'
                item['visits'] = 0
            elif item['state'] == 'closedHarvestable':
                item['state'] = 'closed'
                item['visits'] = 0
            elif item['state'] == 'grown':
                item['state'] = 'planted'
                
            if item['state'] == 'planted':
                item['plantTime'] = timestamp() * 1000 # in milliseconds.

            # Business coin yields are multiplied by # of visitors
            coinMultiplier = getBonus(userId,resource,'coinYield')
            if item['className'] == 'Business':
                print(params)
                storeCount = params[3][0] # TODO: Probably needs fixing the [0].
                coinMultiplier *= storeCount["npcCount"]
                
            secureRands = collectDoobers(userId,itemName,coinMultiplier)
        else:
            print('No Item')
            secureRands = []
        save(userId)
        return { 'retCoinYield': coinYield , 'secureRands': secureRands }
    elif action == 'startContract':
        print('Starting Contract')
        replaceObjectById(userId,resource['id'],resource)
        cost = 0
        name = resource['contractName']
        if 'cost' in items[name]:
            cost = int(items[name]['cost'])
        print('Planted:',name,'Cost:',cost)
        users[userId]['userInfo']['player']['gold'] -= cost
        save(userId)
    elif action == 'openBusiness':
        print("openBusiness")
        item = getObjectById(userId,resource['id'])
        if item != None:
            item['state'] = 'open'
            item['visits'] = 0
            itemData = items[item['itemName']]
            player = users[userId]['userInfo']['player']
            print(itemData)
            player['commodities']['storage']['goods'] -= int(itemData['commodityReq'])
            save(userId)
            print('Opened business with id:',resource['id'])
    else:
        print("Unknown action of performAction:")
        print(action)
        print(resource)
  
def getItems(settings):
    print("getItems")
    dict = {}
    items  = settings['items']['item']
    for item in items:
        name = item['@name']
        dict[name] = item
    print('Items found:', len(items))
    return dict
    
def getRandomTables(settings):
    print("getRandomTables")
    dict = {}
    randomTables = settings['randomModifierTables']['randomModifierTable']
    for table in randomTables:
        name = table['@name']
        dict[name] = table
    print('Random tables found:', len(randomTables))
    return dict

def createConstructionSite(id,construction,direction,targetName,targetClass,position,state):
    print("createConstructionSite")
    return {
        'position': position,
        'itemName': construction,
        'className': 'ConstructionSite',
        'id': id,
        'targetBuildingClass': targetClass,
        'targetBuildingName': targetName,
        'stage': 0,
        'finishedBuilds': 0,
        'builds': 0,
        'direction': direction,
        'state': state
    }

def getObjectById(userId, itemId):
    print("getObjectById")
    worldObjects = users[userId]['userInfo']['world']['objects']
    for obj in worldObjects:
        if 'id' in obj and obj['id'] == itemId:
            return obj
    return None
 
def replaceObjectById(userId, itemId, newItem):
    print("replaceObjectById")
    worldObjects = users[userId]['userInfo']['world']['objects']
    for i in range(len(worldObjects)):
        if worldObjects[i]['id'] == itemId:
            worldObjects[i] = newItem
            break

def getItemByName(name):
    print("getItemByName")
    if name in items:
        return items[name]
    return None

def getObjectsByName(userId,name):
    print("getObjectsByName")
    result = []
    if userId not in users:
        return result
    worldObjects = users[userId]['userInfo']['world']['objects']
    for obj in worldObjects:
        if obj['itemName'] == name:
            result.append(obj)
    return result

def getObjectsByClass(userId,className):
    print("getObjectsByClass")
    result = []
    if userId not in users:
        return result
    worldObjects = users[userId]['userInfo']['world']['objects']
    for obj in worldObjects:
        if obj['className'] == className:
            result.append(obj)
    return result
    
def acquireLicense(userId,licenses):
    print("acquireLicense")
    # code only seems to allow one license at a time
    player = users[userId]['userInfo']['player']
    itemName = licenses[0]
    item = items[itemName]
    cash = 0
    if 'unlockCost' in item:
        cash = int(item['unlockCost'])
    print('Unlocking',itemName,'for',cash)
    player['licenses'][itemName] = 1
    player['cash'] -= cash
    save(userId)
    return { 'itemName': itemName }

def acquirePermit(userId,params):
    print("acquirePermit")
    itemName = params[0]
    player = users[userId]['userInfo']['player']   
    nextExpansion = player['expansionsPurchased'] + 1
    permits,cash,_ = getExpansionData(nextExpansion)
    print('Acquiring',permits,'zone permits for',cash,'cash')
    player['cash'] -= cash
    inventoryAdd(userId,'permits',permits,False)
    # print('acquirePermit:',itemName)
    return { 'itemName': itemName }
    
def getExpansionData(index):
    print("getExpansionData")
    expansions = settings['expansions']['expansion']
    for expansion in expansions:
        if expansion['@num'] == 'MAX':
            permits = int(expansion['@permits'])
            cash = int(expansion['@cost'])
            multiplier = float(expansion['@goldMultiplier'])
            return permits,cash,multiplier
        else:
            num = int(expansion['@num'])
            if num == index:
                permits = int(expansion['@permits'])
                cash = int(expansion['@cost'])
                multiplier = float(expansion['@goldMultiplier'])
                return permits,cash,multiplier
                

def inventoryAdd(userId,itemName,quantity,isGift):
    print("inventoryAdd")
    # TODO: handle gift case
    # TODO: add max quantity checks
    inventory = users[userId]['userInfo']['player']['inventory']
    inventory['count'] += quantity
    if itemName in inventory['items']:
        inventory['items'][itemName] += quantity
    else:
        inventory['items'][itemName] = quantity
    save(userId)

def inventoryRemove(userId,itemName, quantity):
    print("inventoryRemove")
    inventory = users[userId]['userInfo']['player']['inventory']
    if quantity <= 0 or inventoryCount(userId,itemName) < quantity:
        return
    inventory['count'] -= quantity
    inventory['items'][itemName] -= quantity
    if inventory['items'][itemName] <= 0:
        del inventory['items'][itemName]
    save(userId)

def inventoryCount(userId,itemName):
    print("inventoryCount")
    inventory = users[userId]['userInfo']['player']['inventory']
    if itemName not in inventory['items']:
        return 0
    return inventory['items'][itemName]

def getCollectionByCollectableName(name):
    print("getCollectionByCollectableName")
    collections = settings['collections']['collection']
    for collection in collections:
        collectionName = collection['@name']
        for collectable in collection['collectables']['collectable']:
            if collectable['@name'] == name:
                return collectionName
    return None

def collectionAdd(userId,itemName):
    print("collectionAdd")
    if itemName not in items:
        print('Missing item:',itemName)
        return
    collection = getCollectionByCollectableName(itemName)
    if collection == None:
        print('Missing collection for',itemName)
        return
    collections = users[userId]['userInfo']['player']['collections']
    if collection not in collections:
        collections[collection] = {}
    if itemName in collections[collection]:
        collections[collection][itemName] += 1
    else:
        collections[collection][itemName] = 1
    save(userId)

def collectionRemove(userId,itemName):
    print("collectionRemove")
    collection = getCollectionByCollectableName(itemName)
    collections = users[userId]['userInfo']['player']['collections']
    if collection in collections and itemName in collections[collection]:
        collections[collection][itemName] -= 1
        if collections[collection][itemName] <= 0:
            del collections[collection][itemName]
    save(userId)


def collectionTradeIn(userId,params):
    print("collectionTradeIn")
    name = params[0]
    # remove one of each item in collection
    collections = users[userId]['userInfo']['player']['collections']    
    if name not in collections:
        return False
    collectables = collections[name].copy()
    for collectable in collectables:
        collectionRemove(userId,collectable)
    completedCollections = users[userId]['userInfo']['player']['completedCollections']
    if name not in completedCollections:
        completedCollections[name] = 1
    else:
        completedCollections[name] += 1
    collectionGrantReward(userId,name)

def collectionGrantReward(userId,name):
    print("collectionGrantReward")
    if userId not in users:
        return
    player = users[userId]['userInfo']['player']
    collections = settings['collections'][0]['collection']
    for collection in collections:
        if collection['@name'] == name:
            rewards = collection['tradeInReward']
            print('Collection Trade-In Reward:',rewards)
            for reward in rewards:
                # print('Trade In Reward:',reward,rewards[reward])
                match reward:
                    case 'coin':
                        player['gold'] += int(rewards[reward]['@amount'])
                    case 'xp':
                        player['xp'] += int(rewards[reward]['@amount'])
                    case 'energy':
                        player['energy'] += int(rewards[reward]['@amount'])
                    case 'goods':
                        player['commodities']['storage']['goods'] += int(rewards[reward]['@amount'])
                        if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
                            player['commodities']['storage']['goods'] = users[userId]['storageMax']
                    case 'item':           
                        inventoryAdd(userId,rewards[reward]['@name'],1,True)
                    case _:
                        print('UNKNOWN TRADE-IN REWARD',reward)
            break
    save(userId)

    
def getCollectableCount(userId,itemName):
    print("getCollectableCount")
    if userId not in users:
        return 0
    collection = getCollectionByCollectableName(itemName)
    collections = users[userId]['userInfo']['player']['collections']
    if collection in collections and itemName in collections[collection]:
        return collections[collection][itemName]
    return 0;

        
def getFranchisesByLocation(userId,neighborId):
    print("getFranchiseByLocation")
    result = []
    franchises = users[userId]['franchises']
    for franchise in franchises:
        # print(franchise)
        if neighborId in franchise['locations']:
            # result.append(franchise['locations'][neighborId])
            result.append(franchise)
    return result
    
def getFranchiseCountByLocation(userId,neighborId):
    print("getFranchiseCountByLocation")
    return len(getFranchisesByLocation(userId,neighborId))

def getAllFranchises(userId):
    print("getAllFranchises")
    return users[userId]['franchises']
        
def getAllFranchiseAcceptedLocationsCount(userId):
    print("getAllFranchiseAcceptedLocationsCount")
    result = 0
    franchises = getAllFranchises(userId)
    for franchise in franchises:
        for location in franchise['locations']:
            if franchise['locations'][location]['time_last_operated'] > 0:
                result += 1
    return result

def getAllFranchiseAcceptedLocationsCount(userId):
    print("getAllFranchiseAcceptedLocationsCount")
    result = 0
    franchises = getAllFranchises(userId)
    for franchise in franchises:
        for location in franchise['locations']:
            if franchise['locations'][location]['time_last_operated'] > 0:
                result += 1
    return result
    
def getFranchiseCountByType(userId,name):
    print("getFranchiseCountByType")
    franchises = getAllFranchises(userId)
    for franchise in franchises:
        if franchise['name'] == name:
            return len(franchise['locations'])
    return 0

def franchiseGetHQType(franchiseType):
    print("franchiseGetHQType")
    item = items[franchiseType]
    if item != None:
        return item['headquarters']
    return None
    
def franchiseGrantHQ(userId,franchiseType):
    print("franchiseGrantHQ")
    inventoryAdd(userId,franchiseType,1,True);
    pass

def createFranchise(userId,franchiseType,franchiseName):
    print("createFranchise")
    franchise = {
        'name': franchiseType,
        'franchise_name': franchiseName,
        'locations' : {},
        'time_last_collected': 0
    }
    users[userId]['franchises'].append(franchise)
        
def createFranchiseLocation(resourceId):
    print("createFranchiseLocation")
    now = timestamp()
    location = {
        'star_rating': 1,
        'commodity_left': 0,
        'commodity_max': 1,
        'customers_served': 0,
        'money_collected': 500,
        'obj_id': resourceId,
        'time_last_collected': now,
        'time_last_operated': now,
        'time_last_supplied': 0
    }
    return location

def updateFranchiseName(userId,params):
    print("updateFranchiseName")
    franchiseType = params[0]
    franchiseName = params[1]
    franchises = users[userId]['franchises']
    for franchise in franchises:
        if franchise['name'] == franchiseType:
            franchise['franchise_name'] = franchiseName
            save(userId)
            return
    createFranchise(userId,franchiseType,franchiseName)
    save(userId)
        
def replaceUserResource(userId,params):
    print("replaceUserResource")
    visitorId = params[0]
    resourceId = params[2]
    franchiseType = params[3]
    franchises = users[userId]['franchises']
    for franchise in franchises:
        if franchise['name'] == franchiseType:
            franchise['locations'][visitorId] = createFranchiseLocation(resourceId)
            break
    save(userId)
        
def getFranchiseDailyBonus(userId,params):
    print("getFranchiseDailyBonus")
    franchiseType = params[0]
    player = users[userId]['userInfo']['player']    
    franchises = users[userId]['franchises']
    franchiseIndex = 0
    i = 0
    for franchise in franchises:
        print(franchise)
        if franchise['name'] == franchiseType:
            franchiseIndex = i + 1
            franchise['time_last_collected'] = timestamp()
            break
        i = i+1
    if franchiseIndex == 0:
        print('Franchise not found:',franchiseType)
        return
    coins = getFranchiseCountByType(userId,franchiseType) * int(settings['farming']['@franchise' + str(franchiseIndex) + 'DailyBonus'])
    player['gold'] += int(coins)
    print('getFranchiseDailyBonus:',franchiseType,', Reward:',coins)
    save(userId)
    
    
def handleVisitorHelp(userId,params):
    print("handleVisitorHelp")
    if userId not in users:
        return
    player = users[userId]['userInfo']['player']
    helpType = params[1]
    print('Handling Visitor Help',helpType)
    coins = 0
    rep = 0
    goods = 0
    vars = settings['farming']
    match helpType:
        case 'plotHarvest':
            rep = vars['@friendVisitPlotRepGain']
            goods = vars['@friendHelpDefaultGoodsReward']
        case 'businessSendTour':
            rep = vars['@friendVisitBusinessRepGain']
            coins = vars['@friendHelpDefaultCoinReward']                        
        case 'wildernessClear':
            rep = vars['@friendVisitWildernessRepGain']
            coins = vars['@friendHelpDefaultCoinReward']
        case 'residenceCollectRent':
            rep = vars['@friendVisitResidenceRepGain']
            coins = vars['@friendHelpDefaultCoinReward']
        case _:
            print('Unknown visitor help type:',helpType)
    player['gold'] += int(coins)
    checkSocialLevel(player,int(rep))
    player['socialXp'] += int(rep)
    player['commodities']['storage']['goods'] += int(goods)
    if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
        player['commodities']['storage']['goods'] = users[userId]['storageMax']
    save(userId)

def checkSocialLevel(player,amount):
    print("checkSocialLevel")
    currentRep = player['socialXp']
    newRep = currentRep + amount
    print(currentRep,newRep)
    repLevels = settings['reputation']['level']
    for level in repLevels:
        required = int(level['@requiredXP'])
        num = int(level['@num'])
        reward = int(level['@reward'])
        if currentRep < required and newRep >= required:
            print('Social Level Up!: New Level =',num,', Bonus goods =',reward)
            player['socialLevel'] = num
            player['commodities']['storage']['goods'] += int(reward)
        if newRep < required:
            break
    
    
def placeOrder(userId,params):
    print("placeOrder")
    data = params[0]

    orderType = data['orderType']
    orderAction = 'sent'
    orderStatus = 'accepted'
    recipient = data['recipientID']

    player = users[userId]['userInfo']['player']

    print('Place Order:',orderType,',',orderAction,',',orderStatus,',',recipient)

    if 'Orders' not in player:
        player['Orders'] = {}
    if orderType not in player['Orders']:
        player['Orders'][orderType] = {}
    if orderAction not in player['Orders'][orderType]:
        player['Orders'][orderType][orderAction] = {}
    if orderStatus not in player['Orders'][orderType][orderAction]:
        player['Orders'][orderType][orderAction][orderStatus] = {}
            
    player['Orders'][orderType][orderAction][orderStatus][recipient] = data

    (coins, goods) = getTrainReward(userId,data)
    if coins > 0:
        coins = 0
    if goods > 0:
        goods = 0
    player['gold'] += coins
    player['commodities']['storage']['goods'] += goods
    if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
        player['commodities']['storage']['goods'] = users[userId]['storageMax']
    print('Train Sent: Coins:',coins,'Goods',goods)
    save(userId)
        
    
def getTrainGoodsPrice(trainName,action):
    print("getTrainGoodsPrice")
    price = 50.0
    if trainName in items:
        trainItem = items[trainName]
        if action == 'buy':
            price = float(trainItem['trainBuyPrice'])
        elif action == 'sell':
            price = float(trainItem['trainSellPrice'])
    return price

def getTrainReward(userId,order):
    print("getTrainReward")
    amount = order['amountFinal']
    name = order['trainItemName']
    action = order['orderAction']
    price = getTrainGoodsPrice(name,action)
    coins = 0
    goods = 0
    if action == 'sell':
        coins = int(amount * price)
        goods = -amount
    elif action == 'buy':
        coins = -int(amount * price)
        goods = amount
    return (coins,goods)

def collectTrainReward(userId,order):
    print("collectTrainReward")
    (coins, goods) = getTrainReward(userId,order)
    if coins < 0:
        coins = 0
    if goods < 0:
        goods = 0
    player = users[userId]['userInfo']['player']
    player['gold'] += coins
    player['commodities']['storage']['goods'] += goods
    if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
        player['commodities']['storage']['goods'] = users[userId]['storageMax']    
    print('Train Finished: Coins:',coins,'Goods',goods)
    save(userId)

def stats(userId):
    print("stats")
    player = users[userId]['userInfo']['player']
    coins = player['gold']
    cash = player['cash']
    goods = player['commodities']['storage']['goods']
    xp = player['xp']
    energy = player['energy']
    print('Coins:',coins,'Cash:',cash,'Energy:',energy,'Goods:',goods,'XP:',xp)
        

def completeTrainOrders(userId):
    print('Completing Train Orders')
    player = users[userId]['userInfo']['player']
    if 'Orders' not in player:
        return
    if 'order_train' not in player['Orders']:
        return
    trainOrders = player['Orders']['order_train']
    for _, orderAction in trainOrders.items():
        for _, orderStatus in orderAction.items():
            for _, recipient in orderStatus.items():
                collectTrainReward(userId,recipient)
    trainOrders.clear()
    save(userId)
        
def welcomeTrain(userId,params):
    print("welcomeTrain")
    order = params[0]
    welcomeAmount = order['amountFinal']
    player = users[userId]['userInfo']['player']
    player['commodities']['storage']['goods'] += welcomeAmount
    if player['commodities']['storage']['goods'] > users[userId]['storageMax']:
        player['commodities']['storage']['goods'] = users[userId]['storageMax']
    print('Addeded welcome train goods:',welcomeAmount)
    save(userId)
        
        
def handleStreak(userId,params):
    print("handleStreak")
    coins = params[0]['amount']
    player = users[userId]['userInfo']['player']
    player['gold'] += coins
    print('Streak bonus:',coins)
    save(userId)
        

def updateEnergyInternal(userId):
    print("updateEnergyInternal")
    regenSeconds = 300 # strictly speaking, should read this from game config
    player = users[userId]['userInfo']['player']
    levelNum = str(player['level'])
    energyMax = 12
    for level in settings['levels_cv_level_regrade_var_0']['level']:
        if level['@num'] == levelNum:
            energyMax = int(level['@energyMax'])
            break
    # print('Energy Max:',energyMax)
    energy = int(player['energy'])
    currEnergyCheck = (timestamp() // regenSeconds) * regenSeconds
    if energy < 0:
        energy = 0
    if energy < energyMax:
        lastEnergyCheck = 0
        if 'lastEnergyCheck' in player:
            lastEnergyCheck = int(player['lastEnergyCheck'])
        duration = currEnergyCheck - lastEnergyCheck
        energy += (duration // regenSeconds)
        if energy > energyMax:
            energy = energyMax
    player['energy'] = energy
    player['energyMax'] = energyMax
    player['lastEnergyCheck'] = currEnergyCheck
    
   
def updateEnergy(userId):
    print("updateEnergy")
    updateEnergyInternal(userId)
    player = users[userId]['userInfo']['player']
    gamedata = { 'energy': player['energy'], 'energyMax': player['energyMax'], 'lastEnergyCheck': player['lastEnergyCheck'] }
    metadata = { 'gamedata': gamedata }
    print('UpdateEnergy:',gamedata)
    return metadata

def buyEnergy(userId,params):
    print("buyEnergy")
    energyName = params[0]
    player = users[userId]['userInfo']['player']
    cost = int(items[energyName]['cash'])
    energy = int(items[energyName]['energyRewards'])
    player['energy'] += energy
    player['cash'] -= cost
    save(userId)
    print('Battery purchase.  Energy added:',energy)
        

def bonusApplies(bonus,targetClass):
    print("bonusApplies")
    if len(bonus['allowedType']) == 1:
        return bonus['allowedType']['@type'] == targetClass
    
    for allowedType in bonus['allowedType']:
        if allowedType['@type'] == targetClass:
            return True
    return False
    
def itemWithinRadius(item,target,radius):
    print("itemWithinRadius")

    itemData = items[item['itemName']]
    itemX = float(item['position']['x'])
    itemY = float(item['position']['y'])
    itemWidth = float(itemData['sizeX'])
    itemHeight = float(itemData['sizeY'])
    itemCenterX = itemX + itemWidth * 0.5
    itemCenterY = itemY + itemHeight * 0.5

    targetData = items[target['itemName']]
    targetX = float(target['position']['x'])
    targetY = float(target['position']['y'])
    targetWidth = float(targetData['sizeX'])
    targetHeight = float(targetData['sizeY'])
    targetCenterX = targetX + targetWidth * 0.5
    targetCenterY = targetY + targetHeight * 0.5
    
    # print(itemX,itemY,itemWidth,itemHeight)
    # print(targetX,targetY,targetWidth,targetHeight)
    
    distX = abs(itemCenterX - targetCenterX)
    distY = abs(itemCenterY - targetCenterY)
    allowedX = radius + (itemWidth + targetWidth) / 2
    allowedY = radius + (itemHeight + targetHeight) / 2
    # print(distX,distY)
    return distX < allowedX and distY < allowedY

def getBonus(userId,target,rewardType):
    print("getBonus")
    result = 1
    targetClass = items[target['itemName']]['@type']
    worldObjects = users[userId]['userInfo']['world']['objects']
    for object in worldObjects:
        name = object['itemName']
        itemData = items[name]
        if 'bonuses' in itemData:
            for i in itemData['bonuses']:
                bonus = itemData['bonuses'][i]
                if rewardType != bonus['@field'] and rewardType != 'all':
                    continue
                radius = float(bonus['@radius'])
                if bonusApplies(bonus,targetClass) and itemWithinRadius(object,target,radius):
                    percent = int(bonus['@percentModifier']) / 100.0
                    result += percent
    if result > 1:
        print('Bonus Modifier:',format((result-1), ".0%"))
    return result

def buyConsumable(userId,params):
    print('buyConsumable',params)
    itemName = params[0]
    amount = params[1]
    inventoryAdd(userId,itemName,amount,False)
    item = items[itemName]
    # print(item)
    player = users[userId]['userInfo']['player']
    if 'cost' in item:
        cost = int(item['cost'])
        player['gold'] -= amount * cost
        print('Bought consumable for',(amount*cost))
    elif 'cash' in item:
        cash = int(item['cash'])
        player['cash'] -= amount * cash
        print('Bought',amount,'of',itemName,'for',(amount*cash))
    save(userId)
    
    
def purchaseCrewMember(userId,params):
    print("purchaseCrewMember")
    objectId = params[0]
    if 'crews' not in users[userId]:
        users[userId]['crews'] = {}    
    crews = users[userId]['crews']
    if str(objectId) in crews:
        crews[str(objectId)].append("-1")
    else:
        crews[str(objectId)] = ["-1"]
        
    item = getObjectById(userId,objectId)
    itemName = item["itemName"]
    if "targetBuildingName" in item:
        itemName = item["targetBuildingName"]
    itemData = items[itemName]
    print(itemData)
    gate = itemData['gates']['gate'][0] # TODO: Check why items returns a list
    print(gate)
    cash = 1 # technically should be settings\farming\crewMemberCashCost
    if '@cashCost' in gate['key']:
        cash = int(gate['key']['@cashCost'])
    player = users[userId]['userInfo']['player']
    player['cash'] -= cash 
    print('Purchased crew member for cash:',cash)
    save(userId)
    
    

def payCash(userId,amount):
    print("payCash")
    player = users[userId]['userInfo']['player']
    player['cash'] -= amount
    # save performed by parent function, not required here

def createGates(itemData):
    print("createGates")
    result = []
    # print('Create Gates')
    gateData = itemData['gates']['gate'][0] # TODO: Check why items returns a list
    if '@type' in gateData and gateData['@type'] == 'crew':
        count = gateData['key']['@amount']
        gate = { 'type': 'crew', 'keys': { 'required_crew' : count } }
        result.append(gate)
    else:
        gate = {'type': 'inventory', 'keys': {} }
        print(gateData)
        if not type(gateData["key"]) == list:
            gateData = [gateData["key"]]
        else:
            gateData = gateData["key"]
        for key in gateData:
            print(key)
            name = key['@name']
            amount = int(key['@amount'])
            gate['keys'][name] = amount
        result.append(gate)
    return result
    
def franchiseOnSupply(userId,params):
    print("franchiseOnSupply")
    franchiseName = params[0]
    locationId = params[1]
    franchise = None
    franchises = users[userId]['franchises']
    for franchiseType in franchises:
        if franchiseType['name'] == franchiseName:
            franchise = franchiseType['locations'][locationId]
    
    if franchise == None:
        print(franchiseName,locationId,'not found')
        return

    franchise['time_last_supplied'] = timestamp()
    coins = franchise['money_collected'] # TODO: floor(moneyCollected * percent/100)
    item = items[franchiseName]
    goods = int(item['commodityReq']) // 2
    player = users[userId]['userInfo']['player']
    player['gold'] += coins
    player['commodities']['storage']['goods'] -= goods
    save(userId)
    print('Supplied franchise with',goods,'goods and received',coins,'coins')
    # return { 'star_rating': newStarRating }  // only used for friend spam
    
    