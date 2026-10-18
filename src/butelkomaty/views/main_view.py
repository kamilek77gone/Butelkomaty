import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from butelkomaty.services.baza import BazaDanych
from butelkomaty.services.mapa import MapaService
from butelkomaty.services.ranking import RankingService


class MainView:
    def __init__(self, main_app):
        self.main_app = main_app
        
        # Inicjalizacja serwisów biznesowych aplikacji
        self.baza_service = BazaDanych()
        self.mapa_service = MapaService()
        self.ranking_service = RankingService()
        
        # Budowa pełnego interfejsu
        self.container = self.build()

    def build(self):
        # Główny kontener aplikacji
        main_box = toga.Box(
            style=Pack(
                direction=COLUMN,
                padding=15,
                alignment="center"
            )
        )

        # Nagłówek aplikacji
        title_label = toga.Label(
            "Butelkomaty - Mapa, Baza i Ranking",
            style=Pack(
                padding_bottom=15,
                font_size=18,
                font_weight="bold"
            )
        )
        main_box.add(title_label)

        # Wczytanie danych z bazy / serwisów
        dane_bazy = self.baza_service.wczytaj_dane()
        sklepy = self.mapa_service.pobierz_sklepy() if hasattr(self.mapa_service, "pobierz_sklepy") else []
        
        liczba_baza = len(dane_bazy) if isinstance(dane_bazy, list) else 0
        liczba_sklepow = len(sklepy) if isinstance(sklepy, list) else 0

        # Etykieta statusu wczytanych danych
        status_text = f"Załadowane punkty: {liczba_baza} | Sklepy/Mapa: {liczba_sklepow}"
        status_label = toga.Label(
            status_text,
            style=Pack(padding_bottom=15, font_size=11)
        )
        main_box.add(status_label)

        # Tabela prezentująca punkty / butelkomaty
        self.tabela_punktow = toga.Table(
            headings=["ID", "Nazwa / Punkt", "Miasto", "Status"],
            style=Pack(flex=1, padding_bottom=15, height=260)
        )
        
        # Wypełnienie tabeli danymi
        self.wypelnij_tabelę(dane_bazy if dane_bazy else sklepy)
        main_box.add(self.tabela_punktow)

        # Panel przycisków akcji
        buttons_box = toga.Box(
            style=Pack(
                direction=ROW,
                padding_top=5,
                alignment="center"
            )
        )

        btn_odswiez = toga.Button(
            "Odśwież dane",
            on_press=self.on_odswiez_klikniety,
            style=Pack(padding_right=10, width=140)
        )

        btn_ranking = toga.Button(
            "Ranking",
            on_press=self.on_ranking_klikniety,
            style=Pack(width=140)
        )

        buttons_box.add(btn_odswiez)
        buttons_box.add(btn_ranking)
        main_box.add(buttons_box)

        return main_box

    def wypelnij_tabelę(self, dane):
        data_rows = []
        if dane and isinstance(dane, list):
            for idx, item in enumerate(dane):
                if isinstance(item, dict):
                    row_id = str(item.get("id", idx + 1))
                    nazwa = str(item.get("nazwa", item.get("name", "Punkt recyklingu")))
                    miasto = str(item.get("miasto", item.get("city", "Wrocław")))
                    status = str(item.get("status", "aktywny"))
                    data_rows.append((row_id, nazwa, miasto, status))
        
        if not data_rows:
            data_rows.append(("-", "Brak danych w bazie", "-", "-"))
        
        self.tabela_punktow.data = data_rows

    def on_odswiez_klikniety(self, widget):
        dane = self.baza_service.wczytaj_dane()
        self.wypelnij_tabelę(dane)
        if hasattr(self.main_app, "main_window") and self.main_app.main_window:
            self.main_app.main_window.info_dialog(
                "Odświeżono",
                f"Pomyślnie odświeżono bazę. Liczba elementów: {len(dane) if isinstance(dane, list) else 0}"
            )

    def on_ranking_klikniety(self, widget):
        if hasattr(self.main_app, "main_window") and self.main_app.main_window:
            self.main_app.main_window.info_dialog(
                "Ranking",
                "Moduł rankingu butelkomatów."
            )
