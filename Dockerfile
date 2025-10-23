FROM --platform=linux/amd64 ubuntu:22.04 as builder

# Install system packages
RUN echo 'APT::Install-Recommends 0;' >> /etc/apt/apt.conf.d/01norecommends \
    && echo 'APT::Install-Suggests 0;' >> /etc/apt/apt.conf.d/01norecommends \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        bash postgresql-client vim.tiny wget sudo net-tools \
        ca-certificates unzip apt-transport-https tzdata \
        python3 python3-pip python3-dev libpq-dev \
        libxml2-dev libxslt-dev libffi-dev \
        gcc g++ make libssl-dev gettext \
        nodejs npm ruby ruby-dev nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js tools (using LESS 2.7.3 for Bootstrap 2 compatibility)
RUN npm install -g less@2.7.3 yuglify@0.1.4

# Install Ruby sass
RUN gem install sass -v 3.7.4

# Upgrade pip
RUN pip3 install --upgrade pip setuptools

WORKDIR /app
ADD . .

RUN pip3 install -r requirements.txt

RUN cp ./nginx/default.site-example /etc/nginx/sites-available/default \
    && cp ./frontend/frontend/settings.py.example ./frontend/frontend/settings.py

RUN chmod +x ./wait-for-it.sh
