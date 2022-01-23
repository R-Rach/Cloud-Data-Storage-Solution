import argparse, json, datetime, os

from flask import Flask, request, Response, jsonify
from kazoo.client import KazooClient, KazooState
from read_write import readData, writeData, readSecondaryIndex

# To handle looger for kazoo client
import logging
logging.basicConfig()


# Defining crushmap
# crushmap = """
# {
#   "trees": [
#     {
#       "type": "root", "name": "dc1", "id": -1,
#       "children": [
#         {
#          "type": "host", "name": "host0", "id": -2,
#          "children": [
#           { "id": 0, "name": "n1p1", "weight": 65536 },
#           { "id": 1, "name": "n1p2", "weight": 65536 }
#          ]
#         },
#         {
#          "type": "host", "name": "host1", "id": -3,
#          "children": [
#           { "id": 2, "name": "n2p1", "weight": 65536 },
#           { "id": 3, "name": "n2p2", "weight": 65536 }
#          ]
#         },
#         {
#          "type": "host", "name": "host2", "id": -4,
#          "children": [
#           { "id": 4, "name": "n3p1", "weight": 65536 },
#           { "id": 5, "name": "n3p2", "weight": 65536 }
#          ]
#         }
#       ]
#     }
#   ],
#   "rules": {
#     "data": [
#       [ "take", "dc1" ],
#       [ "chooseleaf", "firstn", 0, "type", "host" ],
#       [ "emit" ]
#     ]
#   }
# }
# """

crushmap = """
{
  "trees": [
    {
      "type": "root", "name": "dc1", "id": -1,
      "children": [
        { "id": 0, "name": "p1", "weight": 65536 },
        { "id": 1, "name": "p2", "weight": 65536 },
        { "id": 2, "name": "p3", "weight": 65536 }
      ]
    }
  ],
  "rules": {
    "data": [
      [ "take", "dc1" ],
      [ "chooseleaf", "firstn", 1, "type", "root" ],
      [ "emit" ]
    ]
  }
}
"""



app = Flask(__name__)

@app.route('/')
def hello():
   return 'Server Up and Running!'


@app.route('/listusercart', methods=['GET', 'POST'])
def listUserCart():
    if request.form.get('userId') == None or request.form.get('userId') == "":
      response = jsonify("Please enter user id.")
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response
    else:
      userId = str(request.form["userId"])
      response = jsonify(readData(userId, zk))
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response


@app.route('/additems', methods=['GET', 'POST'])
def addUserItems():
    if request.form.get('userId') == None or request.form.get('userId') == "" or request.form.get('item') == None or request.form.get('item') == "" or request.form.get('itemCount') == None or request.form.get('itemCount') == "":
      response = jsonify("Please enter userId, item and itemCount in request form data.")
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response
    else:
      userId = str(request.form["userId"])
      item = str(request.form["item"])
      itemCount = int(request.form["itemCount"])
      response = jsonify(writeData("add", userId, item, itemCount, zk))
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response


@app.route('/deleteitems', methods=['GET', 'POST'])
def deleteUserItems():
    if request.form.get('userId') == None or request.form.get('userId') == "" or request.form.get('item') == None or request.form.get('item') == "":
      response = jsonify("Please enter userId, item in request form data.")
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response
    else:
      userId = str(request.form["userId"])
      item = str(request.form["item"])
      response = jsonify(writeData("delete", userId, item, None, zk))
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response


@app.route('/updateitems', methods=['GET', 'POST'])
def updateUserItems():
    if request.form.get('userId') == None or request.form.get('userId') == "" or request.form.get('item') == None or request.form.get('item') == "" or request.form.get('itemCount') == None or request.form.get('itemCount') == "":
      response = jsonify("Please enter userId, item and itemCount in request form data.")
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response	
    else:
      userId = str(request.form["userId"])
      item = str(request.form["item"])
      itemCount = int(request.form["itemCount"])
      response = jsonify(writeData("update", userId, item, itemCount, zk))
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response


@app.route('/adminlistusers', methods=['GET', 'POST'])
def adminListUsers():
    userIdList = zk.get_children("/users")
    output = {}
    for userId in userIdList:
        output[userId] = readData(str(userId), zk)
    response = jsonify(output)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/adminitems', methods=['GET', 'POST'])
