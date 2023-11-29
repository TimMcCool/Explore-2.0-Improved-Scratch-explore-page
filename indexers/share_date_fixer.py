# Iterates over the top projects of the explore 2.0 page and checks if they were reshared:
# This script aims to detect if a project was reshared by comparing the API share date of the project with the API share date of the first remix (Scratch API used through a proxy hosted on pythonanywhere)
# When a reshare is detected, the share date of the reshared project saved in the db is set to the share date of the first remix

import os
import subprocess
import requests
import json
from flask import Flask
from threading import Thread
from replit import db as replit_db
import time
from datetime import datetime

loops = 0


def connect_to_db():
    return pymongo.MongoClient("MongoDB connection URI")

import subprocess
subprocess.call(['pip', "install", "pymongo[srv]"])
import pymongo
client = connect_to_db()

db = client["projects"]
coll = db["all"]
run_now = False

def to_seconds(timestamp):
    return (datetime.now() - datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')).total_seconds()

def fix_sharedates():
    global loops
    global run_now
    
    while True:
        if datetime.now().hour != 20 and datetime.now().hour !=8 and run_now is False:
            time.sleep(20)
            continue
        requests.get("https://explore-page-for-scratch.moved.repl.co/force")
        time.sleep(60)
        run_now = False
        try:
            r = requests.get("https://explore-page-for-scratch.moved.repl.co/api/all/?limit=100&requester=share_date_fixer").json()
            r = r + requests.get("https://explore-page-for-scratch.moved.repl.co/api/all/?limit=100&requester=share_date_fixer&mode=popular").json()
            for i in r:
                smallest_timestamp = i["first_share"]
                biggest_timedelta = to_seconds(smallest_timestamp)
                
                remixes = requests.get(
                    f"http://35.173.69.207/scratch/api/?endpoint=/projects/{i['id']}/remixes/", headers={"host":"explodingstar.pythonanywhere.com"}
                ).json()
                for remix in remixes:
                    _timedelta = to_seconds(remix["history"]["shared"])
                    if _timedelta > biggest_timedelta:
                        biggest_timedelta = _timedelta
                        smallest_timestamp = remix["history"]["shared"]
                        
                if i["first_share"] != smallest_timestamp:
                    try:
                        objects = list(coll.find({"id":i["id"]}))
                        o = objects[0]
                        print(smallest_timestamp, o)
                        o["first_share"] = smallest_timestamp
                        o.pop("_id")
                        if len(objects) == 1:
                            coll.replace_one({"id":i["id"]}, o)
                        else:
                            coll.delete_many({"id":i["id"]})
                            coll.insert_one(o)
                        requests.get("https://explore-page-for-scratch.moved.repl.co/force")
                    except Exception as e:
                        print(e)
                        if "Temporary failure in name res" in str(e):
                            os.system("kill 1")

            loops += 1
        except Exception as e:
            print(e)
            if "Temporary failure in name res" in str(e):
                os.system("kill 1")
        time.sleep(3600)
app = Flask('app')


@app.route('/')
def index():
    return {"status":"up", "loops":loops}

@app.route("/force/")
def force():
    global run_now
    run_now = True
    return "A run will be forced"
    
Thread(target=fix_sharedates).start()
app.run(host='0.0.0.0', port=8080)
