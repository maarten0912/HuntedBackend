import random
import string

from flask import Flask, request, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, current_user, login_required

import database
from database import db

app = Flask(__name__)
# Change secret key to random string in production
app.secret_key = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hunted.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()


login_manager = LoginManager()


@login_manager.user_loader
def load_user(username):
    user = database.User.query.filter_by(username=username).first()
    return user


@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return str(current_user.is_authenticated)
    elif request.method == 'POST':
        # Get username and password from body
        try:
            username = request.values['username']
            password = request.values['password']
        except KeyError:
            return "Please specify a username and password", 400

        # Get user object and verify password
        user = load_user(username)
        if user is None:
            return "Invalid username or password", 401
        if user.password == password:
            login_user(user)
            return redirect(request.values.get('next') or url_for('index'))
        else:
            return "Invalid username or password", 401


@app.route('/')
def index():
    return "Hello world", 200


# TODO: add sessions, so only hunters in the base can get locations
@app.route('/api/locations', methods=['GET', 'POST'])
@login_required
def locations():
    if request.method == 'GET':
        # Hunter is trying to view the coordinates

        # TODO: Change to location instead of newlocation
        newlocation = database.NewLocation.query.all()
        return {"newlocations": newlocation_schema.dump(newlocation, many=True)}

    else:
        # TODO: tijd automatisch?
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
    database.register_update_job()

    # For marshmallow (de)serialization
    newlocation_schema = database.NewLocationSchema()
    location_schema = database.LocationSchema()
    user_schema = database.UserSchema()

    # Initialise login manager
    login_manager.init_app(app)

    # TODO: add WSGI for security
    app.run("0.0.0.0", debug=True)
