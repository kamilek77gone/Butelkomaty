import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime


# ============================================================
# KONFIGURACJA
# ============================================================

BASE_URL = "https://www.biedronka.pl/pl/sklepy/lista,city,{city},special,7"
API_MIASTA = "https://www.biedronka.pl/api/shop/cities"
FILE_MIASTA = "miasta_biedronka.json"
FILE_BAZA = "baza_biedronka_recyklomaty.json"


# ============================================================
# FUNKCJE POMOCNICZE
# ============================================================

def wydobadz_id_z_url(url):
    """Z URL '/pl/sklepy/shop,id,37' wydobywa 37."""
    if not url:
        return None
    try:
        czesci = url.split(",")
        for i, czesc in enumerate(czesci):
            if czesc == "id" and i + 1 < len(czesci):
                return int(czesci[i + 1])
    except (ValueError, IndexError):
        pass
    return None


def wydobadz_id_z_rekordu(rekord):
    """Uniwersalne wyciaganie ID z dowolnego formatu rekordu."""
    if not isinstance(rekord, dict):
        return None

    if "id" in rekord:
        try:
            return int(rekord["id"])
        except (ValueError, TypeError):
            pass

    if "url" in rekord:
        return wydobadz_id_z_url(rekord["url"])

    return None


def wydobadz_adres_i_kod(tekst):
    """Z tekstu wydobywa adres i kod pocztowy."""
    if not tekst:
        return "", ""

    linie = [l.strip() for l in tekst.split("\n") if l.strip()]
    if not linie:
        return tekst, ""

    kod = ""
    adres = ""

    for linia in linie[1:]:
        if "-" in linia and len(linia) <= 6 and linia[0:2].isdigit():
            kod = linia
        elif not adres:
            adres = linia
        else:
            adres += " " + linia

    if not kod:
        match = re.search(r'\d{2}-\d{3}', tekst)
        if match:
            kod = match.group()

    if not adres and len(linie) > 1:
        adres = " ".join(linie[1:])

    return adres, kod


def pobierz_miasta_z_api():
    """Pobiera unikalne miasta z API Biedronki - metoda z test_puste_api.py"""
    print("=" * 60)
    print("POBIERANIE LISTY MIAST Z API BIEDRONKI")
    print("=" * 60)

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.biedronka.pl/pl/sklepy"
    }

    print("Krok 1: Otwieram strone glowna...")
    r1 = session.get(
        "https://www.biedronka.pl/pl/sklepy",
        headers=headers
    )
    print(f"  Status strony glownej: {r1.status_code}")

    print("Krok 2: Pobieram API miast...")
    r2 = session.get(
        API_MIASTA,
        headers=headers
    )
    print(f"  Status API: {r2.status_code}")

    if r2.status_code != 200:
        print(f"  BLAD: API zwrocilo status {r2.status_code}")
        return []

    try:
        data = r2.json()
    except json.JSONDecodeError as e:
        print(f"  BLAD: Nie mozna sparsowac JSON: {e}")
        return []

    sklepy = data.get("items", [])

    if not sklepy:
        print("  BLAD: Brak pola 'items' w odpowiedzi")
        print(f"  Klucze odpowiedzi: {list(data.keys())}")
        return []

    miasta = set()
    for sklep in sklepy:
        miasto = sklep.get("city", "").strip().lower()
        miasto = miasto.replace(" ", "_")
        if miasto:
            miasta.add(miasto)

    miasta = sorted(list(miasta))

    print(f"\nZnaleziono {len(miasta)} unikalnych miast")

    with open(FILE_MIASTA, "w", encoding="utf-8") as f:
        json.dump(miasta, f, ensure_ascii=False, indent=2)

    print(f"Zapisano do: {FILE_MIASTA}")
    print(f"Pierwsze 10: {miasta[:10]}")
    print(f"Ostatnie 10: {miasta[-10:]}")

    return miasta


def wczytaj_miasta():
    """Wczytuje liste miast z pliku lub pobiera z API."""
    if os.path.exists(FILE_MIASTA):
        print(f"\n[Wczytano miasta z: {FILE_MIASTA}]")
        with open(FILE_MIASTA, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return pobierz_miasta_z_api()


def pobierz_strone(url):
    """Pobiera strone z Biedronki."""
    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        timeout=20
    )
    print(f"  Pobrano: {url}")
    print(f"  Status: {r.status_code}")
    return r.text


def znajdz_sklepy(html, miasto):
    """Znajduje sklepy z recyklomatem w HTML."""
    soup = BeautifulSoup(html, "html.parser")
    wynik = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/pl/sklepy/shop,id," in href:
            parent = a.find_parent()
            if parent:
                tekst = parent.get_text(" ", strip=True)
            else:
                tekst = a.get_text(" ", strip=True)

            tekst = " ".join(tekst.split())
            sklep_id = wydobadz_id_z_url(href)

            if sklep_id is not None:
                adres, kod = wydobadz_adres_i_kod(tekst)
                wynik.append({
                    "id": sklep_id,
                    "siec": "biedronka",
                    "miasto": miasto,
                    "adres": adres,
                    "kod": kod,
                    "url": href
                })

    return wynik


