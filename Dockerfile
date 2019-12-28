FROM ubuntu:bionic as builder

RUN echo 'APT::Install-Recommends 0;' >> /etc/apt/apt.conf.d/01norecommends \
    && echo 'APT::Install-Suggests 0;' >> /etc/apt/apt.conf.d/01norecommends \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y bash mysql-client vim.tiny wget sudo net-tools ca-certificates unzip apt-transport-https \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y python-minimal libmysqlclient-dev libxml2-dev libxslt-dev python-dev libffi-dev gcc libssl-dev gettext \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-setuptools nodejs node-gyp npm ruby nginx \
    && pip install --upgrade pip \
    && npm install -g less@2.7.1 \
    && npm install -g yuglify@0.1.4 \
    && gem install sass -v 3.4.22

WORKDIR /app
ADD . .

RUN pip install -r requirements.txt

RUN cp ./nginx/default.site-example /etc/nginx/sites-available/default \
    && cp ./frontend/frontend/settings.py.example ./frontend/frontend/settings.py

RUN cd /var/lib/gems/2.5.0/gems/sass-3.4.22/lib/sass/ \
    && sed -i "s/when\ Fixnum/when\ Integer/" util.rb

#WORKDIR ./frontend
RUN chmod +x ./wait-for-it.sh

#ENTRYPOINT ["/bin/bash", "start.sh"]
