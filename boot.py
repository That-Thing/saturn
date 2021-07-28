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
from datetime import datetime, timedelta
import pathlib
import math
import random
import string
from captcha.image import ImageCaptcha
from PIL import Image
import re
import hashlib
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
#add more board settings
#polish up thread creation
#add expansion of thumbnail on click for posts
#Add captcha deletion
#add post deletion
#catalog
#add floating reply thing.
#add replying by clicking on the post number


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

#global settings
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
        bannerLocation = reloadData["bannerLocation"],
        mimeTypes = reloadData["mimeTypes"],
        maxFiles = int(configData["maxFiles"]),
        spoilerImage =  reloadData["spoilerImage"],
        tripLength = reloadData["tripLength"],
        pageThreads = reloadData["pageThreads"]
    )
    return globalSettings
globalSettings = reloadSettings()

#gets user groups from the groups table. 
def getUserGroups():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM groups")
        groups = cursor.fetchall()
        return groups
groups = getUserGroups()
#This gets the salt from the server table in the database
def getSalt():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM server")
        server = cursor.fetchone()
        return server['salt']
salt = getSalt()
groups = getUserGroups()
def getThemes():
    with open('./config/themes.json') as themes:
        themeData = json.load(themes)
    return themeData
themes = getThemes()

#return correct filesize name. Thanks StackOverflow
def convertSize(size_bytes):
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

#get total number of posts. 
def getTotal():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM server")
    serverInfo = cursor.fetchone()
    return serverInfo['posts']
#get the number of posts in the last hour
def lastHour():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    count = 0
    now = datetime.now()
    for post in posts:
        if now-timedelta(hours=1) <= datetime.utcfromtimestamp(post['date']) <= now+timedelta(hours=1):
            count = count+1
    return count
#check if there's a file password in the session
def checkFilePass():
    if 'filePassword' in session:
        return session['filePassword']
    else:
        characters = string.ascii_letters + string.digits
        password =  "".join(random.choice(characters) for x in range(8))
        session['filePassword'] = password
        return password
#allow files in the media folder to be served
@app.route('/media/<path:path>')
def showMedia(path):
    return send_from_directory(globalSettings['mediaLocation'], path)
#strip HTML tags from entered text. 
def stripHTML(text):
    text = text.replace('<','&lt;')
    text = text.replace('>','&gt;')
    return text
#bump order
def bumpOrder(board):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #long and drawn out sql query to get bump order.

    #add checks for sage in options
    cursor.execute(''' 
        SELECT parent.*, child.number, (SELECT MAX(c1.number) FROM posts c1 WHERE c1.thread = parent.number AND c1.options != "sage") AS threadNum FROM posts parent,
        posts child
        WHERE child.thread = parent.number AND parent.board=%s
        AND child.number = (SELECT MAX(c1.number) FROM posts c1
        WHERE c1.thread = parent.number)
        UNION 
        SELECT parent.*, parent.number, parent.number AS threadNum
        FROM posts parent
        WHERE parent.board=%s AND
            NOT EXISTS (SELECT * FROM posts c2
            WHERE c2.thread = parent.number)
            AND NOT EXISTS (SELECT * FROM posts c3
            WHERE parent.thread = c3.number)
        ORDER BY threadNum desc
        ;
    ''', (board, board))
    posts = cursor.fetchall()
    return posts
def returnHash(password):
    password = password+salt
    password = hashlib.sha512(password.encode("UTF-8")).hexdigest()
    return password

def checkTrip(name, role): #check if tripcode password is included and hash it if it is.
    if "##" in name:
        password = name.split("##",1)[1]
        if password == "rs":
            password = groups[role]['name']
            return password
        else:
            password = returnHash(password)
            return password[:int(globalSettings["tripLength"])]
    else: 
        return False

def checkGroup():
    if 'group' not in session:
        session['group'] = 99

def get404():
    path = './static/images/404'
    image = os.path.join(path, random.choice(os.listdir(path)))
    return image


def checkPostLink(text): #I know I already have this in the checkMarkdown function, but this is just an easier way of doing it (for me)
    lines = text.splitlines(True)
    replies = []
    for x in lines:
        words = x.split(" ")
        for word in words:
            if bool(re.match(r"^&gt;&gt;[0-9]+\W?$", word)) == True:
                number = re.findall(r"[0-9]+", word[8:])
                replies.append(number[0])
    if len(replies) > 0:
        return replies
    else:
        return False


