from email.mime import base
from flask import Flask, request, jsonify, send_from_directory, abort, session, url_for, render_template
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
import jwt
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__, template_folder='./docs/_build/html', static_folder='./docs/_build/html/_static')
cors = CORS(app, resources={r"*": {"origins": "*"}})
app.secret_key = config('APP_SECRET_KEY')
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

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
    database=config('DB_DATABASE'),
    port='3306'
  )

  mycursor = mydb.cursor()

  return {"mydb":mydb, "mycursor":mycursor}


def checkUserAdmin(authToken):
  db_obj=db_connection()
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT user.id FROM user INNER JOIN role ON user.idRole=role.id WHERE authToken=%s AND role.name='admin'", (authToken,))
  myresult = mycursor.fetchall()

  if len(myresult)>0:
    return True

  return False

@app.route("/docs", methods=["GET"])
@app.route("/docs/", methods=["GET"])
@app.route("/docs/<filename>", methods=["GET"])
def docs(filename="index.html"):
  return render_template(filename)


@app.route("/docs/_modules", methods=["GET"])
@app.route("/docs/_modules/", methods=["GET"])
@app.route("/docs/_modules/<filename>", methods=["GET"])
def docsModules(filename="index.html"):
  return render_template("_modules/" + filename)


@app.route("/account/login", methods=["GET"])
def accountLogin():
  """

  
    Description: Logs the user in.

    Endpoint:
    - /account/login

    Headers:
    - none

    Parameters GET:
    - email
    - password

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


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
    queryString = "SELECT email, password, authToken, id, idRole, name FROM user WHERE email=%s"
    cursor.execute(queryString, (credentials['email'],))
    myresult = cursor.fetchall()
    QUERY_EMAIL    = 0
    QUERY_PASSWORD = 1
    QUERY_TOKEN    = 2
    QUERY_ID       = 3
    QUERY_ROLE     = 4
    QUERY_USERNAME = 5

    # If the email doesn't exist, we don't even bother to check if the password is correct
    if len(myresult) < 1:
      return jsonify({"status" : "unauthorized - user does not exist"})
    else:
      # If it exists, we then check if the password is correct
      # Note: The encrypted password is being returned as "bytearray(b'')", and we want what is between the '', which is what this regex returns (this could be improved)
      passwordToCheck = re.search(r'\'(.*?)\'',str(myresult[0][QUERY_PASSWORD])).group(1)
      if not check_password_hash(passwordToCheck, credentials["password"]):
        return jsonify({"status" : "unauthorized - invalid password"})
      else:
        # Generate new AuthToken
        payload = {
                  'exp': datetime.utcnow() + timedelta(days=0, seconds=5),
                  'iat': datetime.utcnow(),
                  'sub': credentials['email']
                  }
        authToken = jwt.encode(
                  payload,
                  config('APP_SECRET_KEY'),
                  algorithm='HS256'
                  )

        # Return payload
        if myresult[0][QUERY_ROLE] == 1:
          userRole = "admin"
        elif myresult[0][QUERY_ROLE] == 2:
          userRole = "user"
        else:
          userRole = None
        currentUser = { "username": myresult[0][QUERY_USERNAME], "userID": myresult[0][QUERY_ID], "authToken": authToken, "userRole": str(userRole) }

        # Update authToken
        queryString = "UPDATE user SET authToken=%s WHERE email=%s"
        cursor.execute(queryString, (authToken,credentials['email']))

        # Log user in
        session["loggedin"] = True
        session["authToken"] = authToken
        return jsonify(currentUser)
  else:
    return jsonify({"status" : "unauthorized - a user is already logged in"})


@app.route("/account/signup", methods=["POST"])
def accountSignup():
  """


    Description: Creates a new account.

    Endpoint: 
    - /account/signup

    Headers:
    - none

    Parameters GET:
    - none

    Parameters POST:
    - name
    - email
    - password

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )


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

      # Generate AuthToken
      payload = {
                'exp': datetime.utcnow() + timedelta(days=0, seconds=5),
                'iat': datetime.utcnow(),
                'sub': credentials['email']
                }
      authToken = jwt.encode(
                payload,
                config('APP_SECRET_KEY'),
                algorithm='HS256'
                )

      # Register the new user into the database
      queryString = "INSERT INTO user (name, password, email, idRole, authToken) VALUES(%s, %s, %s, 1, %s)"
      cursor.execute(queryString, (credentials['name'], encryptedPassword, credentials['email'], authToken))
      mydb.commit()

      # Log the newly created user in
      session["loggedin"] = True
      session["authToken"] = authToken

      return jsonify({"status":"account created successfully"})


