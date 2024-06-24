from mongoengine import Document, StringField, IntField, ListField, DateTimeField

class Plants(Document):
    plantID = IntField(required=True, unique=True)
    plantName = StringField(required=True)
    plantType = StringField(required=True)
    location = StringField(required=True)
    controllerID = IntField(required=True)
    sensorIDs = ListField(IntField())
    pumpIDs = ListField(IntField())
    waterRequirement = IntField(required=True)
    lastWatered = DateTimeField(required=True)
    imagePath = StringField(required=True)
    meta = {'indexes': [{'fields': ['plantID'], 'unique': True}]}