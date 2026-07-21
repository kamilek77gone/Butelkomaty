import requests
import json
import os
from datetime import datetime

"""
SCRAPER LIDL v1.0
Cel: pobranie WSZYSTKICH sklepow Lidl w Polsce
Kazdy sklep Lidl w Polsce ma butelkomat - nie trzeba filtrowac
"""

URL = "https://live.api.schwarz/odj/stores-api/v2/myapi/stores-frontend/stores"
FILE_BAZA = "baza_lidl_recyklomaty.json"

# Przyblizona Polska - geo_box
GEO_BOX_PL = "49.0,14.0:55.0,25.0"

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36",
    "x-apikey": "16QaHsGX3Uc3JLhNlS2ZG1CmosbzVPs2",
    "Referer": "https://www.lidl.pl/",
    "Accept": "application/json"
}


def pobierz_strone(offset):
    """Pobiera strone sklepow z API Lidla."""
    params = {
        "limit": 100,
        "offset": offset,
        "country_code": "PL",
        "geo_box": GEO_BOX_PL
    }
    
    r = requests.get(URL, headers=headers, params=params, timeout=30)
    print(f"  Offset: {offset} | Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        return data.get("items", [])
    return []


print("=" * 60)
print("SCRAPER LIDL v1.0 - CALA POLSKA")
print("=" * 60)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Backup jesli istnieje
if os.path.exists(FILE_BAZA):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(FILE_BAZA, "r", encoding="utf-8") as f_src:
        with open(f"baza_lidl_BACKUP_{timestamp}.json", "w", encoding="utf-8") as f_dst:
            f_dst.write(f_src.read())
    print(f"\n[BACKUP] Stworzono kopie")

# Pobieranie wszystkich sklepow
wszystkie_sklepy = []
offset = 0

while True:
    print(f"\n--- Pobieram offset: {offset} ---")
    sklepy = pobierz_strone(offset)
    
    if not sklepy:
        print("Brak wynikow - koniec.")
        break
    
    nowe = 0
    for sklep in sklepy:
        # Normalizujemy format
        adres = sklep.get("address", {})
        
        rekord = {
            "id": sklep.get("objectNumber"),
            "siec": "lidl",
            "nazwa": sklep.get("storeName", ""),
            "miasto": adres.get("city", ""),
            "ulica": adres.get("streetName", ""),
            "numer": adres.get("streetNumber", ""),
            "kod": adres.get("zip", ""),
            "wojewodztwo": adres.get("state", ""),
            "latitude": adres.get("latitude"),
            "longitude": adres.get("longitude"),
            "status": sklep.get("status", ""),
            "godziny": sklep.get("openingHours", {})
        }
        
        # Sprawdzamy czy nie ma duplikatu
        if not any(s.get("id") == rekord["id"] for s in wszystkie_sklepy):
            wszystkie_sklepy.append(rekord)
            nowe += 1
    
    print(f"  Pobrano: {len(sklepy)} | Nowe: {nowe} | Lacznie: {len(wszystkie_sklepy)}")
    
    if len(sklepy) < 100:
        print("Mniej niz 100 - to ostatnia strona.")
        break
    
    offset += 100


# Zapis
with open(FILE_BAZA, "w", encoding="utf-8") as f:
    json.dump(wszystkie_sklepy, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("BAZA ZAPISANA")
print("=" * 60)
print(f"Liczba sklepow Lidl: {len(wszystkie_sklepy)}")
print(f"Plik: {FILE_BAZA}")
print("=" * 60)
print("\nKazdy sklep Lidl w Polsce ma butelkomat.")
print("Baza gotowa do polaczenia z innymi sieciami.")
print("=" * 60)