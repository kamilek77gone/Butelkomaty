# Butelkomaty

Aplikacja mobilna na Androida mapująca automaty do recyklingu (butelkomaty) w Polsce.
Zbudowana z użyciem [BeeWare](https://beeware.org/) / [Briefcase](https://briefcase.beeware.org/) i [Toga](https://toga.beeware.org/).

## Funkcje

- Wyświetlanie punktów zbiórki butelek i puszek na mapie (OpenStreetMap / Leaflet)
- Filtrowanie punktów po sieciach handlowych (Żabka, Biedronka, Lidl, Dino, Netto)
- Bottom sheet z detalami punktu: adres, typ zbiórki, godziny otwarcia, status
- Nawigacja do wybranego punktu (aplikacja map)
- Tygodniowy ranking użytkowników — kto zwrócił najwięcej butelek w danym tygodniu
- Zniżki dla najlepszych w rankingu (1. miejsce: 10%, 2.: 7%, 3.: 5%)

## Wymagania

- Python 3.11+
- [Briefcase](https://briefcase.beeware.org/) (`pip install briefcase`)
- Do budowania Androida: JDK 17 oraz Android SDK (pobierane automatycznie przez Briefcase)

## Uruchomienie lokalne (Windows)

```bash
# Sklonuj repozytorium
git clone https://github.com/kamilek77gone/Butelkomaty.git
cd Butelkomaty

# Zainstaluj zależności
pip install briefcase

# Uruchom aplikację w trybie deweloperskim
briefcase dev
```

## Budowanie Androida (GitHub Actions)

Budowanie APK odbywa się zdalnie przez GitHub Actions — nie wymaga lokalnej instalacji Android Studio ani Gradle.

### Ręczne uruchomienie budowania

1. Wejdź w zakładkę **Actions** w repozytorium na GitHubie
2. Wybierz workflow **"Build Android APK"**
3. Kliknij **Run workflow**
4. Po zakończeniu pobierz artefakt `butelkomaty-android-apk` z podsumowania uruchomienia

Workflow uruchamia się również automatycznie przy każdym `push` na gałąź `main` lub `master`.

### Lokalne budowanie Androida (opcjonalnie)

```bash
briefcase build -a android
briefcase package -a android
```

Gotowy APK znajdzie się w folderze `build/butelkomaty/android/`.

## Struktura projektu

```
Butelkomaty/
├── pyproject.toml              # Konfiguracja projektu (Briefcase)
├── .github/workflows/android.yml  # CI: budowanie APK na GitHub Actions
├── README.md                   # Ten plik
├── LICENSE                     # Licencja MIT
├── CHANGELOG                   # Historia wersji
├── PROJEKT.md                  # Dziennik projektu (po polsku)
├── src/butelkomaty/
│   ├── __init__.py
│   ├── __main__.py             # Punkt wejścia
│   ├── app.py                  # Główna klasa aplikacji Toga
│   ├── baza_butelkomaty.json   # Baza punktów zbiórki (używana przez Mapę)
│   ├── data/sklepy_mapa.json   # Baza sklepów (alternatywne źródło)
│   ├── resources/map.html      # Mapa (Leaflet, OpenStreetMap)
│   ├── services/
│   │   ├── baza.py             # Obsługa bazy danych punktów
│   │   ├── mapa.py             # Serwis mapy i GeoJSON
│   │   └── ranking.py          # Serwis rankingu i zniżek
│   ├── views/
│   │   ├── main_view.py        # Główna widok (mapa + filtry + ranking)
│   │   └── ranking_view.py     # Widok tygodniowego rankingu
│   ├── models/__init__.py
│   └── utils/__init__.py
└── tests/                      # Testy aplikacji
```

## Uwagi dotyczące mapy

Mapa ładuje biblioteki Leaflet i kafelki OpenStreetMap z zewnętrznych serwerów (CDN). Na Androidzie wymagane jest uprawnienie `INTERNET` w `AndroidManifest.xml` oraz dostęp do sieci.

## Brak kluczy API

Projekt nie zawiera żadnych kluczy API, haseł ani tokenów. Wszystkie dane pochodzą z publicznych źródeł (OpenStreetMap, bazy sklepów).

## Licencja

MIT — patrz plik `LICENSE`.
