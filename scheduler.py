# TODO: send also with websocket
import atexit
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from flask.ctx import AppContext

from database import NewLocation, Location, db


def update_locations(emit_websocket: Callable[[str, any], None], context: AppContext):
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
            emit_websocket("locations", loc)
            db.session.add(Location(time=loc.time, hunter=loc.hunter, name=loc.name, lat=loc.lat, long=loc.long))

        db.session.commit()


def register_update_job(emit_websocket: Callable[[str, any], None], context: AppContext):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_locations, args=[emit_websocket, context],
                      trigger="interval", seconds=15, start_date="2022-01-01 12:00:00")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(scheduler.shutdown)
