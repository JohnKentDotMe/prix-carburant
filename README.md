# prix-carburant

A lightweight CLI tool that tracks fuel prices at French gas stations using the official government open data feed.

## What it does

On each run it:

1. Downloads the nationwide fuel price feed from `donnees.roulez-eco.fr` (official government source, updated throughout the day)
2. Filters to the stations you configured
3. Stores new price records in a local SQLite database (`prices.db`)
4. Prints a live price summary in the terminal

The feed is cached once per day — repeated runs on the same day reuse the local file.

## Requirements

- Python 3.8+
- `requests` and `lxml` libraries

## Installation

```bash
git clone https://github.com/JohnKentDotMe/prix-carburant.git
cd prix-carburant
pip install requests lxml
```

## Configuration

Open `config.ini` and set the IDs of the stations you want to track:

```ini
[prix-carburant]
station_ids = 78170002, 78170003
```

Station IDs come from the official site [prix-carburants.gouv.fr](https://www.prix-carburants.gouv.fr). They appear in the URL when you view a station's page.

## Usage

```bash
python main.py
```

Example output:

```
[i] Watching 1 station(s): 78170002
[i] Downloading open data... OK
[i] Extracting... OK
[i] 1 station(s) updated, 6 new price record(s) stored

  [78170002] LA CELLE-SAINT-CLOUD — 5 Av. du Général Leclerc
    Diesel       1.749 €/L   (updated 2024-03-15T08:00:00)
    E85          0.899 €/L   (updated 2024-03-15T08:00:00)
    GPLc         0.899 €/L   (updated 2024-03-15T08:00:00)
    SP95         1.849 €/L   (updated 2024-03-15T08:00:00)
    SP95-E10     1.819 €/L   (updated 2024-03-15T08:00:00)
    SP98         1.929 €/L   (updated 2024-03-15T08:00:00)
```

## Automating with cron

To run every morning at 8:00:

```
0 8 * * * cd /path/to/prix-carburant && python main.py
```

## Data storage

Prices are stored in `prices.db` (SQLite). You can query it directly:

```bash
# All recorded prices for a station
sqlite3 prices.db "SELECT fuel_type, price, updated_at FROM price WHERE station_id='78170002' ORDER BY updated_at DESC LIMIT 20;"
```

## Project structure

```
prix-carburant/
├── main.py          # Entry point
├── fetcher.py       # Downloads and caches the open data ZIP
├── fuel_parser.py   # Parses the XML feed into dataclasses
├── db.py            # SQLite schema and queries
├── config.ini       # Your station IDs
└── data/            # Cached daily downloads (git-ignored)
```
