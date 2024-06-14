from mongoengine import Document, StringField, IntField, ListField, DateTimeField

class Plant(Document):
    plantID = IntField(required=True)
    plantName = StringField(required=True)
    plantType = StringField(required=True)
    controllerID = IntField(required=True)
    sensorIDs = ListField(IntField(), required=True)
    pumpIDs = ListField(IntField(), required=True)
    waterRequirement = IntField(required=True)
    lastWatered = DateTimeField(required=True)
    imagePath = StringField(required=True)