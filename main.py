import json
import os
import pymongo

from flask import Flask, Response, render_template, jsonify

application = Flask(__name__,
                    template_folder='frontend',
                    static_folder='frontend')

# Set up mongo client and collections
CLIENT = pymongo.MongoClient(os.environ.get('MONGOLAB_URI'))
DB = CLIENT['production']
TOURNAMENTS_COLLECTION = DB['tournaments']
PLAYER_COLLECTION = DB['players']

# Determine `pwd` of this executing file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


@application.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@application.route("/rankings/<region>")
def rankings(region='national'):
    """ Return raw json from file. """
    players_in_region = list(PLAYER_COLLECTION.find({'ratings.' + region: {'$exists': True}},
                                                    {'name': 1, 'ratings.' + region: 1}))

    players_in_region = sorted(players_in_region,
                               key=lambda x: x['ratings'][region]['mu'] - 3 * x['ratings'][region]['sigma'],
                               reverse=True)

    ranks = []
    rank = 1
    for player in players_in_region:
        rating = player['ratings'][region]['mu'] - 3 * player['ratings'][region]['sigma']
        name = player['name']
        data = {'rating': rating, 'name': name, 'rank': rank}
        ranks.append(data)
        rank += 1

    result = {'ranks': ranks, 'region': region.title()}

    return jsonify(**result)


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
