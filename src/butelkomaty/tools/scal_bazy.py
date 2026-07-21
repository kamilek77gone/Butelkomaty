from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


KATALOG_TOOLS = Path(__file__).resolve().parent
KATALOG_APLIKACJI = KATALOG_TOOLS.parent
KATALOG_DANYCH = KATALOG_APLIKACJI / "data"

PLIKI_ZRODLOWE = {
    "Zabka": KATALOG_DANYCH / "sklepy_mapa.json",
    "Biedronka": KATALOG_DANYCH / "baza_biedronka_recyklomaty.json",
    "Lidl": KATALOG_DANYCH / "baza_lidl_recyklomaty.json",
    "Dino": KATALOG_DANYCH / "baza_dino_recyklomaty.json",
}

PLIK_WYNIKOWY = KATALOG_APLIKACJI / "baza_butelkomaty.json"


def tekst(wartosc: Any) -> str:
    if wartosc is None:
        return ""

    wynik = str(wartosc).strip()
    wynik = re.sub(r"\s+", " ", wynik)

    if wynik.lower() in {"none", "null", "nan"}:
        return ""

    return wynik


def liczba(wartosc: Any) -> float | None:
    if wartosc is None or isinstance(wartosc, bool):
        return None

    if isinstance(wartosc, (int, float)):
        wynik = float(wartosc)
    else:
        wartosc_tekstowa = tekst(wartosc).replace(",", ".")

        if not wartosc_tekstowa:
            return None

        try:
            wynik = float(wartosc_tekstowa)
        except (TypeError, ValueError):
            return None

    if not math.isfinite(wynik):
        return None

    return wynik


def poprawne_gps(
    latitude: float | None,
    longitude: float | None,
) -> bool:
    if latitude is None or longitude is None:
        return False

    return (
        48.5 <= latitude <= 55.5
        and 13.5 <= longitude <= 24.5
    )


def wczytaj_json(sciezka: Path) -> list[dict[str, Any]]:
    if not sciezka.exists():
        raise FileNotFoundError(
            f"Brak pliku źródłowego: {sciezka}"
        )

    try:
        with sciezka.open("r", encoding="utf-8-sig") as plik:
            dane = json.load(plik)
    except json.JSONDecodeError as blad:
        raise ValueError(
            f"Niepoprawny JSON w pliku {sciezka.name}: "
            f"linia {blad.lineno}, kolumna {blad.colno}"
        ) from blad

    if isinstance(dane, dict):
        for klucz in (
            "data",
            "records",
            "results",
            "sklepy",
            "punkty",
        ):
            kandydat = dane.get(klucz)

            if isinstance(kandydat, list):
                dane = kandydat
                break

    if not isinstance(dane, list):
        raise TypeError(
            f"Plik {sciezka.name} nie zawiera listy rekordów."
        )

    wynik: list[dict[str, Any]] = []

    for numer, rekord in enumerate(dane, start=1):
        if not isinstance(rekord, dict):
            print(
                f"OSTRZEŻENIE: {sciezka.name}, rekord {numer} "
                f"nie jest obiektem i został pominięty."
            )
            continue

        wynik.append(rekord)

    return wynik


def rozdziel_adres(adres: str) -> tuple[str, str]:
    adres = tekst(adres)

    if not adres:
        return "", ""

    dopasowanie = re.match(
        r"^(.*?\D)\s+(\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)?)$",
        adres,
    )

    if not dopasowanie:
        return adres, ""

    return (
        tekst(dopasowanie.group(1)),
        tekst(dopasowanie.group(2)),
    )


def pobierz_gps(
    rekord: dict[str, Any],
) -> tuple[float | None, float | None, bool]:
    latitude = liczba(
        rekord.get("latitude", rekord.get("lat"))
    )
    longitude = liczba(
        rekord.get("longitude", rekord.get("lon"))
    )

    gps_ok = poprawne_gps(latitude, longitude)

    if not gps_ok:
        return None, None, False

    return latitude, longitude, True


def przygotuj_status(wartosc: Any) -> Any:
    if wartosc is None:
        return "aktywny"

    if isinstance(wartosc, str):
        return tekst(wartosc) or "aktywny"

    return wartosc


def normalizuj_zabke(
    rekord: dict[str, Any],
    numer: int,
) -> dict[str, Any]:
    adres_pelny = tekst(rekord.get("adres"))
    ulica, numer_budynku = rozdziel_adres(adres_pelny)

    latitude, longitude, gps_ok = pobierz_gps(rekord)

    return {
        "id": f"zabka_{numer:05d}",
        "siec": "Żabka",
        "nazwa": "Żabka",
        "miasto": tekst(rekord.get("miasto")),
        "ulica": ulica,
        "numer": numer_budynku,
        "kod": tekst(rekord.get("kod")),
        "wojewodztwo": tekst(
            rekord.get("wojewodztwo")
        ),
        "latitude": latitude,
        "longitude": longitude,
        "adres_pelny": adres_pelny,
        "typ_zbiorki": "R",
        "typ_zbiorki_opis": "ręczna",
        "status": przygotuj_status(
            rekord.get("status")
        ),
        "godziny": rekord.get("godziny"),
        "zrodlo": "data/sklepy_mapa.json",
        "gps_poprawne": gps_ok,
    }


