from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


KATALOG_GLOWNY = Path(__file__).resolve().parent

KATALOG_ARCHIWUM = KATALOG_GLOWNY / "archive"
KATALOG_DANYCH = KATALOG_GLOWNY / "data"
KATALOG_SCRAPEROW = KATALOG_GLOWNY / "scrapers"
KATALOG_NARZEDZI = KATALOG_GLOWNY / "tools"

ZNACZNIK_CZASU = datetime.now().strftime("%Y%m%d_%H%M%S")

KATALOG_TESTOW = KATALOG_ARCHIWUM / "tests"
KATALOG_ANALIZ = KATALOG_ARCHIWUM / "analizy"
KATALOG_DINO = KATALOG_ARCHIWUM / "dino"
KATALOG_POZOSTALE = KATALOG_ARCHIWUM / "pozostale"

PLIK_RAPORTU = (
    KATALOG_ARCHIWUM
    / f"raport_porządkowania_{ZNACZNIK_CZASU}.json"
)


def bezpieczna_nazwa_docelowa(
    katalog_docelowy: Path,
    nazwa: str,
) -> Path:
    """
    Zwraca wolną ścieżkę docelową.

    Jeżeli plik o tej samej nazwie już istnieje,
    dodaje numer zamiast go nadpisywać.
    """
    cel = katalog_docelowy / nazwa

    if not cel.exists():
        return cel

    sciezka = Path(nazwa)
    podstawa = sciezka.stem
    rozszerzenie = sciezka.suffix

    numer = 1

    while True:
        cel = katalog_docelowy / (
            f"{podstawa}_kopia_{numer}{rozszerzenie}"
        )

        if not cel.exists():
            return cel

        numer += 1


def przenies(
    zrodlo: Path,
    katalog_docelowy: Path,
    raport: list[dict[str, str]],
) -> None:
    """
    Przenosi plik lub katalog bez usuwania jego zawartości
    i bez nadpisywania istniejących danych.
    """
    if not zrodlo.exists():
        raport.append(
            {
                "status": "pominięto",
                "źródło": str(zrodlo),
                "cel": "",
                "powód": "plik lub katalog nie istnieje",
            }
        )
        return

    katalog_docelowy.mkdir(
        parents=True,
        exist_ok=True,
    )

    cel = bezpieczna_nazwa_docelowa(
        katalog_docelowy,
        zrodlo.name,
    )

    shutil.move(str(zrodlo), str(cel))

    raport.append(
        {
            "status": "przeniesiono",
            "źródło": str(zrodlo),
            "cel": str(cel),
            "powód": "",
        }
    )

    print(f"PRZENIESIONO: {zrodlo.name}")
    print(f"          DO: {cel.relative_to(KATALOG_GLOWNY)}")


def czy_test(nazwa: str) -> bool:
    nazwa_mala = nazwa.casefold()

    return (
        nazwa_mala.startswith("test_")
        and nazwa_mala.endswith(".py")
    )


def czy_analizator(nazwa: str) -> bool:
    nazwa_mala = nazwa.casefold()

    prefiksy = (
        "sprawdz_",
        "szukaj_",
        "audyt_",
        "analizuj_",
        "analiza_",
    )

    return (
        nazwa_mala.endswith(".py")
        and nazwa_mala.startswith(prefiksy)
    )


def czy_scraper(nazwa: str) -> bool:
    nazwa_mala = nazwa.casefold()

    aktywne_nazwy = {
        "dino_playwright.py",
        "pobierz_dane.py",
        "scraper_biedronka.py",
        "scraper_lidl.py",
        "scraper_dino.py",
    }

    return (
        nazwa_mala in aktywne_nazwy
        or (
            nazwa_mala.startswith("scraper_")
            and nazwa_mala.endswith(".py")
        )
    )


def czy_narzedzie(nazwa: str) -> bool:
    nazwa_mala = nazwa.casefold()

    aktywne_narzedzia = {
        "scal_bazy.py",
        "audyt_json.py",
        "walidator.py",
        "waliduj_baze.py",
        "sprawdz_baze.py",
    }

    return nazwa_mala in aktywne_narzedzia


def czy_baza_zrodlowa(nazwa: str) -> bool:
    """
    Przenosi źródłowe JSON-y do data.

    Główna baza aplikacji baza_butelkomaty.json
    pozostaje na razie w katalogu aplikacji.
    """
    nazwa_mala = nazwa.casefold()

    if not nazwa_mala.endswith(".json"):
        return False

    pliki_pozostajace = {
        "baza_butelkomaty.json",
    }

    return nazwa_mala not in pliki_pozostajace


