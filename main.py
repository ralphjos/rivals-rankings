import os
from flask import Flask, Response,render_template, request, redirect
import pymongo
from pymongo import MongoClient

application = Flask(__name__,
					template_folder='frontend')

@application.route("/", methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host='0.0.0.0', port=port)