def normalizuj_biedronke(
    rekord: dict[str, Any],
    numer: int,
) -> dict[str, Any]:
    adres_pelny = tekst(rekord.get("adres"))
    ulica, numer_budynku = rozdziel_adres(adres_pelny)

    latitude, longitude, gps_ok = pobierz_gps(rekord)

    identyfikator = tekst(rekord.get("id"))

    if not identyfikator:
        identyfikator = f"biedronka_{numer:05d}"

    return {
        "id": identyfikator,
        "siec": "Biedronka",
        "nazwa": tekst(rekord.get("nazwa"))
        or "Biedronka",
        "miasto": tekst(rekord.get("miasto")),
        "ulica": ulica,
        "numer": numer_budynku,
        "kod": tekst(rekord.get("kod")),
        "wojewodztwo": tekst(
            rekord.get("wojewodztwo")
        ),
        "latitude": latitude,
        "longitude": longitude,
        "adres_pelny": adres_pelny,
        "typ_zbiorki": "A",
        "typ_zbiorki_opis": "automat",
        "status": przygotuj_status(
            rekord.get("status")
        ),
        "godziny": rekord.get("godziny"),
        "zrodlo": tekst(rekord.get("url"))
        or "data/baza_biedronka_recyklomaty.json",
        "gps_poprawne": gps_ok,
    }


def normalizuj_lidl(
    rekord: dict[str, Any],
    numer: int,
) -> dict[str, Any]:
    latitude, longitude, gps_ok = pobierz_gps(rekord)

    ulica = tekst(rekord.get("ulica"))
    numer_budynku = tekst(rekord.get("numer"))
    adres_pelny = tekst(rekord.get("adres_pelny"))

    if not adres_pelny:
        adres_pelny = " ".join(
            element
            for element in (ulica, numer_budynku)
            if element
        )

    identyfikator = tekst(rekord.get("id"))

    if not identyfikator:
        identyfikator = f"lidl_{numer:05d}"

    return {
        "id": identyfikator,
        "siec": "Lidl",
        "nazwa": tekst(rekord.get("nazwa"))
        or "Lidl",
        "miasto": tekst(rekord.get("miasto")),
        "ulica": ulica,
        "numer": numer_budynku,
        "kod": tekst(rekord.get("kod")),
        "wojewodztwo": tekst(
            rekord.get("wojewodztwo")
        ),
        "latitude": latitude,
        "longitude": longitude,
        "adres_pelny": adres_pelny,
        "typ_zbiorki": "A",
        "typ_zbiorki_opis": "automat",
        "status": przygotuj_status(
            rekord.get("status")
        ),
        "godziny": rekord.get("godziny"),
        "zrodlo": tekst(rekord.get("zrodlo"))
        or "data/baza_lidl_recyklomaty.json",
        "gps_poprawne": gps_ok,
    }


def normalizuj_dino(
    rekord: dict[str, Any],
    numer: int,
) -> dict[str, Any]:
    latitude, longitude, gps_ok = pobierz_gps(rekord)

    ulica = tekst(rekord.get("ulica"))
    numer_budynku = tekst(rekord.get("numer"))
    adres_pelny = tekst(rekord.get("adres_pelny"))

    if not adres_pelny:
        adres_pelny = " ".join(
            element
            for element in (ulica, numer_budynku)
            if element
        )

    identyfikator = tekst(rekord.get("id"))

    if not identyfikator:
        identyfikator = f"dino_{numer:05d}"

    return {
        "id": identyfikator,
        "siec": "Dino",
        "nazwa": tekst(rekord.get("nazwa"))
        or "Dino",
        "miasto": tekst(rekord.get("miasto")),
        "ulica": ulica,
        "numer": numer_budynku,
        "kod": tekst(rekord.get("kod")),
        "wojewodztwo": tekst(
            rekord.get("wojewodztwo")
        ),
        "latitude": latitude,
        "longitude": longitude,
        "adres_pelny": adres_pelny,
        "typ_zbiorki": "A",
        "typ_zbiorki_opis": "automat",
        "status": przygotuj_status(
            rekord.get("status")
        ),
        "godziny": rekord.get("godziny"),
        "zrodlo": tekst(rekord.get("zrodlo"))
        or "data/baza_dino_recyklomaty.json",
        "gps_poprawne": gps_ok,
    }


