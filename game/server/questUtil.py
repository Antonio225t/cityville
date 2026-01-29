import users

def onValidCityName(userId, transaction, questName):
    if transaction[0] == 'onValidCityName':
        return 1
    return 0
      
def seenQuest(userId, transaction, questName):
    if transaction[0] == 'seenQuest' and transaction[1] == questName:
        return 1
    return 0
      
def popNews(userId, transaction, questName):
    if transaction[0] == 'popNews' and transaction[1] == questName:
        return 1
    return 0

def sendTrain(userId, transaction, resource):
    if transaction[0] == 'placeInitialOrder':
        return 1
    return 0


def welcomeTrain(userId, transaction, itemType):
    if transaction[0] == 'welcomeTrain':
        return 1
    return 0
    
def countHeadquarters(userId, transaction, itemType):
    objects = users.getObjectsByClass(userId,'Headquarter')
    return len(objects)
    
def countPlayerResourceByType(userId,transaction,playerResource):
    match playerResource:
        case "coin":
            return users.getGold(userId)
        case "xp":
            return users.getXP(userId)
        case "goods":
            return users.getGoods(userId)
        case "population":
            # if(!Global.isVisiting() && !Global.isTransitioningWorld)
            return users.getPopulation(userId)
        case "neighbors":
            return users.getNeighborCount(userID)
    return 0;

def neighborVisit(userId,transaction,recipient):
    if transaction[0] == 'neighborVisit':
        if recipient == '' or recipient == None or recipient == transaction[1]['recipientId']:
            return 1
    return 0

def citySamHQ(userId,transaction,targetId):
    if targetId == None:
        targetId = '-1'  # fake user
    return users.getFranchiseCountByLocation(userId,targetId)

def placeBuildingByName(userId,transaction,name):
    return countTransactionByNameHelper('place',transaction,name)

def countPlayerMapExpansions(userId,transaction,resource):
    return users.getExpansions(userId)



def harvestByClass(userId, transaction, classType):
    return countTransactionByClassHelper('harvest',transaction,classType)

def harvestBusinessByName(userId, transaction, name):
    return countTransactionByNameHelper('harvest',transaction,name)
 
def countFranchiseExpansionsByName(userId,transaction, name):
    if name == None or name == '':
        return users.getAllFranchiseAcceptedLocationsCount(userId)
    return users.getFranchiseAcceptedLocationsCount(userId,name)

def countCollectableByName(userId,transaction,name):
    return users.getCollectableCount(userId,name)
    
def countTransactionByClassHelper(action, transaction, className):    
    if transaction[0] != action:
        return 0
    
    worldObject = transaction[1]
    if worldObject == None:
        return 0   
        
    if worldObject['className'] == className:
        return 1
    return 0



def openBusinessByName(userId,transaction, name):
    return countTransactionByNameHelper('openBusiness',transaction,name);


def startContractByClass(userId, transaction, className):
    return countTransactionByClassHelper('startContract',transaction,className);

def harvestBusinessByClass(userId,transaction,className):
    return countTransactionByClassHelper('harvest',transaction,className)
      
def harvestResidenceByName(userId,transaction,name):
    return countTransactionByNameHelper('harvest',transaction,name)

def placeByClass(userId,transaction, className):
    return countTransactionByClassHelper('place',transaction,className);

      
def visitorHelp(userId,transaction, helpType):
    print(transaction)
    print(helpType)
    if transaction[0] == 'visitorHelp' and transaction[1] == helpType:
       return 1
    return 0

def countWorldObjectByName(userId, transaction, name):
    objects = users.getObjectsByName(userId,name)
    result = len(objects)
    return result;

def countConstructionOrBuildingByName(userId, transaction, name):
    result = 0    
    targets = []
    sites = users.getObjectsByClass(userId,'ConstructionSite')
    for site in sites:
        if site['targetBuildingName'] == name:
            targets.append(site)
    result += len(targets)
    result += len(users.getObjectsByName(userId,name))
    return result

def clearByClass(userId,transaction,className):
    return countTransactionByClassHelper("clear",transaction,className);

def harvestPlotByName(userId,transaction,name):
    return countTransactionByContractNameHelper('harvest',transaction,name);

def countTransactionByNameHelper(action, transaction, itemName):    
    if transaction[0] != action:
        return 0
    
    worldObject = transaction[1]
    if worldObject == None:
        return 0   
        
    if worldObject['itemName'] == itemName:
        return 1
    return 0


def countTransactionByContractNameHelper(action, transaction, name):
    if transaction[0] != action:
        return 0
    
    worldObject = transaction[1]
    if worldObject == None:
        return 0
    
    if 'contractName' in worldObject and worldObject['contractName'] == name:
        return 1
    return 0

def consumeItemsAtInit(userId, transaction, itemName):
    result = 0
    if transaction[0] == 'pingFeedQuests':
        result = users.inventoryCount(userId,itemName)
        if result > 0:
            users.inventoryRemove(userId, itemName,result);
    return result

def sendFranchiseSupply(userId, transaction, data):
    if transaction[0] == 'onSupply':
        if data is None or data == '':
            return 1
        elif transaction[1] == data:
            return 1
    return 0
    
def moveByName(userId, transaction, name):
    return countTransactionByNameHelper('move',transaction,name);


def countNewNeighbors(userId, transaction, name):
    print('TODO: implement countNewNeighbors')
    return 10
    return 0