from flask import Flask, request, jsonify, session
import json
import mysql.connector
import os
import re
from decouple import config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "TOP_SECRET"

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


@app.route("/account/login", methods=["GET"])
def accountLogin():
  """
  Logs the user in.

  Endpoint: /account/login

  Parameters: 
    email: User email.
    password: User password.

  Returns: 
          200 OK ( {"status" : "success"} )
          400 Bad Request ( {"status" : "bad request"} )
          401 Unauthorized ( {"status" : "unauthorized"} )
  """

  # Get the JSON containing the user input
  credentials=request.get_json()

  # Database connection
  db     = db_connection()
  mydb   = db["mydb"]
  cursor = db["mycursor"]

  # User input validation
  if not credentials["email"] or not credentials["password"]:
    return jsonify({"status":"unauthorized - invalid credentials"})

  # Check if the input email exists (password verification is done in another step)
  cursor.execute(f"SELECT email, password FROM user WHERE email='{credentials['email']}'")
  myresult = cursor.fetchall()

  # If the email doesn't exist, we don't even bother to check if the password is correct
  if len(myresult) < 1:
    return jsonify({"status" : "unauthorized - user does not exist"})
  else:
    # If it exists, we then check if the password is correct
    # Note: The encrypted password is being returned as "bytearray(b'')", and we want what is between the '', which is what this regex returns (this could be improved)
    passwordToCheck = re.search(r'\'(.*?)\'',str(myresult[0][1])).group(1)
    if not check_password_hash(passwordToCheck, credentials["password"]):
      return jsonify({"status" : "unauthorized - invalid password"})
    else:
      # Log user in #TODO
      session["loggedin"] = True
      session["email"] = myresult[0][0]
      return jsonify({"status" : "success"})


@app.route("/account/signup", methods=["POST"])
def accountSignup():
  """
  Creates a new account.

  Endpoint: /account/signup

  Parameters: 
    name: User name.
    email: User email.
    password: User password.

  Returns: 
          200 OK ( {"status" : "success"} )
          400 Bad Request ( {"status" : "bad request"} )
  """

  # Get the JSON containing the user input
  credentials=request.get_json()

  emailExists = False

  # Database connection
  db     = db_connection()
  mydb   = db["mydb"]
  cursor = db["mycursor"]

  # SQL Query to obtain all emails
  cursor.execute("SELECT email FROM user")
  myresult = cursor.fetchall()

  # User input validation
  if not credentials["name"] or not credentials["email"] or not credentials["password"]:
    return jsonify({"status":"bad request - missing parameters"})

  # Password must contain 8 characters, 1 capital, 1 lower case, 1 number and 1 special symbol (At least)
  pwdRegex   = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$')
  emailRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
  nameRegex  = re.compile(r'[A-Za-z]{2,}')

  if not nameRegex.match(credentials["name"]):
    return jsonify({"status":"bad request - invalid name"})
  elif not emailRegex.match(credentials["email"]):
    return jsonify({"status":"bad request - invalid email"})
  elif not pwdRegex.match(credentials["password"]):
    return jsonify({"status":"bad request - invalid password"})
  else:

    # Verify if email already exists
    for email in myresult:
      if email[0] == credentials['email']:
        print(email[0], "===", credentials['email'])
        emailExists = True

    if not emailExists:

      # Encrypt the password using sha256
      encryptedPassword = generate_password_hash(credentials['password'], method='sha256')

      # Register the new user into the database
      cursor.execute(f"INSERT INTO user (name, password, email, idRole) VALUES('{credentials['name']}', '{encryptedPassword}', '{credentials['email']}', 1)")
      mydb.commit()

      # Log the newly created user in
      session["loggedin"] = True
      session["email"] = credentials['email']

      return jsonify({"status":"success"})
    else:
      return jsonify({"status":"bad request - email already exists"})


@app.route("/account/forgot", methods=["GET", "POST"])
def accountForgot():
  if request.method=="GET":
    pass

  if request.method=="POST":
    pass

  return jsonify({})


@app.route("/account/logout", methods=["PUT"])
@login_required
def accountLogout():
  """
  Logs the current user out.

  Endpoint: /account/logout

  Returns: 200 OK ( {"status" : "success"} )
  """
  logout_user()
  return jsonify({"status" : "success"})


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