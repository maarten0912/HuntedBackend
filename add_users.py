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
    user_id = random.randint(0, 99999)

    return database.User(id=user_id, username=username, password=password, role=role)


def create_users(filename: str):
    with open(filename) as file:
        reader = csv.reader(file, delimiter=',')
        for entry in reader:
            user = create_user(entry[0], entry[1])
            print(f"{user}\t{user.password}")
            session.add(user)


if __name__ == '__main__':
    engine = create_engine('sqlite:///hunted.db')
    session = Session(engine)
    create_users(USERS_CSV)
    session.commit()
