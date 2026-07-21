import requests

BASE = "https://www.biedronka.pl"

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.biedronka.pl/pl/sklepy"
}

print("Pobieram dane...")

session.get(
    BASE + "/pl/sklepy",
    headers=headers
)

r = session.get(
    BASE + "/api/shop/cities",
    headers=headers
)

print("Status:", r.status_code)

data = r.json()

print("Liczba elementów:", len(data.get("items", [])))

print("\nPierwsze 5:")

for sklep in data.get("items", [])[:5]:
    print(
        sklep.get("name"),
        "|",
        sklep.get("city"),
        "|",
        sklep.get("latitude"),
        sklep.get("longitude")
    )