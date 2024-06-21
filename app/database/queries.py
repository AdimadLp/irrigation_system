from app.database.connection import MongoDB

def query_all_plant_name_ids():
    db = MongoDB().connect()
    plants = db['plants'].find()
    for plant in plants:
        print(plant)

def query_plant_by_name(name):
    db = MongoDB().connect()
    plant = db['plants'].find_one({'name': name})
    return plant