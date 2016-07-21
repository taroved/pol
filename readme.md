== Installation of development server

Install required packages

sudo apt-get install python-minimal libmysqlclient-dev libxml2-dev libxslt-dev python-dev libffi-dev gcc libssl-dev gettext

Install pip
```
pushd /tmp
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
popd
```

Install pip packages
```
sudo pip install -r requirements.txt
```

Install less
```
sudo apt-get install nodejs npm
sudo npm install -g less
sudo ln -s /usr/bin/nodejs /usr/bin/node
```

Install sass
```
sudo apt-get install ruby
sudo su -c "gem install sass"
```

Install and setup nginx
```
sudo apt-get install nginx
sudo cp pol/nginx/default.site-example /etc/nginx/sites-available/default
sudo service nginx reload
```

Install and setup mysql. **Use password 'toor' for root user**
```
sudo apt-get install mysql-server
mysql -uroot -ptoor -e 'CREATE DATABASE pol DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;'
```

Initialise database
```
pushd pol/frontend
python manage.py migrate
python manage.py loaddata fields.json
popd

Create django config
```
cp pol/frontend/frontend/settings.py.example pol/frontend/frontend/settings.py
```

== Run servers

Run downloader server
```
pushd pol
python downloader.py
popd
```

Run frontend server
```
pushd pol/frontend
python manage.py runserver
popd
```
