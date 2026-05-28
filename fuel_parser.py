import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Station:
    station_id: str
    address: str
    city: str
    postcode: str
    latitude: float
    longitude: float


@dataclass
class Price:
    station_id: str
    fuel_type: str
    price: float
    updated_at: str


def parse(xml_path: Path, station_ids: set) -> tuple:
    tree = ET.parse(xml_path)
    stations, prices = [], []

    for pdv in tree.getroot().findall("pdv"):
        sid = pdv.get("id", "")
        if station_ids and sid not in station_ids:
            continue

        stations.append(Station(
            station_id=sid,
            address=(pdv.findtext("adresse") or "").strip(),
            city=(pdv.findtext("ville") or "").strip(),
            postcode=pdv.get("cp", ""),
            latitude=float(pdv.get("latitude", 0)) / 100000,
            longitude=float(pdv.get("longitude", 0)) / 100000,
        ))

        for prix in pdv.findall("prix"):
            val = prix.get("valeur")
            nom = prix.get("nom")
            maj = prix.get("maj")
            if val and nom and maj:
                prices.append(Price(
                    station_id=sid,
                    fuel_type=nom,
                    price=float(val),
                    updated_at=maj,
                ))

    return stations, prices
