import requests
import re

URL = "https://static.biedronka.pl/js/shop.js?v=1106119"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.biedronka.pl/"
}

print("Pobieram shop.js...\n")

tekst = requests.get(
    URL,
    headers=headers,
    timeout=30
).text

print("Status: OK")
print("Długość pliku:", len(tekst))

print("\n========================================")
print("SZUKAM WSZYSTKICH ENDPOINTÓW API")
print("========================================\n")

wzorce = [
    r'["\'](/api/[^"\']+)["\']',
    r'["\'](api/[^"\']+)["\']',
    r'https://[^"\']+/api/[^"\']+'
]

znalezione = set()

for wzorzec in wzorce:
    for wynik in re.findall(wzorzec, tekst, re.IGNORECASE):
        znalezione.add(wynik)

if not znalezione:
    print("Nie znaleziono żadnych endpointów.")
else:
    print("Znalezione endpointy:\n")
    for adres in sorted(znalezione):
        print(adres)

print("\n========================================")
print("KONIEC TESTU")
print("========================================")