@app.route("/account/forgot", methods=["GET"])
@app.route("/account/forgot/<resetToken>", methods=["POST"])
def accountForgot(resetToken=None):
  """


    Description: Allows user to recover their lost password. Allows GET and POST methods. GET -> Receives an email to which a message will be sent with a link to insert the new password. POST -> Allows the user to insert the new password, updating the database

    Endpoint: 
    - (GET) /account/forgot 
    - (POST) /accout/forgot/<token> 

    Headers:
    - none

    Parameters GET:
    - email

    Parameters POST:
    - email
    - password

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

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
      encryptedPassword = generate_password_hash(credentials["password"], method='sha256')

      queryString = "UPDATE user SET password=%s WHERE email=%s"
      cursor.execute(queryString, (encryptedPassword, email))
      mydb.commit()
    except:
      return jsonify({"status":f"bad request - token expired {resetToken}"})

    return jsonify({"status":f"success - {email} password updated"})


@app.route("/account/logout", methods=["PUT"])
def accountLogout():
  """


    Description: Logs the current user out.

    Endpoint: 
    - /account/logout

    Headers:
    - none

    Parameters GET:
    - none

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

  # Checks if the user is logged in
  if "loggedin" in session:
    # Deletes the session cookie
    session.pop('loggedin', None)
    session.pop('authToken', None)
    return jsonify({"status" : "success"})
  else:
    return jsonify({"status" : "unauthorized - no logged in user"})


