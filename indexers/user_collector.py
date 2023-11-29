# Fetches the 10k most followed users from ScratchDB v3

from flask import Flask, jsonify, request
import os
from replit import db as replit_db
from datetime import datetime
import requests
from threading import Thread

def connect_to_db():
    return pymongo.MongoClient(f"mongodb connection URI")

import subprocess
subprocess.call(['pip', "install", "pymongo[srv]"])
import pymongo
client = connect_to_db()

def collect_users():
    collected_users = 0
    page = 0
    db = client["users"]
    coll = db["topFollowed"]
    while True:
        try:
            r = requests.get(f"https://scratchdb.lefty.one/v3/user/rank/global/followers/{page}").json()
            for i in r:
                print(i["username"])
                if len(
                    list(coll.find({"user":i["username"]}))
                ) == 0:
                    coll.insert_one({"user":i["username"]})
                    collected_users += 1
                print(collected_users)
            page += 1
        except Exception as e:
            print(e)
            page = 0


app = Flask('app')

@app.route('/')
def index():
    return {"status":"up"}

Thread(target=collect_users).start()
app.run(host='0.0.0.0', port=8080)
