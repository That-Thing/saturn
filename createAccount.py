import mysql.connector
import argparse
import json
parser = argparse.ArgumentParser()
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
query = "INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)"
values = (username, password, email, group)
cursor.execute(query, values)
database.commit()