import flask
from flask import request, jsonify, render_template, url_for, session, redirect
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask import session
import json
with open('./config/config.json') as configFile: #global config file
    configData = json.load(configFile)
with open('./config/database.json') as configFile: #database config
    databaseConfig = json.load(configFile)


#           _                        
#           \`*-.                    
#            )  _`-.                 
#           .  : `. .                
#           : _   '  \               
#           ; *` _.   `*-._          
#           `-.-'          `-.       
#             ;       `       `.     
#             :.       .        \    
#             . \  .   :   .-'   .   
#             '  `+.;  ;  '      :   
#             :  '  |    ;       ;-. 
#             ; '   : :`-:     _.`* ;
#          .*' /  .*' ; .*`- +'  `*' 
#          `*-*   `*-*  `*-*'        
#ASCII Art cat to keep me sane. 





#TO DO:
#Polish server settings
#Make User settings
#make board creation
#make board settings



#flask app configuration
app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'test'

#database
app.config['MYSQL_HOST'] = databaseConfig["host"]
app.config['MYSQL_USER'] = databaseConfig["user"]
app.config['MYSQL_PASSWORD'] = databaseConfig["password"]
app.config['MYSQL_DB'] = databaseConfig["name"]
mysql = MySQL(app)

#settings for use in html
globalSettings = dict(
    port = configData["port"],
    mediaLocation = configData["mediaLocation"],
    siteName = configData["siteName"],
    logoUrl = configData["siteLogo"],
    faviconUrl = configData["siteFavicon"],
    enableRegistration = configData["enableRegistration"],
    requiredRole = configData["requiredRole"]
)
def reloadSettings():
    with open('./config/config.json') as configFile: #global config file
        reloadData = json.load(configFile)
    globalSettings = dict(
        port = reloadData["port"],
        mediaLocation = reloadData["mediaLocation"],
        siteName = reloadData["siteName"],
        logoUrl = reloadData["siteLogo"],
        faviconUrl = reloadData["siteFavicon"],
        enableRegistration = reloadData["enableRegistration"],
        requiredRole = reloadData["requiredRole"]
    )
    return globalSettings






#index
@app.route('/', methods=['GET'])
def index():
    globalSettings = reloadSettings()
    return render_template('index.html', data=globalSettings)

#boards
@app.route('/boards', methods=['GET'])
def boards():
    globalSettings = reloadSettings()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    sqlData = cursor.fetchall()
    return render_template('boards.html', data=globalSettings, sqlData=sqlData)

#help page
@app.route('/help', methods=['GET'])
def help():
    globalSettings = reloadSettings()
    return render_template('help.html', data=globalSettings)


#global settings redirect
@app.route('/globalsettings', methods=['GET'])
def siteSettings():
    globalSettings = reloadSettings()
    try:
        if session['group'] == 'administrator':
            return render_template('siteSettings.html', data=globalSettings)
        else:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings)    
    except Exception as e:
        return render_template('error.html', errorMsg="Not logged in", data=globalSettings)    
#Save global settings
@app.route('/saveSettings', methods=['POST'])
def saveSettings():
    globalSettings = reloadSettings()
    if request.method == 'POST':
        try:
            if session['group'] == 'administrator':
                result = request.form.to_dict()
                with open('./config/config.json', 'w') as f:
                    json.dump(result, f, indent=4)
                return redirect(url_for('siteSettings'))
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings)   
        except Exception as e:
            return render_template('error.html', errorMsg="Not logged in", data=globalSettings)   



@app.route('/accountsettings', methods=['GET'])
def accountSettings():
    globalSettings = reloadSettings()
    try:
        if session['loggedin'] == True:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards")
            sqlData = cursor.fetchall()
            return render_template('accountSettings.html', data=globalSettings, sqlData=sqlData)
        else:
            return render_template('error.html', errorMsg="Not logged in", data=globalSettings) 
    except Exception as e:
        return render_template('error.html', errorMsg="Not logged in", data=globalSettings)   
# @app.route('/saveAccountSettings', methods=['POST'])
# def saveAccountSettings():

