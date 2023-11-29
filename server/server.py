# This is the server for Explore 2.0 website. It uses a background thread to constantly fetch and cache data from the database and sort it based on the recent / trending / popular mode keys
# Server framework: Flask
# Used databases: MongoDB to store contents of explore page, replit db to cache the most recent version of the page 1 trending data (so it won't be empty until it is loaded in from MongoDB in case the server restarts) and to store stats about site usage

from flask import Flask, request, jsonify, render_template
from threading import Thread
from replit import db as replit_db
import json
import time
from datetime import datetime
import requests
import os
from copy import deepcopy

# Init database
def connect_to_db():
    try:
        return pymongo.MongoClient(f"mongodb connection URI")
    except pymongo.errors.ConfigurationError:
        os.system("kill 1")
        
import pymongo
client = connect_to_db()

db = client["projects"]
coll = db["all"]

# Available languages and modes
languages = {
    None : "Global",
    "en" : "English",
    "fr" : "French",
    "ja" : "Japanese",
    "af": "Afrikaans",
    "ar" : "Arabic",
    "bu" : "Bulgarian",
    "ca" : "Catalan",
    "hr" :"Croatian",
    "cz" : "Czech",
    "da" : "Danish",
    "nl" : "Dutch",
    "ka" : "Georgian",
    "el" : "Greek",
    "de" : "German",
    "hu" : "Hungarian",
    "id" : "Indonesian",
    "it" : "Italian",
    "ko":"Korean",
    "ne":"Nepali",
    "pl" : "Polish",
    "ru" : "Russian",
    "sk" : "Slovak",
    "sv" : "Swedish",
    "es" : "Spanish",
    "uk" : "Ukrainian",
    "vi" : "Vietnamese"
}
modes = {
    "trending" : "🔥 Trending",
    "rising" : "🚀 Rising",
    "popular" : "👀 Popular"
}

# Init variables
raw_data = []
extra_data = []
raw_trending = replit_db["trending"]
last_update = last_update = str(datetime.now())
runtime = last_update = str(datetime.now())

default_tags = ["*", "all", "animations", "games", "tutorials", "stories", "platformers", "contests", "intros"]

# Load in cached version of page 1 trending data
try:
    trending = json.loads(raw_trending)
except Exception as e:
    print(e)
    trending = []
rising = []
popular = []

