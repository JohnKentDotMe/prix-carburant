import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "prices.db"

_CREATE_STATION = """
CREATE TABLE IF NOT EXISTS station (
    station_id TEXT PRIMARY KEY,
    address    TEXT,
    city       TEXT,
    postcode   TEXT,
    latitude   REAL,
    longitude  REAL
)
"""

_CREATE_PRICE = """
CREATE TABLE IF NOT EXISTS price (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id  TEXT NOT NULL REFERENCES station(station_id),
    fuel_type   TEXT NOT NULL,
    price       REAL NOT NULL,
    updated_at  TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    UNIQUE(station_id, fuel_type, updated_at)
)
"""


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init():
    with _conn() as conn:
        conn.execute(_CREATE_STATION)
        conn.execute(_CREATE_PRICE)


def upsert_stations(stations) -> None:
    with _conn() as conn:
        conn.executemany(
            """INSERT INTO station(station_id, address, city, postcode, latitude, longitude)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(station_id) DO UPDATE SET
                 address=excluded.address, city=excluded.city,
                 postcode=excluded.postcode, latitude=excluded.latitude,
                 longitude=excluded.longitude""",
            [(s.station_id, s.address, s.city, s.postcode, s.latitude, s.longitude)
             for s in stations],
        )


def insert_prices(prices) -> int:
    recorded_at = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        cur = conn.executemany(
            """INSERT OR IGNORE INTO price(station_id, fuel_type, price, updated_at, recorded_at)
               VALUES(?,?,?,?,?)""",
            [(p.station_id, p.fuel_type, p.price, p.updated_at, recorded_at)
             for p in prices],
        )
        return cur.rowcount


def latest_prices(station_id: str) -> list:
    with _conn() as conn:
        return conn.execute(
            """SELECT fuel_type, price, updated_at
               FROM price
               WHERE station_id = ?
               GROUP BY fuel_type
               HAVING updated_at = MAX(updated_at)
               ORDER BY fuel_type""",
            (station_id,),
        ).fetchall()
