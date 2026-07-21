import requests

s = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.biedronka.pl/pl/sklepy/",
    "X-Requested-With": "XMLHttpRequest"
}

url = "https://www.biedronka.pl/api/shop/serachbyname"

params = {
    "name": "a",
    "special": ""
}

print("Pobieram...")

r = s.get(
    url,
    params=params,
    headers=headers
)

print("Status:", r.status_code)

data = r.json()

print("Liczba sklepów:", len(data["items"]))

print("Pierwsze 3:")
for sklep in data["items"][:3]:
    print(
        sklep["name"],
        "|",
        sklep["city"],
        "|",
        sklep["latitude"],
        sklep["longitude"]
    )