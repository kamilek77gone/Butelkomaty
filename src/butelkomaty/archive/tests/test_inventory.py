from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent

FILES = [
    "baza_biedronka_recyklomaty.json",
    "baza_dino_recyklomaty.json",
    "baza_lidl_recyklomaty.json",
    "sklepy_mapa.json",
    "biedronka.json",
]


def describe_value(value: Any) -> str:
    if value is None:
        return "null"

    if isinstance(value, bool):
        return f"bool: {value}"

    if isinstance(value, int):
        return f"int: {value}"

    if isinstance(value, float):
        return f"float: {value}"

    if isinstance(value, str):
        text = value.replace("\n", " ")

        if len(text) > 120:
            text = text[:117] + "..."

        return f"str: {text!r}"

    if isinstance(value, list):
        return f"list({len(value)})"

    if isinstance(value, dict):
        return f"dict({len(value)})"

    return f"{type(value).__name__}: {value!r}"


def find_records(data: Any) -> tuple[str, list[Any]]:
    if isinstance(data, list):
        return "$", data

    if isinstance(data, dict):
        candidate_keys = (
            "sklepy",
            "stores",
            "markets",
            "recyklomaty",
            "punkty",
            "locations",
            "data",
            "features",
        )

        for key in candidate_keys:
            value = data.get(key)

            if isinstance(value, list):
                return f"$.{key}", value

        list_candidates = [
            (key, value)
            for key, value in data.items()
            if isinstance(value, list)
        ]

        if list_candidates:
            key, value = max(
                list_candidates,
                key=lambda item: len(item[1]),
            )

            return f"$.{key}", value

    return "$", []


def analyze_file(path: Path) -> None:
    print()
    print("=" * 78)
    print(path.name)
    print("=" * 78)

    if not path.exists():
        print("STATUS: BRAK PLIKU")
        return

    print(f"Rozmiar: {path.stat().st_size} B")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"STATUS: BŁĘDNY JSON")
        print(f"Błąd: {error}")
        return

    print(f"Typ główny: {type(data).__name__}")

    if isinstance(data, dict):
        print(f"Klucze główne: {list(data.keys())[:50]}")

    records_path, records = find_records(data)

    print(f"Ścieżka rekordów: {records_path}")
    print(f"Liczba rekordów: {len(records)}")

    if not records:
        print("Brak rekordów do analizy.")
        return

    type_counter = Counter(
        type(record).__name__
        for record in records
    )

    print(f"Typy rekordów: {dict(type_counter)}")

    dict_records = [
        record
        for record in records
        if isinstance(record, dict)
    ]

    if not dict_records:
        print("Brak rekordów typu dict.")
        print("Pierwszy rekord:")
        print(describe_value(records[0]))
        return

    key_counter: Counter[str] = Counter()

    for record in dict_records:
        key_counter.update(str(key) for key in record.keys())

    print()
    print("Klucze rekordów i liczba wystąpień:")

    for key, count in key_counter.most_common():
        print(f"  {count:6}  {key}")

    print()
    print("Pierwszy rekord:")

    first_record = dict_records[0]

    for key, value in first_record.items():
        print(f"  {key}: {describe_value(value)}")

    print()
    print("Pierwsze 3 skrócone rekordy:")

    for index, record in enumerate(dict_records[:3], start=1):
        print(f"  REKORD {index}")

        for key in (
            "id",
            "siec",
            "sieć",
            "nazwa",
            "name",
            "adres",
            "adres_pelny",
            "address",
            "miasto",
            "city",
            "latitude",
            "longitude",
            "lat",
            "lon",
            "lng",
            "recyklomat",
            "butelkomat",
            "status",
        ):
            if key in record:
                print(
                    f"    {key}: "
                    f"{describe_value(record.get(key))}"
                )


def main() -> int:
    print("=" * 78)
    print("AUDYT FORMATÓW BAZ — BUTELKOMATY")
    print("=" * 78)

    for filename in FILES:
        analyze_file(ROOT / filename)

    print()
    print("=" * 78)
    print("KONIEC AUDYTU")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())