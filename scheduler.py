# TODO: send also with websocket
import atexit
import json
import time
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from flask.ctx import AppContext

from database import NewLocation, Location, db, LastUpdate, SkipUpdate

# Default update interval (in seconds)
interval = 600


def update_locations(emit_websocket: Callable[[str, any], None], emit_information: Callable[[str, str], None], context: AppContext):
    import datetime
    print(datetime.datetime.now())

    with context:
        newlocations = NewLocation.query.order_by(NewLocation.time.desc()).all()
        oldlocations = Location.query.order_by(Location.time.desc()).all()

        # Save the time of this update
        timestamp = round(time.time() * 1000)
        last_update = LastUpdate.query.first()
        last_update.timestamp = timestamp

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
            print(f"[WARNING] Found names that had no update in the last {round(interval / 60)} minutes:")
            for n in notupdated:
                print(f"\t{n}")

        # Get list of locations that we should skip
        skips = {skip.id for skip in SkipUpdate.query.all()}

        # Update the Locations table
        for newloc in newlocs:
            # Check if we should skip this location
            if newloc.id in skips:
                print("Skipping location of " + newloc.name)
                # Remove this skip (so that it does not skip again next time)
                SkipUpdate.query.filter_by(id=newloc.id).delete()
                # Don't send the location
                newlocs.remove(newloc)
                continue

            # Add or update the location
            location = Location.query.filter_by(id=newloc.id).first()
            if not location:
                location = Location(id=newloc.id, time=newloc.time, hunter=newloc.hunter,
                                    name=newloc.name, lat=newloc.lat, long=newloc.long)
            else:
                location.lat = newloc.lat
                location.long = newloc.long
                location.time = newloc.time

            # Add to database
            db.session.add(location)

        # Send over websocket
        locations = [loc.to_json() for loc in newlocs]
        emit_websocket("locations", locations)
        # Send the skipped locations
        emit_websocket("skipped", list(skips))
        # Send to the huntee that the location has been sent
        # TODO send to skipped locations, that their location has not been sent
        emit_information("huntee", "Your location has been sent to the hunters!")

        # Commit database changes
        db.session.commit()
        # Send over websocket
        emit_websocket("last_update", timestamp)


scheduler = BackgroundScheduler()


def register_update_job(emit_websocket: Callable[[str, any], None], emit_information: Callable[[str, str], None], context: AppContext):
    scheduler.add_job(func=update_locations, args=[emit_websocket, emit_information, context],
                      trigger="interval", seconds=interval, start_date="2022-01-01 12:00:00",
                      id="locations")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(scheduler.shutdown)


def change_update_interval(seconds: int):
    print(f"Setting scheduler to every {seconds} seconds")
    scheduler.reschedule_job("locations", trigger="interval", seconds=seconds)
    global interval
    interval = seconds

