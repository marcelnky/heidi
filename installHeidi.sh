 #! /bin/sh.

#sudo apt install python3-pip   # auf raspi
#sudo pip install virtualenv    # auf raspi
#das shell script mit source aufrufen! sonst geht das venv nicht

pip install virtualenv

mkdir logs
mkdir db
mkdir vendor/aiml/botdata/standard

cp examples/example.db db/heidi.db
cp examples/.env_example ./.env

rm -r examples/

virtualenv -p python3 env
source env/bin/activate

pip install -r requirements.txt

#python heidi.py