def adminListSecondaryIndex():
    if request.form.get('item') == None or request.form.get('item') == "":
      response = jsonify("Please enter item in request form data.")
      response.headers.add('Access-Control-Allow-Origin', '*')
      return response 
    else:
      item = str(request.form["item"])
      total_data = readSecondaryIndex(item, zk)
      if item in total_data:
        response = jsonify(total_data[item])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
      else:
        response = jsonify("Item " + item + " not present.")
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/clearallfiles', methods=['GET', 'POST'])
def clearAllFiles():

  if zk.exists("/users"):
    userIdList = zk.get_children("/users")
    for userId in userIdList:
      node = "/users/"+userId
      zk.delete(node)

  for i in range(1,4):
    for j in range(1,4):
      open(os.getcwd()+"/data/main_data/n"+str(i)+"/p"+str(j)+"_temp.json", 'w').close()
      open(os.getcwd()+"/data/main_data/n"+str(i)+"/p"+str(j)+".json", 'w').close()
  for i in range(1,4):
    open(os.getcwd()+"/data/secondary_data/p"+str(i)+"_sec.json", 'w').close()

  response = jsonify("ALL FILES CLEARED")
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response


zk = KazooClient(hosts='zookeeper:2181')
zk.start()

# delete users nodes is exists, before starting the application
if zk.exists("/users"):
	userIdList = zk.get_children("/users")
	for userId in userIdList:
		node = "/users/"+userId
		zk.delete(node)

# reinitalise crushmap
if zk.exists("/crushmap"):
	zk.delete("/crushmap")
zk.create("/crushmap",bytes(crushmap, 'utf-8'))

num_nodes = 3
num_partition = 3
# INITIALLY WE HAVE 3 NODES (1 main and 2 replicas), EACH NODE HAVE 3 partitions to store the data
#reinitialise it first, befor starting application... DELETE ALL FIRST
if zk.exists("/main_data"):
  for i in range(1, num_nodes+1):
    for j in range(1, num_partition+1):
      partition = "/main_data/n"+str(i)+"/p"+str(j)
      if zk.exists(partition):
        zk.delete(partition)
    node = "/main_data/n"+str(i)
    if zk.exists(node):
      zk.delete(node)
  zk.delete("/main_data")

for i in range(1, num_nodes+1):
  zk.ensure_path("/main_data/n"+str(i))
  for j in range(1, num_partition+1):
    data_path = os.getcwd()+"/data/main_data/n"+str(i)+"/p"+str(j)
    node = "/main_data/n"+str(i)+"/p"+str(j)
    zk.create(node, bytes(data_path, 'utf-8'))


num_sec_nodes = 3
# there is 3 nodes to store sec index data, reinitialise it
if zk.exists("/sec_data"):
  for i in range(1, num_sec_nodes+1):
    sec_node = "/sec_data/p"+str(i)
    if zk.exists(sec_node):
      zk.delete(sec_node)
  zk.delete("/sec_data")

for i in range(1, 4):
  zk.ensure_path("/sec_data")
  sec_data_path = os.getcwd()+"/data/secondary_data/p"+str(i)+"_sec.json"
  sec_node = "/sec_data/p"+str(i)
  zk.create(sec_node, bytes(sec_data_path, 'utf-8'))


if __name__ == '__main__':

	# arg parse for different instance run
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', '--port', type=int, default=5000)
  args = parser.parse_args()

  app.run(host = '0.0.0.0', port = args.port, debug = True)




# crushmap = """
# {
#   "trees": [
#     {
#       "type": "root", "name": "dc1", "id": -1,
#       "children": [
#         {
#          "type": "host", "name": "host0", "id": -2,
#          "children": [
#           { "id": 0, "name": "n1p1", "weight": 65536 },
#           { "id": 1, "name": "n1p2", "weight": 65536 },
#           { "id": 2, "name": "n1p3", "weight": 65536 }
#          ]
#         },
#         {
#          "type": "host", "name": "host1", "id": -3,
#          "children": [
#           { "id": 3, "name": "n2p1", "weight": 65536 },
#           { "id": 4, "name": "n2p2", "weight": 65536 },
#           { "id": 5, "name": "n2p3", "weight": 65536 }
#          ]
#         },
#         {
#          "type": "host", "name": "host2", "id": -4,
#          "children": [
#           { "id": 6, "name": "n3p1", "weight": 65536 },
#           { "id": 7, "name": "n3p2", "weight": 65536 },
#           { "id": 8, "name": "n3p3", "weight": 65536 }
#          ]
#         }
#       ]
#     }
#   ],
#   "rules": {
#     "data": [
#       [ "take", "dc1" ],
#       [ "chooseleaf", "firstn", 0, "type", "host" ],
#       [ "emit" ]
#     ]
#   }
# }
# """