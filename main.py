import json
import os
import pymongo

from flask import Flask, request, Response, render_template, jsonify
from flask_cache import Cache, current_app
from requests import get, put

app = Flask(__name__,
            template_folder='frontend',
            static_folder='frontend')

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# Set up mongo client and collections
CLIENT = pymongo.MongoClient(os.environ.get('MONGOLAB_URI'))
DB = CLIENT['production']
TOURNAMENTS_COLLECTION = DB['tournaments']
PLAYER_COLLECTION = DB['players']

# Challonge key for POST-ing to Challonge
CHALLONGE_KEY = os.environ.get('CHALLONGE_KEY')

# Determine `pwd` of this executing file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/", methods=['GET'])
@cache.cached(timeout=86400)
def index():
    return render_template('index.html')


@app.route("/rankings/<region>")
@cache.memoize(timeout=86400)
def rankings(region='national'):
    players_in_region = list(
        PLAYER_COLLECTION.find({'region': {'$ne': 'europe'}}, {'name': 1, 'rating': 1})) if region == 'national' else \
        list(PLAYER_COLLECTION.find({'region': region}, {'name': 1, 'rating': 1}))

    print players_in_region
    players_in_region = sorted(players_in_region,
                               key=lambda x: x['rating']['mu'] - 3 * x['rating']['sigma'],
                               reverse=True)

    ranks = []
    rank = 1
    for player in players_in_region:
        rating = player['rating']['mu'] - 3 * player['rating']['sigma']
        name = player['name']
        data = {'rating': rating, 'name': name, 'rank': rank}
        ranks.append(data)
        rank += 1

    result = {'ranks': ranks, 'region': region.title()}

    return jsonify(**result)


@app.route("/players")
def all_players():
    path = os.path.join(CURRENT_DIR, 'data_processing/data/all_players.json')
    with open(path, 'r') as data:
        player_data = json.load(data)
    return Response(json.dumps(player_data),
                    mimetype='application/json')


@app.route("/autoseed/<tournament>")
def autoseed(tournament):
    def get_tournament_participants():
        url = 'https://api.challonge.com/v1/tournaments/{}/{}.json'
        params = {'api_key': CHALLONGE_KEY}
        tournament_participants = get(url.format(tournament, 'participants'), params=params).json()
        tournament_participants = [{'challonge_username': player['participant']['challonge_username'],
                                    'id': player['participant']['id']}
                                   for player in tournament_participants]
        return tournament_participants

    password = request.args.get('password')

    if password is os.environ.get('AUTOSEED_PASSWORD'):
        participants = get_tournament_participants()

        players_in_region = list(PLAYER_COLLECTION.find({'rating': {'$exists': True}},
                                                        {'name': 1, 'rating': 1}))

        players_in_region = sorted(players_in_region,
                                   key=lambda x: x['rating']['mu'] - 3 * x['rating']['sigma'],
                                   reverse=True)

        current_rankings = {}

        for index, player in enumerate(players_in_region):
            rank = index + 1
            current_rankings[player['name']] = rank

        participants = sorted(participants,
                              key=lambda participant: current_rankings.get(participant['challonge_username'], 99999)
                              )

        url = 'https://api.challonge.com/v1/tournaments/{}/participants/{}.json'
        seed = 1
        for participant in participants:
            body = {'api_key': CHALLONGE_KEY, 'seed': seed}
            put(url.format(tournament, participant['id']), json=body).raise_for_status()
            seed += 1
    else:
        return "incorrect password"

    return "Seeding successful.  pls check the bottom seeds and manually adjust accordingly thx!!!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
