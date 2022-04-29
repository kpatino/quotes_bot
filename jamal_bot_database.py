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


def create_db(db_name: str):
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
    """
    Return a string with all names in the people table.

    Returns:
        str: String containing the names separated by commas
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        names.sort()
        names = ', '.join(map(str, names,))
        return(names)


def get_names_list():
    """
    Return a list of the first 20 names in the people table in alphabetical
    order.

    Returns:
        list: List of names
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names_list = [
            v[0] for v in cursor.fetchall()
        ]
        names_list.sort()
        return(names_list[:20])


def add_name(name: str):
    """
    Adds a name to the to the people table.

    Args:
        name (str): Name that should added into the bot's database.
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("INSERT INTO people ('name') VALUES (?)", (name,))


def remove_name(name: str):
    """
    Remove a name and all their quotes from the bot's database.
    This action is not reversible.

    Args:
        name (str): Name that should be removed from the database if it exists.
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("DELETE FROM quotes WHERE name == (?);", (name,))
        cursor.execute("DELETE FROM people WHERE name == (?);", (name,))


def check_name(name: str):
    """
    Checks if the name exists in the people table.

    Args:
        name (str): Name that should be checked if it exists
    Returns:
        bool: Return whether or not the name exists in the database
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT count(name) FROM people WHERE name=?", (name,))
        if cursor.fetchone()[0] == 1:
            return(True)
        else:
            return(False)


def get_quote(name: str):
    """
    Retrieves a random quote from the database by name in the table quotes.
    If no quotes are are found return a message informing there are no
    quotes under the given name.

    Args:
        name (str): Name used to retrieve a random quote
    Returns:
        str: String containing the random quote or error message
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        try:
            cursor.execute(
                "SELECT quote FROM quotes "
                "WHERE name=? ORDER BY RANDOM() LIMIT 1",
                (name,))
            return(str(cursor.fetchone()[0]))
        except TypeError:
            return(f"{name} does not have any quotes")


def add_quote(name: str, quote: str):
    """
    Add an attributed quote to the database.

    Args:
        name (str): Name used for database entry
        quote (str): Quote used for database entry
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "INSERT INTO quotes ('name', 'quote') VALUES (?, ?)",
            (name, quote,))


def random_name():
    """
    Retrieve a random name from the "people" table

    Returns:
        str: String value containing a name
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names_list = [
            v[0] for v in cursor.fetchall()
        ]
        name = random.choice(names_list)
        return(str(name))


def list_quotes(name: str):
    """
    Unused function to retrieve a list of all the quotes attributed to the
    given name.

    Args:
        name (str): Name used to retrieve all quotes
    Returns:
        list: List of string values
    """
    with OpenDatabase('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT * FROM quotes WHERE name == (?);", (name,))
        items = cursor.fetchall()
        return(items)
