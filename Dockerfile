FROM ubuntu:bionic as builder

RUN echo 'APT::Install-Recommends 0;' >> /etc/apt/apt.conf.d/01norecommends \
    && echo 'APT::Install-Suggests 0;' >> /etc/apt/apt.conf.d/01norecommends \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y bash vim.tiny wget sudo net-tools ca-certificates unzip apt-transport-https \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y python-minimal libmysqlclient-dev libxml2-dev libxslt-dev python-dev libffi-dev gcc libssl-dev gettext \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-setuptools nodejs node-gyp npm ruby nginx \
    && pip install --upgrade pip \
    && npm install -g less@2.7.1 \
    && npm install -g yuglify@0.1.4 \
    && gem install sass -v 3.4.22

ARG DB_NAME=pol
ARG DB_USER=root
ARG DB_PASSWORD=toor
ARG DB_HOST=127.0.0.1
ARG DB_PORT=3306
ARG TIME_ZONE=UTC

EXPOSE 80
WORKDIR /app
ADD . .

RUN pip install -r requirements.txt

RUN cp ./nginx/default.site-example /etc/nginx/sites-available/default \
    && cp ./frontend/frontend/settings.py.example ./frontend/frontend/settings.py \
    && sed -i -E -e "s/(DEBUG = ).*/\1True/" \
    -e "s/('NAME': ')pol(',)/\1${DB_NAME}\2/" \
    -e "s/('USER': ')root(',)/\1${DB_USER}\2/" \
    -e "s/('PASSWORD': ')toor(',)/\1${DB_PASSWORD}\2/" \
    -e "s/('HOST': ')127\.0\.0\.1(',)/\1${DB_HOST}\2/" \
    -e "s/('PORT': ')3306(',)/\1${DB_PORT}\2/" \
    -e "s/(TIME_ZONE = ').*/\1${TIME_ZONE}'/" \
    -e "s/when\ Fixnum/when\ Integer/" \
    ./frontend/frontend/settings.py \
    && service nginx reload

RUN cd /var/lib/gems/2.5.0/gems/sass-3.4.22/lib/sass/ \
    && sed -i "s/when\ Fixnum/when\ Integer/" util.rb

WORKDIR ./frontend

ENTRYPOINT ["/bin/bash", "start.sh"]
