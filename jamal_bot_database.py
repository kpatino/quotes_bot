import sqlite3
import random


class OpenDatabase(object):
    """
    File context manager used for opening and closing database connections

    Args:
        object (str): filepath of the database file
    """
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


def create_db(db_name):
    """
    Creates a database with people and quotes tables that the is designed to
    store quotes in.

    Args:
        db_name (str): name of the database file
    """
    create_people_table = """CREATE TABLE IF NOT EXISTS people(
                                'name' TEXT NOT NULL UNIQUE
                            );"""

    create_quotes_table = """CREATE TABLE IF NOT EXISTS quotes(
                                'id' INTEGER NOT NULL UNIQUE,
                                'name' TEXT NOT NULL,
                                'quote' TEXT NOT NULL,
                                FOREIGN KEY('name')
                                REFERENCES 'people'('name'),
                                PRIMARY KEY('id' AUTOINCREMENT)
                            );"""
    with OpenDatabase(db_name) as cursor:
        cursor.execute(create_people_table)
        cursor.execute(create_quotes_table)


def get_names():
    """Retrive all names in people table."""
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        names = ', '.join(map(str, names,))
        return(names)


def add_name(name):
    """
    Adds a name to the to the people table.

    Args:
        name (str): name that should added into the bot's database.
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("INSERT INTO people ('name') VALUES (?)", (name,))


def remove_name(name):
    """
    Remove a name and all their quotes from the bot's database.
    This action is not reversible.

    Args:
        name (str): name that should be removed from the database if it exists.
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("DELETE FROM quotes WHERE name == (?);", (name,))
        cursor.execute("DELETE FROM people WHERE name == (?);", (name,))


def check_name(name):
    """
    Checks if the name exists in the people table.

    Args:
        name (str): name that should be checked if it exists
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT count(name) FROM people WHERE name=?", (name,))
        if cursor.fetchone()[0] == 1:
            return(True)
        else:
            return(False)


def get_quote(name):
    """
    Retrieves random quote from the database by name in the table quotes.
    If no quotes are are found return a message informing there are no
    quotes under the name.

    Args:
        name (str): name used to retrieve a random quote
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        try:
            cursor.execute(
                "SELECT quote FROM quotes "
                "WHERE name=? ORDER BY RANDOM() LIMIT 1",
                (name,))
            return(cursor.fetchone()[0])
        except TypeError:
            return(f"{name} does not have any quotes")


def add_quote(name, quote):
    """
    Add quote to the bot's database using string variables name and quote

    Args:
        name (str): name used for database entry
        quote (str): quote used for database entry
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "INSERT INTO quotes ('name', 'quote') VALUES (?, ?)",
            (name, quote,))


def random_name():
    """Retrieve a random name from "people" table"""
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        name = random.choice(names)
        return(name)


def list_quotes(name):
    """
    Retrieve all quotes from the quotes table by name

    Args:
        name (str): name used to retrieve all quotes
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT * FROM quotes WHERE name == (?);", (name,))
        items = cursor.fetchall()
        return(items)
