"""
Query Challonge for tournament data and upsert to Mongo.
"""
import pymongo
import os
from requests import get
from config import TOURNAMENTS

CLIENT = pymongo.MongoClient(os.environ.get('MONGOLAB_URI'))
CHALLONGE_KEY = os.environ.get('CHALLONGE_KEY')
TOURNAMENTS = TOURNAMENTS


def get_tournament_data(tournament):
    """ Query challonge API for player and match details.

    :param tournament: Challonge tournament id
    :returns list, list:
    """

    def get_match_data(match_list):
        match_data = []
        for match in match_list:
            completed_at = match['match']['updated_at']
            if completed_at is None:
                print tournament
            winner_id = match['match']['winner_id']
            loser_id = match['match']['loser_id']
            data = {'completed_at': completed_at, 'winner_id': winner_id, 'loser_id': loser_id}
            match_data.append(data)
        return match_data

    def get_player_data(player_list):
        player_data = []
        for player in player_list:
            id = player['participant']['id']
            name = player['participant']['challonge_username']
            data = {'id': id, 'name': name}
            player_data.append(data)
        return player_data

    url = 'https://api.challonge.com/v1/tournaments/{}/{}.json'
    params = {'api_key': CHALLONGE_KEY}
    matches = get(url.format(tournament, 'matches'), params=params).json()
    players = get(url.format(tournament, 'participants'), params=params).json()

    return {
        'players': get_player_data(players),
        'matches': get_match_data(matches),
        'tournament': tournament,
        'created_at': players[-1]['participant']['created_at']
    }


def upload_tournament_data(data, client=CLIENT):
    """ Insert tournament data into Mongo."""
    tournaments_collection = client['production']['tournaments']
    tournaments_collection.insert(data)


def main(client=CLIENT):
    # clear current tournament data
    db = client['production']
    db.drop_collection('tournaments')

    # fetch tournament data
    for tournament in TOURNAMENTS:
        print "Fetching data for tournament: " + tournament
        tournament_data = get_tournament_data(tournament)
        upload_tournament_data(tournament_data)


if __name__ == '__main__':
    main()
