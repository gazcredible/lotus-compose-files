<b>Build for Mac</b>
<br>install cmake and swig from brew
<br><i>brew install --cask cmake</i>
<br><i>brew install swig</i>

<br>aqua3s-keyrock-test
https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-ubuntu-16-04

Setup venv
python3.9 -m venv venv

source venv/bin/activate

pip install -r requirements.txt 


167.172.49.166:8100

167.172.49.166:8100/map

167.172.49.166:8100/charting


https://www.tecmint.com/find-out-which-process-listening-on-a-particular-port/

list of processes using port id

lsof -i : <port_id>

f4w is running on python3.8

python3 manage.py runserver 167.172.49.166:21000 


git restore . - abandon local changes
git checkout <branch>
git pull - get latest
git branch - which branch are you on

!!!!Resource Building!!!!
User orion_view_build in unexe-aqua3s package

<b>Local Host</b>
<br>
sudo docker run --publish 8200:8200 --add-host="localhost:<your ip>" kr12-demo-2.1
<br>

<br>
sudo docker-compose restart <i>container</i>
<br>

sudo docker logs --tail 50 --follow --timestamps <i>instance</i>

docker-compose up --detach --build <i>container</i>
<br>docker exec -it <mycontainer> bash

<br>
<br>
<b>Persistent external volumes</b>
<br>docker volume create <i>volume</i>

<br>
<br>
don't forget to copy all the userlayer data (source & dest) over when you update it locally


<br><b>fun stuff with PIDs</b><br>
sudo docker inspect -f '{{.State.Pid}}' <i>container id</i><br>
cat /proc/<i>pid</i>/cmdline | sed -e "s/\x00/ /g"; echo<br>