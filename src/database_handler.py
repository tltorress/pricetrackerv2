import pymongo
from config import mongoConn
import time

class Database:

    def __init__(self):
        self.client = pymongo.MongoClient(mongoConn)
        self.database = self.client['price_list']

    def insert_game(self, game, collection):
        self.database[collection].insert_one(game)

    def insert_many_games(self, games_arr, collection):
        try:
            self.database[collection].drop()
            time.sleep(3)
            self.database[collection].insert_many(games_arr)
            self.database[collection].create_index([("name", "text")])
        except Exception as e:
            print(e)
