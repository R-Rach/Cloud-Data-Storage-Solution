import os, random, json, datetime
from crush import Crush


def readData(userId,zk,readQuorom=2):
	
    c = Crush()
    c.parse(json.loads(zk.get('/crushmap')[0]))


    main_data_node_list = zk.get_children("/main_data")

    partition_num = c.map(rule="data", value=int(userId), replication_count=1)[0]
    print("partition num--> "+str(partition_num) + "   for userid = " + userId)
    print("readdata ALL NODE LIST------ "+str(main_data_node_list) + "   for userid = " + userId)
    random.shuffle(main_data_node_list)
    # pick any @readQuorom nodes
    rq_nodelist = main_data_node_list[:readQuorom]
    stale_nodelist = main_data_node_list[readQuorom:]
    print("readdata NODE LIST after read_quorom------ "+str(rq_nodelist) + "   for userid = " + userId)
    print("readdata STALE NODE LIST after read_quorom------ "+str(stale_nodelist) + "   for userid = " + userId)

    #call read repair
    read_repair(rq_nodelist, stale_nodelist, partition_num, userId, zk)

    # now rq_nodelist nodes are updated, fetch data from any one of @rq_nodelist
    mainNode_filename = get_filename(rq_nodelist[0], partition_num, zk) + ".json"
    prev_content = ''
    total_data = ''

    with open(mainNode_filename, 'r') as file:
        prev_content = file.read()
        if prev_content != '':
            total_data = json.loads(prev_content)
        else:
            total_data = {}

    if userId not in total_data:
        return "User not present"
    else:
        # return json.dumps(total_data[userId])
        return total_data[userId]



