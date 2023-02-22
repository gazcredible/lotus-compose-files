#don't forget to version things!

#just restart the service, not the whole app:
#sudo docker-compose pull
#sudo docker-compose restart unexe-visualisation-service
#sudo docker-compose up --detach --build unexe-visualisation-service

#docker-repo
#9F?Xrn9v;i,RwJ7
#sudo docker build -t gaztastic/unexe-visualiser-p3 .
#sudo docker buildx build --platform linux/amd64 --push -t gaztastic/unexe-visualisation .
#sudo docker push gaztastic/unexe-visualiser-p3

#sudo docker build -t gaztastic/unexe-visualisation-2b .
#sudo docker push gaztastic/unexe-visualisation-2b

#for M1 mac
#sudo docker buildx build --platform linux/amd64 -t gaztastic/unexe-visualisation-2b .
#sudo docker push gaztastic/unexe-visualisation-2b

#run from docker-repo
#sudo docker login
#sudo docker pull gaztastic/unexe-visualisation

#run as part of docker-compose

#http://52.50.143.202:8100/nokeyrock
#ssh -i unexe.pem unexe@52.50.143.202
#sudo docker-compose down
#sudo docker-compose pull
#sudo docker-compose up
#have a look and see what's going on ...
#sudo docker exec -it unexe-multiprocessing_unexe-visualisation-service_1 /bin/bash

#sudo docker login
#sudo docker pull gaztastic/aqua3s-visualisation-service:kr10-demo-2.0
#sudo docker run --publish 8100:8100 gaztastic/aqua3s-visualisation-service:kr10-demo-2.0


FROM ubuntu:20.04

ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python3.9
RUN apt-get install -y apt-utils
RUN apt-get install -y python3-pip
RUN pip install --upgrade pip
RUN pip install setuptools wheel
RUN apt-get install -y make
RUN apt-get install -y swig
RUN apt-get install -y python3-venv
RUN apt-get install -y nano

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
COPY . /app

COPY ./packages/ /app/packages/
RUN pip3 install cmake
RUN pip3 install scikit-build
RUN pip3 install owa-epanet

WORKDIR /app
RUN pip3 install -r requirements.txt
CMD [ "python3", "-u", "visualisation_service.py"]

#debug docker container
#CMD [ "python3", "dummy.py"]
