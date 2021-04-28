import flask
from flask import request, jsonify, render_template, url_for, session, redirect, send_from_directory
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.utils import secure_filename
from flask import session
import json
import os
import time
import pathlib
import math
import random
import string
from captcha.image import ImageCaptcha
with open('./config/config.json') as configFile: #global config file
    configData = json.load(configFile)
with open('./config/database.json') as configFile: #database config
    databaseConfig = json.load(configFile)

captcha = ImageCaptcha(fonts=['./static/fonts/quicksand.ttf']) #Fonts for captcha. 


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
#polish user settings
#Invade poland
#add more board settings
#finish making board template
#write thing to sell data to google for cheap >:)

#flask app configuration
app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'test'

#database
app.config['MYSQL_HOST'] = databaseConfig["host"]
app.config['MYSQL_USER'] = databaseConfig["user"]
app.config['MYSQL_PASSWORD'] = databaseConfig["password"]
app.config['MYSQL_DB'] = databaseConfig["name"]
app.config['TEMPLATES_AUTO_RELOAD'] = True
mysql = MySQL(app)

#settings for use in html
globalSettings = dict(
    port = configData["port"],
    mediaLocation = configData["mediaLocation"],
    siteName = configData["siteName"],
    logoUrl = configData["siteLogo"],
    faviconUrl = configData["siteFavicon"],
    enableRegistration = configData["enableRegistration"],
    requiredRole = configData["requiredRole"],
    bannerLocation = configData["bannerLocation"]
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
        requiredRole = reloadData["requiredRole"],
        bannerLocation = reloadData["bannerLocation"]
    )
    return globalSettings

#return correct filesize name. Thanks StackOverflow
def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


#Random string generator for captcha. Thanks StackOverflow :^)
def randomString(size, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#convert file to binary data.
def convertToBinary(f):
    binaryData = f.read()
    return binaryData

#allow files in the media folder to be served
@app.route('/media/<path:path>')
def showMedia(path):
    return send_from_directory(globalSettings['mediaLocation'], path)

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
@app.route('/updatePassword', methods=['POST'])
def updatePassword():
    if request.method == 'POST':
        if session['loggedin'] == True:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts WHERE username=%s", [session['username']])
            accountData = cursor.fetchall()
            accountData = accountData[0]
            currentPassword = request.form['currentPassword']
            newPassword = request.form['newPassword']
            confirmPassword = request.form['confirmPassword']
            if currentPassword == accountData['password']:
                if newPassword == confirmPassword:
                    cursor.execute("UPDATE accounts SET password=%s WHERE username=%s", (newPassword, session['username']))
                    mysql.connection.commit()
                    session.pop('loggedin', None)
                    session.pop('id', None)
                    session.pop('username', None)
                    session.pop('group', None)
                    return render_template('login.html', msg="Password successfully updated, please log in.", data=globalSettings)
                else:
                    return render_template('error.html', errorMsg="New passwords don't match.", data=globalSettings)  
            else:
                return render_template('error.html', errorMsg="Current password is incorrect.", data=globalSettings)  

            


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
    cursor.execute("SELECT * FROM banners WHERE board=%s", [uri])
    bannerData = cursor.fetchall()
    # try:
    if session['group'] == 'administrator' or sqlData['owner'] == session['username']:
        return render_template('manageBoard.html', data=globalSettings, sqlData=sqlData, bannerData=bannerData, msg=msg)
    # except Exception as e:
    #     return render_template('error.html', errorMsg="Not logged in", data=globalSettings)
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
                    cursor.execute("INSERT INTO boards VALUES (%s, %s, %s, %s, 'Anonymous', '', 0, 0, 0, 0)",(request.form['uri'], request.form['name'], request.form['description'], session['username'])) #create the board in the MySQL database
                    mysql.connection.commit()
                    path = os.path.join(globalSettings['bannerLocation'], request.form['uri']) #make folder for banner. 
                    os.mkdir(path) 
                    path = os.path.join(globalSettings['mediaLocation'], request.form['uri']) #make folder for files.  
                    os.mkdir(path) 
                    return redirect(url_for('boardManagement'))
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings) 
        except Exception as e:
            print(e)
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
        try:
            if boardData['owner'] == session['username'] or session['group'] == 'administrator':
                try:
                    if request.form["deleteBoard"] == "on":
                        cursor.execute("DELETE FROM boards WHERE  uri=%s AND owner=%s LIMIT 1", (uri, session['username']))
                        mysql.connection.commit()
                        path = os.path.join(globalSettings['bannerLocation'], uri) #path for banner folder for specific board. 
                        os.rmdir(path)#remove banner folder
                        path = os.path.join(globalSettings['mediaLocation'], uri) #path for banner folder for specific board. 
                        os.rmdir(path)#remove media sub-folder
                        return redirect(url_for('boardManagement', msg=uri + " successfully deleted"))
                except Exception as e:
                    return render_template('manageBoard.html', data=globalSettings, sqlData=sqlData, msg="Please confirm board deletion") #probably could have done better
        except Exception as e:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings) 

