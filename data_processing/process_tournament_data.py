"""
Before Nightly Processing
==========
- Get players and matches data from challonge -> "tournaments" collection
- Get player records for tournaments they entered -> store in "players" collection

Apply TrueSkill Algorithm
=========
1) Sort all tournaments by date
2) Build map of {id: rating}. Rating is calculated as mu - 2 * sigma
3) Run TrueSkill on matches chronologically.

Upsert Data
=========
- Store all of a player's matches on their player record.
- Sort by rating to produce Rankings -> data/current_rankings.json
- Upsert ratings to player records & upsert ranking to player record.
"""
import json
import os
import pymongo
import trueskill

from collections import defaultdict

# Initialize pointers to Mongo collections
CLIENT = pymongo.MongoClient(os.environ.get('MONGOLAB_URI'))
DB = CLIENT['production']
TOURNAMENTS_COLLECTION = DB['tournaments']
PLAYER_COLLECTION = DB['players']


def update_all_tournament_matches(tournament):
    """ Update all tournament matches for a tournament to use the tag that the
    player entered as rather than an id. """
    # Build a map of player_id to player_name
    id_to_name = {}
    for player in tournament['players']:
        id_to_name[player['id']] = player['name']

    # Update winner and loser id to player_name from player_id
    for match in tournament['matches']:
        match['winner_id'] = id_to_name[match['winner_id']]
        match['loser_id'] = id_to_name[match['loser_id']]

    return tournament


def update_player_trueskill(tournament):
    """ Update rating for each player by iterating over each match
    in chronological order and applying trueskill."""

    # Calculate TrueSkill from each map
    def get_trueskill_rating(player_db_object, match_region):
        if player_db_object and region in player_db_object['ratings']:
            mu = player_db_object['ratings'][match_region]['mu']
            sigma = player_db_object['ratings'][match_region]['sigma']
            return trueskill.Rating(mu=mu, sigma=sigma)

        return trueskill.Rating(mu=25, sigma=25 / 3.0)

    region = tournament['region']
    for match in tournament['matches']:
        winner, loser = match['winner_id'], match['loser_id']
        # If the player exists in our map, we will take their current rating.
        # Otherwise we will initialize a 0 Rating placeholder player.
        winner_db_object = PLAYER_COLLECTION.find_one({'tag': winner})

        loser_db_object = PLAYER_COLLECTION.find_one({'tag': loser})

        winner_regional_rating = get_trueskill_rating(winner_db_object, region)
        loser_regional_rating = get_trueskill_rating(loser_db_object, region)

        updated_winner_regional_rating, loser_regional_rating = \
            trueskill.rate_1vs1(winner_regional_rating, loser_regional_rating)

        PLAYER_COLLECTION.update_one({'tag': winner},
                                     {
                                         '$set': {
                                             'ratings.' + region: {
                                                 'mu': updated_winner_regional_rating.mu,
                                                 'sigma': updated_winner_regional_rating.sigma
                                             }
                                         }
                                     },
                                     upsert=True)
        
        PLAYER_COLLECTION.update_one({'tag': loser},
                                     {
                                         '$set': {
                                             'ratings.' + region: {
                                                     'mu': loser_regional_rating.mu,
                                                     'sigma': loser_regional_rating.sigma
                                             }
                                         }
                                     },
                                     upsert=True)


def build_player_matches_list(tournament, player_matches):
    """ Build list of matches for each player."""
    for match in tournament['matches']:
        winner, loser = match['winner_id'], match['loser_id']
        player_matches[winner].append(match)
        player_matches[loser].append(match)
    return player_matches

def main():
    """ Nightly processing main hook."""
    tournaments = list(TOURNAMENTS_COLLECTION.find())

    for tournament in tournaments:
        tournament = update_all_tournament_matches(tournament)

    # Iterate over each tournament chronologically and update trueskill
    tournaments.sort(key=lambda x: x['created_at'])

    for tournament in tournaments:
        update_player_trueskill(tournament)

    # Update list of matches on each individual player record
    player_matches = defaultdict(list)
    for tournament in tournaments:
        build_player_matches_list(tournament, player_matches)
    for tag, matches in player_matches.items():
        PLAYER_COLLECTION.update_one({'tag': tag},
                                   {'$set': {'matches': matches}},
                                   upsert=True)

if __name__ == '__main__':
    main()
