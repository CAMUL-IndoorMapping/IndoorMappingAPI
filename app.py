from flask import Flask, request, jsonify
import json
import mysql.connector
import os
from decouple import config

app = Flask(__name__)

def db_connection():

  mydb = mysql.connector.connect(
    host=config('DB_HOST'),
    user=config('DB_USER'),
    password=config('DB_PASSWORD'),
    database=config('DB_DATABASE')
  )

  mycursor = mydb.cursor()

  return {"mydb":mydb, "mycursor":mycursor}

#Message #backend


"""@app.route("/<name>")
def hello(name):
  obj1={"key":"value", "key2":"valye2"}
  obj3={}
  obj2={}

  lista = [1,2,3,4,5]
  lista2 = ["oal", "adeus", "byebye"]
  lista3 = [obj1, obj2, obj3]
  lista4 = [lista, lista2, lista3]

  for x in lista:
    print(x)

  for x in lista4:
    for y in x:
      print(y)

  lista = [x for x in range(1,6)] #list compreension
  print(lista)

  return jsonify(obj1)

@app.route("/beacons/<id>")
def beacon(id):
  #conection to database
  return jsonify({""})

@app.route("/beacons", methods=["POST"])
def beaconInsert():
  nome = request.json["nome"]

  print(nome)
  #conection to database
  return "criei o beacon " + nome

@app.route("/2", methods=["POST"])
def hello2():
  return "Hello World 2!"

@app.route("/reviews", methods=["GET"])
def getReviews():
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT user.name, review.text FROM review INNER JOIN user ON review.idUser=user.id")

  myresult = mycursor.fetchall()

  retorno=[]
  for x in myresult:
    retorno.append({"userName":x[0], "review":x[1]})

  return jsonify(retorno)"""


# vitor (não te esqueças que vais ter de receber o auth token no header de alguns requests)
@app.route("/account/login", methods=["GET"])
def accountLogin():
  return jsonify({})


@app.route("/account/signup", methods=["POST"])
def accountSignup():
  return jsonify({})


@app.route("/account/forgot", methods=["GET", "POST"])
def accountForgot():
  if request.method=="GET":
    pass

  if request.method=="POST":
    pass

  return jsonify({})


@app.route("/account/logout", methods=["PUT"])
def accountLogout():
  return jsonify({})


# ancre g.
@app.route("/search/beacons/<id>", methods=["GET"])
def searchBeacon(id):

  #Connect to database
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  #Variavels
  query_string="SELECT * FROM beacon WHERE id=%s"

  #Execute search cammand
  mycursor.execute(query_string, (id,))

  #Save result 
  myresult=mycursor.fetchall()

  #Cheaking if it exists
  if len(myresult) > 0:
    return jsonify({"status":"Not Found - This beacon was not found"})

  #Beacon array
  beacons=[]
  for x in myresult:
    beacons.append({"idDevice":x[1], "IdClassroom":x[2], "x":x[3], "y":x[4], "z":x[5]})

  return jsonify({"feedback":beacons[0]})


@app.route("/map/beacons", methods=["POST"])
def placeBeacon():

  #Connect to database
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  #Get data from request
  parameters=request.get_json()

  #Check if parameters where inputed correctly
  if not parameters["idDevice"] or not parameters["IdClassroom"] or not parameters["x"] or not parameters["y"] or not parameters["z"]:
    return jsonify({"status":"bad request - missing parameters"})
  

  #MySQL cammand
  query_string="INSERT INTO beacon (idDevice, IdClassroom, x, y, z) VALUES (%s, %s, %s, %s, %s)"
  """search_idclassroom_query="SELECT IdClassroom FROM beacon WHERE IdClassroom=%s"
  check_iddevice_query="SELECT idDevice FROM beacon"""
  query_getData="SELECT * FROM beacon"

  #Get Data
  mycursor.execute(query_getData)
  myresult=mycursor.fetchall()

  #Check if beacon exists
  for y in myresult:
    print(y)
    if y[1] == parameters["idDevice"]:
      return jsonify({"status":"bad request - This device already is being use"})
    elif y[3] == parameters["x"] and y[4] == parameters["y"] and y[5] == parameters["z"]:
      return jsonify({"status":f"bad request - A beacon with these coordinates x:({parameters['x']}), y:({parameters['y']}) and z:({parameters['z']}) already exists"})
  
  #Execute insert cammand
  mycursor.execute(query_string, (parameters["idDevice"], int(parameters["IdClassroom"]), parameters["x"], parameters["y"], parameters["z"]))
  mydb.commit()

  #Check if the new beacon was added
  query_confirm_id="SELECT id FROM beacon WHERE idDevice=%s AND IdClassroom=%s"
  mycursor.execute(query_confirm_id, (parameters["idDevice"], int(parameters["IdClassroom"])))
  mysearchresult=mycursor.fetchall()

  #Check if it was found
  if len(mysearchresult) < 1:
    return jsonify({"status":"Error - Beacon wasn't haded"})
  
  
  return jsonify({"feedback": mysearchresult[0]})


# daniel
@app.route("/search/waypoints", methods=["GET"])
def searchWaypoint():
  return jsonify({})


@app.route("/search/classrooms/<id>", methods=["GET"])
def searchClassrooms():
  return jsonify({})


@app.route("/search/departments/<id>", methods=["GET"])
def searchDepartments():
  return jsonify({})


# andre m.
@app.route("/map/waypoint", methods=["POST"])
def placeWaypoint():
  return jsonify({})


@app.route("/map/path", methods=["POST"])
def placePath():
  return jsonify({})


@app.route("/account/feedback", methods=["GET", "POST"])
def feedback():
  if request.method=="GET":
    pass

  if request.method=="POST":
    pass

  return jsonify({})


# francisco (não te esqueças que tens de receber o header com o token de autenticação)
@app.route("/account/delete", methods=["DELETE"])
def accountDelete():
  return jsonify({})


@app.route("/account/change", methods=["PUT"])
def accountChange():
  return jsonify({})


@app.route("/account/reviews", methods=["GET", "POST"])
def accountReviews():
  if request.method=="GET":
    pass

  if request.method=="POST":
    pass

  return jsonify({})


if __name__ == "__main__":
  app.run()