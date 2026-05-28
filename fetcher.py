import requests
from datetime import date
from pathlib import Path
from zipfile import ZipFile

DATA_DIR = Path(__file__).parent / "data"
OPEN_DATA_URL = "https://donnees.roulez-eco.fr/opendata/instantane"
XML_NAME = "PrixCarburants_instantane.xml"


def fetch_xml() -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    zip_path = DATA_DIR / f"{date.today()}.zip"
    xml_path = DATA_DIR / XML_NAME

    if zip_path.exists():
        print(f"[i] Using cached data from {date.today()}")
        return xml_path

    print("[i] Downloading open data...", end=" ", flush=True)
    r = requests.get(OPEN_DATA_URL, stream=True, timeout=60)
    r.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("OK")

    print("[i] Extracting...", end=" ", flush=True)
    with ZipFile(zip_path) as z:
        z.extractall(DATA_DIR)
    print("OK")

    return xml_path
