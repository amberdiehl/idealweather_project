from playhouse.postgres_ext import *
from config import DATABASE


class Station(Model):
    WBAN = IntegerField(unique=True, index=True)
    attributes = BinaryJSONField()

    class Meta:
        database = DATABASE


class Monthly(Model):
    WBAN = IntegerField(index=True)
    YearMonth = CharField(index=True)
    attributes = BinaryJSONField()

    class Meta:
        database = DATABASE


class Humidity(Model):
    WBAN = IntegerField(index=True)
    YearMonthDay = CharField(index=True)
    readings = BinaryJSONField()

    class Meta:
        database = DATABASE


def initialize():
    try:
        DATABASE.connect()
    except OperationalError:
        pass
    # DATABASE.drop_tables([Station, Humidity, Monthly])
    DATABASE.create_tables([Station, Monthly, Humidity], safe=True)
    DATABASE.close()