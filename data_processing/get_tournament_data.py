"""
Query Challonge for tournament data and upsert to Mongo.
"""
import pymongo
import os
from requests import get
from config import TOURNAMENTS

DATABASE_NAME = 'production'

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
                print "completed_at is None in tournament " + tournament

            winner_id = match['match']['winner_id']
            loser_id = match['match']['loser_id']
            scores_csv = match['match']['scores_csv']

            # if winner_id is None:
            #     print "Winner ID is None in tournament " + tournament
            #     continue

            data = {'completed_at': completed_at, 'winner_id': winner_id, 'loser_id': loser_id, 'scores_csv': scores_csv}
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
        'created_at': players[-1]['participant']['created_at'],
        'region': determine_region(tournament)
    }


def upload_tournament_data(data, client=CLIENT):
    """ Insert tournament data into Mongo."""
    tournaments_collection = client[DATABASE_NAME]['tournaments']
    tournaments_collection.insert(data)


# regions
EAST = 'eastern'
CENTRAL = 'central'
WEST = 'western'
GET_GOOD = 'getgood'
NATIONAL = 'national'
EUROPE = 'europe'


def determine_region(tournament):
    """ Determine region from tournament name """
    tournament_name = tournament.lower()
    if WEST in tournament_name:
        return WEST
    elif CENTRAL in tournament_name:
        return CENTRAL
    elif EAST in tournament_name:
        return EAST
    elif GET_GOOD in tournament_name or NATIONAL in tournament_name:
        return NATIONAL
    else:
        return EUROPE


def main(client=CLIENT, tournaments=TOURNAMENTS):
    db = client[DATABASE_NAME]
    tournament_collection = db.tournaments

    # fetch tournament data
    for tournament in tournaments:
        print "Fetching data for tournament: " + tournament
        if tournament_collection.find_one({"tournament" : tournament}) is None:
            tournament_data = get_tournament_data(tournament)
            upload_tournament_data(tournament_data)


if __name__ == '__main__':
    main()