# andre g.
@app.route("/search/beacons/<id>", methods=["GET"])
def searchBeacon(id):
  """
      

    Description: Returns information about one specific beacon

    Endpoint: 
    - /search/beacons/<id>

    Headers:
    - none

    Parameters GET:
    - none

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"idDevice":"", "idClassroom":"", "x":"", "y":"", "z":""} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

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
  if len(myresult) == 0:
    return jsonify({"status":"Not Found - This beacon was not found"})

  #Beacon array
  beacon={}
  for x in myresult:
    beacon = {"idDevice":x[1], "idClassroom":x[2], "x":x[3], "y":x[4], "z":x[5]}

  return jsonify(beacon)


@app.route("/map/beacons", methods=["GET", "POST", "PUT"])
def beaconsOperation():
  """


    Description: returns all the beacons in the map

    Endpoint: 
    - /map/beacons
    Headers:
    - (POST / PUT) authToken

    Parameters GET:
    - none

    Parameters POST:
    - idDevice
    - IdClassroom
    - x
    - y
    - z

    Parameters PUT:
    - beaconId : mandatory
    - beaconName : optional
    - classroomId : optional
    - x : optional
    - y : optional
    - z : optional

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Unauthorized ( {"status":"bad request - missing parameters; at least 2 parameters; beaconId is mandatory"} )
    - 403 Unauthorized ( {"status":"bad request - no permission"} )


  """
  #Connect to database
  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if request.method=="GET":
    sql_query="SELECT beacon.id, beacon.idDevice, beacon.x, beacon.y, beacon.z, classroom.id, classroom.name FROM beacon INNER JOIN classroom ON classroom.id=beacon.idClassroom"
    mycursor.execute(sql_query)
    myresult=mycursor.fetchall()

    retorno=[]
    for b in myresult:
      retorno.append({"beaconId":b[0], "beaconName":b[1], "x":b[2], "y":b[3], "z":b[4], "classroomId":b[5], "classroomName":b[6]})

    if len(retorno)>0:
      return jsonify({"beacons": retorno})
    else:
      return jsonify({"status": "no beacons to show"})

  if request.method=="POST":
    #Get data from request
    parameters=request.get_json()

    # check if user is an admin
    if not request.headers.get("authToken") or not checkUserAdmin(request.headers.get("authToken")):
      return jsonify({"status":"bad request - no permission"})

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
        return jsonify({"status":"bad request - This device already is being used"})
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

    return jsonify({"beaaconId": mysearchresult[0][0]})

  if request.method=="PUT":
    parameters=request.get_json()

    # check if user is an admin
    if not request.headers.get("authToken") or not checkUserAdmin(request.headers.get("authToken")):
      return jsonify({"status":"bad request - no permission"})

    #Check if parameters where inputed correctly
    if not parameters["beaconId"] or len(parameters)<2:
      return jsonify({"status":"bad request - missing parameters; at least 2 parameters; beaconId is mandatory"})

    query_update="UPDATE beacon SET id=id"
    query_param=()

    # add parameters to database
    if "beaconName" in parameters:
      query_update+=", idDevice=%s"
      query_param+=(parameters["beaconName"],)

    if "classroomId" in parameters:
      query_update+=", idClassroom=%s"
      query_param+=(parameters["classroomId"],)

    if "x" in parameters:
      query_update+=", x=%s"
      query_param+=(parameters["x"],)

    if "y" in parameters:
      query_update+=", y=%s"
      query_param+=(parameters["y"],)

    if "z" in parameters:
      query_update+=", z=%s"
      query_param+=(parameters["z"],)
    
    # add suffix to query
    query_update+=" WHERE id=%s"
    query_param+=(parameters["beaconId"],)

    mycursor.execute(query_update, query_param)
    mydb.commit()

    return jsonify({"status":"success"})


# daniel
@app.route("/search/waypoints", methods=["GET"])
def searchWaypoint():
  """


    Description: Returns all waypoints between 2 beacons.

    Endpoint: 
    - /search/waypoints

    Headers:
    - none

    Parameters GET:
    - beaconOrigin
    - beaconDestination

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

  beacons=request.get_json()
  if not beacons["beaconOrigin"] or not beacons["beaconDestination"]:
    return jsonify({"status" : "bad request - missing parameters"})

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT * FROM waypoint INNER JOIN path ON path.id=waypoint.idPath WHERE (path.idBeacon_To=%s and path.idBeacon_From=%s) OR (path.idBeacon_To=%s and path.idBeacon_From=%s)", (int(beacons["beaconOrigin"]), int(beacons["beaconDestination"]), int(beacons["beaconDestination"]), int(beacons["beaconOrigin"])))

  myresult = mycursor.fetchall()

  retorno=[]
  for x in myresult:
    retorno.append({"idPath":x[0], "x":x[1],"y":x[2],"z":x[3]})

  return jsonify(retorno)

@app.route("/map/classrooms", methods=["GET"])
@app.route("/search/classrooms/<id>", methods=["GET"])
def searchClassrooms(id=None):
  """


    Description: Returns all the classrooms / Returns the classroom identified by the ID inserted

    Endpoint: 
    - /map/classrooms
    - /search/classrooms/<id>

    Headers:
    - none

    Parameters GET:
    - none

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if id:
    mycursor.execute("SELECT * FROM classroom WHERE id = '%s' ;" % id)

    myresult = mycursor.fetchall()

    retorno=[]
    for x in myresult:
      retorno.append({"id":x[0], "name":x[1],"occupancy":x[2],"image":x[3],"idDepartment":x[4]})
  else:
    mycursor.execute("SELECT * FROM classroom")

    myresult = mycursor.fetchall()

    retorno=[]
    for x in myresult:
      retorno.append({"id":x[0], "name":x[1],"occupancy":x[2],"image":x[3],"idDepartment":x[4]})


  return jsonify(retorno)


@app.route("/search/departments/<id>", methods=["GET"])
def searchDepartments(id):
  """


    Description: Returns the departments identified by the ID inserted.

    Endpoint: 
    - /search/departments/<id>

    Headers:
    - none

    Parameters GET:
    - none

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  mycursor.execute("SELECT department.id, department.designation, classroom.id, classroom.name, classroom.occupancy, classroom.image FROM department INNER JOIN classroom ON department.id=classroom.idDepartment WHERE department.id=%s ;", (int(id),))

  myresult = mycursor.fetchall()

  departmentId=0
  departmentDesignation=""
  classrooms=[]
  for x in myresult:
    departmentId=x[0]
    departmentDesignation=x[1]
    classrooms.append({"id":x[2], "name":x[3], "occupancy":x[4], "image":x[5]})

  if departmentId>0:
    return jsonify({"departmentId":departmentId, "departmentDesignation":departmentDesignation, "classrooms":classrooms})
  else:
    return jsonify({"status":"bad request - nothing to show"})