epoch_time = datetime(2000, 1, 1)
def to_seconds(timestamp):
    return (datetime.now() - datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')).total_seconds()
    
def key_trending(o):
    #parameters for calculating the scores
    loves_weight = 1
    favorites_weight = 0.4
    views_weight = 0.003

    #Key for sorting projects
    try:
        
        x = (to_seconds(o["first_share"]) / 86400)
        score = - (o["stats"]["loves"] * loves_weight + o["stats"]["favorites"] * favorites_weight + o["stats"]["views"] * views_weight) / max(2 ** (x-7) + 0.85*(x-7)+5.95, 1)#max((4 ** (x-11) + 0.9 * (x-11) + 9.5), 1) #((((to_seconds(o["first_share"]) * 20/86400) ))  + o["stats"]["loves"] + o["stats"]["favorites"]/4 + o["stats"]["views"]/10)
        return score
    except Exception:
        return 0

def key_rising(o):
    #parameters for calculating the scores
    loves_weight = 1
    favorites_weight = 0.6
    views_weight = 0

    #Key for sorting projects
    try:
        
        x = (to_seconds(o["first_share"]) / 86400)
        score = - (o["stats"]["loves"] * loves_weight + o["stats"]["favorites"] * favorites_weight + o["stats"]["views"] * views_weight) / max(4 ** (x-2) + 6*x - 0.25, 3)#max((4 ** (x-11) + 0.9 * (x-11) + 9.5), 1) #((((to_seconds(o["first_share"]) * 20/86400) ))  + o["stats"]["loves"] + o["stats"]["favorites"]/4 + o["stats"]["views"]/10)
        return score
    except Exception:
        return 0

def key_popular(o):
    #parameters for calculating the scores
    loves_weight = 1
    favorites_weight = 0.9
    views_weight = 0.5

    #Key for sorting projects
    try:
        
        x = (to_seconds(o["first_share"]) / 86400)
        score = - (o["stats"]["loves"] * loves_weight + o["stats"]["favorites"] * favorites_weight + o["stats"]["views"] * views_weight) / max(2 ** (x-75)+15, 1)#max((4 ** (x-11) + 0.9 * (x-11) + 9.5), 1) #((((to_seconds(o["first_share"]) * 20/86400) ))  + o["stats"]["loves"] + o["stats"]["favorites"]/4 + o["stats"]["views"]/10)
        return score
    except Exception:
        return 0


def replace_in_data(project_id, new_data):
    #Manually adds projects to the cache
    global extra_data
    try:
        matching = list(filter(lambda x : x["id"] == id, extra_data))[0]
        extra_data.remove(matching)
    except IndexError:
        pass
    extra_data.append(new_data)
       
def create_trending():
    global force_run
    global raw_data
    global raw_trending
    global trending, rising, popular
    global last_update
    global extra_data

    first_run = True # -> Different behavior during the first iteration of the following while True loop
    
    while True:
        try:
            #Fetches / Caches the 10000 projects with the top trending score (based on the scores saved in the database which are from when the project was indexed)
            force_run = False
            _raw_data = list(coll.find({"shared":True}, {"shared":0,"_id":0}).sort("score", -1).limit(5000).skip(0))
            _raw_data += list(coll.find({"shared":True}, {"shared":0,"_id":0}).sort("score", -1).limit(5000).skip(5000))
            
            print(len(_raw_data))

            # Sorts the projects based on their actual trending and rising mode scores. (Popular page is fetched from another API that fetches all projects, not just the top 10k)
            raw_data = _raw_data + extra_data
            trending = sorted(raw_data, key=key_trending)
            rising = sorted(raw_data, key=key_rising)
            #popular = sorted(raw_data, key=key_popular)
            replit_db["trending"] = str(json.dumps(trending[:40]))
            last_update = str(datetime.now())

            first_run = False
            extra_data = []

            while not force_run == True:
                time.sleep(10)

            
        except Exception as e:
            print(e)
            if "Temporary failure in name resolution" in str(e):
                os.system("kill 1")

def get_tag(tag, *, lang, mode):
    # Gets the explore page belonging to a tag
    # mode: The mode of the explore page that is requested (popular, trending or recent). Can't be used for popular mode because popular mode projects are fetched from a different API.
    tag = tag.lower()
    if mode=="popular":
        source = []
    elif mode=="trending":
        source = trending
    elif mode=="rising":
        source = rising
    if tag == "*" or tag=="all":
        results = source
    else:
        def check(x):
            if len(tag) > 4 and tag.endswith("s"):
                if tag[:-1] in x["title"].lower() or tag == x["author"].lower():
                    return True
            else:
                if tag in x["title"].lower() or tag == x["author"].lower():
                    if not (tag=="pen" and "open" in x["title"].lower()) and "pen " in x["title"].lower():
                        return True
            if "tags" in x:
                if tag in x["tags"]:
                    return True
            return False

        
        results = list(filter(check, source))

    def langcheck(x):
        # Function for checking if project x has the requested language lang
        if lang is None:
            return True
        if "lang" in x:
            if x["lang"] == lang:
                return True
        return False
            
    results = list(filter(langcheck, results))
    return results


app = Flask("app",
            static_url_path='', 
            static_folder='templates',
            template_folder='templates')

@app.route('/api/')
def health():
  return {"status":"up", "last_update":last_update, "running_since":runtime}

@app.route('/')
def main():
    # Renders the "All" page
    
    lang=request.args.get("lang")
    if lang == "None":
        lang = None
    if lang not in languages:
        lang = None

    mode=request.args.get("mode")
    if mode is None:
        mode = "trending"

    _languages = deepcopy(languages)
    _modes = deepcopy(modes)
    return render_template("/index.html", active=lambda x : "active" if x == "all" else "", data=get_tag("all", mode=mode, lang=lang)[:16], last_refresh=last_update, langid=lang, langname=_languages.pop(lang), languages=_languages, modeid=mode, modename=_modes.pop(mode), modes=_modes)

@app.route("/force")
def force():
    # Forces the server to reload the cached projects. This ednpoint is called by the indexers after they finished a run to make sure the explore page displays the most recent project data from the database.
    try:
        global force_run
        force_run = True
        requests.get("https://explore-full-api.moved.repl.co/force", timeout=1)
        return "A run will be forced"
    except Exception:
        return "Error", 500
    
@app.route('/explore/projects/<tag>/')
def explore(tag):
    # Returns an explore page for the specified tag
    lang=request.args.get("lang")

    if lang == "None" or lang == "null":
        lang = None
    if lang not in languages:
        lang = None

    mode=request.args.get("mode")
    if mode is None or mode == "None" or mode == "null":
        mode = "trending"

    if tag in default_tags and (lang is None or lang == "en"):
        data = get_tag(tag, lang=lang, mode=mode)[:16]
    else:
        data = requests.get(
            f"https://explore-full-api.moved.repl.co/api/{tag}/?limit=16&offset=0&lang={lang}&mode={mode}"
        ).json()

    
    _languages = deepcopy(languages)
    _modes = deepcopy(modes)
    return render_template("/index.html", active=lambda x : "active" if x == tag else "", data=data, last_refresh=last_update, langid=lang, langname=_languages.pop(lang), languages=_languages, modeid=mode, modename=_modes.pop(mode), modes=_modes)

@app.errorhandler(404)
def page_not_found(e):
    return "Error handler for 404", 404


@app.route('/api/cache/users/<user>/')
def user(user):
    # Returns all projects cached by the server that belong to the specified user
    results = list(filter(lambda x : x["author"] == user, trending))
    return results

@app.route('/api/users/<user>/')
def db_fetch_user(user):
    # Returns all projects stored in the database that belong to the specified user
    return list(coll.find({"author":user}, {"_id":0}))

@app.route('/api/cache/indexcheck/<project>/')
def indexcheck(project):
    # Checks if a project is indexed by checking the cache. (Faster than checking the db)
    results = list(filter(lambda x : x["id"] == int(project), trending))
    if results == []:
        return {"indexed":False}
    else:
        return {"indexed":True, "results":results}
        
@app.route('/api/indexcheck/<project>/')
def db_indexcheck(project):
    # Checks if a project is indexed by checking the db
    results = list(coll.find({"id":int(project)}, {"_id":0}))
    if results == []:
        return {"indexed":False}
    else:
        return {"indexed":True, "results":results}
        
@app.route('/api/<tag>/')
def api(tag):
    # API for a tag. Returns a list with the requested projects
    mode=request.args.get("mode")
    if mode == "None" or mode == "null" or mode is None:
        mode = "trending"

    tag = tag.lower()

    if tag in replit_db["stats"]:
        replit_db["stats"][tag] += 1
    else:
        replit_db["stats"][tag] = 0
        
    try:
        begin = int(request.args.get("offset"))
        offset = begin
    except Exception:
        begin = 0
        offset = 0
    try:
        end = int(request.args.get("limit"))+begin
        limit = int(request.args.get("limit"))
    except Exception:
        end = 40+begin
        limit = 40

    lang = request.args.get("lang")
    if lang == "None" or lang=="null":
        lang = None
    
    if end > len(trending)-1:
        end = len(trending)-1
    if tag in default_tags and (lang is None or lang == "en") and (not mode == "popular"):
        results = get_tag(tag, lang=lang, mode=mode)[begin:end]
    else:
        results = requests.get(
            f"https://explore-full-api.moved.repl.co/api/{tag}/?limit={limit}&offset={offset}&lang={lang}&mode={mode}"
        ).json()
    return jsonify(results)

        
@app.route('/stats/')
def stats():
    # Returns how often the tags are used.
    return dict(replit_db["stats"])

# Run server:
try:
    Thread(target=create_trending).start() # Run background task that constantly fetches and caches projects from db
    app.run(host='0.0.0.0', port=8080) # Run server
except Exception:
    os.system("kill 1")
