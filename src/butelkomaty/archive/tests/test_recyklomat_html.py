import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.biedronka.pl/pl/sklepy/lista,city,krakow,special,7"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.biedronka.pl/pl/sklepy"
}


def pobierz(url):
    r = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print(
        "Pobrano:",
        url,
        "Status:",
        r.status_code
    )

    return r.text


def znajdz_recyklomaty(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    wynik = {}

    sklepy = soup.find_all(
        "li",
        class_="shopListElement"
    )

    for sklep in sklepy:

        if not sklep.find(
            "li",
            class_="icon_8"
        ):
            continue

        link = sklep.find(
            "a",
            href=True
        )

        if not link:
            continue

        znalezione = re.search(
            r"id,(\d+)",
            link["href"]
        )

        if not znalezione:
            continue

        id_sklepu = znalezione.group(1)

        adres = sklep.find(
            "p",
            class_="shopAddress"
        )

        kod = sklep.find(
            "p",
            class_="zipCode"
        )

        wynik[id_sklepu] = {
            "adres": adres.get_text(strip=True) if adres else "",
            "kod": kod.get_text(strip=True) if kod else ""
        }

    return wynik


print("START - KRAKÓW")

wszystkie = {}

strona = 1

while True:

    if strona == 1:
        url = BASE_URL
    else:
        url = BASE_URL + f",page,{strona}"

    html = pobierz(url)

    sklepy = znajdz_recyklomaty(html)

    nowe = 0

    for id_sklepu, dane in sklepy.items():

        if id_sklepu not in wszystkie:
            wszystkie[id_sklepu] = dane
            nowe += 1


    print(
        "Strona:",
        strona,
        "wyniki:",
        len(sklepy),
        "nowe:",
        nowe
    )


    if nowe == 0:
        print("Koniec paginacji.")
        break


    strona += 1


print("\n==============================")
print("PODSUMOWANIE KRAKÓW")
print("==============================")

print(
    "Łącznie recyklomatów:",
    len(wszystkie)
)

print("==============================")

for id_sklepu, dane in wszystkie.items():

    print(
        id_sklepu,
        "|",
        dane["adres"],
        "|",
        dane["kod"]
    )

print("\nKONIEC")