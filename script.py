import sqlite3
import time
from datetime import datetime, timedelta

date_format = "%Y-%m-%d %H:%M:%S.%f"

con = sqlite3.connect('hunted.db')
cur = con.cursor()

while True:
    print("\n"*10)
    print("Hunters:")
    for row in cur.execute('SELECT * FROM new_location, user WHERE hunter=1 AND new_location.id = user.id AND user.alive = 1'):
        date = datetime.strptime(row[1],date_format)
        now = datetime.now()
        difference = now - date
        difference = difference - timedelta(hours=1)
        hours, rem = divmod(difference.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f"\t{row[3]}:{' ' * (20-len(row[3]))}{hours:02d}:{minutes:02d}:{seconds:02d}")

    print("Huntees:")
    for row in cur.execute('SELECT * FROM new_location, user WHERE hunter=0 AND new_location.id = user.id AND user.alive = 1'):
        date = datetime.strptime(row[1],date_format)
        now = datetime.now()
        difference = now - date
        difference = difference - timedelta(hours=1)
        hours, rem = divmod(difference.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f"\t{row[3]}:{' ' * (20-len(row[3]))}{hours:02d}:{minutes:02d}:{seconds:02d}")
    time.sleep(1)
con.close()

