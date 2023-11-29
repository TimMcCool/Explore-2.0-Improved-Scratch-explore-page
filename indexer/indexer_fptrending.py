# Collects the projects from the front page and the top users from explore / trending
# There are error handlers that detect when there is a failure in domain name resolution (these were neccessarry to host the project on replit)
# The code is not documented very well, sorry

import os
import subprocess
import requests
import json
from flask import Flask
from threading import Thread
from replit import db as replit_db
import time
import random
from datetime import datetime
try:
    from langdetect import detect as langdetect
except Exception:
    os.system("pip install langdetect")
    from langdetect import detect as langdetect


def connect_to_db():
    return pymongo.MongoClient(
        "mongodb connection URI")


import subprocess
try:
    import pymongo
except Exception:
    subprocess.call(['pip', "install", "pymongo[srv]"])
    import pymongo

client = connect_to_db()

threads = []
run_timestamp = time.time()

epoch_time = datetime(2000, 1, 1)


def to_seconds(timestamp):
    return (
        datetime.now() -
        datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')).total_seconds()


#tags that are being looked for
tags = [
    "animations", "art", "games", "tutorials", "platformers", "stories",
    "contests", "cloud", "math", "pen"
]


def get_tags(project):
    project_tags = []
    for tag in tags:
        if "#" + tag.lower() in project["description"].lower(
        ) or "#" + tag.lower() in project["instructions"].lower():
            project_tags.append(tag)
    return project_tags


#parameters for calculating the scores
loves_weight = 1
favorites_weight = 0.4
views_weight = 0.03


def key(o):
    try:
        x = (to_seconds(o["first_share"]) / 86400)
        return (
            o["stats"]["loves"] * loves_weight + o["stats"]["favorites"] *
            favorites_weight + o["stats"]["views"] * views_weight
        ) / max(
            (4**(x - 11) + 0.2 * (x - 11) + 2.8), 1
        )  #((((to_seconds(o["first_share"]) * 20/86400) ))  + o["stats"]["loves"] + o["stats"]["favorites"]/4 + o["stats"]["views"]/10)
    except Exception:
        return 0


threads = []
run_timestamp = time.time()

db = client["projects"]
coll = db["all"]

db_users = client["users"]


def collect_from_trending_users(*, limit=10000, offset=0):
    global threads
    global all_users
    
    loop = 0
    total_checked_users = 0
    
    while True:
        if datetime.now().hour != 19 and datetime.now().hour != 7:
            time.sleep(20)
            continue
        try:
            requests.get(
                "https://explore-page-for-scratch.moved.repl.co/force")
        except Exception:
            os.system("kill 1")

        try:
            collected = 0
            checked_users = 0
            users = all_users[offset:offset+limit]
            random.shuffle(users)
            for user in users:
                try:
                    projects = requests.get(
                        f"http://35.173.69.207/scratch/user/projects/{user}/",
                        headers={
                            'host': 'explodingalt.pythonanywhere.com'
                        }).json()
                    to_insert = []
                    to_update = list(coll.find({"author": user}))

                    updated_ids = []
                    for project in projects:

                        try:
                            if list(
                                    filter(lambda x: x["id"] == project["id"],
                                           to_update)) != []:
                                p = list(
                                    filter(lambda x: x["id"] == project["id"],
                                           to_update))[0]
                                p["stats"] = project["stats"]
                                p["title"] = project["title"]
                                p["author"] = user

                            else:
                                p = {
                                    "first_share":
                                    project["history"]["shared"],
                                    "shared": True,
                                    "stats": project["stats"],
                                    "title": project["title"],
                                    "author": user,
                                    "id": project["id"],
                                    "v": "new"
                                }
                                '''requests.post(
                                    "https://SE-Sorter.1tim.repl.co/api/internal/append",
                                      headers = {
                                          "object" : json.dumps(p)
                                      }
                                )'''
                            p["tags"] = get_tags(project)
                            p["score"] = key(p)

                            if not "lang" in p or not "1.07" in p["v"]:
                                try:
                                    if project["instructions"] == "":
                                        p["lang"] = langdetect(
                                            project["title"])
                                    else:
                                        p["lang"] = langdetect(
                                            project["instructions"])
                                except Exception as e:
                                    print(e)
                                    if "Temporary failure in name resolution" in str(
                                            e):
                                        os.system("kill 1")
                                    p["lang"] = "en"
                            if p["v"] == "new":
                                p["v"] = "new1.07b"
                            else:
                                p["v"] = "1.07b"

                            if p["id"] not in updated_ids:
                                updated_ids.append(p["id"])
                                to_insert.append(p)
                        except Exception as e:
                            print("Failed to index project", project, e)
                            if "Temporary failure in name resolution" in str(
                                    e):
                                os.system("kill 1")

                    coll.delete_many({"author": user})
                    coll.insert_many(to_insert)

                    #log progress
                    collected += len(projects)
                    checked_users += 1
                    total_checked_users += 1
                    try:
                        threads.remove(
                            list(
                                filter(lambda x: x["offset"] == offset,
                                       threads))[0])
                    except IndexError:
                        pass
                    threads.append({
                        "offset": offset,
                        "source": "trending",
                        "collected": collected,
                        "checked_users": checked_users,
                        "total_checked_users": total_checked_users,
                        "loop": loop
                    })
                    #print("collect from", collection, offset, collected)
                except Exception as e:
                    print("Error", user, e)
                    if "Temporary failure in name resolution" in str(e):
                        os.system("kill 1")

            try:
                requests.get(
                    "https://explore-page-for-scratch.moved.repl.co/force")
            except Exception:
                pass

            loop += 1
        except Exception as e:
            print("Fatal error", e)
            if "Temporary failure in name resolution" in str(e):
                os.system("kill 1")
        time.sleep(3600)


app = Flask('app')


@app.route('/')
def index():
    total = {"threads": len(threads), "checked_users": 0, "collected": 0}
    for thread in threads:
        total["checked_users"] += thread["checked_users"]
        total["collected"] += thread["collected"]

    return app.response_class(response=json.dumps(
        {
            "status": "up",
            "runtime": round(time.time() - run_timestamp),
            "total": total,
            "threads": threads
        },
        indent=4),
                              status=200,
                              mimetype='application/json')


all_users = []

def create_coll_users():
    global all_users

    while True:
        if datetime.now().hour != 18 and datetime.now().hour != 8:
            time.sleep(3300)
            continue
        for i in range(20):
            data = requests.get(f"https://explodingstar.pythonanywhere.com/scratch/explore/projects/?limit=40&offset={i*40}&q=*").json()
            all_users = all_users + [i["author"]["username"] for i in data]
            print(len(all_users))
        data = requests.get("https://explodingstar.pythonanywhere.com/scratch/api/?endpoint=/proxy/featured").json()
        all_users = all_users + [i["creator"] for i in data["community_featured_projects"]]
        all_users = all_users + [i["creator"] for i in data["community_most_loved_projects"]]
        all_users = all_users + [i["creator"] for i in data["curator_top_projects"]]

            
Thread(target=create_coll_users).start()

for i in range(0, 50):
    Thread(target=collect_from_trending_users,
           kwargs={
               "limit": 100,
               "offset": i * 100
           }).start()
app.run(host='0.0.0.0', port=8080)
