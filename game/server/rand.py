import hashlib
from ast import literal_eval

import users

# WARNING: this is not decoupled from users.py.  Requires users.init() to be called first.
# TODO: Special case 'holiday_tree_2010' not working


HARD_CODED_SECRET = 'YOUR_LIKE_AN_8'
secretHandshake = ''

def rand(userId, min, max):
    # TODO: move side effect changes to roll counter outta here...
    rollCounter = users.users[userId]['userInfo']['player']['rollCounter']
    rollCounter += 1
    s = HARD_CODED_SECRET + '::' + secretHandshake + "::" + userId + "::" + str(rollCounter)
    hash = hashlib.md5(s.encode('utf-8'))
    hexString = '0x' + hash.hexdigest()[:8]
    hexValue = literal_eval(hexString)        
    range = max - min + 1
    val = hexValue % range + min
    users.users[userId]['userInfo']['player']['rollCounter'] = rollCounter
    return val


def generateDoobers(userId, itemName, randomModifierGroup=None):
    item = users.items[itemName]
    return processRandomModifiers(userId, item,'', randomModifierGroup)
        
def processRandomModifiers(userId, item, resource, randomModifierGroup=None):
    # TODO: handle bonuses here

    dooberTypes = []
    dooberYields = []
    if 'coinYield' in item:
        dooberTypes.append('coin')
        dooberYields.append(item['coinYield'])
    if 'xpYield' in item:
        dooberTypes.append('xp')
        dooberYields.append(item['xpYield'])
    if 'goodsYield' in item:
        dooberTypes.append('goods')
        dooberYields.append(item['goodsYield'])
    if "populationYield" in item:
        dooberTypes.append("population")
        dooberYields.append(item["populationYield"])
    
    randomModifiers = []
    secureRand = []
    if 'randomModifierGroups' in item:
        groups = item["randomModifierGroups"]["group"]
        if type(groups) != list:
            groups = [groups]
        for group in groups:
            print(randomModifierGroup)
            if group["@name"] == randomModifierGroup:
                randModNames = group["modifiers"]
                if type(randModNames) != list:
                    randModNames = [randModNames]
                
                secureRand = [rand(userId, 0, 99)]
                prevRollPercent = 0
                for roll in randModNames:
                    if '@percent' not in roll:
                        continue
                    rollPercent = float(roll['@percent']) + prevRollPercent
                    prevRollPercent = rollPercent
                    if secureRand[0] < rollPercent:
                        for randMod in item["randomModifiers"]:
                            if randMod["@name"] == roll["@name"]:
                                randomModifiers = [randMod]
                                break
    else:
        randomModifiers = item["randomModifiers"]
        if type(randomModifiers) != list:
            randomModifiers = [randomModifiers]
    
    if len(randomModifiers) < 1:
        print(f"Error: Random Modifier table is empty, probably coulsn't find the '{randomModifierGroup}' group!")
    
    return processRandomModifiersConfig(userId, randomModifiers, dooberTypes, dooberYields, secureRand)

def processRandomModifiersConfig(userId, randomModifiers, dooberTypes, dooberModifiers, secureRands):
    result = []
    
    for modifiers in randomModifiers:
        modifiers = modifiers['modifier']
        if type(modifiers) is list:
            modifiers = modifiers
        else:
            modifiers = [modifiers]
        for modifier in modifiers:
            secureRand = rand(userId,0,99)
            secureRands.append(secureRand)
            
            print("Modifier:")
            print(modifier)
            if modifier['@tableName'] == 'colltable': # No collectables for this item
                continue            
            if modifier['@tableName'] not in users.randomTables:
                print('Missing random table:',modifier['@tableName'])
                continue
            modifierTable = users.randomTables[modifier['@tableName']]
            itemType = modifierTable['@type']
            rolls = []
            if type(modifierTable['roll']) is list:
                rolls = modifierTable['roll']
            else:
                rolls.append(modifierTable['roll'])
            
            prevRollPercent = 0
            for roll in rolls:
                # print(roll)
                if '@percent' not in roll:
                    continue
                rollPercent = float(roll['@percent']) + prevRollPercent
                prevRollPercent = rollPercent
                if secureRand < rollPercent:
                    if type(roll[itemType]) is list:
                        items = roll[itemType]
                    else:
                        items = [roll[itemType]]
                    for item in items:
                        print(roll)
                        print(item)
                        if itemType == 'collectable':
                            dooberType = 'collectable'
                            quantity = item['@name']
                        else:
                            dooberType = itemType
                            quantity = float(item['@amount']) if "@amount" in item else 1
                        result.append([dooberType,quantity])
                    break;
    return [result,secureRands]
            

def chooseRandomModifiersXML(item, randomModifiers, randomModifierName):
    randomModifier = randomModifiers[randomModifierName]
    runningTotalPercent = 0
    secureRand = rand(0,99)
    for modifier in randomModifier['modifiers']:
        rollPercent = float(modifier['@percent'])
        runningTotalPercent += rollPercent
        if secureRand < runningTotalPercent:
            selectedModifier = modifier['@name']
            break
    
        
        


    