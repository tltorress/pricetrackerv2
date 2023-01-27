import pymongo
from config import mongoConn


class Database:

    def __init__(self):
        self.client = pymongo.MongoClient(mongoConn)
        self.database = self.client['Price_List']

    def insert_game(self, game, collection):
        self.database[collection].insert_one(game)

    def insert_many_games(self, games_arr, collection):
        try:
            self.database[collection].drop()
            self.database[collection].insert_many(games_arr)

        except Exception as e:
            print(e)
