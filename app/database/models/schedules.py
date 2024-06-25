from mongoengine import Document, StringField, IntField, ListField, DateTimeField

class Schedules(Document):
    scheduleID = IntField(required=True, unique=True)
    weekdays = ListField(StringField())
    startTime = DateTimeField(required=True)
    endTime = DateTimeField(required=True)
    type = StringField(required=True)
    plantID = IntField(required=True)
    threshold = IntField(required=True)
    meta = {'indexes': [{'fields': ['scheduleID'], 'unique': True}]}

    def get_schedules_by_plant_id(plant_id):
        return Schedules.objects(plantID=plant_id)