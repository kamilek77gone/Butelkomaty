from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


PAGE_URL = "https://www.marketdino.pl/map/"
TIMEOUT = 60

OUTPUT_FILE = Path("baza_dino_recyklomaty.json")


def create_session() -> requests.Session:
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/json,text/plain,*/*"
            ),
            "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.7",
            "Connection": "keep-alive",
        }
    )

    return session


def find_payload_url(html: str, page_url: str) -> str | None:
    patterns = (
        r'["\']([^"\']*/map/_payload\.json\?[^"\']+)["\']',
        r'["\']([^"\']*/_payload\.json\?[^"\']+)["\']',
        r'([^"\'\s<>]+_payload\.json\?[^"\'\s<>]+)',
    )

    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)

        if not match:
            continue

        path = match.group(1)
        path = path.replace("\\/", "/")
        path = path.replace("\\u0026", "&")

        return urljoin(page_url, path)

    return None


class NuxtPayloadDecoder:
    def __init__(self, table: list[Any]) -> None:
        self.table = table
        self.cache: dict[int, Any] = {}
        self.processing: set[int] = set()

    def decode_reference(self, reference: int) -> Any:
        if reference < 0:
            special_values = {
                -1: None,
                -2: float("nan"),
                -3: float("inf"),
                -4: float("-inf"),
            }

            return special_values.get(reference)

        if reference >= len(self.table):
            raise IndexError(
                f"Indeks {reference} wykracza poza tablicę "
                f"o długości {len(self.table)}."
            )

        if reference in self.cache:
            return self.cache[reference]

        if reference in self.processing:
            return None

        self.processing.add(reference)

        try:
            raw_value = self.table[reference]
            decoded_value = self.decode_raw_value(raw_value)
            self.cache[reference] = decoded_value

            return decoded_value
        finally:
            self.processing.discard(reference)

    def decode_raw_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): self.decode_container_value(child)
                for key, child in value.items()
            }

        if isinstance(value, list):
            return [
                self.decode_container_value(child)
                for child in value
            ]

        return value

    def decode_container_value(self, value: Any) -> Any:
        if isinstance(value, int) and not isinstance(value, bool):
            return self.decode_reference(value)

        if isinstance(value, dict):
            return {
                str(key): self.decode_container_value(child)
                for key, child in value.items()
            }

        if isinstance(value, list):
            return [
                self.decode_container_value(child)
                for child in value
            ]

        return value


def find_feature_collection(value: Any) -> dict[str, Any] | None:
    collections: list[dict[str, Any]] = []

    def walk(child: Any) -> None:
        if isinstance(child, dict):
            if (
                child.get("type") == "FeatureCollection"
                and isinstance(child.get("features"), list)
            ):
                collections.append(child)

            for nested_value in child.values():
                walk(nested_value)

        elif isinstance(child, list):
            for nested_value in child:
                walk(nested_value)

    walk(value)

    if not collections:
        return None

    return max(
        collections,
        key=lambda collection: len(collection.get("features", [])),
    )


def has_recyklomat(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "tak",
            "yes",
        }

    return False


def valid_coordinate(value: Any, minimum: float, maximum: float) -> bool:
    if not isinstance(value, (int, float)):
        return False

    return minimum <= float(value) <= maximum


def split_address(address: str | None) -> dict[str, str]:
    result = {
        "ulica": "",
        "numer": "",
        "kod": "",
        "miasto": "",
    }

    if not address:
        return result

    cleaned = " ".join(address.split()).strip()

    postal_match = re.search(
        r"(\d{2}-\d{3})\s+(.+)$",
        cleaned,
    )

    before_postal = cleaned

    if postal_match:
        result["kod"] = postal_match.group(1)
        result["miasto"] = postal_match.group(2).strip()
        before_postal = cleaned[:postal_match.start()].rstrip(" ,")

    before_postal = re.sub(
        r"^(ul\.|al\.|aleja|plac|pl\.)\s+",
        "",
        before_postal,
        flags=re.IGNORECASE,
    )

    number_match = re.search(
        r"\s+(\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)?)$",
        before_postal,
    )

    if number_match:
        result["numer"] = number_match.group(1)
        result["ulica"] = before_postal[
            :number_match.start()
        ].strip()
    else:
        result["ulica"] = before_postal.strip()

    return result


def normalize_hours(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "poniedzialek": properties.get("mondayHours"),
        "wtorek": properties.get("tuesdayHours"),
        "sroda": properties.get("wednesdayHours"),
        "czwartek": properties.get("thursdayHours"),
        "piatek": properties.get("fridayHours"),
        "sobota": properties.get("saturdayHours"),
        "niedziela": properties.get("sundayHours"),
    }


def create_record(
    feature: dict[str, Any],
) -> dict[str, Any] | None:
    geometry = feature.get("geometry")
    properties = feature.get("properties")

    if not isinstance(geometry, dict):
        return None

    if not isinstance(properties, dict):
        return None

    if not has_recyklomat(properties.get("recyklomat")):
        return None

    coordinates = geometry.get("coordinates")

    if (
        not isinstance(coordinates, list)
        or len(coordinates) < 2
    ):
        return None

    longitude = coordinates[0]
    latitude = coordinates[1]

    if not valid_coordinate(latitude, 49.0, 55.0):
        return None

    if not valid_coordinate(longitude, 14.0, 25.0):
        return None

    name = properties.get("name")
    address = properties.get("address")

    if not isinstance(name, str) or not name.strip():
        return None

    if not isinstance(address, str) or not address.strip():
        return None

    address_parts = split_address(address)

    identifier_source = (
        f"{name.strip()}|"
        f"{float(latitude):.7f}|"
        f"{float(longitude):.7f}"
    )

    identifier = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        identifier_source.lower(),
    ).strip("-")

    return {
        "id": f"dino-{identifier}",
        "siec": "Dino",
        "nazwa": name.strip(),
        "miasto": address_parts["miasto"],
        "ulica": address_parts["ulica"],
        "numer": address_parts["numer"],
        "kod": address_parts["kod"],
        "wojewodztwo": "",
        "latitude": round(float(latitude), 7),
        "longitude": round(float(longitude), 7),
        "status": "aktywny",
        "recyklomat": True,
        "inpost": properties.get("inpost"),
        "godziny": normalize_hours(properties),
        "adres_pelny": address.strip(),
        "zrodlo": PAGE_URL,
        "data_pobrania": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
    }


