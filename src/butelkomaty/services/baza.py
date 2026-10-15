"""Obsługa lokalnej bazy punktów aplikacji Butelkomaty.

Moduł korzysta wyłącznie ze standardowej biblioteki Pythona, dzięki czemu
jest bezpieczny dla BeeWare, Briefcase, Androida i GitHub Actions.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


APP_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = APP_DIR / "data" / "sklepy_mapa.json"

FALLBACK_DATABASE_PATHS = (
    APP_DIR / "sklepy_mapa.json",
    APP_DIR / "baza_butelkomaty.json",
)

POLAND_LATITUDE_RANGE = (48.5, 55.5)
POLAND_LONGITUDE_RANGE = (13.5, 24.5)


class BladBazy(RuntimeError):
    """Podstawowy błąd modułu bazy."""


class BrakPlikuBazy(BladBazy):
    """Plik bazy nie został znaleziony."""


class NiepoprawnyFormatBazy(BladBazy):
    """Plik istnieje, ale nie zawiera poprawnej bazy JSON."""


def znajdz_plik_bazy(sciezka: str | Path | None = None) -> Path:
    """Zwraca istniejącą ścieżkę do produkcyjnej bazy danych."""
    if sciezka is not None:
        wybrana = Path(sciezka).expanduser().resolve()
        if not wybrana.is_file():
            raise BrakPlikuBazy(f"Nie znaleziono pliku bazy: {wybrana}")
        return wybrana

    kandydaci = (DEFAULT_DATABASE_PATH, *FALLBACK_DATABASE_PATHS)
    for kandydat in kandydaci:
        if kandydat.is_file():
            return kandydat

    lista = "\n".join(f"- {element}" for element in kandydaci)
    raise BrakPlikuBazy(
        "Nie znaleziono bazy Butelkomatów. Sprawdzono:\n" + lista
    )


def _lista_rekordow(dane: Any) -> list[dict[str, Any]]:
    """Obsługuje bazę będącą listą albo słownikiem z listą rekordów."""
    if isinstance(dane, list):
        return [rekord for rekord in dane if isinstance(rekord, dict)]

    if isinstance(dane, dict):
        for klucz in ("sklepy", "punkty", "data", "records", "results"):
            rekordy = dane.get(klucz)
            if isinstance(rekordy, list):
                return [
                    rekord for rekord in rekordy if isinstance(rekord, dict)
                ]

    raise NiepoprawnyFormatBazy(
        "Główny element JSON musi być listą punktów albo słownikiem "
        "z listą pod kluczem: sklepy, punkty, data, records lub results."
    )


def _liczba(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        liczba = float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None

    return liczba if math.isfinite(liczba) else None


def _poprawne_gps(latitude: float | None, longitude: float | None) -> bool:
    return (
        latitude is not None
        and longitude is not None
        and POLAND_LATITUDE_RANGE[0] <= latitude <= POLAND_LATITUDE_RANGE[1]
        and POLAND_LONGITUDE_RANGE[0] <= longitude <= POLAND_LONGITUDE_RANGE[1]
    )


def wczytaj_punkty(
    sciezka: str | Path | None = None,
    *,
    wymagaj_poprawnego_gps: bool = True,
) -> list[dict[str, Any]]:
    """Wczytuje bazę i zwraca punkty gotowe do użycia przez aplikację.

    Funkcja nie zmienia pliku źródłowego. Każdy zwrócony rekord jest kopią
    słownika z bazy.
    """
    plik = znajdz_plik_bazy(sciezka)

    try:
        with plik.open("r", encoding="utf-8-sig") as uchwyt:
            dane = json.load(uchwyt)
    except json.JSONDecodeError as exc:
        raise NiepoprawnyFormatBazy(
            f"Niepoprawny JSON w pliku {plik.name}: "
            f"linia {exc.lineno}, kolumna {exc.colno}."
        ) from exc
    except OSError as exc:
        raise BladBazy(f"Nie można odczytać pliku {plik}: {exc}") from exc

    wynik: list[dict[str, Any]] = []

    for rekord in _lista_rekordow(dane):
        punkt = dict(rekord)
        latitude = _liczba(punkt.get("latitude", punkt.get("lat")))
        longitude = _liczba(punkt.get("longitude", punkt.get("lon")))

        punkt["latitude"] = latitude
        punkt["longitude"] = longitude
        punkt["gps_poprawne"] = _poprawne_gps(latitude, longitude)

        if wymagaj_poprawnego_gps and not punkt["gps_poprawne"]:
            continue

        wynik.append(punkt)

    return wynik


def filtruj_punkty(
    punkty: Iterable[dict[str, Any]],
    *,
    sieci: Iterable[str] | None = None,
    typy_zbiorki: Iterable[str] | None = None,
    statusy: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Filtruje punkty bez modyfikowania listy źródłowej."""
    dozwolone_sieci = (
        {str(value).strip().casefold() for value in sieci}
        if sieci is not None
        else None
    )
    dozwolone_typy = (
        {str(value).strip().casefold() for value in typy_zbiorki}
        if typy_zbiorki is not None
        else None
    )
    dozwolone_statusy = (
        {str(value).strip().casefold() for value in statusy}
        if statusy is not None
        else None
    )

    wynik = []

    for punkt in punkty:
        siec = str(punkt.get("siec", "")).strip().casefold()
        typ = str(punkt.get("typ_zbiorki", "")).strip().casefold()
        status = str(punkt.get("status", "")).strip().casefold()

        if dozwolone_sieci is not None and siec not in dozwolone_sieci:
            continue
        if dozwolone_typy is not None and typ not in dozwolone_typy:
            continue
        if dozwolone_statusy is not None and status not in dozwolone_statusy:
            continue

        wynik.append(punkt)

    return wynik


def podsumowanie_bazy(
    punkty: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Tworzy lekkie podsumowanie przydatne w testach i diagnostyce."""
    lista = list(punkty)

    return {
        "liczba_punktow": len(lista),
        "sieci": dict(
            sorted(
                Counter(
                    str(punkt.get("siec") or "Nieznana").strip()
                    for punkt in lista
                ).items()
            )
        ),
        "typy_zbiorki": dict(
            sorted(
                Counter(
                    str(punkt.get("typ_zbiorki") or "Nieznany").strip()
                    for punkt in lista
                ).items()
            )
        ),
        "statusy": dict(
            sorted(
                Counter(
                    str(punkt.get("status") or "Nieznany").strip()
                    for punkt in lista
                ).items()
            )
        ),
    }


def _test_modulu() -> int:
    print("=" * 72)
    print("TEST MODUŁU BAZY — BUTELKOMATY")
    print("=" * 72)

    try:
        plik = znajdz_plik_bazy()
        punkty = wczytaj_punkty(plik)
        raport = podsumowanie_bazy(punkty)
    except BladBazy as exc:
        print(f"BŁĄD: {exc}")
        return 1

    print(f"Plik: {plik}")
    print(f"Poprawne punkty GPS: {raport['liczba_punktow']}")
    print()
    print("Sieci:")
    for siec, liczba in raport["sieci"].items():
        print(f"- {siec}: {liczba}")

    print()
    print("Typy zbiórki:")
    for typ, liczba in raport["typy_zbiorki"].items():
        print(f"- {typ}: {liczba}")

    print()
    print("Statusy:")
    for status, liczba in raport["statusy"].items():
        print(f"- {status}: {liczba}")

    print()
    print("TEST ZAKOŃCZONY POMYŚLNIE")
    print("Plik bazy nie został zmieniony.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_test_modulu())