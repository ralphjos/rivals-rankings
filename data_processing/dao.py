from model import *

DEFAULT_RATING = TrueskillRating()
DATABASE_NAME = 'production'
PLAYERS_COLLECTION_NAME = 'players'
TOURNAMENTS_COLLECTION_NAME = 'tournaments'


class Dao(object):
    def __init__(self, mongo_client, database_name=DATABASE_NAME):
        self.mongo_client = mongo_client

        self.players_col = mongo_client[database_name][PLAYERS_COLLECTION_NAME]
        self.tournaments_col = mongo_client[database_name][TOURNAMENTS_COLLECTION_NAME]

    def get_player_rating(self, name):
        player = Player.from_json(self.players_col.find_one({'name': name}))
        return player.rating.get_effective_rating()
