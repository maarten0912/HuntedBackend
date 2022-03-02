# TODO: send also with websocket
import atexit
import json
import time
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from flask.ctx import AppContext

from database import NewLocation, Location, db, LastUpdate

# Default update interval (in seconds)
INTERVAL = 600


def update_locations(emit_websocket: Callable[[str, any], None], emit_information: Callable[[str, str], None], context: AppContext):
    import datetime
    print(datetime.datetime.now())

    with context:
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
        for loc in newlocs:
            print(loc)
            db.session.add(Location(id=loc.id, time=loc.time, hunter=loc.hunter, name=loc.name, lat=loc.lat, long=loc.long))

        # Send over websocket
        locations = [loc.to_json() for loc in newlocs]
        emit_websocket("locations", locations)
        # Send to the huntee that the location has been sent
        emit_information("huntee", "Your location has been sent to the hunters!")

        # Save the time of this update
        timestamp = round(time.time() * 1000)
        last_update = LastUpdate.query.first()
        last_update.timestamp = timestamp
        db.session.commit()
        # Send over websocket
        emit_websocket("last_update", timestamp)


scheduler = BackgroundScheduler()


def register_update_job(emit_websocket: Callable[[str, any], None], emit_information: Callable[[str, str], None], context: AppContext):
    scheduler.add_job(func=update_locations, args=[emit_websocket, emit_information, context],
                      trigger="interval", seconds=INTERVAL, start_date="2022-01-01 12:00:00",
                      id="locations")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(scheduler.shutdown)


def change_update_interval(seconds: int):
    print(f"Setting scheduler to every {seconds} seconds")
    scheduler.reschedule_job("locations", trigger="interval", seconds=seconds)

