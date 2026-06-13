"""
db.py — PawPost database bootstrap

Every time the app starts, this module rebuilds pawpost.db from the CSV
files in /data. This keeps the CSVs as the "source of truth" for now
(useful for a demo / early-stage build). When PawPost is ready for a
more permanent setup, swap SQLite for Postgres here without changing
the rest of the app — just point SQLALCHEMY_DATABASE_URI elsewhere and
remove the CSV-rebuild step (or make it a one-off migration instead).
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "pawpost.db")

SCHEMA = """
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS sitters;

CREATE TABLE sitters (
    sitter_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    rating      REAL,
    joined_date TEXT,
    services    TEXT
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    pet_name    TEXT,
    pet_type    TEXT,
    signup_date TEXT
);

CREATE TABLE bookings (
    booking_id    INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL,
    sitter_id     INTEGER NOT NULL,
    service_type  TEXT,
    booking_date  TEXT,
    duration_days INTEGER,
    price         REAL,
    status        TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    FOREIGN KEY (sitter_id) REFERENCES sitters (sitter_id)
);
"""


def _load_csv(conn, table, filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        rows = [tuple(row[c] for c in cols) for row in reader]
        conn.executemany(sql, rows)


def init_db(force=True):
    """Rebuild the SQLite database from the CSV files in /data.

    force=True (default) always rebuilds on boot, which is what we want
    while data is still coming from CSV exports. Set force=False to skip
    rebuilding if the DB file already exists (handy for local testing).
    """
    if not force and os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        _load_csv(conn, "sitters", "sitters.csv")
        _load_csv(conn, "customers", "customers.csv")
        _load_csv(conn, "bookings", "bookings.csv")
        conn.commit()
    finally:
        conn.close()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    init_db()
    print(f"Database rebuilt at {DB_PATH}")
