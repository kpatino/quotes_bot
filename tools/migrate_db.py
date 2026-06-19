#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Kevin Patino
# SPDX-License-Identifier: MIT

"""Migrate a pre-guild_id quotes database to the current per-guild schema.

Usage:
    python migrate_db.py [--db quotes.db]
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone


def migrate(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='guilds'"
    )
    if cursor.fetchone() is not None:
        cursor.execute("PRAGMA table_info(people)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'created_at' in columns:
            print("Database already has the current schema. Nothing to do.")
            conn.close()
            return

    print("Detected old schema. Starting migration...")
    print()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='people'"
    )
    if cursor.fetchone() is None:
        print("No people table found. Nothing to migrate.")
        conn.close()
        return

    cursor.execute("SELECT count(*) FROM people")
    people_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM quotes")
    quotes_count = cursor.fetchone()[0]
    print(f"Found {people_count} people and {quotes_count} quotes to migrate.")

    guild_id_input = input(
        "Enter the Discord guild (server) ID to assign all existing data to: "
    ).strip()
    if not guild_id_input:
        print("Guild ID cannot be empty. Aborting.")
        sys.exit(1)
    try:
        guild_id = int(guild_id_input)
    except ValueError:
        print("Guild ID must be a numeric value. Aborting.")
        sys.exit(1)

    cursor.execute("ALTER TABLE people RENAME TO people_old")
    cursor.execute("ALTER TABLE quotes RENAME TO quotes_old")
    cursor.execute("DROP TABLE IF EXISTS guilds")

    cursor.execute("""CREATE TABLE guilds(
        'id' INTEGER NOT NULL UNIQUE,
        'guild_id' INTEGER NOT NULL UNIQUE,
        PRIMARY KEY('id')
    );""")

    cursor.execute("""CREATE TABLE people(
        'id' INTEGER NOT NULL UNIQUE,
        'guild_id' INTEGER NOT NULL,
        'name' TEXT NOT NULL,
        'created_at' TEXT NOT NULL,
        'added_by' INTEGER NOT NULL,
        UNIQUE('guild_id', 'name'),
        FOREIGN KEY('guild_id') REFERENCES 'guilds'('id'),
        PRIMARY KEY('id' AUTOINCREMENT)
    );""")

    cursor.execute("""CREATE TABLE quotes(
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

    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("INSERT INTO guilds (guild_id) VALUES (?)", (guild_id,))
    cursor.execute(
        "INSERT INTO people (guild_id, name, created_at, added_by)"
        " SELECT 1, name, ?, 0 FROM people_old",
        (now,),
    )
    cursor.execute(
        "INSERT INTO quotes (person_id, quote, created_at, added_by)"
        " SELECT p.id, q.quote, ?, 0 FROM quotes_old q"
        " JOIN people p ON p.name = q.name",
        (now,),
    )

    cursor.execute("DROP TABLE people_old")
    cursor.execute("DROP TABLE quotes_old")

    conn.commit()
    conn.close()

    print(f"Migration complete. All existing data assigned to guild {guild_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate quotes database to current per-guild schema"
    )
    parser.add_argument(
        "--db",
        default="quotes.db",
        help="Path to the SQLite database file (default: quotes.db)",
    )
    args = parser.parse_args()

    try:
        migrate(args.db)
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Database file not found: {args.db}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
