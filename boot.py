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
from deepdiff import DeepDiff
from flask_socketio import SocketIO, send
with open('./config/config.json') as configFile: #global config file
    configData = json.load(configFile)
with open('./config/logs.json') as logFile: #log config file
    logConfig = json.load(logFile)
with open('./config/database.json') as configFile: #database config
    databaseConfig = json.load(configFile)
with open('./config/markdown.json') as markdownFile: #Loads markdown config
    markdown = json.load(markdownFile)
with open('./config/errors.json') as errors: #Loads errors
    errors = json.load(errors)
captcha = ImageCaptcha(fonts=['./static/fonts/quicksand.ttf']) #Fonts for captcha. 




#Startup tasks

#Deletes all the orphaned captchas
for f in os.listdir("./static/captchas"):
    os.remove(os.path.join("./static/captchas", f))







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
#add expansion of thumbnail on click for posts
#catalog
#add floating reply thing.


#flask app configuration
app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'test'
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")



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
        globalSettings = json.load(configFile)
    # globalSettings = dict(
    #     port = reloadData["port"],
    #     mediaLocation = reloadData["mediaLocation"],
    #     siteName = reloadData["siteName"],
    #     logoUrl = reloadData["siteLogo"],
    #     faviconUrl = reloadData["siteFavicon"],
    #     enableRegistration = reloadData["enableRegistration"],
    #     requiredRole = reloadData["requiredRole"],
    #     bannerLocation = reloadData["bannerLocation"],
    #     mimeTypes = reloadData["mimeTypes"],
    #     maxFiles = int(configData["maxFiles"]),
    #     spoilerImage =  reloadData["spoilerImage"],
    #     tripLength = reloadData["tripLength"],
    #     pageThreads = reloadData["pageThreads"],
    #     captchaDifficulty = int(reloadData['captchaDifficulty']),
    #     captchaExpire = int(reloadData['captchaExpire'])
    # )
    return globalSettings
globalSettings = reloadSettings()
def reloadLogSettings():
    with open('./config/logs.json') as logFile: #log config file
        logConfig = json.load(logFile)
    return logConfig
logConfig = reloadLogSettings()
#gets user groups from the groups table. 
def getUserGroups():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM `groups`")
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
    now = datetime.utcnow()
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


