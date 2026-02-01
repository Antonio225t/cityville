from flask import Flask, request, send_file, Response
from pyamf import remoting
from datetime import datetime
import pyamf
import json
import os.path

import users
import quests

writeStats = False
CLIENT_DIR = '../client'

def timestamp():
    return datetime.now().timestamp()
    

users.init()
quests.init()

app = Flask(__name__)


@app.route('/')
def hello():
    return send_file('go.html')

@app.route('/record_stats.php', methods=['POST'])
@app.route('/127.0.0.1record_stats.php', methods=['POST'])
def stats():
    print('Stats Received')
    if writeStats:
        with open('stats.txt', 'a') as file:
            json.dump(request.get_json(), file, indent=4)
    return ''

@app.route('/error.php', methods=['POST'])
@app.route('/127.0.0.1error.php', methods=['POST'])
def post_error():
    print('Error Received')
    if writeStats:
        with open('error.txt', 'a') as file:
            json.dump(request.get_json(), file, indent=4)
    # print(request.get_json())
    return ''

@app.route('/dataServices.php', methods=['POST'])
def post_data_services():
    print("DataService Recieved")
    print(request.data)
    return ""

@app.route('/flashservices/gateway.php', methods=['POST'])
def post_gateway():
    resp_msg = remoting.decode(request.data)        
    responses = []
    userId = resp_msg.bodies[0][1].body[0]['zyUid']
    
    for req in resp_msg.bodies[0][1].body[1]:        
        print(req)
        match req.functionName:
            case 'UserService.initUser':
                responses.append(userResponse(userId))

            case 'UserService.initNeighbors':
                responses.append(neighborResponse(userId))

            case 'UserService.getZEventCount':
                responses.append(zCount(userId))

            case 'QuestService.requestManualQuest':
                responses.append(questResponse(userId,req.params))

            case 'UserService.pingFeedQuests':
                quests.handleQuestProgress(userId,['pingFeedQuests'])
                responses.append(feedQuests(userId))

            case 'UserService.setCityName':
                responses.append(setCityNameResponse(userId,req.params[1]))

            case 'UserService.checkForNewNeighbors':
                responses.append(dummy_response(userId))                

            case 'UserService.updateTopFriends':
                responses.append(dummy_response(userId))            

            case 'UserService.seenQuest':
                quests.handleQuestProgress(userId,req.params);
                responses.append(dummy_response(userId))

            case 'WorldService.performAction':
                data = users.performAction(userId,req.params)
                quests.handleQuestProgress(userId,req.params)
                responses.append(performAction(userId,data))

            case 'WorldService.loadWorld':
                responses.append(visit(userId,req.params))

            case 'UserService.onValidCityName':
                quests.handleQuestProgress(userId,['onValidCityName'])
                responses.append(dummy_response(userId))

            case 'UserService.popNews':
                quests.handleQuestProgress(userId,req.params)
                responses.append(dummy_response(userId))

            case 'UserService.saveOptions':
                users.updateOptions(userId,req.params)
                responses.append(dummy_response(userId))

            case 'UserService.completeTutorial':
                users.completedTutorial(userId)
                responses.append(dummy_response(userId))

            case 'VisitorService.initialVisit':
                quests.handleQuestProgress(userId,req.params)
                responses.append(initialVisit(userId))

            case 'VisitorService.help':
                users.handleVisitorHelp(userId,req.params)
                quests.handleQuestProgress(userId,req.params)
                responses.append(dummy_response(userId))

            case 'TrainService.completeWelcomeTrainOrder':
                users.welcomeTrain(userId,req.params)
                quests.handleQuestProgress(userId,['welcomeTrain',req.params])
                responses.append(dummy_response(userId))
            
            case 'TrainService.placeInitialOrder':
                users.placeOrder(userId,req.params)
                quests.handleQuestProgress(userId,['placeInitialOrder',req.params])
                responses.append(dummy_response(userId))

            case 'TrainService.completeAllSentOrders':
                users.completeTrainOrders(userId)
                responses.append(dummy_response(userId))                

            case 'UserService.purchaseQuestProgress':
                quests.purchaseQuestProgress(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'FarmService.expandCity':
                data = users.expandCity(userId,req.params)
                responses.append(wrap(userId,data))

            case 'UserService.processVisitsBatch':
                users.handleVisits(userId,req.params)
                responses.append(dummy_response(userId))

            case 'UserService.acquireLicense':
                data = users.acquireLicense(userId,req.params)
                responses.append(wrap(userId,data))

            case 'UserService.acquirePermit':
                data = users.acquirePermit(userId,req.params)
                responses.append(wrap(userId,data))

            case 'FranchiseService.onSupply':
                users.franchiseOnSupply(userId,req.params)
                quests.handleQuestProgress(userId,['onSupply',req.params])
                responses.append(dummy_response(userId))
            
            case 'FranchiseService.updateFranchiseName':
                users.updateFranchiseName(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'FranchiseService.onCollectDailyBonus':
                users.getFranchiseDailyBonus(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'UserService.onReplaceUserResource':
                users.replaceUserResource(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'UserService.streakBonus':
                users.handleStreak(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'UserService.updateEnergy':
                metadata = users.updateEnergy(userId)
                responses.append(wrap(userId,{},metadata))
            
            case 'UserService.buyEnergy':
                users.buyEnergy(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'CollectionsService.onTradeIn':
                users.collectionTradeIn(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'UserService.buyConsumable':
                users.buyConsumable(userId,req.params)
                responses.append(dummy_response(userId))
            
            case 'UserService.purchaseCrewMember':
                users.purchaseCrewMember(userId,req.params)
                responses.append(dummy_response(userId))
            
            case _:
                print("Unknown request:")
                print(req)
                responses.append(dummy_response(userId))
        
    emsg = {
        "serverTime": timestamp(),
        "errorType": 0,
        "data": responses
    }

    req = remoting.Response(emsg)
    ev = remoting.Envelope(pyamf.AMF0)
    ev[resp_msg.bodies[0][0]] = req
    ret_body = remoting.encode(ev, strict=True, logger=True).getvalue()  # .read()
    return Response(ret_body, mimetype='application/x-amf')

@app.route("/snapi/<path:path>")
def snapi(path):
    print("SNAPI get")
    print(path)
    return ""

@app.route('/<path:path>')
def send_sol_assets_alternate(path):
    try:
        return send_file(os.path.join(CLIENT_DIR,path))
    except:
        print(f"Could not find asset: '{path}'!")
        return send_file(os.path.join(CLIENT_DIR, "assets", "noimage.png"))

def dummy_response(userId):
    dummy_response = {"errorType": 0, "userId": userId, "metadata": {"newPVE": 0}, "data": [], "serverTime": timestamp()}
    return dummy_response

def wrap(userId,data,meta = {}):
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": data, "serverTime": timestamp()}
    return user_response

def zCount(userId):
    msg = { "count": 0 } 
    meta = {}
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": msg, "serverTime": timestamp()}
    return user_response

def initialVisit(userId):
    msg = { "energyLeft": 4 } 
    meta = {}
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": msg, "serverTime": timestamp()}
    return user_response
    

def userResponse(userId):
    user = initUser(userId)
    meta = {}
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": user, "serverTime": timestamp()}
    return user_response

def questResponse(userId,quest):
    print('Quest Started:',quest[0])
    data = { "questStarted": 1 } 
    if quest[0] == 'holiday_tree1':
        data = { "questStarted": 0 } 
    meta = {}
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": data, "serverTime": timestamp()}
    return user_response
    
def setCityNameResponse(userId, newName):
    data = users.renameCity(userId, newName) 
    meta = {}
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": data, "serverTime": timestamp()}
    return user_response    

def visit(userId, params):
    visitId = params[0]
    data = users.getUser(visitId)['userInfo']
    data['franchises'] = [] 
    meta = {}
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": data, "serverTime": timestamp()}
    return user_response    

def feedQuests(userId):
    quest = { } 
    meta = quests.getQuests(userId)
    user_response = {"errorType": 0, "userId": userId, "metadata": meta, "data": quest, "serverTime": timestamp()}
    return user_response

# workaround for too many neighbours issue.    
first = True

def neighborResponse(userId):
    global first
    meta = {}
    neighbors = { "neighbors": [] }
    neighbors = { "neighbors": [ { "uid": -1, "fake": 1}, { "uid": 3}, {"uid": 4}, {"uid": 5}, {"uid": 6} ] }
    response = {"errorType": 0, "userId": userId, "metadata": meta, "data": neighbors, "serverTime": timestamp()}
    if not first:
        return {}
    first = False
    return response

def performAction(userId,data):
    meta = {}        
    response = {"errorType": 0, "userId": userId, "metadata": meta, "data": data, "serverTime": timestamp()}
    return response

def initUser(userId):
    global first
    first = True
    user = users.getUser(userId)
    return user

