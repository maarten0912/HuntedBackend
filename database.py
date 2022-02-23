import enum
import json

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from sqlalchemy import Enum

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

    def to_json(self):
        user = User.query.filter_by(username=self.name).first()
        return json.dumps({"id": user.id, "lat": self.lat, "long": self.long, "hunter": self.hunter})


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


class Role(enum.Enum):
    huntee = 0
    hunter = 1
    admin = 2


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, unique=False, nullable=False)
    role = db.Column(Enum(Role), unique=False, nullable=False)

    def get_id(self):
        return self.username

    def is_admin(self):
        return self.role == Role.admin

    def __repr__(self):
        return f"{self.role}:\t{self.username}"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, unique=False, nullable=False)
    message = db.Column(db.String, unique=False, nullable=False)
    role = db.Column(Enum(Role), unique=False, nullable=False)


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


class UserSchema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True


class MessageSchema(SQLAlchemySchema):
    class Meta:
        model = Message
        load_instance = True

    timestamp = auto_field()
    message = auto_field()
