import os
from flask import Flask, Response,render_template, request, redirect
import pymongo
from pymongo import MongoClient


MONGO_URL = os.environ.get('MONGOLAB_URI')
client = MongoClient(MONGO_URL)

# Specify the database
db = client.heroku_7xvlpzvh
collection = db.shoutouts

application = Flask(__name__)

@application.route("/", methods=['GET'])
def index():
    shouts = collection.find()
    return render_template('index.html', shouts=shouts)

if __name__ == "__main__":
    application.run()