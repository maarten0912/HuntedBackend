from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Team


def create_teams(count: int):
    for _ in range(count):
        session.add(Team())


if __name__ == '__main__':
    engine = create_engine('sqlite:///hunted.db')
    session = Session(engine)
    create_teams(int(input("How many teams do you want to add? ")))
    session.commit()