#filters
@app.template_filter('ut') #convert unix time to normal datetime
def normalizetime(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%m/%d/%Y %H:%M:%S')
@app.template_filter('splittext') #split text by .
def splittext(text):
    return text.split('.')
@app.template_filter('filesize') #get filesize
def fileSize(file):
    size = os.path.getsize(file)
    return convertSize(size)
@app.template_filter('checkimage') #check if file is a valid image
def checkImage(file):
    im = Image.open(file)
    if str(im.verify()) == "None":
        return True
    else:
        return False
@app.template_filter('dimensions') #get image dimensions
def getDimensions(file):
    im = Image.open(file)
    if str(im.verify()) == "None":
        width, height = im.size
        return (f"{width}x{height}")
    else:
        pass
@app.template_filter('fivePosts') #get last 5 posts in a thread
def fivePosts(thread, board):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts WHERE board=%s AND thread=%s AND type=2", (board, thread))
    posts = cursor.fetchall()
    numbers = []
    for post in posts:
        numbers.append(post['number'])
    numbers.sort(reverse=True)
    final = []
    index = 0
    for x in numbers:
        cursor.execute("SELECT * FROM posts WHERE board=%s AND number=%s", (board, x))
        tmp = cursor.fetchone()
        final.append(tmp)
        index += 1
        if index == 5:
            break
    final.reverse()
    return final
@app.template_filter('checkMarkdown') #Handles markdown
def checkMarkdown(text, thread, board, post):
    gtRegex = r"^&gt;$" #greentext regex
    ptRegex = r"^&lt;.*$" #pinktext regex
    lbRegex = r"^&gt;&gt;&gt;\/(.*?)\/$" #link board regex
    lqRegex = r"^&gt;&gt;[0-9]+\W?$" #link post/quote regex
    codeSRegex = r"^\[code\]$" #code start regex ([code])
    codeERegex = r"^\[/code\]$" #code end regex ([/code])
    urlRegex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)" #URL regex
    text = stripHTML(text) #Turns potentially unsafe text into database-friendly text
    if bool(re.match(codeSRegex, text[:6])) and bool(re.match(codeERegex, text[-7:])): #checks if code tags are present at start and end of string
        text = f"<code>{text[6:-7]}</code>"
        return text
    lines = text.splitlines(True)
    result = ""
    for x in lines:
        words = x.split(" ")
        newWords = []
        for word in words:
            if bool(re.match(lqRegex, word)) == True:
                number = re.findall(r"[0-9]+", word[8:])
                word = f"<a class='link-quote' href='/{board}/thread/{thread}#{number[0]}'>{word}</a>"
            elif bool(re.match(lbRegex, word)) == True:
                word = f"<a class='link-board' href='/{word.strip('&gt;&gt;&gt;').strip('/')}/'>{word}</a>"
            elif bool(re.match(urlRegex, word)) == True: #checks if a URL was entered
                word = f"<a href='{word}' target='_blank'>{word}</a>"
            newWords.append(word) 
        x = " ".join(newWords)
        if bool(re.match(gtRegex, x[:4])) == True: #Checks for greentext
            x = f"<span class='greentext'>{x}</span>"
        elif bool(re.match(ptRegex, x[:4])): #Checks for pinktext
            x = f"<span class='pinktext'>{x}</span>"
        result = result+x
    return result

@app.template_filter('checkQuote') #checks if post has a quoted post. 
def checkQuote(text):
    text = stripHTML(text)
    lines = text.splitlines(True)
    result = ""
    for x in lines:
        if x.startswith("gt;gt;"):
            x = f'<a href="">{x}</a>'
@app.template_filter('checkRole') #checks the poster's role
def checkRole(role):
    for group in groups:
        if group['id'] == int(role):
            return group['name']
@app.template_filter("hasSignature") #Returns true if user has a role. 
def hasSignature(trip):
    for group in groups:
        if group['name'] == trip:
            return True
    return False
#Make local timestamps
#add relative times

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404




#index
@app.route('/', methods=['GET'])
def index():
    checkGroup()
    globalSettings = reloadSettings()
    return render_template('index.html', data=globalSettings, currentTheme=request.cookies.get('theme'), total=getTotal(), lastHour=lastHour(), themes=themes)

