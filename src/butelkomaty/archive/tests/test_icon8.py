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

print("\nSzukam icon_8...\n")

wyniki = re.findall(
    r".{0,500}icon_8.{0,500}",
    tekst,
    re.IGNORECASE
)

print("Liczba fragmentów:", len(wyniki))

for i, fragment in enumerate(wyniki[:5], 1):
    print("\n================")
    print("FRAGMENT", i)
    print("================")
    print(fragment)

print("\nKONIEC TESTU")