# andre m.
@app.route("/map/waypoint", methods=["POST"])
def placeWaypoint():
  """


    Description: Adds a new waypoint in the map, between two beacons.

    Endpoint: 
    - /map/waypoint

    Headers:
    - authToken

    Parameters GET:
    - none

    Parameters POST:
    - idPath
    - x
    - y
    - z

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


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


    Description: Adds a new path to the map, by indicating the starting and the ending points.

    Endpoint: 
    - /map/path

    Headers:
    - authToken

    Parameters GET:
    - none

    Parameters POST:
    - beaconFrom
    - beaconTo

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


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


    Description: Returns / Adds feedback inserted by user. This feedback is the daily diary. NOTE: TO ACCESS UPLOADS, USE THE ENDPOINT: /uploads/nomedoficheiro.ext

    Endpoint: 
    - /account/feedback

    Headers:
    - (POST) authToken

    Parameters GET:
    - idUser : optional

    Parameters POST:
    - type -> text ou image ou video ou audio
    - content -> ficheiro em base64 ou texto normal. o plain text em base64 não pode ter o seguinte texto, nem nada que se assemelhe: data:image/png;base64,
    - idUser -> id do utilizador que está a fazer o upload
    - idBeacon -> id do beacon

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

  db_obj=db_connection()
  mydb=db_obj["mydb"]
  mycursor=db_obj["mycursor"]

  if request.method=="GET":
    sql_query="SELECT note.id, note.idBeacon, note.content, note.idUser, note.type, note.dateTime, user.name FROM note INNER JOIN user ON user.id=note.idUser"
    params=()

    if request.args.get("idUser"):
      sql_query+=" WHERE idUser=%s"
      params=(int(request.args.get("idUser")),)

    print(sql_query)
    mycursor.execute(sql_query, params)
    myresult = mycursor.fetchall()

    notes=[]
    for x in myresult:
      notes.append({"id":x[0], "idBeacon":x[1], "content":x[2], "idUser":x[3], "type":x[4], "dateTime": x[5], "username": x[6]})

    return jsonify({"feedback":notes})

  if request.method=="POST":
    parameters=request.get_json()

    # verificar se os parametros de POST são válidos
    if not parameters["type"] or not parameters["content"] or not parameters["idUser"] or not parameters["idBeacon"] or not request.headers.get("authToken"):
      return jsonify({"status":"missing parameter(s)"})

    mycursor.execute("SELECT user.id FROM user INNER JOIN role ON user.idRole=role.id WHERE authToken=%s AND user.id=%s", (request.headers.get("authToken"), int(parameters["idUser"]) ))
    myresult = mycursor.fetchall()

    if len(myresult)>0:
      fileFormats={"image":"jpg", "audio":"wav", "video":"mp4"}

      # a variável content vai assumir valores de texto normal ou de caminhos para o ficheiro
      content=parameters["content"]
      # verificar se está a ser feito upload de um ficheiro ou de texto livre
      if parameters["type"]!="text":
        content=parameters["content"].split(",")[1].encode("ascii")
        # definir um nome para o ficheiro novo
        fileName="uploads/"+secrets.token_hex(8) + "." + fileFormats[parameters["type"]]

        # definir um nome novo para o ficheiro, no caso desse nome já existir
        while exists(fileName):
          fileName="uploads/"+secrets.token_hex(8) + "." + fileFormats[parameters["type"]]

        # converter o ficheiro em base64 para binário e guarda-lo no sistema de ficheiros
        fileBin = base64.b64decode(content)

        my_file = os.path.join(THIS_FOLDER, fileName)
        f=open(my_file, "wb")
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
        

    Description: Returns a file uploaded

    Endpoint: 
    - /uploads/<filename>

    Headers:
    - none

    Parameters GET:
    - none

    Parameters POST:
    - none

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """
  try:
    return send_from_directory("uploads/", filename)
  except FileNotFoundError:
    abort(404)


