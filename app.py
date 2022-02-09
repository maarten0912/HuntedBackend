
from flask import Flask, request, redirect, url_for, render_template
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, current_user, login_required
from flask_socketio import SocketIO

from database import db, User, Role, NewLocation, Location, register_update_job, NewLocationSchema, LocationSchema, \
    UserSchema

app = Flask(__name__)
# Change secret key to random string in production
app.secret_key = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hunted.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

websocket = SocketIO(app)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(username):
    user = User.query.filter_by(username=username).first()
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
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return render_template('login.html')


@app.route('/api/locations', methods=['GET', 'POST'])
@login_required
def locations():
    if request.method == 'GET':
        # Hunter is trying to view the coordinates
        if current_user.role in {Role.admin, Role.hunter}:
            location = Location.query.all()
            return {"newlocations": location_schema.dump(location, many=True)}
        else:
            return 'You are not a hunter or admin', 401

    elif request.method == 'POST':
        # TODO: tijd automatisch?
        # POST
        # Huntee or hunter is posting their location
        location = newlocation_schema.load(request.get_json(force=True), session=db.session)
        db.session.add(location)
        db.session.commit()
        print(location)

        return 'OK', 200


if __name__ == '__main__':
    db.init_app(app)

    # TODO: turn on some form of authentication here
    admin = Admin(app)
    admin.add_view(ModelView(Location, db.session))
    admin.add_view(ModelView(NewLocation, db.session))

    # Create database tables
    db.create_all()

    # Move newest record from newlocations to locations every 15 minutes
    register_update_job()

    # For marshmallow (de)serialization
    newlocation_schema = NewLocationSchema()
    location_schema = LocationSchema()
    user_schema = UserSchema()

    # Initialise login manager
    login_manager.init_app(app)

    # TODO: add WSGI for security
    websocket.run(app, "0.0.0.0", debug=True)
