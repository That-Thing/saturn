# Saturn
The saturn imageboard software project.


## Manual Installation

The installation is fairly straightforward.\
**While Saturn may run on Windows, an installation guide will not be provided for it.**
### Cloning the repository
```
git@github.com:That-Thing/saturn.git
cd saturn
```
### Python 3
```
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
```
### Database Setup
Saturn uses MySQL.
```
sudo apt update
sudo apt-get install mysql-server
```
run the secure installation script
```
sudo mysql_secure_installation
```
Enter `y` when it asks if you want password validation\
Enter `2` for the security level\
Set the password for the root user\
Finish the setup and import the database file
```
sudo mysql < install/database.sql
```
enter the MySQL shell with
```
sudo mysql
```
Create a MySQL user for saturn
>Make sure to replace `password` with a secure password
```
CREATE USER 'saturn'@'localhost' IDENTIFIED WITH authentication_plugin BY 'password';
```
Now grant privileges for the Saturn Database
```
GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on saturn TO 'saturn'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
exit
```
Now your database is set up.

### Configuration
Now you need to fill out the database configuration file\
Edit config/database.json and enter your database connection information

### Initializing Venv
Install the venv package
```
sudo apt install python3-venv
```
Initialize and activate the environment
```
python3 -m venv saturn
source saturn/bin/activate
```
### Installing dependencies
>Do this inside the virtual environment
```
pip3 install -r requirements.txt
```
### Gunicorn
Still inside the virtual environment, enter this
```
gunicorn --bind 0.0.0.0:8080 wsgi
```
This should have started the Gunicorn server
### Creating a SystemD service
CTRL+C out of the Gunicorn process\
run
```
sudo nano /etc/systemd/system/saturn.service
```
Paste this in, and replace `YOUR USER` with your username and `/your/saturn/directory` with the path to your Saturn directory
```
[Unit]
Description=Saturn imageboard software
After=network.target

[Service]
User=YOUR USER
Group=www-data
WorkingDirectory=/your//saturn/directory
Environment="PATH=/your/saturn/directory/saturn/bin"
ExecStart=/your/saturn/directory/saturn/bin/gunicorn --bind unix:saturn.sock -m 007 wsgi

[Install]
WantedBy=multi-user.target
```
To enable this, run
```
sudo systemctl start saturn
sudo systemctl enable saturn
```
Make sure the service was started correctly by entering
```
sudo systemctl status saturn
```
### Nginx Reverse Proxy
This makes it so that saturn can properly work with domains\
Install Nginx
```
sudo apt-get install nginx
```
Create the configuration file
```
sudo nano /etc/nginx/sites-available/saturn
```
Paste this in, replacing `domain.com` with your domain or IP and `/your/saturn/directory` with the path to your Saturn installation
```
server {
    listen 80;
    server_name domain.com www.domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/your/saturn/directory/saturn.sock;
    }
}
```
Save and exit\
Enable the config
```
sudo ln -s /etc/nginx/sites-available/saturn /etc/nginx/sites-enabled
```
Restart Nginx
```
sudo systemctl restart nginx
```
### Creating a root user account
To change settings on the site you will need a user account wiht the highest permission level.\
To do this, run the python file `createAccount.py`
>Replace USERNAME with a username, PASSWORD with a password, and username@test.com with an email (email is optional)
```
python3 createAccount.py -u USERNAME -p PASSWORD -g 0 -e username@test.com
```
