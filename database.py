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


def registerUpdateJob():
    import atexit
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=updateLocations, trigger="interval", minutes=15, start_date = "2022-01-01 12:00:00")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(scheduler.shutdown)

# TODO: send also with websocket
def updateLocations():
    import datetime
    print(datetime.datetime.now())

        newlocations = NewLocation.query.order_by(NewLocation.time.desc()).all()
    oldlocations = Location.query.order_by(Location.time.desc()).all()

    newnames = []
    newlocs = []
    for newlocation in newlocations:
        if newlocation.name not in newnames:
            newnames.append(newlocation.name)
            newlocs.append(newlocation)

    oldnames = []
    for oldlocation in oldlocations:
        assert oldlocation.name not in oldnames
        oldnames.append(oldlocation.name)

    notupdated = list(set(oldnames) - set(newnames))
    if len(notupdated) > 0:
        # TODO: put in some kind of log?
        print("[WARNING] Found names that had no update in the last 15 minutes:")
        for n in notupdated:
            print(f"\t{n}")

    # Delete both tables
    db.session.query(NewLocation).delete()
    db.session.query(Location).delete()

    # Put the newest values in Locations
    for l in newlocs:
        db.session.add(Location(time=l.time, hunter=l.hunter, name=l.name, lat=l.lat, long=l.long))

    db.session.commit()

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