from email.mime import base
from flask import Flask, request, jsonify, send_from_directory, abort
import json
import mysql.connector
import os
from decouple import config
import secrets
from os.path import exists
import base64

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

@app.route("/")
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
    # Content-Type: application/json
    # Parameters POST: 
    #   type -> text ou image ou video ou audio
    #   content -> ficheiro em base64 ou texto normal. o plain text em base64 não pode ter o seguinte texto, nem nada que se assemelhe: data:image/png;base64, 
    #   idUser -> id do utilizador que está a fazer o upload
    #   idBeacon -> id do beacon
    # Parameters GET:
    #   idUser
    #   
    # authToken: <session token>
    #
    # NOTA: PARA ACEDER AOS UPLOADS, USAR O ENDPOINT: /uploads/nomedoficheiro.ext
  
  

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if request.method=="GET":
    pass

  if request.method=="POST":
    parameters=request.get_json()

    # verificar se os parametros de POST são válidos
    if not parameters["type"] or not parameters["content"] or not parameters["idUser"] or not parameters["idBeacon"] or not request.headers.get("authToken"):
      return jsonify({"status":"missing parameter(s)"})
    
    mycursor.execute("SELECT user.id FROM user INNER JOIN role ON user.idRole=role.id WHERE authToken=%s AND user.id=%s AND role.name='admin'", (request.headers.get("authToken"), int(parameters["idUser"]) ))
    myresult = mycursor.fetchall()

    if len(myresult)>0:
      fileFormats={"image":"jpg", "audio":"wav", "video":"mp4"}

      # a variável content vai assumir valores de texto normal ou de caminhos para o ficheiro
      content=parameters["content"]

      # verificar se está a ser feito upload de um ficheiro ou de texto livre
      if parameters["type"]!="text":

        # definir um nome para o ficheiro novo
        fileName="uploads/"+secrets.token_hex(8) + "." + fileFormats[parameters["type"]]

        # definir um nome novo para o ficheiro, no caso desse nome já existir
        while exists(fileName):
          fileName="uploads/"+secrets.token_hex(8) + "." + fileFormats[parameters["type"]]

        # converter o ficheiro em base64 para binário e guarda-lo no sistema de ficheiros
        fileBin = base64.b64decode(parameters["content"] + '==')

        f=open(fileName, "wb")
        f.write(fileBin)

        content=fileName
      else:
        content=content[:149]

      # guardar na base de dados
      mycursor.execute("INSERT INTO note(type, content, idUser, idBeacon) VALUES (%s, %s, %s, %s)", (parameters["type"], content, int(parameters["idUser"]), int(parameters["idBeacon"]) ))
      mydb.commit()

      return jsonify({"status":"success"})

  return jsonify({"status":"no permission"})


@app.route('/uploads/<filename>',methods = ['GET'])
def get_files(filename):
    try:
      return send_from_directory("uploads/", filename)
    except FileNotFoundError:
      abort(404)


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
  app.run(debug=True)