def klucz_dokladnego_duplikatu(
    rekord: dict[str, Any],
) -> str:
    kopia = dict(rekord)

    if kopia.get("siec") == "Żabka":
        kopia.pop("id", None)

    return json.dumps(
        kopia,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def main() -> int:
    print("=" * 70)
    print("SCALANIE BAZ PROJEKTU BUTELKOMATY")
    print("=" * 70)
    print(f"Katalog danych: {KATALOG_DANYCH}")
    print(f"Plik wynikowy:  {PLIK_WYNIKOWY}")
    print("-" * 70)

    normalizatory = {
        "Zabka": normalizuj_zabke,
        "Biedronka": normalizuj_biedronke,
        "Lidl": normalizuj_lidl,
        "Dino": normalizuj_dino,
    }

    wszystkie: list[dict[str, Any]] = []

    for nazwa, sciezka in PLIKI_ZRODLOWE.items():
        rekordy = wczytaj_json(sciezka)

        print(f"{nazwa:11}: {len(rekordy):6} rekordów")

        normalizator = normalizatory[nazwa]

        for numer, rekord in enumerate(
            rekordy,
            start=1,
        ):
            wszystkie.append(
                normalizator(rekord, numer)
            )

    print("-" * 70)
    print(
        f"Razem przed kontrolą duplikatów: "
        f"{len(wszystkie)}"
    )

    unikalne: list[dict[str, Any]] = []
    widziane: set[str] = set()
    liczba_duplikatow = 0

    for rekord in wszystkie:
        klucz = klucz_dokladnego_duplikatu(rekord)

        if klucz in widziane:
            liczba_duplikatow += 1
            continue

        widziane.add(klucz)
        unikalne.append(rekord)

    unikalne.sort(
        key=lambda rekord: (
            tekst(rekord.get("siec")).casefold(),
            tekst(rekord.get("miasto")).casefold(),
            tekst(
                rekord.get("adres_pelny")
            ).casefold(),
            tekst(rekord.get("id")).casefold(),
        )
    )

    automaty = sum(
        rekord["typ_zbiorki"] == "A"
        for rekord in unikalne
    )
    reczne = sum(
        rekord["typ_zbiorki"] == "R"
        for rekord in unikalne
    )
    z_gps = sum(
        bool(rekord["gps_poprawne"])
        for rekord in unikalne
    )
    bez_gps = len(unikalne) - z_gps

    statystyki_sieci: dict[
        str,
        dict[str, int],
    ] = {}

    for rekord in unikalne:
        siec = rekord["siec"]

        if siec not in statystyki_sieci:
            statystyki_sieci[siec] = {
                "razem": 0,
                "z_gps": 0,
                "bez_gps": 0,
            }

        statystyki_sieci[siec]["razem"] += 1

        if rekord["gps_poprawne"]:
            statystyki_sieci[siec]["z_gps"] += 1
        else:
            statystyki_sieci[siec]["bez_gps"] += 1

    dokument_wynikowy = {
        "projekt": "Butelkomaty",
        "wersja_formatu": 1,
        "data_scalenia_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "liczba_rekordow": len(unikalne),
        "statystyki": {
            "automaty": automaty,
            "reczna_zbiorka": reczne,
            "z_poprawnym_gps": z_gps,
            "bez_poprawnego_gps": bez_gps,
            "usuniete_dokladne_duplikaty":
                liczba_duplikatow,
            "sieci": statystyki_sieci,
        },
        "punkty": unikalne,
    }

    plik_tymczasowy = (
        PLIK_WYNIKOWY.with_suffix(".json.tmp")
    )

    with plik_tymczasowy.open(
        "w",
        encoding="utf-8",
    ) as plik:
        json.dump(
            dokument_wynikowy,
            plik,
            ensure_ascii=False,
            indent=2,
        )

    plik_tymczasowy.replace(PLIK_WYNIKOWY)

    print(
        f"Usunięte wyłącznie dokładne duplikaty: "
        f"{liczba_duplikatow}"
    )
    print(
        f"Razem po kontroli:                  "
        f"{len(unikalne)}"
    )
    print(
        f"Automaty:                           "
        f"{automaty}"
    )
    print(
        f"Zbiórka ręczna:                     "
        f"{reczne}"
    )
    print(
        f"Z poprawnym GPS:                    "
        f"{z_gps}"
    )
    print(
        f"Bez poprawnego GPS:                 "
        f"{bez_gps}"
    )
    print("-" * 70)

    for siec in sorted(statystyki_sieci):
        dane = statystyki_sieci[siec]

        print(
            f"{siec:11}: "
            f"razem={dane['razem']}, "
            f"GPS={dane['z_gps']}, "
            f"bez GPS={dane['bez_gps']}"
        )

    print("-" * 70)
    print(f"Zapisano: {PLIK_WYNIKOWY}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as blad:
        print()
        print("=" * 70)
        print("BŁĄD SCALANIA")
        print("=" * 70)
        print(f"{type(blad).__name__}: {blad}")
        raise SystemExit(1)