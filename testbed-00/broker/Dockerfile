#don't forget to version things!

#docker-repo
#9F?Xrn9v;i,RwJ7

#for M1 mac
#sudo docker buildx build --platform linux/amd64 --push -t gaztastic/unexef4w-broker .

FROM ubuntu:20.04

ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python3
RUN apt-get install -y apt-utils
RUN apt-get install -y python3-pip
RUN pip install setuptools wheel
RUN apt-get install -y python3-venv
RUN apt-get install -y nano

# We copy just the ds-requirements.txt first to leverage Docker cache
COPY requirements.txt /app/requirements.txt
COPY . /app

COPY ./packages/ /app/packages/


WORKDIR /app
RUN pip3 install -r requirements.txt
CMD [ "python3", "-u", "app.py"]

#debug docker container
#CMD [ "python3", "dummy.py"]