@app.route('/updateemail', methods=['POST'])
def updateEmail():
    try:
        if session['loggedin'] == True:
            email = request.form['email']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("UPDATE accounts SET email=%s WHERE username=%s", (email, session['username']))
            session.pop('email', None)
            mysql.connection.commit()
            return redirect(url_for('accountSettings'))
    except Exception as e:
        return render_template('error.html', errorMsg="Not logged in", data=globalSettings)  





#board management page
@app.route('/boardmanagement', methods=['GET'])
def boardManagement():
    globalSettings = reloadSettings()
    try:
        if session['group'] == 'administrator':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards")
            sqlData = cursor.fetchall()
            msg=""
            return render_template('boardManagement.html', data=globalSettings, sqlData=sqlData, msg="")
        else:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings)   
    except Exception as e:
        return render_template('error.html', errorMsg="Not logged in", data=globalSettings)  


#Individual board management
@app.route('/manageboard', methods=['GET'])
def manageBoard():
    globalSettings = reloadSettings()
    uri = request.args.get('uri', type=str)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
    sqlData = cursor.fetchall()
    sqlData = sqlData[0]
    msg=""
    try:
        if session['group'] == 'administrator' or sqlData['owner'] == session['username']:
            return render_template('manageBoard.html', data=globalSettings, sqlData=sqlData, msg=msg)
    except Exception as e:
        return render_template('error.html', errorMsg="Not logged in", data=globalSettings)       
#create board
@app.route('/createboard', methods=['POST'])
def createBoard():
    globalSettings = reloadSettings()
    if request.method == 'POST':
        try:
            if session['group'] == 'administrator' or globalSettings['requiredRole'] == session['group']:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM boards WHERE uri=%s", [request.form['uri']])
                board = cursor.fetchone()
                if board:
                    return redirect(url_for('boardManagement', msg="Board already exists"))
                else:    
                    cursor.execute("INSERT INTO boards VALUES (%s, %s, %s, %s, 0, 0, 0)",(request.form['uri'], request.form['name'], request.form['description'], session['username']))
                    mysql.connection.commit()
                    return redirect(url_for('boardManagement'))
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings) 
        except Exception as e:
            return render_template('error.html', errorMsg="Not logged in", data=globalSettings)  
#delete board
@app.route('/deleteboard', methods=['POST'])
def deleteBoard():
    if request.method == 'POST':
        uri = request.args.get('uri', type=str)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        boardData = cursor.fetchall()
        boardData = boardData[0]
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        sqlData = cursor.fetchall()
        sqlData = sqlData[0]
        if boardData['owner'] == session['username']:
            try:
                if request.form["deleteBoard"] == "on":
                    cursor.execute("DELETE FROM boards WHERE  uri=%s AND owner=%s LIMIT 1", (uri, session['username']))
                    mysql.connection.commit()
                    return redirect(url_for('boardManagement', msg=uri + " successfully deleted"))
            except Exception as e:
                return render_template('manageBoard.html', data=globalSettings, sqlData=sqlData, msg="Please confirm board deletion")

#Account stuff  Most of it isn't mine lol. 
@app.route('/login/', methods=['GET', 'POST'])
def login():
    globalSettings = reloadSettings()
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['group'] = account['group']
            session['email'] = account['email']
            # Redirect to home page
            return redirect(url_for('index'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username or password'
    return render_template('login.html', msg=msg, data=globalSettings)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('group', None)
   # Redirect to login page
   return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    globalSettings = reloadSettings()
    if globalSettings['enableRegistration'] == 'on':
        # Output message if something goes wrong...
        msg = ''

        # Check if "username", "password" and "email" POST requests exist (user submitted form)
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
            # Create variables for easy access
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, "user")', (username, password, email))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                return render_template('login.html', msg="Registration complete, please log in", data=globalSettings)
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            msg = 'Please fill out the form!'
        # Show registration form with message (if any)
        return render_template('register.html', msg=msg, data=globalSettings)
    else:
        return render_template('register.html', msg="Registrations are currently disabled.", data=globalSettings)











@app.route('/<board>/', methods=['GET'])
@app.route('/<board>', methods=['GET'])
def boardPage(board):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    boards = cursor.fetchall()
    for x in boards:
        if x['uri'] == board:
            return render_template('thread.html', data=globalSettings, board=board, boardData=x)





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=configData["port"])