def pobierz_miasto(miasto, istniejace_id):
    """Pobiera wszystkie strony paginacji dla miasta."""
    print("\n" + "=" * 50)
    print(f"START - {miasto.upper()}")
    print("=" * 50)

    nowe_sklepy = []
    page = 1

    while True:
        if page == 1:
            url = BASE_URL.format(city=miasto)
        else:
            url = BASE_URL.format(city=miasto) + f",page,{page}"

        try:
            html = pobierz_strone(url)
        except requests.RequestException as e:
            print(f"  BLAD pobierania: {e}")
            break

        sklepy = znajdz_sklepy(html, miasto)

        if not sklepy:
            print("  Brak wynikow - koniec paginacji.")
            break

        nowe_na_stronie = 0
        for sklep in sklepy:
            if sklep["id"] not in istniejace_id:
                nowe_sklepy.append(sklep)
                istniejace_id.add(sklep["id"])
                nowe_na_stronie += 1

        print(f"  Strona: {page} | wyniki: {len(sklepy)} | nowe: {nowe_na_stronie}")

        if nowe_na_stronie == 0:
            print("  Koniec paginacji (brak nowych sklepow).")
            break

        page += 1
        time.sleep(0.5)

    return nowe_sklepy


# ============================================================
# GLOWNY PROGRAM
# ============================================================

print("=" * 60)
print("GENERATOR BAZY RECYKLOMATOW BIEDRONKA v3.2")
print("CALA POLSKA - JEDEN PLIK")
print("=" * 60)
print(f"Czas startu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)


# --- KROK 1: MIASTA ---
cities = wczytaj_miasta()
print(f"\nLiczba miast do przetworzenia: {len(cities)}")


# --- BACKUP BAZY ---
if os.path.exists(FILE_BAZA):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"baza_biedronka_recyklomaty_BACKUP_{timestamp}.json"
    with open(FILE_BAZA, "r", encoding="utf-8") as f_src:
        with open(backup_name, "w", encoding="utf-8") as f_dst:
            f_dst.write(f_src.read())
    print(f"\n[BACKUP] Stworzono kopie: {backup_name}")
else:
    print("\n[BACKUP] Brak istniejacej bazy.")


# --- WCZYTANIE I CZYSZCZENIE BAZY ---
if os.path.exists(FILE_BAZA):
    with open(FILE_BAZA, "r", encoding="utf-8") as f:
        try:
            baza = json.load(f)
            if not isinstance(baza, list):
                print("[OSTRZEZENIE] Baza nie jest lista - startujemy od pustej.")
                baza = []
        except json.JSONDecodeError:
            print("[BLAD] Baza uszkodzona - startujemy od pustej.")
            baza = []
else:
    baza = []

print(f"\n[BAZA STARTOWA] {len(baza)} rekordow (przed czyszczeniem)")


# --- DEDUP I NORMALIZACJA ---
czysta_baza = []
istniejace_id = set()
usunieto = 0

for rekord in baza:
    sklep_id = wydobadz_id_z_rekordu(rekord)

    if sklep_id is None:
        usunieto += 1
        continue

    if sklep_id in istniejace_id:
        usunieto += 1
        continue

    if isinstance(rekord, dict):
        if "siec" in rekord and "adres" in rekord:
            czysta_baza.append(rekord)
        else:
            _, kod = wydobadz_adres_i_kod(rekord.get("tekst", ""))
            czysta_baza.append({
                "id": sklep_id,
                "siec": "biedronka",
                "miasto": rekord.get("miasto", ""),
                "adres": rekord.get("tekst", ""),
                "kod": kod,
                "url": rekord.get("url", f"/pl/sklepy/shop,id,{sklep_id}")
            })

        istniejace_id.add(sklep_id)

baza = czysta_baza

print(f"[CZYSZCZENIE] Usunieto duplikatow/brakow: {usunieto}")
print(f"[BAZA PO CZYSZCZENIU] {len(baza)} unikalnych rekordow")
print(f"[DEDUP] Unikalnych ID: {len(istniejace_id)}")


# --- POBIERANIE NOWYCH ---
wszystkie_nowe = []
miasta_z_wynikami = 0
miasta_bez_wynikow = 0

for i, city in enumerate(cities):
    nowe = pobierz_miasto(city, istniejace_id)
    wszystkie_nowe.extend(nowe)

    if nowe:
        miasta_z_wynikami += 1
    else:
        miasta_bez_wynikow += 1

    if (i + 1) % 10 == 0:
        print(f"\n  === POSTEP: {i+1}/{len(cities)} miast | {len(wszystkie_nowe)} nowych ===")

print(f"\nMiast z recyklomatami: {miasta_z_wynikami}")
print(f"Miast bez recyklomatow: {miasta_bez_wynikow}")


# --- DODANIE DO BAZY ---
baza.extend(wszystkie_nowe)


# --- ZAPIS ---
with open(FILE_BAZA, "w", encoding="utf-8") as f:
    json.dump(baza, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("BAZA ZAPISANA")
print("=" * 60)
print(f"Rekordow po czyszczeniu: {len(baza) - len(wszystkie_nowe)}")
print(f"Nowych dodanych: {len(wszystkie_nowe)}")
print(f"Rekordow lacznie: {len(baza)}")
print(f"Plik: {FILE_BAZA}")
print("=" * 60)
print(f"\nZEBRANO: {len(baza)} unikalnych recyklomatow Biedronki")
print("=" * 60)