def utworz_katalogi() -> None:
    katalogi = (
        KATALOG_ARCHIWUM,
        KATALOG_DANYCH,
        KATALOG_SCRAPEROW,
        KATALOG_NARZEDZI,
        KATALOG_TESTOW,
        KATALOG_ANALIZ,
        KATALOG_DINO,
        KATALOG_POZOSTALE,
    )

    for katalog in katalogi:
        katalog.mkdir(
            parents=True,
            exist_ok=True,
        )


def zapisz_raport(
    raport: list[dict[str, str]],
) -> None:
    dokument = {
        "data": datetime.now().isoformat(),
        "katalog_projektu": str(KATALOG_GLOWNY),
        "zasada": (
            "Żaden plik nie został skasowany. "
            "Elementy zostały wyłącznie przeniesione."
        ),
        "liczba_operacji": len(raport),
        "operacje": raport,
    }

    with PLIK_RAPORTU.open(
        "w",
        encoding="utf-8",
    ) as plik:
        json.dump(
            dokument,
            plik,
            ensure_ascii=False,
            indent=2,
        )


def main() -> int:
    print("=" * 70)
    print("PORZĄDKOWANIE PROJEKTU BUTELKOMATY")
    print("=" * 70)
    print("Nic nie zostanie skasowane ani nadpisane.")
    print()

    utworz_katalogi()

    raport: list[dict[str, str]] = []

    # Katalogi robocze zakończonego etapu Dino.
    for nazwa_katalogu in (
        "dino_js",
        "dino_payload",
    ):
        przenies(
            KATALOG_GLOWNY / nazwa_katalogu,
            KATALOG_DINO,
            raport,
        )

    # Pobieramy listę przed przenoszeniem, aby zmiany
    # nie zakłóciły dalszego przechodzenia po katalogu.
    elementy = list(KATALOG_GLOWNY.iterdir())

    katalogi_systemowe = {
        "archive",
        "data",
        "docs",
        "resources",
        "scrapers",
        "tools",
        "tests",
        "butelkomaty.dist-info",
        "__pycache__",
    }

    pliki_aplikacji = {
        "__init__.py",
        "__main__.py",
        "app.py",
        "baza_butelkomaty.json",
        "porzadkuj_projekt.py",
    }

    for element in elementy:
        nazwa = element.name
        nazwa_mala = nazwa.casefold()

        if nazwa_mala in katalogi_systemowe:
            continue

        if nazwa_mala in pliki_aplikacji:
            continue

        if not element.is_file():
            continue

        if czy_test(nazwa):
            przenies(
                element,
                KATALOG_TESTOW,
                raport,
            )
            continue

        if czy_scraper(nazwa):
            przenies(
                element,
                KATALOG_SCRAPEROW,
                raport,
            )
            continue

        if czy_narzedzie(nazwa):
            przenies(
                element,
                KATALOG_NARZEDZI,
                raport,
            )
            continue

        if czy_analizator(nazwa):
            przenies(
                element,
                KATALOG_ANALIZ,
                raport,
            )
            continue

        if czy_baza_zrodlowa(nazwa):
            przenies(
                element,
                KATALOG_DANYCH,
                raport,
            )
            continue

    zapisz_raport(raport)

    przeniesione = sum(
        operacja["status"] == "przeniesiono"
        for operacja in raport
    )

    pominiete = sum(
        operacja["status"] == "pominięto"
        for operacja in raport
    )

    print()
    print("=" * 70)
    print("PODSUMOWANIE")
    print("=" * 70)
    print(f"Przeniesiono elementów: {przeniesione}")
    print(f"Pominięto elementów:    {pominiete}")
    print()
    print("Nie usunięto żadnego pliku.")
    print("Nie nadpisano żadnego istniejącego pliku.")
    print(f"Raport: {PLIK_RAPORTU}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as blad:
        print()
        print("=" * 70)
        print("BŁĄD PORZĄDKOWANIA")
        print("=" * 70)
        print(f"{type(blad).__name__}: {blad}")
        print()
        print(
            "Pliki przeniesione przed wystąpieniem błędu "
            "nie zostały skasowane."
        )
        raise SystemExit(1)