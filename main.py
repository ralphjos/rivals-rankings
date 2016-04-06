import json
import os
from flask import Flask, Response, render_template

application = Flask(__name__,
                    template_folder='frontend')

# Determine `pwd` of this executing file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


@application.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@application.route("/rankings")
def rankings():
    """ Return raw json from file. """
    path = os.path.join(CURRENT_DIR, 'data_processing/data/current_rankings.json')
    with open(path, 'r') as data:
        ranking_data = json.load(data)
    return Response(json.dumps(ranking_data),
                    mimetype='application/json')


@application.route("/players")
def all_players():
    """ Return raw json from file. """
    path = os.path.join(CURRENT_DIR, 'data_processing/data/all_players.json')
    with open(path, 'r') as data:
        player_data = json.load(data)
    return Response(json.dumps(player_data),
                    mimetype='application/json')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host='0.0.0.0', port=port)
