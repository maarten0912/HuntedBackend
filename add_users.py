import csv
import random
import string

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import database

USERS_CSV = "users.csv"

db = SQLAlchemy()


def create_user(username: str, role: str):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for _ in range(8))

    return database.User(username=username, password=password, role=role)


def create_bulk_users(filename: str):
    users = []

    with open(filename) as file:
        reader = csv.reader(file, delimiter=',')
        for entry in reader:
            user = create_user(entry[0], entry[1])
            print(f"{user}\t{user.password}")
            users.append(user)

    return users


if __name__ == '__main__':
    engine = create_engine('sqlite:///hunted.db')
    session = Session(engine)
    session.bulk_save_objects(create_bulk_users(USERS_CSV))
    session.commit()
