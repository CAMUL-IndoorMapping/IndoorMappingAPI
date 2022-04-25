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

@app.route("/<name>")
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

  return jsonify(retorno)


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
def searchBeacon():
  return jsonify({})


@app.route("/map/beacons", methods=["POST"])
def placeBeacon():
  return jsonify({})


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
  # Content-Type: application/json
  # Parameters: 
  #   idPath -> id do path a que pertence o waypoint
  #   x -> coordenada X no mapa
  #   y -> coordenada Y no mapa
  #   z -> andar do edificio
  # authToken: <session token>

  parameters=request.get_json()

  if not parameters["idPath"] or not parameters["x"] or not parameters["y"] or not parameters["z"] or not request.headers.get("authToken"):
    return jsonify({"status":"missing parameter(s)"})

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT user.id FROM user INNER JOIN role ON user.idRole=role.id WHERE authToken=%s AND role.name='admin'", (request.headers.get("authToken"), ))
  myresult = mycursor.fetchall()

  if len(myresult)>0:
    mycursor.execute("INSERT INTO waypoint(idPath, x, y, z) VALUES (%s, %s, %s, %s)", (int(parameters["idPath"]), parameters["x"], parameters["y"], parameters["z"]))
    mydb.commit()

    return jsonify({"status":"success"})

  return jsonify({"status":"no permission"})
  


@app.route("/map/path", methods=["POST"])
def placePath():
  # Content-Type: application/json
  # Parameters:
  #   beaconFrom -> id do beacon de partida
  #   beaconTo -> id do beacon de chegada
  # authToken: <session token>

  parameters=request.get_json()

  if not parameters["beaconFrom"] or not parameters["beaconTo"] or not request.headers.get("authToken"):
    return jsonify({"status":"missing parameter(s)"})

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT user.id FROM user INNER JOIN role ON user.idRole=role.id WHERE authToken=%s AND role.name='admin'", (request.headers.get("authToken"), ))
  myresult = mycursor.fetchall()

  if len(myresult)>0:
    mycursor.execute("INSERT INTO path(idBeacon_From, idBeacon_To) VALUES (%s, %s)", (int(parameters["beaconFrom"]), int(parameters["beaconTo"]) ))
    mydb.commit()

    return jsonify({"status":"success"})

  return jsonify({"status":"no permission"})


@app.route("/account/feedback", methods=["GET", "POST"])
def feedback():
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if request.method=="GET":
    pass

  if request.method=="POST":
    pass

  return jsonify({"status":"success"})


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