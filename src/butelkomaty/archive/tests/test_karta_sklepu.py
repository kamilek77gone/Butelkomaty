import requests
import re

URL = "https://www.biedronka.pl/pl/sklepy/lista,city,warszawa,special,7"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.biedronka.pl/pl/sklepy"
}

print("Pobieram stronę...")

r = requests.get(
    URL,
    headers=headers,
    timeout=30
)

print("Status:", r.status_code)

tekst = r.text

print("\nSzukam bloków z recyklomatem...\n")

# pokaż większy fragment HTML wokół icon_8
pozycje = [m.start() for m in re.finditer("icon_8", tekst)]

print("Znalezionych pozycji:", len(pozycje))

for nr, pos in enumerate(pozycje[:3], 1):
    print("\n====================")
    print("BLOK", nr)
    print("====================")

    start = max(0, pos - 1500)
    koniec = pos + 500

    print(tekst[start:koniec])

print("\nKONIEC TESTU")