def create_backup() -> Path | None:
    if not OUTPUT_FILE.exists():
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_file = OUTPUT_FILE.with_name(
        f"{OUTPUT_FILE.stem}_BACKUP_{timestamp}"
        f"{OUTPUT_FILE.suffix}"
    )

    shutil.copy2(OUTPUT_FILE, backup_file)

    return backup_file


def main() -> int:
    print("=" * 72)
    print("DINO — GENERATOR KOŃCOWEJ BAZY RECYKLOMATÓW")
    print("=" * 72)
    print("Chromium: NIE")
    print("Playwright: NIE")
    print()

    session = create_session()

    try:
        page_response = session.get(
            PAGE_URL,
            timeout=TIMEOUT,
        )
        page_response.raise_for_status()
    except requests.RequestException as error:
        print(f"BŁĄD POBIERANIA STRONY: {error}")
        return 1

    print(f"Status strony: {page_response.status_code}")

    payload_url = find_payload_url(
        page_response.text,
        page_response.url,
    )

    if not payload_url:
        print("BŁĄD: Nie znaleziono adresu _payload.json.")
        return 2

    print(f"Payload: {payload_url}")

    try:
        payload_response = session.get(
            payload_url,
            timeout=TIMEOUT,
            headers={
                "Referer": PAGE_URL,
                "Accept": "application/json,text/plain,*/*",
            },
        )
        payload_response.raise_for_status()
    except requests.RequestException as error:
        print(f"BŁĄD POBIERANIA PAYLOADU: {error}")
        return 3

    try:
        payload_table = payload_response.json()
    except json.JSONDecodeError as error:
        print(f"BŁĄD ODCZYTU JSON: {error}")
        return 4

    if not isinstance(payload_table, list):
        print(
            "BŁĄD: Oczekiwano tablicy Nuxt, otrzymano "
            f"{type(payload_table).__name__}."
        )
        return 5

    print(f"Elementy payloadu Nuxt: {len(payload_table)}")

    decoder = NuxtPayloadDecoder(payload_table)

    try:
        decoded_root = decoder.decode_reference(0)
    except Exception as error:
        print(
            "BŁĄD ODKODOWANIA: "
            f"{type(error).__name__}: {error}"
        )
        return 6

    collection = find_feature_collection(decoded_root)

    if collection is None:
        print("BŁĄD: Nie znaleziono FeatureCollection.")
        return 7

    features = collection.get("features", [])

    print(f"Wszystkie markety Dino: {len(features)}")

    records_by_id: dict[str, dict[str, Any]] = {}

    skipped_without_recyklomat = 0
    skipped_invalid = 0

    for feature in features:
        if not isinstance(feature, dict):
            skipped_invalid += 1
            continue

        properties = feature.get("properties")

        if (
            isinstance(properties, dict)
            and not has_recyklomat(
                properties.get("recyklomat")
            )
        ):
            skipped_without_recyklomat += 1
            continue

        record = create_record(feature)

        if record is None:
            skipped_invalid += 1
            continue

        records_by_id[record["id"]] = record

    records = sorted(
        records_by_id.values(),
        key=lambda record: (
            record.get("miasto", "").casefold(),
            record.get("nazwa", "").casefold(),
            record.get("adres_pelny", "").casefold(),
        ),
    )

    if not records:
        print("BŁĄD: Nie utworzono żadnych rekordów.")
        return 8

    backup_file = create_backup()

    OUTPUT_FILE.write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("WYNIK")
    print("=" * 72)
    print(f"Wszystkich marketów: {len(features)}")
    print(
        "Bez recyklomatu: "
        f"{skipped_without_recyklomat}"
    )
    print(f"Odrzucone nieprawidłowe: {skipped_invalid}")
    print(f"Duplikaty usunięte: {len(features) - skipped_without_recyklomat - skipped_invalid - len(records)}")
    print(f"Zapisane recyklomaty Dino: {len(records)}")
    print()

    if backup_file:
        print(f"Backup: {backup_file.resolve()}")
    else:
        print("Backup: brak wcześniejszej bazy")

    print(f"Baza: {OUTPUT_FILE.resolve()}")

    print()
    print("Pierwsze 10 rekordów:")

    for record in records[:10]:
        print(
            f"- {record['nazwa']} | "
            f"{record['adres_pelny']} | "
            f"lat={record['latitude']} | "
            f"lon={record['longitude']}"
        )

    if len(records) != 3165:
        print()
        print(
            "UWAGA: Liczba recyklomatów różni się od "
            "poprzedniego testu 3165."
        )
        print(
            "Może to oznaczać aktualizację danych Dino "
            "albo odrzucenie nieprawidłowego rekordu."
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika.")
        raise SystemExit(130)
    except Exception as error:
        print(
            "\nNIEOCZEKIWANY BŁĄD: "
            f"{type(error).__name__}: {error}"
        )
        raise SystemExit(1)