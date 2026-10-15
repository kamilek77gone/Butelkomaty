"""
Aplikacja do mapowania i śledzenia automatów recyklingowych w Polsce
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from .services.mapa import MapaService
from .services.ranking import RankingService
from .views.main_view import MainView


class Butelkomaty(toga.App):

    def startup(self):
        # Inicjalizacja serwisów
        self.mapa_service = MapaService()
        self.ranking_service = RankingService()
        
        # Budowa widoku głównego
        self.main_view = MainView(self, self.mapa_service, self.ranking_service)
        
        # Rejestracja callbacka z JS
        self.main_view.webview.on_message = self.on_webview_message
        
        # Główne okno
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_view.build()
        self.main_window.show()

    def on_webview_message(self, message):
        """Obsługa wiadomości z WebView (marker click)."""
        if message.get('type') == 'marker_click':
            self.main_view.on_marker_click(message.get('data', '{}'))


def main():
    return Butelkomaty()