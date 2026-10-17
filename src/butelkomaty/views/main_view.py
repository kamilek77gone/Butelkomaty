import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from butelkomaty.services.baza import BazaDanych
from butelkomaty.services.mapa import MapaService
from butelkomaty.services.ranking import RankingService


class MainView:
    def __init__(self, main_app):
        self.main_app = main_app
        
        # Inicjalizacja serwisów
        self.baza_service = BazaDanych()
        self.mapa_service = MapaService()
        self.ranking_service = RankingService()
        
        self.container = self.build()

    def build(self):
        # Główny kontener aplikacji
        main_box = toga.Box(
            style=Pack(
                direction=COLUMN,
                alignment="center",
                padding=20
            )
        )

        # Nagłówek
        title_label = toga.Label(
            "Butelkomaty - Mapa i Ranking",
            style=Pack(
                padding_bottom=20,
                font_size=18,
                font_weight="bold"
            )
        )
        main_box.add(title_label)

        # Informacja o danych
        dane = self.baza_service.wczytaj_dane()
        status_text = f"Załadowano punktów: {len(dane)}" if dane else "Brak danych bazy."
        
        status_label = toga.Label(
            status_text,
            style=Pack(padding_bottom=20)
        )
        main_box.add(status_label)

        # Przyciski nawigacyjne / akcji
        btn_odswiez = toga.Button(
            "Odśwież dane",
            on_press=self.on_odswiez_klikniety,
            style=Pack(padding_bottom=10, width=200)
        )
        main_box.add(btn_odswiez)

        return main_box

    def on_odswiez_klikniety(self, widget):
        # Akcja przycisku odświeżania
        dane = self.baza_service.wczytaj_dane()
        self.main_app.main_window.info_dialog(
            "Odświeżono",
            f"Pomyślnie wczytano bazę. Liczba elementów: {len(dane)}"
        )