@app.route('/updateBoard', methods=['POST'])
def updateBoard():
    if request.method == 'POST':
        uri = request.args.get('uri', type=str)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        boardData = cursor.fetchall()
        boardData = boardData[0]
        try:
            if boardData['owner'] == session['username'] or session['group'] == 'administrator':

                name = request.form['name']
                desc = request.form['description']
                anonymous = request.form['anonymous']
                message = request.form['message']
                captcha = request.form['captcha']
                cursor.execute("UPDATE boards SET name=%s, description=%s, anonymous=%s, message=%s, captcha=%s WHERE uri=%s", (name, desc, anonymous, message, captcha, uri))
                mysql.connection.commit()
                return redirect(url_for('manageBoard', uri=uri))
        except Exception as e:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings) 
#banner management

#upload banner and create sql entry
@app.route('/uploadbanner', methods=['POST'])
def uploadBanner():
    globalSettings = reloadSettings()
    uri = request.args.get('uri', type=str)
    if request.method == 'POST':
        banner = request.files['file']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        sqlData = cursor.fetchall()
        sqlData = sqlData[0]
        try:
            if sqlData['owner'] == session['username'] or session['group'] == 'administrator':
                path = os.path.join(globalSettings['bannerLocation'], uri)
                filename = secure_filename(banner.filename)
                extention = pathlib.Path(filename).suffix
                filename = str(time.time())+extention
                banner.save(os.path.join(path, filename))
                size = os.path.getsize(os.path.join(path, filename))
                cursor.execute("INSERT INTO banners VALUES (%s, %s, %s)",(uri, filename, size))
                mysql.connection.commit()
                cursor.execute("SELECT * FROM banners WHERE board=%s", [uri])
                bannerData = cursor.fetchall()
                return redirect(url_for('manageBoard', uri=uri)) #Find a better solution for this. 
        except Exception as e:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings) 
@app.route('/deletebanner', methods=['POST'])
def deleteBanner():
    globalSettings = reloadSettings()
    uri = request.args.get('uri', type=str)
    name = request.args.get('name', type=str)
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        sqlData = cursor.fetchall()
        sqlData = sqlData[0]
        try:
            if sqlData['owner'] == session['username'] or session['group'] == 'administrator':
                cursor.execute("DELETE FROM banners WHERE filename=%s LIMIT 1", [name]) 
                mysql.connection.commit()
                cursor.execute("SELECT * FROM banners WHERE board=%s", [uri])
                bannerData = cursor.fetchall()
                path = os.path.join(globalSettings['bannerLocation'], uri)
                os.remove(os.path.join(path, name))
                return redirect(url_for('manageBoard', uri=uri)) #Find a better solution for this. 
        except Exception as e:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings) 

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



#generate captcha for the board
#Syntax: generateCaptcha(captcha length)
def generateCaptcha(difficulty):
    captchaText = randomString(difficulty)
    print("#########################")
    print(captchaText)
    print("#########################")
    currentCaptcha = captcha.generate(captchaText)
    filename = time.time()
    captcha.write(captchaText, f'./static/captchas/{filename}.png')
    session["captcha"] = captchaText #find a better solution for this
    return f'./static/captchas/{filename}.png'

#get all threads for a board
def getThreads(uri):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts WHERE board = %s AND type = 1", [uri])
    threads = cursor.fetchall()
    return threads

