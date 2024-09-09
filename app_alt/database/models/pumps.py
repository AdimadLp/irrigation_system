from mongoengine import Document, StringField, IntField

class Pumps(Document):
    pumpID = IntField(required=True, unique=True)
    pumpName = StringField(required=True)
    controllerID = IntField(required=True)
    gpioPort = IntField(required=True)
    type = StringField(required=True)
    status = StringField(required=True)
    flowRate = IntField(required=True)
    meta = {'indexes': [{'fields': ['pumpID'], 'unique': True}]}