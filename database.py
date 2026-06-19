# SPDX-FileCopyrightText: 2026 Kevin Patino
# SPDX-License-Identifier: MIT

import logging
import random
import sqlite3
from datetime import datetime, timezone

module_logger = logging.getLogger(f"__main__.{__name__}")


class OpenDatabase(object):
    """SQLite3 context manager for automatically opening and closing connections.

    Args:
        path (str): SQLite database filepath.
    """

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


def _resolve_guild(cursor, guild_id: int) -> int:
    """Return the integer primary key for a guild, creating it if needed.

    Args:
        cursor: Active database cursor.
        guild_id (int): Discord server ID.

    Returns:
        int: Primary key of the guild row.
    """
    cursor.execute("INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("SELECT id FROM guilds WHERE guild_id = ?", (guild_id,))
    return cursor.fetchone()[0]


def create_db(db_name: str) -> None:
    """Create the database tables if they do not already exist.

    Args:
        db_name (str): Name of the database file to create.
    """
    with OpenDatabase(db_name) as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='guilds'"
        )
        if cursor.fetchone() is not None:
            return

        cursor.execute("""CREATE TABLE IF NOT EXISTS guilds(
            'id' INTEGER NOT NULL UNIQUE,
            'guild_id' INTEGER NOT NULL UNIQUE,
            PRIMARY KEY('id')
        );""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS people(
            'id' INTEGER NOT NULL UNIQUE,
            'guild_id' INTEGER NOT NULL,
            'name' TEXT NOT NULL,
            'created_at' TEXT NOT NULL,
            'added_by' INTEGER NOT NULL,
            UNIQUE('guild_id', 'name'),
            FOREIGN KEY('guild_id') REFERENCES 'guilds'('id'),
            PRIMARY KEY('id' AUTOINCREMENT)
        );""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS quotes(
            'id' INTEGER NOT NULL UNIQUE,
            'person_id' INTEGER NOT NULL,
            'quote' TEXT NOT NULL,
            'created_at' TEXT NOT NULL,
            'added_by' INTEGER NOT NULL,
            FOREIGN KEY('person_id') REFERENCES 'people'('id'),
            PRIMARY KEY('id' AUTOINCREMENT)
        );""")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quotes_person_id ON quotes(person_id)"
        )


def get_names(guild_id: int) -> str:
    """Return a comma-separated string of all names for a guild.

    Args:
        guild_id (int): Discord server ID to scope the query to.

    Returns:
        str: Names separated by commas.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        cursor.execute("SELECT name FROM people WHERE guild_id = ?", (guild_int,))
        names = [v[0] for v in cursor.fetchall()]
        names.sort()
        names = ", ".join(map(str, names))
        return names


def get_names_list(guild_id: int) -> list:
    """Return the first 20 names for a guild in alphabetical order.

    Args:
        guild_id (int): Discord server ID to scope the query to.

    Returns:
        list: Sorted list of up to 20 names.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        cursor.execute("SELECT name FROM people WHERE guild_id = ?", (guild_int,))
        names_list = [v[0] for v in cursor.fetchall()]
        names_list.sort()
        return names_list[:20]


def add_name(guild_id: int, name: str, added_by: int) -> None:
    """Add a name to the people table for a guild.

    Args:
        guild_id (int): Discord server ID to scope the entry to.
        name (str): Name to add.
        added_by (int): Discord user ID who added the name.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO people ('guild_id', 'name', 'created_at', 'added_by')"
            " VALUES (?, ?, ?, ?)",
            (guild_int, name, now, added_by),
        )


def remove_name(guild_id: int, name: str) -> None:
    """Remove a name and all its quotes from a guild. Not reversible.

    Args:
        guild_id (int): Discord server ID to scope the query to.
        name (str): Name to remove.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        cursor.execute(
            "DELETE FROM quotes WHERE person_id IN ("
            "SELECT id FROM people WHERE guild_id = ? AND name = ?"
            ")",
            (guild_int, name),
        )
        cursor.execute(
            "DELETE FROM people WHERE guild_id = ? AND name = ?",
            (guild_int, name),
        )


def verify_name(guild_id: int, name: str) -> bool:
    """Check whether a name exists in the people table for a guild.

    Args:
        guild_id (int): Discord server ID to scope the query to.
        name (str): Name to check.

    Returns:
        bool: True if the name exists, False otherwise.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        cursor.execute(
            "SELECT count(name) FROM people WHERE guild_id = ? AND name = ?",
            (guild_int, name),
        )
        if cursor.fetchone()[0] == 1:
            return True
        else:
            return False


def get_random_quote(guild_id: int, name: str) -> str:
    """Return a random quote for a name in a guild.

    Args:
        guild_id (int): Discord server ID to scope the query to.
        name (str): Name to look up.

    Returns:
        str: A random quote, or a message if none exist.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        try:
            cursor.execute(
                "SELECT q.quote FROM quotes q"
                " JOIN people p ON p.id = q.person_id"
                " WHERE p.guild_id = ? AND p.name = ?"
                " ORDER BY RANDOM() LIMIT 1",
                (guild_int, name),
            )
            result = cursor.fetchone()
            return str(result[0])
        except TypeError:
            return f"{name} does not have any quotes"


def add_quote(guild_id: int, name: str, quote: str, added_by: int) -> None:
    """Add a quote attributed to a name for a guild.

    Args:
        guild_id (int): Discord server ID to scope the entry to.
        name (str): Name to attribute the quote to.
        quote (str): Quote text.
        added_by (int): Discord user ID who added the quote.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO quotes ('person_id', 'quote', 'created_at', 'added_by')"
            " SELECT id, ?, ?, ? FROM people"
            " WHERE guild_id = ? AND name = ?",
            (quote, now, added_by, guild_int, name),
        )


def get_random_name(guild_id: int) -> str:
    """Return a random name from a guild.

    Args:
        guild_id (int): Discord server ID to scope the query to.

    Returns:
        str: A randomly chosen name.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        cursor.execute("SELECT name FROM people WHERE guild_id = ?", (guild_int,))
        names_list = [v[0] for v in cursor.fetchall()]
        return str(random.choice(names_list))


def list_quotes(guild_id: int, name: str) -> list:
    """Return all quotes attributed to a name within a guild. (Unused)

    Args:
        guild_id (int): Discord server ID to scope the query to.
        name (str): Name to look up.

    Returns:
        list: Rows from the quotes table.
    """
    with OpenDatabase("./quotes.db") as cursor:
        guild_int = _resolve_guild(cursor, guild_id)
        cursor.execute(
            "SELECT q.* FROM quotes q"
            " JOIN people p ON p.id = q.person_id"
            " WHERE p.guild_id = ? AND p.name = ?",
            (guild_int, name),
        )
        return cursor.fetchall()
