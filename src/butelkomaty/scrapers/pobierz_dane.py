import json
import time
import requests


URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    "User-Agent": "Butelkomaty/1.0"
}

SIEC = "Biedronka"


def pobierz_biedronki():

    print("=" * 50)
    print("Generator Bazy Butelkomatów v1.1")
    print(f"Szukam: {SIEC}")
    print("=" * 50)

    query = f"""
[out:json][timeout:60];

area["ISO3166-1"="PL"][admin_level=2]->.polska;

(
  node["name"~"{SIEC}",i](area.polska);
  way["name"~"{SIEC}",i](area.polska);

  node["brand"~"{SIEC}",i](area.polska);
  way["brand"~"{SIEC}",i](area.polska);

  node["operator"~"{SIEC}",i](area.polska);
  way["operator"~"{SIEC}",i](area.polska);
);

out center;
"""

    try:

        print("Wysyłam zapytanie do Overpass...")

        response = requests.post(
            URL,
            data={"data": query},
            headers=HEADERS,
            timeout=120
        )

        response.raise_for_status()

        dane = response.json()

        sklepy = dane.get("elements", [])

        print(f"Znaleziono: {len(sklepy)}")

        with open(
            "biedronka.json",
            "w",
            encoding="utf-8"
        ) as plik:

            json.dump(
                sklepy,
                plik,
                ensure_ascii=False,
                indent=4
            )

        print("Zapisano biedronka.json")

    except Exception as e:

        print("BŁĄD:")
        print(e)


if __name__ == "__main__":
    pobierz_biedronki()