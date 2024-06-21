from pymongo import MongoClient

class Plant:
    def __init__(self, db):
        self.collection = self.db['plants']

    def insert_plant(self, plant_data):
        return self.collection.insert_one(plant_data).inserted_id

    def find_plant(self, plant_id):
        return self.collection.find_one({"plantID": plant_id})

    def update_plant(self, plant_id, update_data):
        return self.collection.update_one({"plantID": plant_id}, {"$set": update_data})

    def delete_plant(self, plant_id):
        return self.collection.delete_one({"plantID": plant_id})
