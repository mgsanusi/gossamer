############################################################
# Dockerfile to build a Flask app and mysql server
############################################################

# Set the base image
# FROM debian:bullseye AS baseimg
FROM python:3.7 as baseimg

RUN apt-get update && apt-get install -y apache2 \
        libapache2-mod-wsgi-py3 \
        build-essential \
        # python3 \
        # python3-dev\
        # python3-pip \
        # vim \
        && apt-get clean \
        && apt-get autoremove \
        && rm -rf /var/lib/apt/lists/*
        # && ln -sf /usr/bin/pip3 /usr/bin/pip \
        # && ln -sf /usr/bin/python3 /usr/bin/python
 


# Copy over and install the requirements
COPY ./app/requirements.txt requirements.txt
RUN pip install -r requirements.txt
WORKDIR /var/www/gossamer

## Install mod_wsgi
# RUN pip install mod_wsgi
# RUN mod_wsgi-express module-config

# ------------------------------------------ 
FROM baseimg
WORKDIR /var/www/gossamer

# Copy over the apache configuration file and enable the site
COPY ./gossamer.conf /etc/apache2/sites-available/gossamer.conf
RUN a2ensite gossamer \
        && a2enmod headers


# # Setup some services for handling request from flask server   -- Does not work 
# COPY config_files/*.service /etc/systemd/system/
# RUN systemctl daemon-reload && systemctl start summarizer

# Copy over the wsgi file
COPY ./gossamer.wsgi ./run.py startup.sh ./
# VOLUME ./app ./app

RUN a2dissite 000-default.conf \ 
        && a2ensite gossamer.conf

EXPOSE 80 443

HEALTHCHECK --interval=5m --timeout=3s \
        CMD curl -f http://localhost/ || exit 1

ENV PORT=80 DEBUG=1
ENTRYPOINT ./startup.sh && sleep 1 && /usr/sbin/apache2ctl -D FOREGROUND
