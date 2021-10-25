import mysql.connector
import argparse
import json
import hashlib
import time
parser = argparse.ArgumentParser()
print("Usage: python createAccount.py -u Username -p Password -g 4 -e username@test.com")
with open('./config/database.json') as configFile:
    databaseConfig = json.load(configFile)
database = mysql.connector.connect(
  host=databaseConfig["host"],
  user=databaseConfig["user"],
  password=databaseConfig["password"],
  database=databaseConfig["name"]
)
parser.add_argument("-u", "--user", help = "Username for user [required]")
parser.add_argument("-p", "--password", help = "Password for user [required]")
parser.add_argument("-g", "--group", help = "User group [required]")
parser.add_argument("-e", "--email", help = "email for user [optional]")
args = parser.parse_args()
if args.user:
    username = args.user
else:
    print("A username is required (-u or --user)")
    quit()
if args.password:
    password = args.password
else:
    print("A password is required (-p or --password)")
    quit()
if args.group:
    group = args.group
else:
    print("User group must be specified (-g or --group)")
    quit()
if args.email:
    email = args.email
else:
    email = None
cursor = database.cursor()
cursor.execute("SELECT `salt` FROM `server`")
password = password + cursor.fetchone()[0]
query = "INSERT INTO `accounts` VALUES (NULL, %s, %s, %s, %s, %s, NULL, 0)"
values = (username, hashlib.sha512(password.encode("UTF-8")).hexdigest(), email, group, time.time())
cursor.execute(query, values)
database.commit()