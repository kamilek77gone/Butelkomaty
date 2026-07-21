import requests


URL = "https://www.biedronka.pl/pl/sklepy/lista"

headers = {
    "User-Agent": "Mozilla/5.0"
}


print("Pobieram stronę...")

html = requests.get(
    URL,
    headers=headers,
    timeout=30
).text


szukane = [
    "google",
    "map",
    "marker",
    "shopMap",
    "shopList",
    "find",
    "location"
]


for slowo in szukane:

    print("\n====================")
    print("SZUKAM:", slowo)
    print("====================")

    pozycja = html.lower().find(slowo.lower())

    if pozycja != -1:
        print("Znaleziono:", pozycja)
        print(html[pozycja-150:pozycja+300])
    else:
        print("brak")