import sqlite3
import random


class open_db(object):
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


def get_names():
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        names = ', '.join(map(str, names,))
        return(names)


def add_name(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("INSERT INTO people ('name') VALUES (?)", (name,))


def remove_name(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("DELETE FROM people WHERE name == (?);", (name,))


def check_name(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT count(name) FROM people WHERE name=?", (name,))
        if cursor.fetchone()[0] == 1:
            return(True)
        else:
            return(False)


def get_quote(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT quote FROM quotes WHERE name=? ORDER BY RANDOM() LIMIT 1", (name,))
        return(cursor.fetchone()[0])


def add_quote(name, quote):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "INSERT INTO quotes ('name', 'quote') VALUES (?, ?)", (name, quote, ))


def random_name():
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        name = random.choice(names)
        return(name)


def list_quotes(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT * FROM quotes WHERE name == (?);", (name,))
        items = cursor.fetchall()
        return(items)
