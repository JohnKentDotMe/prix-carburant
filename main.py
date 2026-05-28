from configparser import ConfigParser
from pathlib import Path

import db
import fetcher
from fuel_parser import parse

CONFIG_PATH = Path(__file__).parent / "config.ini"


def load_station_ids() -> set:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    raw = cfg.get("prix-carburant", "station_ids", fallback="")
    ids = {sid.strip() for sid in raw.split(",") if sid.strip()}
    if not ids:
        raise ValueError("No station_ids configured in config.ini")
    return ids


def main():
    station_ids = load_station_ids()
    print(f"[i] Watching {len(station_ids)} station(s): {', '.join(sorted(station_ids))}")

    db.init()

    xml_path = fetcher.fetch_xml()
    stations, prices = parse(xml_path, station_ids)

    if not stations:
        print("[!] No matching stations found — check your station_ids in config.ini")
        return

    db.upsert_stations(stations)
    new_prices = db.insert_prices(prices)
    print(f"[i] {len(stations)} station(s) updated, {new_prices} new price record(s) stored")

    for station in stations:
        rows = db.latest_prices(station.station_id)
        print(f"\n  [{station.station_id}] {station.city} — {station.address}")
        if rows:
            for fuel_type, price, updated_at in rows:
                print(f"    {fuel_type:<12} {price:.3f} €/L   (updated {updated_at})")
        else:
            print("    No price data available")


if __name__ == "__main__":
    main()