#boards
@app.route('/boards', methods=['GET'])
def boards():
    checkGroup()
    globalSettings = reloadSettings()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    sqlData = cursor.fetchall()
    return render_template('boards.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, themes=themes)

#help page
@app.route('/help', methods=['GET'])
def help():
    checkGroup()
    globalSettings = reloadSettings()
    return render_template('help.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#FAQ page
@app.route('/faq', methods=['GET'])
def faq():
    checkGroup()
    globalSettings = reloadSettings()
    return render_template('faq.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#global settings redirect
@app.route('/globalsettings', methods=['GET'])
def siteSettings():
    checkGroup()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM rules WHERE type = 0")
    rules = cursor.fetchall()
    try:
        if int(session['group']) <= 1:
            return render_template('siteSettings.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes, groups=groups, rules=rules)
        else:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#Save global settings
@app.route('/saveSettings', methods=['POST'])
def saveSettings():
    checkGroup()
    globalSettings = reloadSettings()
    if request.method == 'POST':
        try:
            if int(session['group']) <= 1:
                result = request.form.to_dict()
                with open('./config/config.json', 'w') as f:
                    json.dump(result, f, indent=4)
                return redirect(url_for('siteSettings'))
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#Global Rules page
@app.route('/rules', methods=['GET'])
def rules():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM rules WHERE type = 0")
    rules = cursor.fetchall()
    return render_template('rules.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes, rules=rules, board="Global")
#Add rule
@app.route('/addRule', methods=['POST'])
def addRule():
    if request.method == 'POST':
        if request.form['board'] == "NULL":
            board = None
        else:
            board = request.form['board']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri = %s", [board])
        currentBoard = cursor.fetchone()
        if currentBoard != None or int(session['group']) <= 1: #checks if the board exists or the user has admin+ perms
            if int(session['group']) <= 1 or currentBoard['owner'] == session['username']: #checks if the user has admin+ perms first
                cursor.execute("INSERT INTO rules VALUES (NULL, %s, %s, %s)", (request.form['newRule'], request.form['type'], board))
                mysql.connection.commit()
                if request.form['type'] == "0":
                    return redirect(url_for("siteSettings"))
        else: #Add exceptions for board rules. 
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)        
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#Delete Rule
#Add checks so you can't delete rules from other boards or global settings by changing the HTML of rules on board management pages. 
@app.route('/deleteRule', methods=['POST'])
def deleteRule():
    if request.method == 'POST':
        if int(session['group']) <= 1:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            print(request.form['board'])
            print(request.form['id'])
            if request.form['board'] == "NULL":
                board = None
                print("board is null")
            else:
                board = request.form['board']
            cursor.execute("SELECT * FROM rules WHERE id = %s", [int(request.form['id'])])
            print(cursor.fetchone())
            cursor.execute("DELETE FROM rules WHERE id = %s", [int(request.form['id'])])
            mysql.connection.commit()
            if request.form['type'] == "0":
                return redirect(url_for("siteSettings"))
        else: #Add check for board owners.
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)        
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/accountsettings', methods=['GET'])
def accountSettings():
    checkGroup()
    globalSettings = reloadSettings()
    try:
        if session['loggedin'] == True:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards")
            sqlData = cursor.fetchall()
            return render_template('accountSettings.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, themes=themes)
        else:
            return render_template('error.html', errorMsg="Not logged in", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)   
@app.route('/updatePassword', methods=['POST'])
def updatePassword():
    checkGroup()
    if request.method == 'POST':
        if session['loggedin'] == True:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts WHERE username=%s", [session['username']])
            accountData = cursor.fetchone()
            saltedPass = request.form['currentPassword'] + salt
            passwordHash = hashlib.sha512(saltedPass.encode("UTF-8")).hexdigest()
            newPassword = request.form['newPassword']
            confirmPassword = request.form['confirmPassword']
            if passwordHash == accountData['password']:
                if newPassword == confirmPassword:
                    newPassword = newPassword + salt
                    newPassword = hashlib.sha512(newPassword.encode("UTF-8")).hexdigest()
                    cursor.execute("UPDATE accounts SET password=%s WHERE username=%s", (newPassword, session['username']))
                    mysql.connection.commit()
                    session.pop('loggedin', None)
                    session.pop('id', None)
                    session.pop('username', None)
                    session.pop('group', None)
                    return render_template('login.html', msg="Password successfully updated, please log in.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                else:
                    return render_template('error.html', errorMsg="New passwords don't match.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            else:
                return render_template('error.html', errorMsg="Current password is incorrect.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            


@app.route('/updateemail', methods=['POST'])
def updateEmail():
    checkGroup()
    if request.method == 'POST':
        try:
            if session['loggedin'] == True:
                email = request.form['email']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("UPDATE accounts SET email=%s WHERE username=%s", (email, session['username']))
                session.pop('email', None)
                mysql.connection.commit()
                return redirect(url_for('accountSettings'))
            else:
                return render_template('error.html', errorMsg="Not logged in", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)




#board management page
@app.route('/boardmanagement', methods=['GET'])
def boardManagement():
    checkGroup()
    globalSettings = reloadSettings()
    try:
        if int(session['group']) <= 1:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards")
            sqlData = cursor.fetchall()
            msg=""
            return render_template('boardManagement.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, msg="", themes=themes)
        else:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)


#Individual board management
@app.route('/manageboard', methods=['GET'])
def manageBoard():
    checkGroup()
    globalSettings = reloadSettings()
    uri = request.args.get('uri', type=str)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
    sqlData = cursor.fetchall()
    sqlData = sqlData[0]
    msg=""
    cursor.execute("SELECT * FROM banners WHERE board=%s", [uri])
    bannerData = cursor.fetchall()
    try:
        if int(session['group']) <= 1 or sqlData['owner'] == session['username']:
            return render_template('manageBoard.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, bannerData=bannerData, msg=msg, themes=themes)
        else:
            return render_template('error.html', errorMsg="Not logged in", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        print(e)
#create board
@app.route('/createboard', methods=['POST'])
def createBoard():
    checkGroup()
    globalSettings = reloadSettings()
    if request.method == 'POST':
        try:
            if int(session['group']) <= 1 or globalSettings['requiredRole'] <= int(session['group']):
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM boards WHERE uri=%s", [request.form['uri']])
                board = cursor.fetchone()
                if board:
                    return redirect(url_for('boardManagement', msg="Board already exists"))
                else:    
                    cursor.execute("INSERT INTO boards VALUES (%s, %s, %s, %s, 'Anonymous', '', 0, 0, 0, 0, %s)",(request.form['uri'].lower(), request.form['name'], request.form['description'], session['username'], globalSettings['pageThreads'])) #create the board in the MySQL database
                    mysql.connection.commit()
                    path = os.path.join(globalSettings['bannerLocation'], request.form['uri']) #make folder for banner. 
                    os.mkdir(path) 
                    path = os.path.join(globalSettings['mediaLocation'], request.form['uri']) #make folder for files.  
                    os.mkdir(path) 
                    return redirect(url_for('boardManagement'))
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            print(e)
#delete board
@app.route('/deleteboard', methods=['POST'])
def deleteBoard():
    checkGroup()
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
            if boardData['owner'] == session['username'] or int(session['group']) <= 1:
                try:
                    if request.form["deleteBoard"] == "on":
                        cursor.execute("DELETE FROM boards WHERE  uri=%s AND owner=%s LIMIT 1", (uri, session['username']))
                        cursor.execute("DELETE FROM posts WHERE board=%s", [uri])
                        mysql.connection.commit()
                        path = os.path.join(globalSettings['bannerLocation'], uri) #path for banner folder for specific board. 
                        os.rmdir(path)#remove banner folder
                        path = os.path.join(globalSettings['mediaLocation'], uri) #path for banner folder for specific board. 
                        for x in os.listdir(path):
                            os.remove(os.path.join(path, x))
                        os.rmdir(path)#remove media sub-folder
                        return redirect(url_for('boardManagement', msg=uri + " successfully deleted"))
                    else:
                        return redirect(url_for('manageboard', uri=uri, msg="Please confirm board deletion"))
                except Exception as e:
                    print(e)
                    return render_template('manageBoard.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, msg="Please confirm board deletion") #probably could have done better, themes=themes
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
             print(e)
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
@app.route('/updateBoard', methods=['POST'])
def updateBoard():
    checkGroup()
    if request.method == 'POST':
        uri = request.args.get('uri', type=str)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        boardData = cursor.fetchall()
        boardData = boardData[0]
        try:
            if boardData['owner'] == session['username'] or int(session['group']) <= 1:
                name = request.form['name']
                desc = request.form['description']
                anonymous = request.form['anonymous']
                message = request.form['message']
                captcha = request.form['captcha']
                perPage = request.form['perPage']
                if perPage > globalSettings['pageThreads']:
                    perPage = globalSettings['pageThreads']
                cursor.execute("UPDATE boards SET name=%s, description=%s, anonymous=%s, message=%s, captcha=%s, perPage=%s WHERE uri=%s", (name, desc, anonymous, message, captcha, perPage, uri))
                mysql.connection.commit()
                return redirect(url_for('manageBoard', uri=uri))
            else:
                return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
    else:
        return "Request must be POST"
#banner management

#upload banner and create sql entry
@app.route('/uploadbanner', methods=['POST'])
def uploadBanner():
    checkGroup()
    globalSettings = reloadSettings()
    uri = request.args.get('uri', type=str)
    if request.method == 'POST':
        banner = request.files['file']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        sqlData = cursor.fetchall()
        sqlData = sqlData[0]
        try:
            if sqlData['owner'] == session['username'] or int(session['group']) <= 1:
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
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    else:
        return render_template('error.html', errorMsg="Request must be POST", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)    
@app.route('/deletebanner', methods=['POST'])
def deleteBanner():
    checkGroup()
    globalSettings = reloadSettings()
    uri = request.args.get('uri', type=str)
    name = request.args.get('name', type=str)
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [uri])
        sqlData = cursor.fetchall()
        sqlData = sqlData[0]
        try:
            if sqlData['owner'] == session['username'] or int(session['group']) <= 1:
                cursor.execute("DELETE FROM banners WHERE filename=%s LIMIT 1", [name]) 
                mysql.connection.commit()
                cursor.execute("SELECT * FROM banners WHERE board=%s", [uri])
                bannerData = cursor.fetchall()
                path = os.path.join(globalSettings['bannerLocation'], uri)
                os.remove(os.path.join(path, name))
                return redirect(url_for('manageBoard', uri=uri)) #Find a better solution for this. 
        except Exception as e:
            return render_template('error.html', errorMsg="Insufficient Permissions", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 

#Account stuff  Most of it isn't mine lol. 
@app.route('/login/', methods=['GET', 'POST'])
def login():
    checkGroup()
    globalSettings = reloadSettings()
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        passwordHash = returnHash(request.form['password']+salt)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (request.form['username'], passwordHash))
        account = cursor.fetchone()
        if account:
            if account['password'] == passwordHash and account['username'] == request.form['username']:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['group'] = account['group']
                session['email'] = account['email']
                return redirect(url_for('index'))
            else:
                msg = 'Incorrect username or password'
        else:
            msg = 'Incorrect username or password'
    return render_template('login.html', msg=msg, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('group', None)
   return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    checkGroup()
    globalSettings = reloadSettings()
    if globalSettings['enableRegistration'] == 'on':
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
            username = request.form['username']
            password = request.form['password'] + salt
            email = request.form['email']
            # Check if account exists
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
                password = returnHash(password)
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, 4)', (username, password, email))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                return render_template('login.html', msg="Registration complete, please log in", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            msg = 'Please fill out the form!'
        # Show registration form with message (if any)
        return render_template('register.html', msg=msg, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return render_template('register.html', msg="Registrations are currently disabled.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)



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
    checkGroup()
    if request.cookies.get('ownedPosts') != None:
        ownedPosts = json.loads(request.cookies.get('ownedPosts')) #gets posts the current user has made for (you)s
    else:
        ownedPosts = {}
    filePass = checkFilePass() #gets user's password for files
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    boards = cursor.fetchall()
    for x in boards:
        if x['uri'] == board:
            posts = bumpOrder(board)
            postLength = len(posts)
            posts = posts[0:1*int(x['perPage'])]
            path = os.path.join(globalSettings['bannerLocation'], board)
            if len(os.listdir(path)) > 0:
                banner = os.path.join(path, random.choice(os.listdir(path)))
            else:
                banner = "static/banners/defaultbanner.png"
            if x['captcha'] == 1:
                captcha = generateCaptcha(5)
                return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board, boardData=x, banner=banner, captcha=captcha, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, page=1, themes=themes)
            else:
                return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board, boardData=x, banner=banner, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, page=1, themes=themes)
    return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404

#individual pages
@app.route('/<board>/<int:page>', methods=['GET'])
def boardNumPage(board, page):
    checkGroup()
    if request.cookies.get('ownedPosts') != None:
        ownedPosts = json.loads(request.cookies.get('ownedPosts')) #gets posts the current user has made for (you)s
    else:
        ownedPosts = {}
    filePass = checkFilePass()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''SELECT * FROM boards''')
    boards = cursor.fetchall()
    for x in boards:
        if x['uri'] == board:
            posts = bumpOrder(board)
            postLength = len(posts)
            posts = posts[(page-1)*int(x['perPage']):page*int(x['perPage'])]
            if posts:
                path = os.path.join(globalSettings['bannerLocation'], board)
                if len(os.listdir(path)) > 0:
                    banner = os.path.join(path, random.choice(os.listdir(path)))
                else:
                    banner = "static/banners/defaultbanner.png"
                if x['captcha'] == 1:
                    captcha = generateCaptcha(5)
                    return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board, boardData=x, banner=banner, captcha=captcha, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, page=page, themes=themes)
                else:
                    return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board, boardData=x, banner=banner, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, page=page, themes=themes)
            else:
                return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
    return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404


#thumbnail generation
def thumbnail(image, board, filename, ext):
    try:
        image = Image.open(image)
        size = 150, 150
        image.thumbnail(size)
        image.save(os.path.join(globalSettings['mediaLocation'], board, filename + "s"+ext))
    except IOError:
        pass
def uploadFile(f, board, filename, spoiler):
    extention = pathlib.Path(secure_filename(f.filename)).suffix
    nFilename = filename+extention
    path = os.path.join(globalSettings['mediaLocation'], board, nFilename)
    f.save(path)
    if spoiler == 0:
        thumbnail(path, board, filename, extention) #generate thumbnail for uploaded image
    return str(path)


@app.route('/newThread', methods=['POST'])
def newThread():
    checkGroup()
    filePass = checkFilePass()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    boards = cursor.fetchall()
    tripcode = None
    for x in boards:
        if x['uri'] == request.form['board']:
            mimeTypes = globalSettings['mimeTypes'].split(',')
            curTime = time.time()
            if "name" in request.form and len(request.form['name']) > 0:
                name = request.form['name']
                name = stripHTML(name)
                session['name'] = name
                tripcode = checkTrip(name, int(session['group']))
                if tripcode != False:
                    name = name.split("##",1)[0]
                else:
                    tripcode = None
            else:
                name = x['anonymous']
            if 'subject' in request.form and len(request.form['subject']) > 0:
                subject = request.form['subject']
                subject = stripHTML(subject)
            else:
                subject = ""
            if 'options' in request.form and len(request.form['options']) > 0:
                options = request.form['options']
                options = stripHTML(options)
                options = options.lower()
            else:
                options = ""     
            if "spoiler" in request.form:
                if request.form['spoiler'] == "on":
                    spoiler = 1
                else:
                    spoiler = 0
            else:
                spoiler = 0
            comment = request.form['comment']
            comment = stripHTML(comment)
            postLink = checkPostLink(comment)
            if 'password' in request.form:
                filePass = request.form['password']
            if x['captcha'] == 1:
                if request.method == 'POST' and 'comment' in request.form and 'captcha' in request.form and request.files['file'].filename != '':
                    if session['captcha'] == request.form['captcha']:
                        files = request.files.getlist("file")
                        if len(files) > globalSettings['maxFiles']: #check if too many files are uploaded
                            return "Maximum file limit exceeded"
                        else:
                            filenames = []
                            filePaths = []
                            for f in files: #downloads the files and stores them on the disk
                                if f.mimetype in mimeTypes:
                                    filename = uploadFile(f, x['uri'], str(curTime), spoiler)
                                    filePaths.append(filename)
                                    filenames.append(secure_filename(f.filename))
                                else:
                                    return "Incorrect file type submitted"
                            filenames = ','.join([str(x) for x in filenames])
                            filePaths = ','.join([str(x) for x in filePaths])
                        cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (name, subject, options, comment, x['posts']+1, curTime, x['posts']+1, x['uri'], str(filePaths), str(filenames), str(request.remote_addr), spoiler,filePass, tripcode))
                        if postLink != False:
                            for x in postLink:
                                cursor.execute("SELECT * FROM posts WHERE number = %s", [x])
                                currentReplies = cursor.fetchone()
                                if currentReplies:
                                    currentReplies = currentReplies['replies']
                                    if currentReplies != None:
                                        currentReplies = currentReplies.split(",")
                                    else:
                                        currentReplies = []
                                    currentReplies.append(f"{str(request.form['thread'])}/{str(number)}")
                                    currentReplies = ",".join(currentReplies)
                                    cursor.execute("UPDATE posts SET replies = %s WHERE number = %s", (currentReplies, x))
                        cursor.execute("UPDATE boards SET posts=%s WHERE uri=%s", (x['posts']+1, x['uri']))
                        cursor.execute("SELECT * FROM server")
                        serverInfo = cursor.fetchone()
                        cursor.execute("UPDATE server SET posts=%s", [serverInfo['posts']+1])
                        mysql.connection.commit()
                        ownedPosts = request.cookies.get('ownedPosts')
                        if ownedPosts == None:
                            ownedPosts = "{}"
                        ownedPosts = json.loads(ownedPosts)
                        ownedPosts[f"{x['uri']}/{x['posts']+1}"] = filePass
                        resp = redirect(f"{x['uri']}/thread/{x['posts']+1}")
                        resp.set_cookie('ownedPosts', json.dumps(ownedPosts))
                        return resp
                    else:
                        return "Incorrect captcha"
                else:
                    return render_template('error.html', errorMsg="Please make sure the message, files, and captcha are present.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
            else:
                if request.method == 'POST' and 'comment' in request.form and request.files['file'].filename != '':
                    files = request.files.getlist("file")
                    if len(files) > globalSettings['maxFiles']: #check if too many files are uploaded
                        return "Maximum file limit exceeded"
                    else:
                        filenames = []
                        filePaths = []
                        for f in files: #downloads the files and stores them on the disk
                            if f.mimetype in mimeTypes:
                                filename = uploadFile(f, x['uri'], str(curTime), spoiler)
                                filePaths.append(filename)
                                filenames.append(secure_filename(f.filename))
                            else:
                                return "Incorrect file type submitted"
                        filenames = ','.join([str(x) for x in filenames])
                        filePaths = ','.join([str(x) for x in filePaths])
                    cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (name, subject, options, comment, x['posts']+1, curTime, x['posts']+1,x['uri'], str(filePaths), str(filenames), str(request.remote_addr), spoiler,filePass, tripcode))
                    if postLink != False:
                        for x in postLink:
                            cursor.execute("SELECT * FROM posts WHERE number = %s", [x])
                            currentReplies = cursor.fetchone()
                            if currentReplies:
                                currentReplies = currentReplies['replies']
                                if currentReplies != None:
                                    currentReplies = currentReplies.split(",")
                                else:
                                    currentReplies = []
                                currentReplies.append(f"{str(request.form['thread'])}/{str(number)}")
                                currentReplies = ",".join(currentReplies)
                                cursor.execute("UPDATE posts SET replies = %s WHERE number = %s", (currentReplies, x))
                    cursor.execute("UPDATE boards SET posts=%s WHERE uri=%s", (x['posts']+1, x['uri']))
                    cursor.execute("SELECT * FROM server")
                    serverInfo = cursor.fetchone()
                    cursor.execute("UPDATE server SET posts=%s", [serverInfo['posts']+1])
                    mysql.connection.commit()
                    ownedPosts = request.cookies.get('ownedPosts')
                    if ownedPosts == None:
                        ownedPosts = "{}"
                    ownedPosts = json.loads(ownedPosts)
                    ownedPosts[f"{x['uri']}/{x['posts']+1}"] = filePass
                    resp = redirect(f"{x['uri']}/thread/{x['posts']+1}")
                    resp.set_cookie('ownedPosts', json.dumps(ownedPosts))
                    return resp
                else:
                    return render_template('error.html', errorMsg="Please make sure the message and files are present.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 


@app.route('/<board>/thread/<thread>', methods=['GET'])
@app.route('/<board>/thread/<thread>', methods=['GET'])
def thread(board, thread):
    checkGroup()
    if request.cookies.get('ownedPosts') != None:
        ownedPosts = json.loads(request.cookies.get('ownedPosts')) #gets posts the current user has made for (you)s
    else:
        ownedPosts = {}
    filePass = checkFilePass()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts WHERE board=%s AND number=%s AND type=1", (board, thread))
    parentPost = cursor.fetchall()
    cursor.execute("SELECT * FROM posts WHERE board=%s AND thread=%s and type=2", (board, thread))
    posts = cursor.fetchall()
    cursor.execute("SELECT * FROM boards")
    boards = cursor.fetchall()
    for x in boards:
        if x['uri'] == board:
            path = os.path.join(globalSettings['bannerLocation'], board)
            if len(os.listdir(path)) > 0:
                banner = os.path.join(path, random.choice(os.listdir(path)))
            else:
                banner = "static/banners/defaultbanner.png"
            if x['captcha'] == 1:
                captcha = generateCaptcha(5)
                return render_template('thread.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board, boardData=x, banner=banner, captcha=captcha, posts=posts, owned=ownedPosts, op=parentPost[0], filePass=filePass, themes=themes)
            else:
                return render_template('thread.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board, boardData=x, banner=banner, posts=posts, op=parentPost[0], owned=ownedPosts, filePass=filePass, themes=themes)
    return render_template('error.html', errorMsg="Board not found", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 


@app.route('/reply', methods=['POST'])
def reply():
    checkGroup()
    if request.method == 'POST':
        filePass = checkFilePass()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM posts where thread=%s", [request.form['thread']])
        posts = cursor.fetchall()
        cursor.execute("SELECT * FROM boards where uri=%s", [request.form['board']])
        board = cursor.fetchone()
        mimeTypes = globalSettings['mimeTypes'].split(',')
        curTime = time.time()
        tripcode = None
        if "name" in request.form and len(request.form['name']) > 0: #checks if the request has a name, if not, the name gets set to the board default anonymous name
            name = request.form['name']
            name = stripHTML(name)
            session['name'] = name
            tripcode = checkTrip(name, int(session['group']))
            if tripcode != False:
                name = name.split("##",1)[0]
            else:
                tripcode = None
        else:
            name = board['anonymous']
        if 'subject' in request.form and len(request.form['subject']) > 0: #Checks if the request has a subject
            subject = request.form['subject']
            subject = stripHTML(subject) #strip any html tags
        else:
            subject = ""
        if 'options' in request.form and len(request.form['options']) > 0: #Checks if there are any options given in the request
            options = request.form['options'] #get options from the form
            options = stripHTML(options) #strip any html tags
            options = options.lower() #lowecase the entered text
        else:
            options = ""
        if "spoiler" in request.form: #Checks if the request is marked as a spoiler
            if request.form['spoiler'] == "on":
                spoiler = 1
            else:
                spoiler = 0
        else:
            spoiler = 0
        if 'password' in request.form: #checks if a password is given in the request
            filePass = request.form['password']
        comment = request.form['comment']
        comment = stripHTML(comment)
        postLink = checkPostLink(comment)
        number = board['posts']+1
        if board['captcha'] == 1: #separate thing if captcha is enabled
            if 'captcha' in request.form:
                if session['captcha'] == request.form['captcha']:
                    if request.files['file'].filename != '':
                        files = request.files.getlist("file")
                        if len(files) > globalSettings['maxFiles']: #check if too many files are uploaded
                            return "Maximum file limit exceeded"
                        else:
                            filenames = []
                            filePaths = []
                            for f in files: #downloads the files and stores them on the disk
                                if f.mimetype in mimeTypes:
                                    filename = uploadFile(f, board['uri'], str(curTime), spoiler)
                                    filePaths.append(filename)
                                    filenames.append(secure_filename(f.filename))
                                else:
                                    return "Incorrect file type submitted"
                            filenames = ','.join([str(x) for x in filenames])
                            filePaths = ','.join([str(x) for x in filePaths])
                    else:
                        if 'comment' not in request.form or len(comment) <= 0 or bool(re.match(r"^\s*$", comment)) == True:
                            return "A file or message is required"
                        filenames = []
                        filePaths = []
                    if len(filePaths) == 0:
                        cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 2, %s, %s, NULL, NULL, %s, %s, %s, %s, NULL)', (name, subject, options, comment, number, curTime, request.form['thread'], board['uri'], str(request.remote_addr), spoiler,filePass, tripcode))
                        if postLink != False:
                            for x in postLink:
                                cursor.execute("SELECT * FROM posts WHERE number = %s", [x])
                                currentReplies = cursor.fetchone()
                                if currentReplies:
                                    currentReplies = currentReplies['replies']
                                    if currentReplies != None:
                                        currentReplies = currentReplies.split(",")
                                    else:
                                        currentReplies = []
                                    currentReplies.append(f"{str(request.form['thread'])}/{str(number)}")
                                    currentReplies = ",".join(currentReplies)
                                    cursor.execute("UPDATE posts SET replies = %s WHERE number = %s", (currentReplies, x))
                    else:
                        cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 2, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (name, subject, options, comment, number, curTime, request.form['thread'], board['uri'], str(filePaths), str(filenames), str(request.remote_addr), spoiler,filePass, tripcode))
                        if postLink != False:
                            for x in postLink:
                                cursor.execute("SELECT * FROM posts WHERE number = %s", [x])
                                currentReplies = cursor.fetchone()
                                if currentReplies:
                                    currentReplies = currentReplies['replies']
                                    if currentReplies != None:
                                        currentReplies = currentReplies.split(",")
                                    else:
                                        currentReplies = []
                                    currentReplies.append(f"{str(request.form['thread'])}/{str(number)}")
                                    currentReplies = ",".join(currentReplies)
                                    cursor.execute("UPDATE posts SET replies = %s WHERE number = %s", (currentReplies, x))
                    cursor.execute("UPDATE boards SET posts=%s WHERE uri=%s", (number, board['uri']))
                    cursor.execute("SELECT * FROM server")
                    serverInfo = cursor.fetchone()
                    cursor.execute("UPDATE server SET posts=%s", [serverInfo['posts']+1])
                    mysql.connection.commit()
                    ownedPosts = request.cookies.get('ownedPosts')
                    if ownedPosts == None:
                        ownedPosts = "{}"
                    ownedPosts = json.loads(ownedPosts)
                    ownedPosts[f"{board['uri']}/{number}"] = filePass
                    resp = redirect(f"{board['uri']}/thread/{request.form['thread']}#{number}")
                    resp.set_cookie('ownedPosts', json.dumps(ownedPosts))
                    return resp
                else:
                    return "Incorrect Captcha"
            else:
                return "Please fill out all the required fields"
        else:
            if request.files['file'].filename != '':
                files = request.files.getlist("file")
                if len(files) > globalSettings['maxFiles']: #check if too many files are uploaded
                    return "Maximum file limit exceeded"
                else:
                    filenames = []
                    filePaths = []
                    for f in files: #downloads the files and stores them on the disk
                        if f.mimetype in mimeTypes:
                            filename = uploadFile(f, board['uri'], str(curTime), spoiler)
                            filePaths.append(filename)
                            filenames.append(secure_filename(f.filename))
                        else:
                            return "Incorrect file type submitted"
                    filenames = ','.join([str(x) for x in filenames])
                    filePaths = ','.join([str(x) for x in filePaths])
            else:
                if 'comment' not in request.form or len(comment) <= 0 or bool(re.match(r"^\s*$", comment)) == True:
                    return "A file or message is required"
                filenames = []
                filePaths = []
            if len(filePaths) == 0:
                cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 2, %s, %s, NULL, NULL, %s, %s, %s, %s, NULL)', (name, subject, options, comment, number, curTime, request.form['thread'], board['uri'], str(request.remote_addr), spoiler,filePass,tripcode))
                if postLink != False:
                    for x in postLink:
                        cursor.execute("SELECT * FROM posts WHERE number = %s", [x])
                        currentReplies = cursor.fetchone()
                        if currentReplies:
                            currentReplies = currentReplies['replies']
                            if currentReplies != None:
                                currentReplies = currentReplies.split(",")
                            else:
                                currentReplies = []
                            currentReplies.append(f"{str(request.form['thread'])}/{str(number)}")
                            currentReplies = ",".join(currentReplies)
                            cursor.execute("UPDATE posts SET replies = %s WHERE number = %s", (currentReplies, x))
            else:
                cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 2, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (name, subject, options, comment, number, curTime, request.form['thread'], board['uri'], str(filePaths), str(filenames), str(request.remote_addr), spoiler,filePass,tripcode))
                if postLink != False:
                    for x in postLink:
                        cursor.execute("SELECT * FROM posts WHERE number = %s", [x])
                        currentReplies = cursor.fetchone()
                        if currentReplies:
                            currentReplies = currentReplies['replies']
                            if currentReplies != None:
                                currentReplies = currentReplies.split(",")
                            else:
                                currentReplies = []
                            currentReplies.append(f"{str(request.form['thread'])}/{str(number)}")
                            currentReplies = ",".join(currentReplies)
                            cursor.execute("UPDATE posts SET replies = %s WHERE number = %s", (currentReplies, x))
            cursor.execute("UPDATE boards SET posts=%s WHERE uri=%s", (board['posts']+1, board['uri']))
            cursor.execute("SELECT * FROM server")
            serverInfo = cursor.fetchone()
            cursor.execute("UPDATE server SET posts=%s", [serverInfo['posts']+1])
            mysql.connection.commit()
            ownedPosts = request.cookies.get('ownedPosts')
            if ownedPosts == None:
                ownedPosts = "{}"
            ownedPosts = json.loads(ownedPosts)
            ownedPosts[f"{board['uri']}/{number}"] = filePass
            resp = redirect(f"{board['uri']}/thread/{request.form['thread']}#{number}")
            resp.set_cookie('ownedPosts', json.dumps(ownedPosts))
            return resp
    else:
        return "Request must be POST"  


@app.route('/<board>/postActions', methods=['POST'])
def postActions(board):
    checkGroup()
    if request.method == 'POST':
        if request.form['delete'] == 'Delete': #Post deletion
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM posts WHERE number=%s AND board=%s", (int(request.form['post']), board))
            post = cursor.fetchone()
            if post['password'] == session['filePassword'] or session['group'] < 3 or post['password'] == request.form['password']:
                if post['files'] != None: #delete files from disk
                    files = post['files'].split(',')
                    for file in files:
                        thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                        os.remove(file)
                        os.remove(thumbPath)
                if post['type'] == 1: #Check if post is a thread and delete all child posts. 
                    cursor.execute("SELECT * FROM posts WHERE thread=%s AND board=%s", (int(request.form['post']), board))
                    posts = cursor.fetchall()
                    for x in posts:
                        files = []
                        if x['files'] != None:
                            files = files + x['files'].split(',')
                        for file in files:
                            thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                            os.remove(file)
                            os.remove(thumbPath)
                    cursor.execute("DELETE FROM posts WHERE thread=%s AND board=%s", (int(request.form['post']), board))
                cursor.execute("DELETE FROM posts WHERE number=%s AND board=%s", (int(request.form['post']), board))
                mysql.connection.commit()
                return(redirect(f"/{board}/"))
            else:
                return render_template('error.html', errorMsg="Password is incorrect", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        else:
            return "Still not implemented, check back later"
            #handle reports
    else:
        return "Request must be POST"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=configData["port"])