def writeData(operation, userId, item, itemCount, zk, writeQuorom=2):
    
    path = "/users/"+userId
    zk.ensure_path(path)

    timestamp = str(datetime.datetime.now())

    c = Crush()
    c.parse(json.loads(zk.get('/crushmap')[0]))

    main_data_node_list = zk.get_children("/main_data")

    partition_num = c.map(rule="data", value=int(userId), replication_count=1)[0]
    print("partition num--> "+str(partition_num) + "   for userid = " + userId)
    print("writedata ALL NODE LIST------ "+str(main_data_node_list) + "   for userid = " + userId)
    random.shuffle(main_data_node_list)
    # pick any @writeQuorom nodes
    wq_nodelist = main_data_node_list[:writeQuorom]
    print("writedata NODE LIST after write_quorom------ "+str(wq_nodelist) + "   for userid = " + userId)

    # writing to _trans.json files
    for node_num in wq_nodelist:
        tempNode_filename = get_filename(node_num, partition_num, zk) + "_temp.json"
        prev_content = ''
        total_data = ''

        # for _trans.json files
        with open(tempNode_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                total_data = {}

        with open(tempNode_filename, 'w') as file:
            if operation == 'add':
                if userId not in total_data:
                    total_data[userId] = {}
                total_data[userId][timestamp] = [item, int(itemCount), operation]
                json.dump(total_data,file, indent=4, sort_keys=True)

            elif operation == 'update':
########### CALL read repair before it or user must call '/list' before update or delete calls
                lastest_user_cart = getRecentUserCartData(wq_nodelist, partition_num, userId, zk)

                if item in lastest_user_cart:
                    if userId not in total_data:
                        total_data[userId] = {}
                    total_data[userId][timestamp] = [item, int(itemCount), operation]
                    json.dump(total_data,file, indent=4, sort_keys=True)
                else:
                    return str(userId)+" can't update item that is not there in his cart."


            elif operation == 'delete':
########### CALL read repair or user must call /list before update or delete calls
                lastest_user_cart = getRecentUserCartData(wq_nodelist, partition_num, userId, zk)  #its a dict

                if item in lastest_user_cart:
                    if userId not in total_data:
                        total_data[userId] = {}
                    total_data[userId][timestamp] = [item, int(0), operation]
                    json.dump(total_data,file, indent=4, sort_keys=True)
                else:
                    return "Item: "+ str(item)+" not present for the user: "+str(userId) + " so cannot delete."

    if operation == "add":
        return 'Added item: '+ str(item) + ' with quantity: ' + str(itemCount) + ' for user ' + str(userId) + ' ||timestamp ' + timestamp
    elif operation == 'delete':
        return "Deleted item: "+str(item) + ' for user ' + str(userId)
    elif operation == 'update':
        return 'Updated item: '+ str(item) + ' to COUNT: ' + str(itemCount) + ' for user ' + str(userId)



def read_repair(rq_nodelist, stale_nodelist, partition_num, userId, zk):

    userid_merged_trans = {}

    # get all transaction of user in _trans files and merge them
    for node_num in rq_nodelist:
        tempNode_filename = get_filename(node_num, partition_num, zk) + "_temp.json"
        prev_content = ''
        total_data = ''

        with open(tempNode_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                continue

        if userId in total_data:
            userid_merged_trans.update(total_data[userId])
            total_data.pop(userId,None)
            with open(tempNode_filename, 'w') as file:
                json.dump(total_data,file, indent=4, sort_keys=True)

    # if userid_merged_trans == {}:
    # 	return

    # EXAMPLE for some userid --> userid_merged_trans = {'2020-11-25 14:30:34.165003': ['clock', 120, 'add'], '2020-11-25 14:29:51.172149': ['clock', 12, 'add'], '2020-11-25 14:29:58.047497': ['clock', 111, 'add']}

    # delete stale transactions from leftover list
    for node_num in stale_nodelist:
        tempNode_filename = get_filename(node_num, partition_num, zk) + "_temp.json"
        prev_content = ''
        total_data = ''

        with open(tempNode_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                continue

        if userId in total_data:
        	total_data.pop(userId,None)
        	with open(tempNode_filename, 'w') as file:
        		json.dump(total_data,file, indent=4, sort_keys=True)

    # get most recent userid cart from main json file
    lastest_user_cart = getRecentUserCartData(rq_nodelist, partition_num, userId, zk)

    # insert new transactions in latest user cart
    for i in sorted(userid_merged_trans.keys()):
        # here key is items
        key = userid_merged_trans[i][0]
        if key in lastest_user_cart:
            if userid_merged_trans[i][2] == "add":
                # FOR SEC INDEX
                writeSecondaryIndex(userId=userId, item=key, new_itemCount=userid_merged_trans[i][1], prev_count=lastest_user_cart[key], operation="add", zk=zk)

                new_count = int(userid_merged_trans[i][1]) + int(lastest_user_cart[key])
                lastest_user_cart[key] = int(new_count)

            elif userid_merged_trans[i][2] == "update":
                # FOR SEC INDEX
                writeSecondaryIndex(userId=userId, item=key, new_itemCount=userid_merged_trans[i][1], prev_count=lastest_user_cart[key], operation="update", zk=zk)

                lastest_user_cart[key] = int(userid_merged_trans[i][1])

            elif userid_merged_trans[i][2] == "delete":
                # FOR SEC INDEX
                writeSecondaryIndex(userId=userId, item=key, new_itemCount=userid_merged_trans[i][1], prev_count=lastest_user_cart[key], operation="delete", zk=zk)

                lastest_user_cart.pop(key, None)

        if key not in lastest_user_cart:
            if userid_merged_trans[i][2] == "add":
                # FOR SEC INDEX
                writeSecondaryIndex(userId=userId, item=key, new_itemCount=userid_merged_trans[i][1], prev_count=0, operation="add", zk=zk)

                lastest_user_cart[key] = int(userid_merged_trans[i][1])

    timestamp = str(datetime.datetime.now())
    if lastest_user_cart != {}:
    	lastest_user_cart["|last_update_time|"] = timestamp
    else:
    	return

    # write new updated user cart data back to main json file
    for node_num in rq_nodelist:
        mainNode_filename = get_filename(node_num, partition_num, zk) + ".json"
        prev_content = ''
        total_data = ''

        with open(mainNode_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                total_data = {}

        if userId not in total_data:
            total_data[userId] = {}
        total_data[userId] = lastest_user_cart

        with open(mainNode_filename, 'w') as file:
            json.dump(total_data,file, indent=4, sort_keys=True)


def get_filename(node_num, partition_num, zk):
    path = "/main_data/"+node_num+"/"+partition_num
    val = (zk.get(path)[0]).decode('utf-8')
    return val



def getRecentUserCartData(nodelist, partition_num, userId, zk):

    # get most recent userid cart from main json file
    # it'll be a dict of items as keys
    lastest_user_cart = None

    for node_num in nodelist:
        mainNode_filename = get_filename(node_num, partition_num, zk) + ".json"
        # nxpx_filename_main = os.getcwd()+"/data/main_nodes/"+nxpx+".json" 
        prev_content = ''
        total_data = ''

        with open(mainNode_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                continue

        if userId in total_data:
            if lastest_user_cart is None:
                lastest_user_cart = total_data[userId]
            else:
                if total_data[userId]["|last_update_time|"] > lastest_user_cart["|last_update_time|"]: #take latest update
                    lastest_user_cart = total_data[userId]

    if lastest_user_cart == None:
        lastest_user_cart = {}

    return lastest_user_cart



def writeSecondaryIndex(userId, item, new_itemCount, prev_count, operation, zk):

    map_val = sum(bytes(item, 'utf-8'))
    c = Crush()
    c.parse(json.loads(zk.get('/crushmap')[0]))
    secNodeList = c.map(rule="data", value=int(map_val), replication_count=1)
    
    for sec_nodes in secNodeList:

        path = "/sec_data/"+sec_nodes
        sec_filename = (zk.get(path)[0]).decode('utf-8')

        prev_content = ''
        total_data = ''

        with open(sec_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                total_data = {}

        with open(sec_filename, 'w') as file:
            if operation == 'add':
                if item not in total_data:
                    # total_data[item] = [[], 0]
                    total_data[item] = {}
                    total_data[item]["User List"] = []
                    total_data[item]["Count"] = 0
                if userId not in total_data[item]["User List"]:
                    total_data[item]["User List"].append(userId)
                new_count = int(total_data[item]["Count"]) + int(new_itemCount)
                total_data[item]["Count"] = new_count
                json.dump(total_data,file, indent=4, sort_keys=True)

            elif operation == 'update':
                if item in total_data:
                    if userId in total_data[item]["User List"]:
                        new_count = int(total_data[item]["Count"]) - int(prev_count) + int(new_itemCount)
                        total_data[item]["Count"] = new_count
                        json.dump(total_data,file, indent=4, sort_keys=True)
                else:
                    return "Seconday index update not possible, as item not present"

            elif operation == 'delete':
                if item in total_data:
                    if userId in total_data[item]["User List"]:
                        total_data[item]["User List"].remove(userId)
                        new_count = int(total_data[item]["Count"]) - int(prev_count)
                        total_data[item]["Count"] = new_count
                        json.dump(total_data,file, indent=4, sort_keys=True)
                else:
                    return "Seconday index deletion not possible, as item not present"

    return "Seconday index changed, operation = " + operation


def readSecondaryIndex(item, zk):

    map_val = sum(bytes(item, 'utf-8'))
    c = Crush()
    c.parse(json.loads(zk.get('/crushmap')[0]))
    secNodeList = c.map(rule="data", value=int(map_val), replication_count=1)
    
    for sec_nodes in secNodeList:
        path = "/sec_data/"+sec_nodes
        sec_filename = (zk.get(path)[0]).decode('utf-8')
        prev_content = ''
        total_data = ''

        with open(sec_filename, 'r') as file:
            prev_content = file.read()
            if prev_content != '':
                total_data = json.loads(prev_content)
            else:
                total_data = {}

    return total_data