# francisco (não te esqueças que tens de receber o header com o token de autenticação)
@app.route("/account/delete", methods=["DELETE"])
def accountDelete():
    """
          

      Description: Deletes user account

      Endpoint: 
      - /account/delete

      Headers:
      - authToken

      Parameters GET:
      - none

      Parameters POST:
      - none

      Parameters PUT:
      - none

      Parameters DELETE:
      - username
      - password

      Returns:
      - 200 OK ( {"status" : "success"} )
      - 400 Bad Request ( {"status" : "bad request"} )
      - 401 Unauthorized ( {"status" : "unauthorized"} )


    """

    db_obj=db_connection()
    mydb=db_obj["mydb"]
    mycursor=db_obj["mycursor"]

    parameters=request.get_json()

    if not parameters["username"] or not parameters["password"] or not request.headers.get("authToken"):
      return jsonify({"status":"missing parameter(s)"})

    # Verify user
    mycursor.execute("SELECT user.id,user.password FROM user WHERE authToken=%s AND user.name=%s", (request.headers.get("authToken"), parameters["username"] ))
    myresult = mycursor.fetchall()

    if len(myresult)>0:

      passwordToCheck = re.search(r'\'(.*?)\'',str(myresult[0][1])).group(1)
      if check_password_hash(passwordToCheck, parameters["password"]):
        mycursor.execute("DELETE FROM user WHERE authToken=%s AND user.name=%s", (request.headers.get("authToken"), parameters["username"] ))
        mydb.commit()

        return jsonify({"status":"success"})

      print(parameters["password"])
      return jsonify({"status":"wrong password"})

    return jsonify({"status":"no permission"})


@app.route("/account/change", methods=["PUT"])
def accountChange():
    """
          

      Description: Change user's password

      Endpoint: 
      - /account/change

      Headers:
      - authToken

      Parameters GET:
      - none

      Parameters POST:
      - none

      Parameters PUT:
      - username
      - oldPassword
      - newPassword

      Parameters DELETE:
      - none

      Returns:
      - 200 OK ( {"status" : "success"} )
      - 400 Bad Request ( {"status" : "bad request"} )
      - 401 Unauthorized ( {"status" : "unauthorized"} )


    """

    db_obj=db_connection()
    mydb=db_obj["mydb"]
    mycursor=db_obj["mycursor"]

    parameters=request.get_json()

    if not parameters["username"] or not parameters["oldPassword"] or not parameters["newPassword"] or not request.headers.get("authToken"):
      return jsonify({"status":"missing parameter(s)"})

    # Verify user
    mycursor.execute("SELECT user.id,user.password FROM user WHERE authToken=%s AND user.name=%s", (request.headers.get("authToken"), parameters["username"] ))
    myresult = mycursor.fetchall()

    if len(myresult)>0:

      passwordToCheck = re.search(r'\'(.*?)\'',str(myresult[0][1])).group(1)
      if check_password_hash(passwordToCheck, parameters["oldPassword"]):
        pwdRegex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$')

        if pwdRegex.match(parameters["oldPassword"]):
          encryptedPassword = generate_password_hash(parameters["newPassword"], method='sha256')

          mycursor.execute("UPDATE user SET user.password=%s WHERE user.name=%s", (encryptedPassword, parameters["username"]))
          mydb.commit()

          return jsonify({"status":"success"})

        return jsonify({"status":"new password is invalid"})

      return jsonify({"status":"wrong password"})

    return jsonify({"status":"no permission"})


@app.route("/account/reviews", methods=["GET", "POST"])
def accountReviews():
  """


    Description: Returns all the reviews sent by users / Insert a new review

    Endpoint: 
    - /account/reviews

    Headers:
    - (POST) authToken

    Parameters GET:
    - none

    Parameters POST:
    - idUser
    - body

    Parameters PUT:
    - none

    Parameters DELETE:
    - none

    Returns:
    - 200 OK ( {"status" : "success"} )
    - 400 Bad Request ( {"status" : "bad request"} )
    - 401 Unauthorized ( {"status" : "unauthorized"} )


  """

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
  app.run(debug=True)