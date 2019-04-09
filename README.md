## Heroku conifg
* procfile & runtime is included


## AWS config

* launch an ec2
* prep python
* install gunicorn
* instal nginx
* download some nltk / textblob samples: ```python -m textblob.download_corpora```
* use this config for nginx:
```
server {
	listen 80;

	location / {
		proxy_pass http://127.0.0.1:8000/;
	}

	location /socket.io {
                include proxy_params;
                proxy_pass http://127.0.0.1:8000/socket.io;
                proxy_http_version 1.1;
                proxy_buffering off;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
    }
}
```
* send it to /etc/nginx/sites-available/<fNAME>
* make a link to the file : ```ln -s /etc/nginx/sites-available/<fNAME> /etc/nginx/sites-enabled/<fName>```
* install gunicorn with pip and run it with: ```gunicorn --worker-class eventlet -w 1 demo:app```

**Needed to run on python3 on AWS