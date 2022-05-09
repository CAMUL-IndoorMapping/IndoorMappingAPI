from email.mime import base
from flask import Flask, request, jsonify, send_from_directory, abort, session, url_for
import json
import mysql.connector
import os
import re
from decouple import config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer
import secrets
from os.path import exists
import base64

app = Flask(__name__)
app.secret_key = config('APP_SECRET_KEY')

# Email configurations
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'camulisep2022@gmail.com'
app.config['MAIL_PASSWORD'] = config('EMAIL_PASS')
mail = Mail(app)

tokenSerial = URLSafeTimedSerializer(app.config['SECRET_KEY'])

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
  
  if "loggedin" not in session:
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
    queryString = "SELECT email, password FROM user WHERE email=%s"  
    cursor.execute(queryString, (credentials['email'],))
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
        # Log user in
        session["loggedin"] = True
        session["email"] = myresult[0][0]
        return jsonify({"status" : "success"})
  else:
    return jsonify({"status" : "unauthorized - a user is already logged in"})


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

  # Database connection
  db     = db_connection()
  mydb   = db["mydb"]
  cursor = db["mycursor"]

  # User input validation
  if not credentials["name"] or not credentials["email"] or not credentials["password"]:
    return jsonify({"status":"bad request - missing parameters"})

  # SQL Query to obtain all emails
  queryString = "SELECT email FROM user WHERE email=%s"  
  cursor.execute(queryString, (credentials['email'],))
  myresult = cursor.fetchall()

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
    if len(myresult)>0:
      return jsonify({"status":f"bad request - email already exists ({credentials['email']})"})
    else:

      # Encrypt the password using sha256
      encryptedPassword = generate_password_hash(credentials['password'], method='sha256')

      # Register the new user into the database
      queryString = "INSERT INTO user (name, password, email, idRole) VALUES(%s, %s, %s, 1)"
      cursor.execute(queryString, (credentials['name'], encryptedPassword, credentials['email'],))
      mydb.commit()

      # Log the newly created user in
      session["loggedin"] = True
      session["email"] = credentials['email']

      return jsonify({"status":"account created successfully"})


@app.route("/account/forgot", methods=["GET"])
@app.route("/account/forgot/<resetToken>", methods=["POST"])
def accountForgot(resetToken=None):
  """
  Allows user to recover their lost password. Allows GET and POST methods.
    GET -> Receives an email to which a message will be sent with a link to insert the new password
    POST -> Allows the user to insert the new password, updating the database

  Endpoints: /account/forgot
             /accout/forgot/<token>

  Parameters: 
    GET -> email: User email.
    POST -> email: User email.
            password: User's new password.

  Returns: 
          200 OK ( {"status" : "success"} )
          400 Bad Request ( {"status" : "bad request"} )
  """

  if request.method=="GET":
    # Get the JSON containing the user input
    credentials=request.get_json()

    # User input validation
    if not credentials["email"]:
      return jsonify({"status":"bad request - missing parameters"})
  
    # Database connection
    db     = db_connection()
    mydb   = db["mydb"]
    cursor = db["mycursor"]

    # Check if email exists
    queryString = "SELECT email FROM user WHERE email=%s"  
    cursor.execute(queryString, (credentials['email'],))
    results = cursor.fetchall()

    if len(results)<1:
      return jsonify({"status":"bad request - email does not exist"})

    # Send email with link to recover password
    email = str(credentials['email'])

    token = tokenSerial.dumps(email, salt='reset_password')

    def send_reset_email(email):

      msg = Message('Password Reset Request', sender=('ISEP Indoor Mapping', "test@gmail.com"), recipients=[email])

      #url = f"http://127.0.0.1:5000/account/forgot/{token}"
      url = url_for('accountForgot', resetToken=token, _external=True)
      msg.body = f'''To reset your password, visit the following link:\n{url}\nIf you did not make this request then simply ignore this email and no changes will be made.'''
                  
      mail.send(msg)

    send_reset_email(email)
    return jsonify({"status": f"success - sent email to {email}"})

  if request.method=="POST":

    # Get the JSON containing the user input
    credentials=request.get_json()

    # User input validation
    if resetToken == None:
      return jsonify({"status":f"bad request - missing token - {resetToken}"})

    if not credentials["password"]:
      return jsonify({"status":"bad request - missing parameters"})
  
    # Database connection
    db     = db_connection()
    mydb   = db["mydb"]
    cursor = db["mycursor"]

    try:
      email = tokenSerial.loads(resetToken, salt='reset_password', max_age=3600) # Expires after 1 hour
      encryptedPassword = generate_password_hash(credentials["password"])

      queryString = "UPDATE user SET password =%s WHERE email=%s"  
      cursor.execute(queryString, (encryptedPassword, credentials['email'],))
      mydb.commit()
    except:
      return jsonify({"status":f"bad request - token expired {resetToken}"})

    return jsonify({"status":f"success - {email} password updated"})


