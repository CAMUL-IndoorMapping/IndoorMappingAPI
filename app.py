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
    # Content-Type: application/json
    # Parameters: 
    #   username -> username of the account whose password is being changed
    #   oldPassword -> old password to confirm user's auth
    #   newPassword -> new password to be set
    #
    # authToken: <session token>

    db_obj=db_connection()
    mydb=db_obj["mydb"]
    mycursor=db_obj["mycursor"]

    parameters=request.get_json()

    if not parameters["username"] or not parameters["oldPassword"] or not parameters["newPassword"] or not request.headers.get("authToken"):
      return jsonify({"status":"missing parameter(s)"})

    # Verify user
    mycursor.execute("SELECT user.id FROM user WHERE authToken=%s AND user.name=%s", (request.headers.get("authToken"), parameters["username"] ))
    myresult = mycursor.fetchall()

    if len(myresult)>0:

      mycursor.execute("SELECT user.id FROM user WHERE user.name=%s AND user.password=%s", (parameters["username"], parameters["oldPassword"] ))
      myresult = mycursor.fetchall()

      if len(myresult)>0:
        mycursor.execute("UPDATE user SET user.password=%s WHERE user.name=%s AND user.password=%s", (parameters["newPassword"], parameters["username"], parameters["oldPassword"]))
        mydb.commit()

        return jsonify({"status":"success"})

      return jsonify({"status":"wrong password"})
    
    return jsonify({"status":"no permission"})


@app.route("/account/reviews", methods=["GET", "POST"])
def accountReviews():
    # Content-Type: application/json
    # Parameters POST: 
    #   idUser -> id of the user attempting to post a review
    #   body -> text to be included in said review
    #
    # Parameters GET:
    #   None
    #   
    # authToken: <session token>
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if request.method=="GET":
    mycursor.execute("SELECT user.name, review.text FROM review INNER JOIN user ON review.idUser=user.id")

    myresult = mycursor.fetchall()

    resultList=[]
    for result in myresult:
      resultList.append({"username":result[0], "review":result[1]})

    return jsonify(resultList)

  if request.method=="POST":
    parameters=request.get_json()

    if not parameters["idUser"] or not parameters["body"] or not request.headers.get("authToken"):
      return jsonify({"status":"missing parameter(s)"})

    # Verify user
    mycursor.execute("SELECT user.id FROM user WHERE authToken=%s AND user.id=%s", (request.headers.get("authToken"), int(parameters["idUser"]) ))
    myresult = mycursor.fetchall()

    if len(myresult)>0:
      mycursor.execute("INSERT INTO review(idUser, text) VALUES (%s, %s)", (int(parameters["idUser"]), parameters["body"]))
      mydb.commit()

      return jsonify({"status":"success"})
    
    return jsonify({"status":"no permission"})
  return jsonify({})


if __name__ == "__main__":
  app.run()