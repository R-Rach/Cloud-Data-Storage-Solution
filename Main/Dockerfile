#####################################
#### ---- Ubuntu + Python3 ---- ####
####################################

# ------------------
# Take base image
# ------------------
FROM python:3.6

ENV COMPOSE_PROJECT_NAME=storage_solution_app

######################################################
MAINTAINER Rachit_Rathore "https://github.com/R-Rach"
######################################################

# ------------------------------------------------------------------------------------------
# Install COPY the application from local storage to docker image + Install requirments.txt
# ------------------------------------------------------------------------------------------
COPY . /app
WORKDIR /app

RUN pip3 install --upgrade pip setuptools && \
    pip3 install -r requirements.txt

EXPOSE 5000 5001