@app.route("/account/logout", methods=["PUT"])
def accountLogout():
  """
  Logs the current user out.

  Endpoint: /account/logout

  Returns: 200 OK ( {"status" : "success"} )
           401 Unauthorized ( {"status" : "unauthorized"} )
  """
  
  # Checks if the user is logged in
  if "loggedin" in session:
    # Deletes the session cookie
    session.pop('loggedin', None)
    session.pop('email', None)
    return jsonify({"status" : "success"})
  else:
    return jsonify({"status" : "unauthorized - no logged in user"})


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
  """ 
  Returns all waypoints

  :return: The list of waypoints
  :rtype: list[waypoint]
  """
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT * FROM waypoint")

  myresult = mycursor.fetchall()

  retorno=[]
  for x in myresult:
    retorno.append({"idPath":x[0], "x":x[1],"y":x[2],"z":x[3]})

  return jsonify(retorno)


@app.route("/search/classrooms/<id>", methods=["GET"])
def searchClassrooms(id):
  """ 
  Returns the classroom with the id inserted

  :return: classroom object
  :rtype: object[classroom]
  """
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT * FROM classroom WHERE id = '%s' ;" % id)  

  myresult = mycursor.fetchall()

  retorno=[]
  for x in myresult:
    retorno.append({"id":x[0], "name":x[1],"occupancy":x[2],"image":x[3],"idDepartment":x[4]})

  return jsonify(retorno)

@app.route("/search/departments/<id>", methods=["GET"])
def searchDepartments(id):
  """ 
  Returns the department with the id inserted

  :return: department object
  :rtype: object[department] 
  """

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT * FROM department WHERE id = '%s' ;" % id)
  
  myresult = mycursor.fetchall()

  retorno=[]
  for x in myresult:
    retorno.append({"id":x[0], "designation":x[1]})

  return jsonify(retorno)



# andre m.
@app.route("/map/waypoint", methods=["POST"])
def placeWaypoint():
  """
  Parameters: 
    idPath -> id do path a que pertence o waypoint
    x -> coordenada X no mapa
    y -> coordenada Y no mapa
    z -> andar do edificio
  
  Headers:
    Content-Type: application/json
    authToken: <session token>
  """

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
  """ 
  Parameters:
    beaconFrom -> id do beacon de partida
    beaconTo -> id do beacon de chegada
  Headers:
    authToken: <session token>
    Content-Type: application/json
  """

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
  """
  Parameters POST: 
    type -> text ou image ou video ou audio
    content -> ficheiro em base64 ou texto normal. o plain text em base64 não pode ter o seguinte texto, nem nada que se assemelhe: data:image/png;base64, 
    idUser -> id do utilizador que está a fazer o upload
    idBeacon -> id do beacon
  Parameters GET:
    idUser (optional)
  Headers:
    authToken: <session token>
    Content-Type: application/json
  
  NOTA: PARA ACEDER AOS UPLOADS, USAR O ENDPOINT: /uploads/nomedoficheiro.ext 
  """

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if request.method=="GET":
    sql_query="SELECT id, idBeacon, content, idUser, type FROM note"
    params=()

    if request.args.get("idUser"):
      sql_query+=" WHERE idUser=%s"
      params=(int(request.args.get("idUser")),)

    print(sql_query)
    mycursor.execute(sql_query, params)
    myresult = mycursor.fetchall()

    notes=[]
    for x in myresult:
      notes.append({"id":x[0], "idBeacon":x[1], "content":x[2], "idUser":x[3], "type":x[4]})

    return jsonify({"feedback":notes})

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
  """
    endpoint: /uploads/<nome do ficheiro>
  """
  try:
    return send_from_directory("uploads/", filename)
  except FileNotFoundError:
    abort(404)


# francisco (não te esqueças que tens de receber o header com o token de autenticação)
""" @app.route("/account/delete", methods=["DELETE"])
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

  return jsonify({}) """


if __name__ == "__main__":
  app.run(debug=True)