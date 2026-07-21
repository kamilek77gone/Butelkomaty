import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.biedronka.pl"

CITY = "walbrzych"

URL = f"{BASE}/pl/sklepy/lista,city,{CITY},special,7"


def pobierz_strone(url):
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=20
    )

    print(f"Pobrano: {url}")
    print("Status:", r.status_code)

    return r.text


def znajdz_sklepy(html):
    soup = BeautifulSoup(html, "html.parser")

    wyniki = []

    sklepy = soup.select("li.shopListElement")

    for sklep in sklepy:

        tekst = sklep.get_text(" ", strip=True).lower()

        if "recyklomat" not in tekst:
            continue

        link = sklep.find("a", href=True)

        miasto = ""
        adres = ""
        kod = ""

        h4 = sklep.select_one(".header h4")
        if h4:
            miasto = h4.get_text(strip=True)

        a = sklep.select_one(".shopAddress")
        if a:
            adres = a.get_text(strip=True)

        k = sklep.select_one(".zipCode")
        if k:
            kod = k.get_text(strip=True)

        if link:
            ident = link["href"]
        else:
            ident = "brak"

        wyniki.append(
            (
                ident,
                miasto,
                adres,
                kod
            )
        )

    return wyniki


def main():

    print("START - WAŁBRZYCH")

    wszystkie = {}

    page = 1

    while True:

        if page == 1:
            url = URL
        else:
            url = f"{URL},page,{page}"

        html = pobierz_strone(url)

        sklepy = znajdz_sklepy(html)

        print(
            f"Strona: {page} wyniki: {len(sklepy)}"
        )

        nowe = 0

        for s in sklepy:
            ident = s[0]

            if ident not in wszystkie:
                wszystkie[ident] = s
                nowe += 1

        print("Nowe:", nowe)

        if nowe == 0:
            print("Koniec paginacji.")
            break

        page += 1

        if page > 50:
            break


    print()
    print("==============================")
    print("PODSUMOWANIE WAŁBRZYCH")
    print("==============================")
    print("Łącznie recyklomatów:", len(wszystkie))
    print("==============================")


    for sklep in wszystkie.values():
        print(
            sklep[0],
            "|",
            sklep[2],
            "|",
            sklep[3]
        )


    print()
    print("KONIEC")


if __name__ == "__main__":
    main()