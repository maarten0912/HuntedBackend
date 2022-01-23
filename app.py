from flask import Flask, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

import database
from database import db

app = Flask(__name__)
# Change secret key to random string in production
app.secret_key = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hunted.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()


# TODO: add sessions, so only hunters in the base can get locations
@app.route('/api/locations', methods = ['GET', 'POST'])
def locations():
    if request.method == 'GET':
        # Hunter is trying to view the coordinates
        
        # TODO: Change to location instead of newlocation
        newlocation = database.NewLocation.query.all()
        return {"newlocations": newlocation_schema.dump(newlocation, many=True)}

    else:
        # POST
        # Huntee or hunter is posting their location
        newlocation = newlocation_schema.load(request.get_json(force=True), session=db.session)
        db.session.add(newlocation)
        db.session.commit()
        print(newlocation)

        return 'OK', 200
            
if __name__ == '__main__':
    
    db.init_app(app)

    # TODO: turn on some form of authentication here
    admin = Admin(app)
    admin.add_view(ModelView(database.Location, db.session))
    admin.add_view(ModelView(database.NewLocation, db.session))

    # Create database tables
    db.create_all()

    # Move newest record from newlocations to locations every 15 minutes
    database.registerUpdateJob()

    # For marshmallow (de)serialization
    newlocation_schema = database.NewLocationSchema()
    location_schema = database.LocationSchema()

    # TODO: add WSGI for security
    app.run()