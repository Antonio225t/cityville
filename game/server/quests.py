import xmltodict
import json
import copy
from pathlib import Path
import os.path

import users
import questUtil

START_QUEST = 'q_rename_city'

progress = {}
quests = {}

def init():
    global quests
    with open('../client/questSettings.xml') as f:
        xml_string = f.read()
    xml_dict = xmltodict.parse(xml_string)
    quests = xml_dict["quests"]['quest']
    print('Quests found:', len(quests))
    initUsers()
    
def initUsers():
    global progress
    dir = Path('users')
    i = 0
    for subdir in dir.iterdir():
        userId = subdir.stem
        filename = str(subdir) + '/progress.json'
        if not os.path.exists(filename):
            continue
        with open(filename) as file:
            data = json.load(file)
        progress[userId] = data
        i += 1
    print('Progress files found:',i)

def save(userId):
    filename = 'users/' + userId + '/progress.json'
    data = progress[userId]
    # print(data)
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def getQuests(userId):
    if userId not in progress:
        print('Creating new progress file for:',userId)
        progress[userId] = createprogress()
        save(userId)
    currentQuests = getCurrent(userId,4)
    data = { "QuestComponent": currentQuests }
    handleQuestProgress(userId,['pingFeedQuests'])
    print('Feeding quests:',currentQuests)
    return data

def getCurrent(userId, limit):
    quests = list(progress[userId]['active'].values())
    result = []
    for quest in quests:
        questCopy = copy.deepcopy(quest)
        result.append(questCopy)
        if len(result) >= limit:
            break
    return result

def purchaseQuestProgress(userId, info):
    questName = info[0]
    task = info[1]
    if userId not in progress:
        return
    currentQuests = progress[userId]['active'].values()
    status = None
    for active in currentQuests:
        if active['name'] == questName:
            status = active
            break;
    if status == None:
        print(questName,'not active')
        return
    status['purchased'][task] = 1    
    quest = findQuest(questName)
    tasks = getTasks(questName)
    cost = 0
    if len(tasks) > task and '@cashcost' in tasks[task]:
        cost = int(tasks[task]['@cashcost'])
        users.payCash(userId,cost)
    print('Purchased:',questName,'Task:',task,'Cash:',cost)
    if checkQuestCompletion(status,quest):
        completeQuest(userId,quest)

def createprogress():
    # pending is for quests where requirement is not yet met.
    data = {
    # 'active': { 'q_rename_city': createQuest('q_rename_city') },
    'active': { START_QUEST: createQuest(START_QUEST) },
    'completed': [],
    'pending': [],
    }
    return data


def createQuest(name):    
    length = len(getTasks(name))
    return {
        "name": name,
        "complete": 0,
        "progress": [0] * length,
        "purchased": [0] * length,
    };

def getTasks(name):
    quest = findQuest(name)
    if quest == None:
        print('Quest',name,'not found')
        return []
    if type(quest['tasks']['task']) is list:
        tasks = quest['tasks']['task']
    else:
        tasks = [quest['tasks']['task']]
    return tasks
    
def updateProgress(userId,quest,status,transaction):
    # print(quest)
    tasks = getTasks(quest['@name'])
    for i in range(len(tasks)):
        task = tasks[i]
        if '@action' not in task:
            continue
        taskTotal = int(task['@total'])
        if status['progress'][i] >= taskTotal:
            continue
        # print('Checking quest', quest['@name'], task['@action'])
        progress = 0
        if status['purchased'][i]:
            progress = taskTotal
        else:
            action = getattr(questUtil,task['@action'])
            progress = action(userId, transaction, task['@type'])
        if task['@sticky'] == 'true':
            progress += status['progress'][i]        
        status['progress'][i] = progress        


def handleQuestProgress(userId,transaction):
    if userId not in progress:
        return
    currentQuests = progress[userId]['active'].values()
    completed = []
    for status in currentQuests:
        name = status['name']
        quest = findQuest(name)
        if quest == None or status['complete'] == 1:
            continue
        updateProgress(userId,quest,status,transaction)
        # print(status)
        if checkQuestCompletion(status,quest):
            completed.append(quest)
    for quest in completed:
        completeQuest(userId,quest)
    if len(completed) > 0:
        # if we completed a quest, run once more to check if the new quests are already completed
        handleQuestProgress(userId,transaction)
    save(userId)


def checkQuestCompletion(status,quest):
    tasks = getTasks(quest['@name'])
    for i, task in enumerate(tasks):
        if status['purchased'][i]:
            continue
        if status['progress'][i] < int(task['@total']):
           return False           
    return True

            
def getSequels(quest):
    result = []
    if 'sequels' not in quest:
        return result
    sequel = quest['sequels']['sequel']
    # print(sequel)
    if type(sequel) is list:
        for quest in sequel:
            result.append(quest['@name'])
        return result
    return [sequel['@name']]
    

def awardQuestRewards(userId,quest):
    rewards = getRewards(quest)
    print('Quest Rewards:',rewards)
    users.giveRewards(userId,rewards,True);


def getRewards(quest):
    if 'resourceModifiers' not in quest:
        return {}
    if 'questRewards' not in quest['resourceModifiers']:
        return {}
    rewards = quest['resourceModifiers']['questRewards']
    if type(rewards) is list:
        result = {}
        for reward in rewards:
            for element in reward.keys():
                result[element] = reward[element]
        return result
    return rewards


def completeQuest(userId,quest):
    name = quest['@name']
    print('Completing',name)
    if name not in progress[userId]['active']:
        print('Quest not found:', name)
        return
    progress[userId]['active'].pop(name)
    progress[userId]['completed'].append(name)
    quest = findQuest(name)
    awardQuestRewards(userId,quest)
    sequels = getSequels(quest)
    print('Sequel Quests:',sequels)
    # print(progress[userId]['active'])
    for sequel in sequels:
        newStatus = createQuest(sequel)
        # if meets requirements:
        progress[userId]['active'][sequel] = newStatus
        # else add to pending
    # print(progress[userId]['active'])
    

def findQuest(name):
    for q in quests:
        if q['@name'] == name:
            return q
    return None
    
def findStartingQuests(level):
    result = []
    for q in quests:
        if '@spawns_from' in q and q['@spawns_from'] == "noparent":
            if '@level_block' in q and int(q['@level_block']) > level:
                continue
            if '@worlds' in q and q['@worlds'] == "world_downtown":
                continue # downtown not supported in this version :(
            result.append(q['@name'])
    return result