def storeLog(type, action, user, ip, date, data, board):
    with app.app_context():
        actionData = data
        if type == "selfChange":
            actionData = {
                "user": user,
                "oldData": data['oldData'],
                "newData": data['newData']
            }
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO logs VALUES(NULL, %s, %s, %s, %s, %s, %s, %s)", (type, action, json.dumps(actionData), user, str(ip), board,date))
        mysql.connection.commit()

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

    cursor.execute(''' 
        SELECT parent.*, child.number AS bumporder FROM posts parent,
        posts child
        WHERE child.thread = parent.number
        AND parent.board=%s
        AND child.number = (
            SELECT MAX(c1.number) FROM posts c1 WHERE (c1.options <> 'sage' OR c1.options IS NULL) AND c1.thread = parent.number #This seems to cause the script to only return posts with options
        )
        UNION 
        SELECT parent.*, parent.number
        FROM posts parent
        WHERE parent.board=%s AND
            NOT EXISTS (SELECT * FROM posts c2
            WHERE c2.thread = parent.number)
            AND NOT EXISTS (SELECT * FROM posts c3
            WHERE parent.thread = c3.number)
        ORDER BY bumporder desc
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
            try:
                password = groups[role]['name']
            except:
                password = ''
            return password
        else:
            password = returnHash(password)
            return password[:globalSettings["tripLength"]]
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

#Returns time in minutes
def getMinutes(text):
    time = { #time in minutes
        'y':525600,
        'm':43800,
        'd':1440,
        'h':60     
    }
    minutes = 0
    individual = re.findall(r'[0-9]+[y|m|d|h]|[0-9]+', text.lower())
    for x in individual:
        x = re.findall(r'[0-9]+|[y|m|d|h]', x)
        if len(x) == 2:
            minutes += int(time[x[1]])*int(x[0])
        else:
            minutes += int(x[0])
    return minutes

def checkBanned(ip):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM bans WHERE ip=%s", [ip])
    print(cursor.fetchall())
    if cursor.fetchall() == None:
        return False
    else:
        return True


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
    try:
        im = Image.open(file)
        if str(im.verify()) == "None":
            return True
        else:
            return False
    except:
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
    urlRegex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)" #URL regex
    text = stripHTML(text) #Turns potentially unsafe text into database-friendly text
    for x in markdown:
        m = markdown[x]
        borders = m['text'].split("{TEXT}")
        html = m['html'].split("{TEXT}")
        currentRegex = fr"(?<={re.escape(borders[0])})((.|\n)*)(?={re.escape(borders[1])})"
        if bool(re.search(currentRegex, text)) == True:
            if len(re.search(currentRegex, text).group(0)) > 0:
                text = text.replace(re.search(currentRegex, text).group(0), html[0]+re.search(currentRegex, text).group(0)+html[1])
            text = text.replace(borders[0], "")
            text = text.replace(borders[1], "")
            if m['include'] == "no": #This checks if the text needs to be returned after the tags are matched so other tags aren't added on. This is for something like the [code] tags so that you can safely add something like *text* into the text
                print("")
    lines = text.splitlines(True)
    result = ""
    #This is the part that handles reply quotes, link-quotes, greentext- etc. 
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

@app.template_filter("simplifyTime")
def simplifyTime(minutes):
    time = {
        'Year':525600,
        'Month':43800,
        'Day':1440,
        'Hour':60,
        'Minute':1     
    }
    if minutes == None:
        return "Forever"
    result = ""
    for unit in time:
        if minutes >= time[unit]:
            name = unit
            floor = math.floor(minutes/time[unit])
            if floor > 1:
                name = unit+"s"
            result += f"{str(floor)} {name} "
            minutes = minutes - floor*time[unit]
    return result

@app.template_filter("loadJSON")
def loadJSON(string):
    return json.loads(string)

#Returns MD5 hash of file.
@app.template_filter("getFileHash")
def getFileHash(file):
    return hashlib.md5(open(file,'rb').read()).hexdigest()


#Make local timestamps
#add relative times

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404


#Code ran before every request.
@app.before_request 
def before_request_callback():
    checkGroup() #Checks if user has a group assigned, if not, gives them lowest possible permissions.
    global globalSettings
    if 'username' not in session:
        session['username'] = None
    globalSettings = reloadSettings() #Reloads the global settings. 



#index
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', data=globalSettings, currentTheme=request.cookies.get('theme'), total=getTotal(), lastHour=lastHour(), themes=themes)

#boards
@app.route('/boards', methods=['GET'])
def boards():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards")
    sqlData = cursor.fetchall()
    return render_template('boards.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, themes=themes)

#help page
@app.route('/help', methods=['GET'])
def help():

    return render_template('help.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#FAQ page
@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#global settings redirect
@app.route('/globalsettings', methods=['GET'])
def siteSettings():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM rules WHERE type = 0")
    rules = cursor.fetchall()
    try:
        if int(session['group']) <= 1:
            return render_template('siteSettings.html', data=globalSettings, logData=reloadLogSettings(), currentTheme=request.cookies.get('theme'), themes=themes, groups=groups, rules=rules)
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#Save global settings
@app.route('/saveSettings', methods=['POST'])
def saveSettings():
    if request.method == 'POST':
        try:
            if int(session['group']) <= 1:
                result = request.form.to_dict()
                for x in result:
                    if result[x].isnumeric() == True:
                        result[x] = int(result[x])
                if logConfig['log-global-settings'] == 'on': #Checks if logs are enabled
                    difference = DeepDiff(globalSettings, result, ignore_order=True)
                    if len(difference) > 0:
                        difference = difference.to_json()
                        storeLog("globalSettingsUpdate", "Global Settings Updated", session['username'], request.remote_addr, time.time(), {'changes': difference}, None)
                with open('./config/config.json', 'w') as f:
                    json.dump(result, f, indent=4)
                return redirect(url_for('siteSettings'))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
@app.route('/saveLogSettings', methods=['POST'])
def saveLogSettings():
    if request.method == 'POST':
        try:
            if int(session['group']) <= 1:
                result = request.form.to_dict()
                if logConfig['log-log-settings'] == 'on': #Checks if logs are enabled
                    difference = DeepDiff(logConfig, result, ignore_order=True)
                    if len(difference) > 0:
                        difference = difference.to_json()
                        storeLog("globalSettingsUpdate", "Logging Settings Updated", session['username'], request.remote_addr, time.time(), {'changes': difference}, None)
                with open('./config/logs.json', 'w') as f:
                    json.dump(result, f, indent=4)
                return redirect(url_for('siteSettings'))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

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
        if int(session['group']) <= 1 or currentBoard != None: #checks if the board exists or the user has admin+ perms
            if int(session['group']) <= 1 or currentBoard['owner'] == session['username']: #checks if the user has admin+ perms first
                if logConfig['log-rules'] == 'on':
                    storeLog("addRule", "Rule added", session['username'], request.remote_addr, time.time(), {"board": board, "rule": request.form['newRule']}, None)
                cursor.execute("INSERT INTO rules VALUES (NULL, %s, %s, %s)", (request.form['newRule'], request.form['type'], board))
                mysql.connection.commit()
                if request.form['type'] == "0":
                    return redirect(url_for("siteSettings"))
                else:
                    return redirect(url_for("manageBoard", board=board))
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)        
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#Delete Rule
#Add checks so you can't delete rules from other boards or global settings by changing the HTML of rules on board management pages. 
@app.route('/deleteRule', methods=['POST'])
def deleteRule():
    if request.method == 'POST':
        if request.form['board'] == "NULL":
            board = None
        else:
            board = request.form['board']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri = %s", [board])
        currentBoard = cursor.fetchone()
        if int(session['group']) <= 1 or currentBoard != None:
            if int(session['group']) <= 1 or currentBoard['owner'] == session['username']:
                cursor.execute("SELECT * FROM rules WHERE id = %s", [int(request.form['id'])])
                if logConfig['log-rules'] == 'on':
                    storeLog("removeRule", "Rule deleted", session['username'], request.remote_addr, time.time(), {"board": board, "rule": cursor.fetchone()['content']}, None)
                if board == None:
                    cursor.execute("DELETE FROM rules WHERE id = %s AND board IS NULL", [int(request.form['id'])])
                else:
                    cursor.execute("DELETE FROM rules WHERE id = %s AND board = %s", (int(request.form['id']), board))
                mysql.connection.commit()
            if request.form['type'] == "0":
                return redirect(url_for("siteSettings"))
            else:
                return redirect(url_for("manageBoard", board=board))
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)        
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/account', methods=['GET'])
def accountSettings():
    try:
        if session['loggedin'] == True:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards")
            sqlData = cursor.fetchall()
            return render_template('accountSettings.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, themes=themes)
        else:
            return render_template('error.html', errorMsg=errors['notLoggedIn'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)   
@app.route('/account/passwordchange', methods=['POST'])
def updatePassword():
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
                    if logConfig["log-self-password-change"] == 'on':
                        storeLog("passwordUpdate", "User has changed their password", session['username'], request.remote_addr, time.time(), {}, None)
                    cursor.execute("UPDATE accounts SET password=%s WHERE username=%s", (returnHash(newPassword), session['username']))
                    mysql.connection.commit()
                    session.pop('loggedin', None)
                    session.pop('id', None)
                    session.pop('username', None)
                    session.pop('group', None)
                    return render_template('login.html', msg="Password successfully updated, please log in.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                else:
                    return render_template('error.html', errorMsg=errors['passwordsDoNotMatch'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            else:
                return render_template('error.html', errorMsg=errors['incorrectPassword'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            


@app.route('/account/emailchange', methods=['POST'])
def updateEmail():
    if request.method == 'POST':
        try:
            if session['loggedin'] == True:
                email = request.form['email']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                if logConfig["log-self-email-change"] == 'on':
                    cursor.execute("SELECT * FROM accounts WHERE username=%s", [session['username']])
                    storeLog("emailUpdate", "User has changed their email", session['username'], request.remote_addr, time.time(), {"oldEmail":cursor.fetchone()['email'], "newEmail":email}, None)
                cursor.execute("UPDATE accounts SET email=%s WHERE username=%s", (email, session['username']))
                session.pop('email', None)
                mysql.connection.commit()
                return redirect(url_for('accountSettings'))
            else:
                return render_template('error.html', errorMsg=errors['notLoggedIn'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)




#board management page
@app.route('/boards/manage', methods=['GET'])
def boardManagement():
    try:
        if int(session['group']) <= 1:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards")
            sqlData = cursor.fetchall()
            msg=""
            return render_template('boardManagement.html', data=globalSettings, currentTheme=request.cookies.get('theme'), sqlData=sqlData, msg="", themes=themes)
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)


#Individual board management
@app.route('/<board>/manage', methods=['GET'])
def manageBoard(board):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
    sqlData = cursor.fetchone()
    cursor.execute("SELECT * FROM rules WHERE type = 1 and board = %s", [board])
    rules = cursor.fetchall()
    if sqlData == None:
        return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
    msg=""
    cursor.execute("SELECT * FROM banners WHERE board=%s", [board])
    bannerData = cursor.fetchall()
    try:
        if int(session['group']) <= 1 or sqlData['owner'] == session['username']:
            return render_template('manageBoard.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=sqlData, bannerData=bannerData, msg=msg, themes=themes, rules=rules)
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        print(e)
#create board
@app.route('/createboard', methods=['POST'])
def createBoard():
    if request.method == 'POST':
        try:
            if globalSettings['requiredRole'] >= int(session['group']):
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM boards WHERE uri=%s", [request.form['uri']])
                board = cursor.fetchone()
                if board:
                    return redirect(url_for('boardManagement', msg="Board already exists"))
                else:
                    cursor.execute("INSERT INTO boards VALUES (%s, %s, %s, %s, 'Anonymous', '', 0, 0, 0, 0, %s)",(request.form['uri'].lower(), request.form['name'], request.form['description'], session['username'], globalSettings['pageThreads'])) #create the board in the MySQL database
                    mysql.connection.commit()
                    if logConfig['log-board-creation'] == 'on':
                        cursor.execute("SELECT * FROM boards WHERE uri=%s", [request.form['uri']])
                        storeLog("createBoard", "Board created", session['username'], request.remote_addr, time.time(), cursor.fetchone(), request.form['uri'].lower())
                    path = os.path.join(globalSettings['bannerLocation'], request.form['uri']) #make folder for banner. 
                    os.mkdir(path) 
                    path = os.path.join(globalSettings['mediaLocation'], request.form['uri']) #make folder for files.  
                    os.mkdir(path) 
                    return redirect(url_for('boardManagement'))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            print(e)
#delete board
@app.route('/<board>/delete', methods=['POST'])
def deleteBoard(board):
    if request.method == 'POST':
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
            boardData = cursor.fetchone()
            if boardData == None:
                return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
            if boardData['owner'] == session['username'] or int(session['group']) <= 1:
                if 'deleteBoard' not in request.form:
                    return render_template('error.html', errorMsg=errors['confirmBoardDeletion'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                if request.form["deleteBoard"] != "on":
                    return render_template('error.html', errorMsg=errors['confirmBoardDeletion'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                if logConfig['log-board-deletion'] == 'on':
                    storeLog("deleteBoard", "Board deleted", session['username'], request.remote_addr, time.time(), boardData, board)
                cursor.execute("DELETE FROM boards WHERE  uri=%s AND owner=%s LIMIT 1", (board, session['username']))
                cursor.execute("DELETE FROM posts WHERE board=%s", [board])
                mysql.connection.commit()
                path = os.path.join(globalSettings['bannerLocation'], board) #path for banner folder for specific board. 
                for x in os.listdir(path):
                    os.remove(os.path.join(path, x))
                os.rmdir(path)#remove banner folder
                path = os.path.join(globalSettings['mediaLocation'], board) #path for media folder for specific board. 
                for x in os.listdir(path):
                    os.remove(os.path.join(path, x))
                os.rmdir(path)#remove media sub-folder
                return redirect(url_for('boardManagement'))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            print(e)
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
@app.route('/<board>/update', methods=['POST'])
def updateBoard(board):
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
        boardData = cursor.fetchone()
        if boardData == None:
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        try:
            if boardData['owner'] == session['username'] or int(session['group']) <= 1:
                name = request.form['name']
                desc = request.form['description']
                anonymous = request.form['anonymous']
                message = request.form['message']
                captcha = request.form['captcha']
                perPage = int(request.form['perPage'])
                if perPage > globalSettings['pageThreads']:
                    perPage = globalSettings['pageThreads']
                cursor.execute("UPDATE boards SET name=%s, description=%s, anonymous=%s, message=%s, captcha=%s, perPage=%s WHERE uri=%s", (name, desc, anonymous, message, captcha, perPage, board))
                mysql.connection.commit()
                if logConfig['log-board-update'] == 'on':
                    cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
                    difference = DeepDiff(boardData, cursor.fetchone())
                    if len(difference) > 0:
                        difference = difference.to_json()
                        storeLog("boardUpdate", "Board Settings Updated", session['username'], request.remote_addr, time.time(), {'changes': difference}, board)
                return redirect(url_for('manageBoard', board=board))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return errors['RequestNotPost']

@app.route('/<board>/setowner', methods=['POST'])
def setOwner(board):   
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
        boardData = cursor.fetchone()
        if boardData == None:
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        try:
            if int(session['group']) <= 1 or session['username'] ==  boardData['owner']:
                cursor.execute("UPDATE boards SET owner=%s WHERE uri=%s", (request.form['owner'], board))
                mysql.connection.commit()
                if logConfig['log-board-ownerchange'] == 'on':
                    storeLog("ownerChange", "Board owner changed", session['username'], request.remote_addr, time.time(), {'oldOwner':boardData['owner'], 'newOwner':request.form['owner']}, board)
                return redirect(url_for("manageBoard", board=board))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#banner management

#upload banner and create sql entry
@app.route('/<board>/uploadbanner', methods=['POST'])
def uploadBanner(board):
    if request.method == 'POST':
        banner = request.files['file']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
        sqlData = cursor.fetchone()
        try:
            if sqlData['owner'] == session['username'] or int(session['group']) <= 1:
                path = os.path.join(globalSettings['bannerLocation'], board)
                filename = secure_filename(banner.filename)
                extention = pathlib.Path(filename).suffix
                filename = str(time.time())+extention
                banner.save(os.path.join(path, filename))
                size = os.path.getsize(os.path.join(path, filename))
                cursor.execute("INSERT INTO banners VALUES (%s, %s, %s)",(board, filename, size))
                mysql.connection.commit()
                if logConfig['log-banners'] == 'on':
                    storeLog("bannerUpload", "Banner upload", session['username'], request.remote_addr, time.time(), {'filename': filename}, board)
                return redirect(url_for('manageBoard', board=board)) #Find a better solution for this. 
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
    else:
        return render_template('error.html', errorMsg=errors['RequestNotPost'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)    
@app.route('/<board>/deletebanner', methods=['POST'])
def deleteBanner(board):
    name = request.args.get('name', type=str)
    if request.method == 'POST':
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
            sqlData = cursor.fetchone()
            if sqlData['owner'] == session['username'] or int(session['group']) <= 1:
                cursor.execute("DELETE FROM banners WHERE filename=%s LIMIT 1", [name]) 
                mysql.connection.commit()
                cursor.execute("SELECT * FROM banners WHERE board=%s", [board])
                bannerData = cursor.fetchall()
                path = os.path.join(globalSettings['bannerLocation'], board)
                os.remove(os.path.join(path, name))
                if logConfig['log-banners'] == 'on':
                    storeLog("bannerDelete", "Banner deleted", session['username'], request.remote_addr, time.time(), {'filename': name}, board)
                return redirect(url_for('manageBoard', board=board))
        except Exception as e:
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 

#Account stuff  Most of it isn't mine lol. 
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        passwordHash = returnHash(request.form['password'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (request.form['username'], passwordHash))
        account = cursor.fetchone()
        if account:
            if account['banned'] == 1:
                msg = 'This user is banned.'
            elif account['password'] == passwordHash and account['username'] == request.form['username']:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['group'] = account['group']
                session['email'] = account['email']
                if logConfig['log-logins'] == 'on':
                    storeLog("loginActions", "User logged in", session['username'], request.remote_addr, time.time(), {}, None)
                return redirect(url_for('index'))
            else:
                msg = 'Incorrect username or password'
        else:
            msg = 'Incorrect username or password'
    return render_template('login.html', msg=msg, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/logout')
def logout():
    try:
        if logConfig['log-logout'] == 'on':
            storeLog("loginActions", "User logged out", session['username'], request.remote_addr, time.time(), {}, None)
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        session.pop('group', None)
        return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if globalSettings['enableRegistration'] == 'on':
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            if 'email' in request.form:
                email = request.form['email']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists'
            elif len(email) > 0:
                if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                    msg = 'Invalid email address!'
            elif not re.match(r'^[a-zA-Z0-9_.-]*$', username):
                msg = 'Username must contain only characters and numbers'
            elif not username or not password:
                msg = 'Please fill out the form'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                password = returnHash(password)
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, 4, %s, %s, 0)', (username, password, email, time.time(), str(request.remote_addr)))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                if logConfig['log-register'] == 'on':
                    storeLog("loginActions", "User registered an account", username, request.remote_addr, time.time(), {}, None)
                return render_template('login.html', msg="Registration complete, please log in", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        elif request.method == 'POST':
            msg = 'Please fill out the form!'
        return render_template('register.html', msg=msg, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return render_template('register.html', msg="Registrations are currently disabled.", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#Checks if captcha has expired. If it has, returns true so generateCaptcha() can generate a new one. 
def checkCaptchaState():
    if "captchaExpire" in session and "captcha" in session and "captchaF" in session and os.path.isfile(session["captchaF"]):
        if datetime.now() >= session["captchaExpire"]:
            return True
        else:
            return False
    else:
        return True #Generates a new captcha if required information is missing from the session. 

#generate captcha for the board
#Syntax: generateCaptcha(captcha length)
def generateCaptcha(difficulty):
    if checkCaptchaState() == False: #If current session captcha is not expired, return current captcha. 
        return session["captchaF"]
    if "captchaF" in session and os.path.isfile(session["captchaF"]): #removes old captcha file.
        os.remove(session["captchaF"])
    captchaText = randomString(difficulty)
    print("#########################")
    print(captchaText)
    print("#########################")
    currentCaptcha = captcha.generate(captchaText)
    filename = time.time()
    captcha.write(captchaText, f'./static/captchas/{filename}.png')
    session["captcha"] = captchaText
    session["captchaF"] = f'./static/captchas/{filename}.png'
    session["captchaExpire"] = datetime.now() + timedelta(minutes = globalSettings['captchaExpire']) #Set expire time for captcha. Add into global settings later. 
    return f'./static/captchas/{filename}.png'

def clearCaptcha():
    session.pop('captcha', None)
    if os.path.isfile(session["captchaF"]): #deletes captcha file if it somehow hasn't been deleted already. (Just to make sure)
        os.remove(session["captchaF"])
    session.pop('captchaF', None)
    session.pop('captchaExpire', None)

#get all threads for a board
def getThreads(uri):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM posts WHERE board = %s AND type = 1", [uri])
    threads = cursor.fetchall()
    return threads

#board page
@app.route('/<board>/', methods=['GET'])
def boardPage(board):
    #try:
        if request.cookies.get('ownedPosts') != None:
            ownedPosts = json.loads(request.cookies.get('ownedPosts')) #gets posts the current user has made for (you)s
        else:
            ownedPosts = {}
        if request.cookies.get('hidden') != None:
            hidden = json.loads(request.cookies.get('hidden'))
        else:
            hidden = {}
        filePass = checkFilePass() #gets user's password for files
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
        board = cursor.fetchone()
        if board == None:
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        posts = bumpOrder(board['uri'])
        postLength = len(posts)
        posts = posts[0:1*board['perPage']]
        path = os.path.join(globalSettings['bannerLocation'], board['uri'])
        if len(os.listdir(path)) > 0:
            banner = os.path.join(path, random.choice(os.listdir(path)))
        else:
            banner = "static/banners/defaultbanner.png"
        if board['captcha'] == 1:
            captcha = generateCaptcha(globalSettings['captchaDifficulty'])
            return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board['uri'], boardData=board, banner=banner, captcha=captcha, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, hidden=hidden, page=1, themes=themes)
        else:
            return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board['uri'], boardData=board, banner=banner, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, hidden=hidden,page=1, themes=themes)
        return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
    #except Exception as e:
    #    print(e)
    #    return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#individual pages
@app.route('/<board>/<int:page>', methods=['GET'])
def boardNumPage(board, page):
    try:
        if request.cookies.get('ownedPosts') != None:
            ownedPosts = json.loads(request.cookies.get('ownedPosts')) #gets posts the current user has made for (you)s
        else:
            ownedPosts = {}
        filePass = checkFilePass()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM boards WHERE uri=%s', [board])
        board = cursor.fetchone()
        posts = bumpOrder(board['uri'])
        postLength = len(posts)
        posts = posts[(page-1)*board['perPage']:page*board['perPage']]
        if posts:
            path = os.path.join(globalSettings['bannerLocation'], board['uri'])
            if len(os.listdir(path)) > 0:
                banner = os.path.join(path, random.choice(os.listdir(path)))
            else:
                banner = "static/banners/defaultbanner.png"
            if board['captcha'] == 1:
                captcha = generateCaptcha(globalSettings['captchaDifficulty'])
                return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board['uri'], boardData=board, banner=banner, captcha=captcha, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, page=page, themes=themes)
            else:
                return render_template('board.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board['uri'], boardData=board, banner=banner, threads=posts, filePass=filePass, postLength=postLength, owned=ownedPosts, page=page, themes=themes)
        else:
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/<board>/rules', methods=['GET'])
def boardRules(board):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM boards WHERE uri = %s", [board])
        board = cursor.fetchone()
        if board != None:
            cursor.execute("SELECT * FROM rules WHERE board = %s", [board['uri']])
            rules = cursor.fetchall()
            return render_template('rules.html', data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes, rules=rules, board=f"/{board['uri']}/")
        else:
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#thumbnail generation
def thumbnail(image, board, filename, ext):
    try:
        image = Image.open(image)
        size = globalSettings['thumbnailX'], globalSettings['thumbnailY']
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
    if request.method == 'POST':
        if checkBanned(str(request.remote_addr)) == True:
            return render_template('error.html', errorMsg=errors['banned'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        filePass = checkFilePass()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if "board" not in request.form: #Checks if a board was given.
            return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [request.form['board']])
        board = cursor.fetchone()
        if board == None: #Returns a 404 if board doesn't exist
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        tripcode = None
        mimeTypes = globalSettings['mimeTypes'].split(',')
        curTime = time.time()
        if "name" in request.form and len(request.form['name']) > 0: #Checks if a name is given
            name = request.form['name']
            name = stripHTML(name)
            session['name'] = name
            tripcode = checkTrip(name, int(session['group']))
            if tripcode != False:
                name = name.split("##",1)[0]
            else:
                tripcode = None
        else:
            name = board['anonymous'] #sets name to default board anon name
        if 'subject' in request.form and len(request.form['subject']) > 0: #Checks if a subject was given
            subject = request.form['subject']
            subject = stripHTML(subject)
        else:
            subject = None
        if 'options' in request.form and len(request.form['options']) > 0: #Checks if options were given
            options = request.form['options']
            options = stripHTML(options)
            options = options.lower()
        else:
            options = None     
        if "spoiler" in request.form: #Checks if a spoiler was indicated
            if request.form['spoiler'] == "on":
                spoiler = 1
            else:
                spoiler = 0
        else:
            spoiler = 0
        if 'password' in request.form: #Checks if a password was given in the request
            filePass = request.form['password']
        if 'comment' not in request.form and len(request.files['file'].filename) == 0: #Checks if all required files are present
            return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        comment = request.form['comment']
        comment = stripHTML(comment)
        postLink = checkPostLink(comment)
        if board['captcha'] == 1: #Checks if the board has captcha enabled, and if so, checks if the entred captcha text is correct
            clearCaptcha() #clears captcha so it can't be used again to make a new thread.
            if 'captcha' not in request.form:
                return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            if session['captcha'] != request.form['captcha']: #Checks if the captcha is incorrect.
                return render_template('error.html', errorMsg=errors['incorrectCaptcha'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        files = request.files.getlist("file") #Gets all the files from the request
        if len(files) > globalSettings['maxFiles']: #check if too many files are uploaded
            return render_template('error.html', errorMsg=errors['fileLimitExceeded'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        else:
            filenames = []
            filePaths = []
            for f in files: #downloads the files and stores them on the disk
                if f.mimetype in mimeTypes:
                    filename = uploadFile(f, board['uri'], str(curTime), spoiler)
                    filePaths.append(filename)
                    filenames.append(secure_filename(f.filename))
                else:
                    return render_template('error.html', errorMsg=errors['incorrectFiletype'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
            filenames = ','.join([str(x) for x in filenames])
            filePaths = ','.join([str(x) for x in filePaths])
        number = board['posts']+1
        cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (name, subject, options, comment, number, curTime, number, board['uri'], str(filePaths), str(filenames), str(request.remote_addr), spoiler,filePass, tripcode))
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
        resp = redirect(f"{board['uri']}/thread/{number}")
        resp.set_cookie('ownedPosts', json.dumps(ownedPosts))
        if logConfig['log-thread-creation'] == 'on':
            storeLog("threadCreation", "Thread created", session['username'] if 'username' in session else None, request.remote_addr, curTime, {"number": number, "files": str(filenames), "url": f"/{board['uri']}/thread/{number}"}, board['uri'])
        return resp
    else:
        return errors['RequestNotPost'] 

@app.route('/<board>/thread/<thread>', methods=['GET'])
@app.route('/<board>/thread/<thread>', methods=['GET'])
def thread(board, thread):
    try:
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
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [board])
        board = cursor.fetchone()
        if board == None: #board doesn't exist
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        path = os.path.join(globalSettings['bannerLocation'], board['uri'])
        if len(os.listdir(path)) > 0:
            banner = os.path.join(path, random.choice(os.listdir(path)))
        else:
            banner = "static/banners/defaultbanner.png"
        if board['captcha'] == 1:
            captcha = generateCaptcha(globalSettings['captchaDifficulty'])
            return render_template('thread.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board['uri'], boardData=board, banner=banner, captcha=captcha, posts=posts, owned=ownedPosts, thread=parentPost[0], filePass=filePass, themes=themes)
        else:
            return render_template('thread.html', data=globalSettings, currentTheme=request.cookies.get('theme'), board=board['uri'], boardData=board, banner=banner, posts=posts, thread=parentPost[0], owned=ownedPosts, filePass=filePass, themes=themes)
        return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/reply', methods=['POST'])
def reply():
    if request.method == 'POST':
        if checkBanned(str(request.remote_addr)) == True:
            return render_template('error.html', errorMsg=errors['banned'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        filePass = checkFilePass()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if "board" not in request.form: #Checks if a board was given.
            return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        cursor.execute("SELECT * FROM boards WHERE uri=%s", [request.form['board']])
        board = cursor.fetchone()
        if board == None: #Returns a 404 if board doesn't exist
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        tripcode = None
        mimeTypes = globalSettings['mimeTypes'].split(',')
        curTime = time.time()
        number = board['posts']+1
        if "name" in request.form and len(request.form['name']) > 0: #Checks if a name is given
            name = request.form['name']
            name = stripHTML(name)
            session['name'] = name
            tripcode = checkTrip(name, int(session['group']))
            if tripcode != False:
                name = name.split("##",1)[0]
            else:
                tripcode = None
        else:
            name = board['anonymous'] #sets name to default board anon name
        if 'subject' in request.form and len(request.form['subject']) > 0: #Checks if a subject was given
            subject = request.form['subject']
            subject = stripHTML(subject)
        else:
            subject = None
        if 'options' in request.form and len(request.form['options']) > 0: #Checks if options were given
            options = request.form['options']
            options = stripHTML(options)
            options = options.lower()
        else:
            options = None     
        if "spoiler" in request.form: #Checks if a spoiler was indicated
            if request.form['spoiler'] == "on":
                spoiler = 1
            else:
                spoiler = 0
        else:
            spoiler = 0
        if 'password' in request.form: #Checks if a password was given in the request
            filePass = request.form['password']
        if 'comment' not in request.form:
            return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        comment = request.form['comment']
        comment = stripHTML(comment)
        postLink = checkPostLink(comment)        
        if board['captcha'] == 1: #Checks if the board has captcha enabled, and if so, checks if the entred captcha text is correct
            clearCaptcha() #clears captcha so it can't be used again to make a new thread.
            if 'captcha' not in request.form:
                return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            if session['captcha'] != request.form['captcha']: #Checks if the captcha is incorrect.
                return render_template('error.html', errorMsg=errors['incorrectCaptcha'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        files = request.files.getlist("file")
        filenames = []
        if request.files['file'].filename != '':
            if len(files) > globalSettings['maxFiles']: #check if too many files are uploaded
                return render_template('error.html', errorMsg=errors['fileLimitExceeded'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            else:
                filenames = []
                filePaths = []
                for f in files: #downloads the files and stores them on the disk
                    if f.mimetype in mimeTypes:
                        filename = uploadFile(f, board['uri'], str(time.time()), spoiler)
                        filePaths.append(filename)
                        filenames.append(secure_filename(f.filename))
                    else:
                        return render_template('error.html', errorMsg=errors['incorrectFiletype'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes) 
                filenames = ','.join([str(x) for x in filenames])
                filePaths = ','.join([str(x) for x in filePaths])
                cursor.execute('INSERT INTO posts VALUES (%s, %s, %s, %s, %s, %s, 2, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (name, subject, options, comment, number, curTime, request.form['thread'], board['uri'], str(filePaths), str(filenames), str(request.remote_addr), spoiler,filePass, tripcode))                
        else: #No files are given
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
        socketio.emit("replyEvent", broadcast=True) #Send reload signal through websocket
        if logConfig['log-thread-creation'] == 'on':
            storeLog("reply", "Reply to thread", session['username'] if 'username' in session else None, request.remote_addr, curTime, {"number": number, "files": str(filenames), "thread": request.form['thread'], "url": f"/{board['uri']}/thread/{request.form['thread']}#{number}"}, board['uri'])
        return resp
    else:
        return errors['RequestNotPost']





@app.route('/<board>/postActions', methods=['POST'])
def postActions(board):
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
                    cursor.execute("SELECT * FROM posts WHERE thread=%s AND board=%s AND type=2", (int(request.form['post']), board))
                    posts = cursor.fetchall()
                    for x in posts:
                        files = []
                        if x['files'] != None:
                            files = files + x['files'].split(',')
                        for file in files:
                            thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                            os.remove(file)
                            os.remove(thumbPath)
                    cursor.execute("DELETE FROM posts WHERE thread=%s AND board=%s  AND type=2", (int(request.form['post']), board))
                if logConfig['log-post-delete'] == 'on':
                    if session['group'] <= 3:
                        storeLog("modPostDelete", "A moderator deleted posts", session['username'], request.remote_addr, time.time(), {'posts': int(request.form['post'])}, board)
                    else:
                        storeLog("postDelete", "A user deleted posts", session['username'], request.remote_addr, time.time(), {'posts': int(request.form['post'])}, board)
                cursor.execute("DELETE FROM posts WHERE number=%s AND board=%s", (int(request.form['post']), board))
                mysql.connection.commit()
                return redirect(url_for("boardPage", board=board))
            else:
                return render_template('error.html', errorMsg=errors['incorrectPassword'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        else:
            return "Still not implemented, check back later"
            #handle reports
    else:
        return errors['RequestNotPost']

@app.route('/<board>/passworddelete', methods=['POST'])
def passworddelete(board):
    if request.method == 'POST':
        if "password" not in request.form:
            return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM posts WHERE password=%s and board=%s", (request.form['password'], board))
        posts = cursor.fetchall()
        if posts == None:
            return redirect(url_for("boardPage", board=board))
        for post in posts:
            if post['files'] != None: #delete files from disk
                files = post['files'].split(',')
                for file in files:
                    thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                    os.remove(file)
                    os.remove(thumbPath)
            if post['type'] == 1: #Check if post is a thread and delete all child posts. 
                cursor.execute("SELECT * FROM posts WHERE thread=%s AND board=%s AND type=2", (post['number'], board))
                children = cursor.fetchall()
                for x in children:
                    files = []
                    if x['files'] != None:
                        files = files + x['files'].split(',')
                    for file in files:
                        thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                        os.remove(file)
                        os.remove(thumbPath)
                cursor.execute("DELETE FROM posts WHERE thread=%s AND board=%s AND type=2", (post['number'], board))
        if logConfig['log-post-delete'] == 'on':
            numbers = []
            for post in posts:
                numbers.append(post['number'])
            storeLog("postDelete", "A user deleted their posts", session['username'], request.remote_addr, time.time(), {'posts': str(numbers)}, board)
        cursor.execute("DELETE FROM posts WHERE password=%s and board=%s", (request.form['password'], board))
        mysql.connection.commit()
        return redirect(url_for("boardPage", board=board))
    else:
        return errors['RequestNotPost']
#Moderation pages. 

#Account moderation
@app.route('/users', methods=['GET'])
def users():
    try:
        if session['group'] <= 1:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts")
            users = cursor.fetchall()
            cursor.execute("SELECT * FROM groups")
            groups = cursor.fetchall()
            cursor.execute("SELECT * FROM boards")
            boards = cursor.fetchall()
            cursor.execute("SELECT * FROM groups WHERE id > %s", [session['group']])
            availableGroups = cursor.fetchall()
            return render_template('users.html', users=users, groups=groups, aGroups=availableGroups,boards=boards,data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

#Manage individual user
@app.route('/user/<user>/manage', methods=['GET'])
def manageUser(user):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = %s", [user])
        user = cursor.fetchone()
        cursor.execute("SELECT * FROM groups WHERE id > %s", [session['group']])
        groups = cursor.fetchall()
        cursor.execute("SELECT * FROM bans WHERE user = %s", [user['username']])
        ban = cursor.fetchone()
        if user == None: 
            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
        if user['group'] <= session['group']: #Returns an insufficient permission error if the user's group has less permissions than the requested user
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        if session['group'] <= 1:
            return render_template('manageUser.html', user=user, groups=groups, ban=ban, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        else:
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    except Exception as e:
        print(e)
        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
#Update user information
@app.route("/user/<user>/update", methods=['POST'])
def updateUser(user):
    if request.method == 'POST':
        try:
            if session['group'] <= 1:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM accounts WHERE username = %s", [user])
                userData = cursor.fetchone()
                if userData == None:
                    return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
                email = request.form['email']
                if len(email) == 0:
                    email = None
                if 'newPassword' and 'confirmPassword' in request.form and len(request.form['newPassword']) > 0 and len(request.form['confirmPassword']) > 0:
                    if request.form['newPassword'] == request.form['confirmPassword']:
                        cursor.execute("UPDATE accounts SET password=%s, `email`=%s, `group`=%s WHERE username=%s", (returnHash(request.form['newPassword']), email, int(request.form['group']), user))
                    else:
                        return render_template('error.html', errorMsg=errors['passwordsDoNotMatch'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                else:
                    cursor.execute("UPDATE accounts SET email=%s, `group`=%s WHERE username=%s", (email, int(request.form['group']), user))
                mysql.connection.commit()
                if logConfig['log-mod-user-update'] == 'on':
                    cursor.execute("SELECT * FROM accounts WHERE username = %s", [user])
                    difference = DeepDiff(userData, cursor.fetchone())
                    if len(difference) > 0:
                        difference = difference.to_json()
                        storeLog("modUserUpdate", "A moderator updated a user", session['username'], request.remote_addr, time.time(), {'user':user, 'changes':str(difference)}, None)
                return redirect(url_for("manageUser", user=user))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return errors['RequestNotPost']
#Delete user
@app.route("/user/<user>/delete", methods=['POST'])
def deleteUser(user):
    if request.method == 'POST':
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts WHERE username=%s", [user])
            userData = cursor.fetchone()
            if session['group'] < userData['group'] or user == session['username']: #Checks if the user has perms over the user being deleted or if the user is deleting themselves. 
                if 'confirm-delete' in request.form and request.form['confirm-delete'] == 'confirm':
                    try:
                        if userData == None: #User doesn't exist
                            return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
                        if userData['group'] < session['group']: #Permissions are too low
                            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                        cursor.execute("SELECT * FROM boards WHERE owner=%s", [user]) #Checks if the deleted user owned any boards, and if so, transfers ownership of the boards to the current user. 
                        boards = cursor.fetchall()
                        if boards != None:
                            for board in boards:
                                cursor.execute("UPDATE boards SET owner=%s WHERE owner=%s", (session['username'], user))
                        mysql.connection.commit()
                        cursor.execute("DELETE FROM accounts WHERE username=%s AND id=%s", (user, userData['id'])) #Delete account
                        cursor.execute("DELETE FROM bans WHERE username=%s", [user]) #Remove bans so that if anther user with the same username is registered it won't mess up the DB
                        mysql.connection.commit()
                        if logConfig['log-mod-user-update'] == 'on':
                            storeLog("modUserDelete", "A moderator deleted a user", session['username'], request.remote_addr, time.time(), {'user':user}, None)
                        return redirect(url_for("users"))
                    except Exception as e:
                        print(e)
                        return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                else:
                    return render_template('error.html', errorMsg="You must confirm user deletion", data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return errors['RequestNotPost']

#User creation through the /users page
@app.route("/user/create", methods=['POST'])
def createUser():
    if request.method == 'POST':
        try:
            if int(session['group']) <= 1: 
                if 'username' and 'password' and 'confirm-password' and 'group' not in request.form:
                    return render_template('error.html', errorMsg=errors['unfilledFields'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                if request.form['password'] != request.form['confirm-password']:
                    return render_template('error.html', errorMsg=errors['passwordsDoNotMatch'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                if int(request.form['group']) <= int(session['group']):
                    return "Insufficient permissions"
                if bool(re.match(r'^[a-zA-Z0-9_.-]*$', request.form['username'])) == False:
                    return render_template('error.html', errorMsg=errors['usernameRegexFail'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM accounts WHERE username=%s", [request.form['username']])
                if cursor.fetchone() != None:
                    return render_template('error.html', errorMsg=errors['accountExists'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                if 'email' in request.form and len(request.form['email']) > 0:
                    if bool(re.match(r'[^@]+@[^@]+\.[^@]+', request.form['email'])) == False:
                        return render_template('error.html', errorMsg=errors['emailRegexFail'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
                    email = request.form['email']
                else:
                    email = None
                creationTime = time.time()
                cursor.execute("INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, %s, %s, 0)", (request.form['username'], returnHash(request.form['password']), email, request.form['group'], creationTime, str(request.remote_addr)))
                if logConfig['log-mod-user-update'] == 'on':
                    storeLog("modUserCreate", "A moderator created a user", session['username'], request.remote_addr, creationTime, {'user':request.form['username'], "group":request.form['group'], "email":email}, None)
                mysql.connection.commit()                
                return redirect(url_for("manageUser", user=request.form['username']))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return errors['RequestNotPost']

#Ban User
@app.route("/user/<user>/ban", methods=['POST'])
def banUser(user):
    if request.method == 'POST':
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts WHERE username=%s", [user])
            userData = cursor.fetchone()
            if userData == None: #Checks if the user exists. 
                return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
            if userData['banned'] == 1: #Checks if the user is already banned. 
                return render_template('error.html', errorMsg=errors['alreadyBanned'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            if int(session['group']) <= 1 and session['group'] < userData['group']:
                if 'reason' in request.form and len(request.form['reason']) > 0: #Checks if a reason was given
                    reason = request.form['reason']
                else:
                    reason = None
                if 'length' in request.form and len(request.form['length']) > 0: #Checks if a reason was given
                    length = getMinutes(request.form['length'])
                else:
                    length = None
                cursor.execute("UPDATE accounts SET banned=1 WHERE username=%s", [user])
                currentTime = time.time()
                cursor.execute("INSERT INTO bans VALUES(NULL, %s, %s, %s, NULL, %s)", (reason, length, user, currentTime))
                if logConfig['log-user-ban'] == 'on':
                    cursor.execute("SELECT * FROM bans WHERE user=%s", [user])
                    storeLog("userBan", "A user has been banned", session['username'], request.remote_addr, currentTime, {"id":cursor.fetchone()['id'],'user':user, "reason": reason, "length":length}, None)
                mysql.connection.commit()
                return redirect(url_for("manageUser", user=user))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    else:
        return errors['RequestNotPost']  
#Unban user
@app.route("/user/<user>/unban", methods=['POST'])
def unbanUser(user):
    if request.method == 'POST':
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts WHERE username=%s", [user])
            userData = cursor.fetchone()
            if userData == None: #Checks if the user exists. 
                return render_template('404.html', image=get404(), data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes), 404
            if userData['banned'] == 0: #Checks if the user is not banned. 
                return render_template('error.html', errorMsg=errors['notBanned'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
            if int(session['group']) <= 1 and session['group'] < userData['group']:
                cursor.execute("DELETE FROM bans WHERE user=%s", [user])
                cursor.execute("UPDATE accounts SET banned=0 WHERE username=%s", [user])
                if logConfig['log-user-unban']:
                    storeLog("userUnban", "A user has been unbanned", session['username'], request.remote_addr, time.time(), {'user':user}, None)
                mysql.connection.commit()
                return redirect(url_for("manageUser", user=user))
            else:
                return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        except Exception as e:
            print(e)
            return render_template('error.html', errorMsg=e, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route("/logs", methods=['GET'])
def logs():
    if not request.args.get('board', type=str): #Board filter arguments
        board = "board OR board=NULL"
    else:
        board = f'"{request.args.get("board", type=str)}"'
    if not request.args.get('user', type=str): #user filter arguments
        user = "user OR user=NULL"
    else:
        user = f'"{request.args.get("user", type=str)}"'
    if not request.args.get('ip', type=str): #IP filter arguments
        ip = "ip OR ip=NULL"
    else:
        ip = f'"{request.args.get("ip", type=str)}"'
    if not request.args.get("action", type=str): #type of action
        action = "type"
    else:
        action = f'"{request.args.get("action", type=str)}"'
    if not request.args.get('id', type=str): # ID filter arguments
        id = "id"
    else:
        id = f'"{request.args.get("id", type=str)}"'
    query = f"SELECT * FROM logs WHERE id={id} AND type={action} AND user={user} AND ip={ip} AND board={board} ORDER BY id desc" #It just has to be done like this
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    logs = cursor.fetchall()
    return render_template('logs.html', logs=logs, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/latest', methods=['GET'])
def latest():
    if not request.args.get('board', type=str): #Board filter arguments
        board = "board OR board=NULL"
    else:
        board = f'"{request.args.get("board", type=str)}"'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = f"SELECT * FROM posts WHERE board={board} ORDER BY number desc"
    cursor.execute(query)
    posts = cursor.fetchall()
    return render_template('latest.html', posts=posts, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)

@app.route('/latest/actions', methods=['POST'])
def latestActions():
    if request.method == 'POST':
        if session['group'] > 3: #Returns error if insufficient perms
            return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        requestData = json.loads(json.dumps(request.form))
        for x in requestData:
            if x.startswith("post-"):
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                cursor.execute("SELECT * FROM posts WHERE number=%s AND board=%s", (number, board))
                post = cursor.fetchone()
                if "multiple-ban-posters" in request.form: #Checks if the post need to be banned.
                    if request.form['multiple-ban-posters'] == "on": #Checks if the posters need to be banned before the files are deleted
                        reason = None
                        length = None
                        if 'multiple-ban-reason' in request.form: #Checks if a reason is given
                            if len(request.form['multiple-ban-reason']) > 0:
                                reason = request.form['multiple-ban-reason']
                        if 'multiple-ban-length' in request.form: #Checks if the length is given
                            if len(request.form['multiple-ban-length']) > 0:
                                reason = request.form['multiple-ban-reason']
                        cursor.execute("INSERT INTO bans VALUES (NULL, %s, %s, %s, %s)", (reason, length, post['ip'], time.time()))
                if 'multiple-hash-ban-media' in request.form: #Checks if media needs to be banned. STILL NEED TO CHECK AND CREATE DB TABLE!!
                    reason = None
                    if request.form['multiple-hash-ban-media'] == 'on':
                        if 'multiple-hash-ban-reason' in request.form: #Checks if a reason for the hash ban was given
                            if len(request.form['multiple-hash-ban-reason']) > 0:
                                reason = request.form['multiple-hash-ban-reason']
                        for file in post["files"].split(","):
                            cursor.execute("INSERT INTO hashbans VALUES (%s, %s, %s, %s)", (hashlib.md5(open(file,'rb').read()).hexdigest(), reason, session['username'], time.time()))
                if 'multiple-delete-media' in request.form: #Checks if the media needs to be deleted.
                    print(post['files'])
                    if request.form['multiple-delete-media'] == 'on':
                        if post['files'] != None: #delete files from disk
                            files = post['files'].split(',')
                            for file in files:
                                thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                                os.remove(file)
                                os.remove(thumbPath)
                        cursor.execute("UPDATE posts SET files=NULL, fileNames=NULL WHERE number=%s AND board=%s", (number, board))
                if 'multiple-delete-posts' in request.form: #Checks if the post needs to be deleted.
                    if request.form['multiple-delete-posts'] == 'on':
                        if post['files'] != None: #delete files from disk
                            files = post['files'].split(',')
                            for file in files:
                                thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                                os.remove(file)
                                os.remove(thumbPath)
                        cursor.execute("DELETE FROM posts WHERE number=%s AND board=%s", (number, board))
            if x.startswith("ban-"): #Ban individual poster
                currentTime = time.time()
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                cursor.execute("SELECT * FROM posts WHERE number=%s AND board=%s", (number, board))
                post = cursor.fetchone()
                reason = None
                length = None
                if f"banreason-{number}-{board}" in request.form: #Check if reaosn for ban was given
                    if len(request.form[f"banreason-{number}-{board}"]) > 0:
                        reason = request.form[f"banreason-{number}-{board}"]
                if f"banduration-{number}-{board}" in request.form: #Check if length of ban was given
                    if len(request.form[f"banduration-{number}-{board}"]) > 0:
                        length = request.form[f"banduration-{number}-{board}"]
                cursor.execute("INSERT INTO bans VALUES (NULL, %s, %s, NULL, %s, %s)", (reason, length, str(post['ip']), currentTime))
                if logConfig['log-user-ban'] == 'on':
                    storeLog("userBan", "A user has been banned", session['username'], request.remote_addr, currentTime, {'ip':str(post['ip'])  , 'reason': reason, 'length':length}, None)
            if x.startswith("deletemedia-"): #Remove media from post
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                cursor.execute("SELECT * FROM posts WHERE number=%s AND board=%s", (number, board))
                post = cursor.fetchone()
                if post['files'] != None:
                    files = post['files'].split(',')
                    for file in files:
                        thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                        os.remove(file)
                        os.remove(thumbPath)
                    cursor.execute("UPDATE posts SET files=NULL WHERE number=%s AND board=%s", (number, board))
            if x.startswith("spoil-"): #Spoil files
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                cursor.execute("UPDATE posts SET spoiler=1 WHERE number=%s AND board=%s", (number, board))
            if x.startswith("unspoil-"): #Remove spoiler
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                cursor.execute("UPDATE posts SET spoiler=0 WHERE number=%s AND board=%s", (number, board))
            if x.startswith("hashban-"): #Individual post hash ban
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                reason = None
                cursor.execute("SELECT * FROM posts WHERE number=%s AND board=%s", (number, board))
                post = cursor.fetchone()
                if f'hashbanreason-{number}-{board}' in request.form:
                    if len(request.form[f'hashbanreason-{number}-{board}']) > 0:
                        reason = request.form[f'hashbanreason-{number}-{board}']
                for file in post["files"].split(","):
                    cursor.execute("INSERT INTO hashbans VALUES (%s, %s, %s, %s)", (hashlib.md5(open(file,'rb').read()).hexdigest(), reason, session['username'], time.time()))
            if x.startswith("delete-"): #Delete individual post
                print(requestData[x])
                print(requestData[x].split("-"))
                number = requestData[x].split('-')[0]
                board = requestData[x].split('-')[1]
                cursor.execute("SELECT * FROM posts WHERE number=%s AND board=%s", (number, board))
                post = cursor.fetchone()
                if post['files'] != None: #delete files from disk
                    files = post['files'].split(',')
                    for file in files:
                        thumbPath = ".".join(file.split('.')[:-1])+"s."+file.split('.')[3]
                        os.remove(file)
                        os.remove(thumbPath)
                cursor.execute("DELETE FROM posts WHERE number=%s AND board=%s", (number, board))
            mysql.connection.commit()
        return redirect(url_for('latest'))
    else:
        return errors['RequestNotPost']




@app.route('/media', methods=['GET'])
def media():
    if session['group'] > 3:
        return render_template('error.html', errorMsg=errors['insufficientPermissions'], data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM posts WHERE files IS NOT NULL')
    posts = cursor.fetchall()
    return render_template('mediaManagement.html', posts=posts, data=globalSettings, currentTheme=request.cookies.get('theme'), themes=themes)





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=configData["port"])