#board page
@app.route('/<board>/', methods=['GET'])
@app.route('/<board>', methods=['GET'])
def boardPage(board):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    boards = cursor.fetchall()
    for x in boards:
        if x['uri'] == board:
            path = os.path.join(globalSettings['bannerLocation'], board)
            if len(os.listdir(path)) > 0:
                banner = os.path.join(path, random.choice(os.listdir(path)))
            else:
                banner = "static/banners/defaultbanner.png"

            print(x['captcha'])
            if x['captcha'] == 1:
                captcha = generateCaptcha(5)
                return render_template('board.html', data=globalSettings, board=board, boardData=x, banner=banner, captcha=captcha, threads=getThreads(board))
            else:
                return render_template('board.html', data=globalSettings, board=board, boardData=x, banner=banner, threads=getThreads(board))


def uploadFile(f, board, filename):
    extention = pathlib.Path(secure_filename(f.filename)).suffix
    filename = filename+extention
    f.save(os.path.join(globalSettings['mediaLocation'], board, filename))
    return str(os.path.join(globalSettings['mediaLocation'], board, filename))
@app.route('/newThread', methods=['POST'])
def newThread():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    boards = cursor.fetchall()
    for x in boards:
        if x['uri'] == request.form['board']:
            if x['captcha'] == 1:
                if request.method == 'POST' and 'comment' in request.form and 'captcha' in request.form and 'file' in request.form:
                    if session['captcha'] == request.form['captcha']:
                        if "name" in request.form:
                            name = request.form['name']
                        else:
                            name = x['anonymous']
                        if 'subject' in request.form:
                            subject = request.form['subject']
                        else:
                            subject = ""
                        if 'options' in request.form:
                            options = request.form['options']
                        else:
                            options = ""
                        #add max file amount exceeded here.                    
                        files = request.files.getlist("file")
                        curTime = time.time()
                        filenames = []
                        filePaths = []
                        for f in files: #CHANGE SO THAT IT STORES FILES ON DISK BECAUSE IM FUCKING STUPID
                            filename = uploadFile(f, x['uri'], str(curTime))
                            filePaths.append(filename)
                            filenames.append(secure_filename(f.filename))
                        filenames = ','.join([str(x) for x in filenames])
                        filePaths = ','.join([str(x) for x in filePaths])
                        cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 1, NULL, %s, %s, %s)', (name, subject, options, request.form['comment'], x['posts']+1, curTime, x['uri'], str(filePaths), str(filenames))) #parse message later
                        cursor.execute("UPDATE boards SET posts=%s WHERE uri=%s", (x['posts']+1, x['uri']))
                        mysql.connection.commit()
                        return 'thread created' #change to something better
                    else:
                        return "Incorrect captcha"
                else:
                    return "Please fill out all required forms"
            else:
                if request.method == 'POST' and 'comment' in request.form:
                    print(request.form)
                    if "name" in request.form and len(request.form['name']) > 0:
                        name = request.form['name']
                    else:
                        name = x['anonymous']
                    if 'subject' in request.form and len(request.form['subject']) > 0:
                        subject = request.form['subject']
                    else:
                        subject = "NULL"
                    if 'options' in request.form and len(request.form['options']) > 0:
                        options = request.form['options']
                    else:
                        options = "NULL"
                    #add max file amount exceeded here.
                    files = request.files.getlist("file")
                    curTime = time.time()
                    filenames = []
                    filePaths = []
                    for f in files: #CHANGE SO THAT IT STORES FILES ON DISK BECAUSE IM FUCKING STUPID
                        filename = uploadFile(f, x['uri'], str(curTime))
                        filePaths.append(filename)
                        filenames.append(secure_filename(f.filename))
                    filenames = ','.join([str(x) for x in filenames])
                    filePaths = ','.join([str(x) for x in filePaths])
                    cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 1, NULL, %s, %s, %s)', (name, subject, options, request.form['comment'], x['posts']+1, curTime, x['uri'], str(filePaths), str(filenames))) #parse message later
                    cursor.execute("UPDATE boards SET posts=%s WHERE uri=%s", (x['posts']+1, x['uri']))
                    mysql.connection.commit()
                    return 'thread created' #change to something better
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=configData["port"])