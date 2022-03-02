import time
from datetime import datetime
from typing import Optional

import eventlet

from flask import Flask, request, redirect, url_for, render_template
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, current_user, login_required
from flask_socketio import SocketIO, join_room, leave_room

from database import db, User, Role, NewLocation, Location, NewLocationSchema, LocationSchema, \
    UserSchema, Message, MessageSchema, LastUpdate
from scheduler import register_update_job, change_update_interval

# Patch threads etc, to use eventlets
eventlet.monkey_patch()

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


@app.route('/information')
@login_required
def information():
    return render_template('information.html')


@app.route('/api/locations', methods=['GET', 'POST'])
@login_required
def locations():
    if request.method == 'GET':
        # Hunter is trying to view the coordinates
        if current_user.role == Role.huntee:
            return 'You are not a hunter or admin', 401
        dead = User.query.filter_by(alive=False, role='huntee')
        dead_ids = {user.id for user in dead}
        if current_user.role == Role.hunter:
            location = Location.query.all() + NewLocation.query.filter_by(hunter=True).all()
            # Filter out dead people
            location = [loc for loc in location if loc.id not in dead_ids]
            return {"locations": [loc.to_object() for loc in location]}
        elif current_user.role == Role.admin:
            location = Location.query.all() + NewLocation.query.all()
            # Filter out dead people
            location = [loc for loc in location if loc.id not in dead_ids]
            return {"locations": [loc.to_object() for loc in location]}


    elif request.method == 'POST':
        # Huntee or hunter is posting their location
        # Update or insert new location
        location = NewLocation.query.filter_by(id=current_user.id).first()
        if not location:
            location = NewLocation(id=current_user.id,
                                   time=datetime.now(), hunter=(current_user.role == Role.hunter),
                                   name=current_user.username, lat=float(request.values["lat"]),
                                   long=float(request.values["long"]))
        else:
            location.time = datetime.now()
            location.lat = float(request.values["lat"])
            location.long = float(request.values["long"])
        # Send to admins
        emit_admin_websockets("locations", [location.to_json()])
        # If this is a hunter, send their location immediately
        if current_user.role == Role.hunter:
            emit_websocket("locations", [location.to_json()])

        # Add to database
        db.session.add(location)
        db.session.commit()
        print(location)

        return 'OK', 200


@app.route("/api/admin/interval", methods=["POST"])
def update_interval():
    # TODO admin frontend? (curl is ook een frontend, nou en)
    if request.method == 'POST':
        if current_user.role == Role.admin:
            change_update_interval(int(request.values["interval"]))
            return '', 204
        else:
            return "You are not an admin", 401


@app.route("/api/messages", methods=["GET", "POST"])
@login_required
def messages():
    if request.method == 'GET':
        # Get the messages for the current users role
        if current_user.role != Role.admin:
            message_list = Message.query.filter_by(role=current_user.role).all()
        else:
            message_list = Message.query.all()
        return {"messages": message_schema.dump(message_list, many=True)}
    elif request.method == 'POST':
        if current_user.role == Role.admin:
            timestamp = round(time.time() * 1000)
            # Save to database
            message = Message(timestamp=timestamp,
                              message=request.values["message"],
                              role=request.values["role"])

            db.session.add(message)
            db.session.commit()

            # Send to appropriate websockets
            emit_information(request.values["role"],
                             request.values["message"], timestamp)
            return '', 204
        else:
            return "You are not an admin", 401


@app.route("/api/admin/kill", methods=["POST"])
def kill():
    if current_user.role == Role.admin:
        # Get user
        user = User.query.filter_by(username=request.values["username"]).first()
        if not User:
            return "User not found", 400
        # Kill user
        user.alive = False
        db.session.commit()
        # Send updated user count and kill message
        emit_websocket("alive", get_alive_count())
        emit_websocket("kill", user.id)
        return '', 204
    else:
        return "You are not an admin", 401


@app.route("/test")
def test():
    emit_admin_websockets("locations", [{"id": 1, "lat": 52.22, "long": 6.89}])
    return '', 204


def emit_websocket(event: str, message):
    print(f"Emitting: {message}")
    websocket.emit(event, message, namespace="/", broadcast=True)


def emit_admin_websockets(event: str, message):
    print(f"Emitting ADMIN: {message}")
    websocket.emit(event, message, namespace="/", to="admin")


def emit_information(room: str, message: str, timestamp: Optional[int] = None):
    print(f"Emitting {room}: {message}")
    if timestamp is None:
        timestamp = round(time.time() * 1000)
    websocket.emit("message", {"timestamp": timestamp, "message": message}, namespace="/info-socket", to=room)


def get_alive_count():
    alive = User.query.filter_by(role='huntee', alive=True).all()
    return len(alive)


@websocket.on("connect")
def on_websocket_connect():
    if current_user.role == Role.admin:
        join_room("admin")
    timestamp = LastUpdate.query.first().timestamp
    # TODO only send to this user, not to everyone
    emit_websocket("last_update", timestamp)
    emit_websocket("alive", get_alive_count())


@websocket.on("connect", namespace="/info-socket")
def on_websocket_info_connect():
    if current_user.role in {Role.admin, Role.huntee}:
        join_room("huntee")
    elif current_user.role in {Role.admin, Role.hunter}:
        join_room("hunter")


@websocket.on("disconnect")
def on_websocket_disconnect():
    if current_user.role == Role.admin:
        leave_room("admin")


@app.before_first_request
def init():
    # Move newest record from newlocations to locations every 15 minutes
    register_update_job(emit_websocket, emit_information, app.app_context())


if __name__ == '__main__':
    db.init_app(app)

    # TODO: turn on some form of authentication here
    admin = Admin(app)
    admin.add_view(ModelView(Location, db.session))
    admin.add_view(ModelView(NewLocation, db.session))

    # Create database tables
    db.create_all()

    # Create needed entries, if necessary
    last_update = LastUpdate.query.first()
    if not last_update:
        last_update = LastUpdate(timestamp=0)
        db.session.add(last_update)
        db.session.commit()


    # For marshmallow (de)serialization
    newlocation_schema = NewLocationSchema()
    location_schema = LocationSchema()
    user_schema = UserSchema()
    message_schema = MessageSchema()

    # Initialise login manager
    login_manager.init_app(app)

    websocket.run(app, "0.0.0.0", debug=True)
