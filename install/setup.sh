#!/bin/bash


echo "Saturn install script"
echo "This script assumes that you have Python3 and MySQL set up"
#Dependency installation
echo "Install dependencies?"
select yn in "Yes" "No"; do
  case $yn in
    Yes ) 
        cd ..
        source saturn/bin/activate
        pip3 install -r requirements.txt
        cd install
        echo "Done"
        echo
        break;;
    No ) break;;
  esac
done
#Initialize venv
echo "Initialize virtual environment? (must be root)"
select yn in "Yes" "No"; do
  case $yn in
    Yes )
        if [ `whoami` != 'root' ]
        then
            echo "Please run this script as root."
            exit
        fi
        sudo apt install python3-venv
        cd ..
        python3 -m venv saturn
        cd install
        echo "Done"
        echo
        break;;
    No ) break;;
  esac
done
#Import SQL file into database
echo "Initialize database?"
select yn in "Yes" "No"; do
  case $yn in
    Yes ) 
        echo "Enter mysql username: "
        read username
        echo "Enter mysql password: "
        read password
        echo "Database name: "
        mysql -u $username --password=$password < database.sql
        echo "Done"
        echo
        break;;
    No ) break;;
  esac
done
echo "Create SystemD service? (must be root)"
select yn in "Yes" "No"; do
  case $yn in
    Yes ) 
        #Check if user is root
        if [ `whoami` != 'root' ]
        then
            echo "Please run this script as root."
            exit
        fi
        touch saturn.service
        #Create service file
        cd ..
        echo "
        [Unit]
        Description=Saturn imageboard software
        After=network.target

        [Service]
        User=$USER
        Group=www-data
        WorkingDirectory=$PWD
        Environment="PATH=$PWD/saturn/bin"
        ExecStart=$PWD/saturn/bin/gunicorn --bind unix:saturn.sock -m 007 wsgi

        [Install]
        WantedBy=multi-user.target
        " > install/saturn.service
        sudo mv saturn.service /etc/systemd/system
        cd install
        echo
        break;;
    No ) break;;
  esac
done

#Enable SystemD service
echo "Enable systemD service at startup? (must be root)"
select yn in "Yes" "No"; do
  case $yn in
    Yes ) 
        if [ `whoami` != 'root' ]
        then
            echo "Please run this script as root."
            exit
        fi
        sudo systemctl start saturn
        sudo systemctl enable saturn
        echo
        break;;
    No ) break;;
  esac
done

#Create Nginx proxy
echo "Create Nginx proxy server? (must be root)"
select yn in "Yes" "No"; do
  case $yn in
    Yes ) 
        if [ `whoami` != 'root' ]
        then
            echo "Please run this script as root."
            exit
        fi 
        touch saturn
        echo "Enter domain: "
        read domain
        cd ..
        echo "
        server {
            listen 80;
            server_name $domain www.$domain;

            location / {
                include proxy_params;
                proxy_pass http://unix:$PWD/saturn.sock;
            }
        }
        " > install/saturn
        sudo mv install/saturn /etc/nginx/sites-available
        sudo ln -s /etc/nginx/sites-available/saturn /etc/nginx/sites-enabled
        sudo systemctl restart nginx
        echo "Done"
        echo
        break;;
    No ) break;;
  esac
done
echo
echo "Saturn installation completed."