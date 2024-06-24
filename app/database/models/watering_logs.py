from mongoengine import Document, StringField, IntField, ListField, DateTimeField

class WateringLogs(Document):
    plantID = IntField(required=True)
    pumpIDs = ListField(IntField())
    amount = IntField(required=True)
    timestamp = DateTimeField(required=True)
    trigger = StringField(required=True)
    scheduleID = IntField(required=True)
    meta = {'indexes': [{'fields': ['timestamp'], 'unique': False}]}