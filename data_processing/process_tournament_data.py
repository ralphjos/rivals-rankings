"""
Before Nightly Processing
==========
- Get players and matches data from challonge -> "tournaments" collection
- Get user records for tournaments they entered -> store in "users" collection

Apply TrueSkill Algorithm
=========
1) Sort all tournaments by date
2) Build map of {id: rating}. Rating is calculated as mu - 2 * sigma
3) Run TrueSkill on matches chronologically.

Upsert Data
=========
- Store all of a user's matches on their user record.
- Sort by rating to produce Rankings -> data/current_rankings.json
- Upsert ratings to user records & upsert ranking to user record.
"""
import json
import os
import pymongo
import trueskill

from collections import defaultdict


def update_all_tournament_matches(tournament):
    """ Update all tournament matches for a tournament to use the tag that the
    player entered as rather than an id. """
    # Build a map of player_id to player_name
    print "TOURNAMENT", tournament
    id_to_name = {}
    for player in tournament['players']:
        id_to_name[player['id']] = player['name']

    # Update winner and loser id to player_name from player_id
    for match in tournament['matches']:
        match['winner_id'] = id_to_name[match['winner_id']]
        match['loser_id'] = id_to_name[match['loser_id']]
    return tournament


def update_player_trueskill(tournament, ratings_map):
    """ Update rating for each player by iterating over each match
    in chronological order and applying trueskill."""
    # Calculate TrueSkill from each map
    region = tournament['region']

    for match in tournament['matches']:
        winner, loser = match['winner_id'], match['loser_id']
        # If the user exists in our map, we will take their current rating.
        # Otherwise we will initialize a 0 Rating placeholder player.
        winner_regional_ratings = ratings_map.setdefault(winner, {})
        loser_regional_ratings = ratings_map.setdefault(loser, {})
        winner_rating_in_region = winner_regional_ratings.get(region, trueskill.Rating(25, 25 / 3.0))
        loser_rating_in_region = loser_regional_ratings.get(region, trueskill.Rating(25, 25 / 3.0))
        winner_rating_in_region, loser_rating_in_region = \
            trueskill.rate_1vs1(winner_rating_in_region, loser_rating_in_region)
        # Update the dictionary with new ratings
        winner_regional_ratings[region] = winner_rating_in_region
        loser_regional_ratings[region] = loser_rating_in_region

    return ratings_map


def build_user_matches_list(tournament, player_matches):
    """ Build list of matches for each user."""
    for match in tournament['matches']:
        winner, loser = match['winner_id'], match['loser_id']
        player_matches[winner].append(match)
        player_matches[loser].append(match)
    return player_matches


def update_rankings(ratings_map,
                    outdir='data/', user_collection=None):
    """ Build a list of rankings with the ratings map. Update each
    player in Mongo with their respective regional rankings and output
    regional rankings to json files. """
    ratings_by_region = {}

    for player, player_ratings in ratings_map.items():
        for region, rating in player_ratings.items():
            regional_ratings = ratings_by_region.setdefault(region, [])
            regional_ratings.append({'name': player, 'rating': rating.mu - 3 * rating.sigma})

    for region, ratings in ratings_by_region.items():
        ratings.sort(key=lambda x: x['rating'], reverse=True)
        for index, rating in enumerate(ratings):
            rating['rank'] = index + 1

    for region, ratings in ratings_by_region.items():
        with open(outdir + region + '_rankings.json', 'w') as ranking_file:
            ranking_file.write(json.dumps({'ranks': ratings, 'region': region.title()}))

    # TODO: update ratings data in mongo


def build_all_players_list(ratings_map, outfile='data/all_players.json'):
    """ Build a list of all players and output to a json file."""
    all_players = {"players": [x for x in ratings_map.keys()]}
    with open(outfile, 'w') as all_players_file:
        all_players_file.write(json.dumps(all_players))
    return all_players


def main():
    """ Nightly processing main hook."""
    # Initialize pointers to Mongo collections
    client = pymongo.MongoClient(os.environ.get('MONGOLAB_URI'))
    db = client['production']
    db.drop_collection('users')
    tournaments_collection = db['tournaments']
    user_collection = db['users']

    tournaments = {tourney['tournament']: tourney for \
                   tourney in tournaments_collection.find()}

    for tid, tournament in tournaments.items():
        tournaments[tid] = update_all_tournament_matches(tournament)

    # Iterate over each tournament chronologically and update trueskill
    ordered_tournaments = tournaments.values()
    ordered_tournaments.sort(key=lambda x: x['created_at'])
    ratings_map = {}
    for tournament in ordered_tournaments:
        update_player_trueskill(tournament, ratings_map)

    # Update list of matches on each individual user record
    player_matches = defaultdict(list)
    for tournament in ordered_tournaments:
        build_user_matches_list(tournament, player_matches)
    for tag, matches in player_matches.items():
        user_collection.update_one({'tag': tag},
                                   {'$set': {'matches': matches}},
                                   upsert=True)

    # Update rankings for each user record and write rankings to json file
    update_rankings(ratings_map, user_collection=user_collection)

    # Build a list of all players and store in json file
    build_all_players_list(ratings_map)


if __name__ == '__main__':
    main()
