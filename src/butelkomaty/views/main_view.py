import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

# POPRAWIONO TYLKO BŁĘDNY IMPORT: z "from butelkomaty.views.services import ..." na poprawny:
from butelkomaty.services import baza, mapa, ranking


class MainView:
    def __init__(self, main_app):
        self.main_app = main_app
        self.container = self.build()

    def build(self):
        # Główny kontener widoku
        box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        title_label = toga.Label(
            "Witaj w aplikacji Butelkomaty!",
            style=Pack(padding_bottom=10, font_weight="bold")
        )
        
        info_label = toga.Label(
            "Wybierz opcję poniżej:",
            style=Pack(padding_bottom=10)
        )

        box.add(title_label)
        box.add(info_label)
        
        return box
