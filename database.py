from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

db = SQLAlchemy()

# This table should contain the newest location of each device
class NewLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.TIMESTAMP, unique=False, nullable=False)
    hunter = db.Column(db.Boolean, unique=False, nullable=False)
    name = db.Column(db.String(20), unique=False, nullable=False)
    lat = db.Column(db.Float(), unique=False, nullable=False)
    long = db.Column(db.Float(), unique=False, nullable=False)
 
    def __repr__(self):
        if self.hunter:
            return f"[{self.time}]\tHunter {self.name}\t{self.lat}, {self.long}"
        else:
            return f"[{self.time}]\tHuntee {self.name}\t{self.lat}, {self.long}"

# This table should contain last sent location of each device
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.TIMESTAMP, unique=False, nullable=False)
    hunter = db.Column(db.Boolean, unique=False, nullable=False)
    name = db.Column(db.String(20), unique=False, nullable=False)
    lat = db.Column(db.Float(), unique=False, nullable=False)
    long = db.Column(db.Float(), unique=False, nullable=False)
 
    def __repr__(self):
        if self.hunter:
            return f"[{self.time}]\n\tHunter {self.name}\n\t{self.lat}, {self.long}"
        else:
            return f"[{self.time}]\n\tHuntee {self.name}\n\t{self.lat}, {self.long}"


# TODO: make function to remove all records before a set time
def registerUpdateJob():
    import time
    import atexit
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=updateLocations, trigger="interval", minutes=15, start_date = "2022-01-01 12:00:00")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

# TODO: send also with websocket
def updateLocations():
    return None

class NewLocationSchema(SQLAlchemySchema):
    class Meta:
        model = NewLocation
        load_instance = True

    id = auto_field()
    time = auto_field()
    hunter = auto_field()
    name = auto_field()
    lat = auto_field()
    long = auto_field()


class LocationSchema(SQLAlchemySchema):
    class Meta:
        model = Location
        load_instance = True

    id = auto_field()
    time = auto_field()
    hunter = auto_field()
    name = auto_field()
    lat = auto_field()
    long = auto_field()