"""
Widok główny aplikacji - mapa z filtrami i bottom sheet.
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, HIDDEN
import json
import webbrowser
from pathlib import Path

from .services.ranking import RankingService
from .views.ranking_view import RankingView


class MainView:
    def __init__(self, app, mapa_service, ranking_service):
        self.app = app
        self.mapa_service = mapa_service
        self.ranking_service = ranking_service
        self.webview = None
        self.filter_chips = {}
        self.bottom_sheet = None
        self.bottom_sheet_content = None
        self.selected_point = None
        self._map_ready = False
        
        self.chain_colors = {
            'Żabka': '#ff9800', 'Biedronka': '#4caf50', 'Lidl': '#e91e63',
            'Dino': '#2196f3', 'Netto': '#9c27b0'
        }
        self.chain_icons = {
            'Żabka': '🏪', 'Biedronka': '🛒', 'Lidl': '🛍️', 'Dino': '🦖', 'Netto': '🏬'
        }

    def build(self):
        toolbar = toga.Box(style=Pack(direction=ROW, padding=10, background_color='#1e88e5'))
        
        title = toga.Label(
            '🗺️ Butelkomaty',
            style=Pack(color='white', font_size=18, font_weight='bold', flex=1)
        )
        
        btn_locate = toga.Button('📍', on_press=self.on_locate, style=Pack(width=44, height=44, background_color='white', color='#1e88e5'))
        btn_refresh = toga.Button('🔄', on_press=self.on_refresh, style=Pack(width=44, height=44, background_color='white', color='#1e88e5'))
        btn_menu = toga.Button('☰', on_press=self.on_menu, style=Pack(width=44, height=44, background_color='white', color='#1e88e5'))
        btn_ranking = toga.Button('🏆', on_press=self.on_ranking, style=Pack(width=44, height=44, background_color='white', color='#1e88e5'))
        
        toolbar.add(title)
        toolbar.add(btn_locate)
        toolbar.add(btn_refresh)
        toolbar.add(btn_menu)
        toolbar.add(btn_ranking)

        map_html_path = Path(self.app.resources_path) / 'map.html'
        self.webview = toga.WebView(
            style=Pack(flex=1),
            url=map_html_path.as_uri(),
            on_webview_load=self.on_webview_load
        )

        self.filter_bar = toga.ScrollContainer(style=Pack(height=50, background_color='#f5f5f5'))
        filter_box = toga.Box(style=Pack(direction=ROW, padding=8, gap=8))
        
        chains = self.mapa_service.get_chains() if self.mapa_service else []
        for chain in chains:
            chip = self.create_filter_chip(chain)
            self.filter_chips[chain] = chip
            filter_box.add(chip)
        
        btn_all = toga.Button(
            '✓ Wszystkie', on_press=lambda w: self.toggle_all_filters(True),
            style=Pack(padding=(6, 12), background_color='#e0e0e0', border_radius=20)
        )
        filter_box.add(btn_all)
        
        self.filter_bar.content = filter_box

        self.bottom_sheet = toga.Box(style=Pack(direction=COLUMN, background_color='white', height=0, visibility=HIDDEN))
        
        handle = toga.Box(style=Pack(height=6, background_color='#e0e0e0'))
        handle_line = toga.Box(style=Pack(width=40, height=4, background_color='#999', border_radius=2, margin_top=1))
        handle.add(handle_line)
        
        self.bottom_sheet_content = toga.Box(style=Pack(direction=COLUMN, padding=16, flex=1))
        self.bottom_sheet.add(handle)
        self.bottom_sheet.add(self.bottom_sheet_content)

        main_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        main_box.add(toolbar)
        main_box.add(self.webview)
        main_box.add(self.filter_bar)
        main_box.add(self.bottom_sheet)

        return main_box

    def create_filter_chip(self, chain):
        color = self.chain_colors.get(chain, '#1e88e5')
        icon = self.chain_icons.get(chain, '📍')
        
        chip = toga.Button(
            f'{icon} {chain}',
            on_press=lambda w, c=chain: self.toggle_filter(c),
            style=Pack(
                padding=(6, 12),
                background_color=color,
                color='white',
                border_radius=20,
                font_weight='bold'
            )
        )
        chip.chain = chain
        chip.enabled_state = True
        return chip

    def toggle_filter(self, chain):
        chip = self.filter_chips[chain]
        chip.enabled_state = not chip.enabled_state
        
        if chip.enabled_state:
            chip.style.background_color = self.chain_colors.get(chain, '#1e88e5')
        else:
            chip.style.background_color = '#bdbdbd'
        
        self.webview.evaluate_javascript(f'window.py_set_filter("{chain}", {str(chip.enabled_state).lower()})')

    def toggle_all_filters(self, enabled):
        for chain, chip in self.filter_chips.items():
            chip.enabled_state = enabled
            chip.style.background_color = self.chain_colors.get(chain, '#1e88e5') if enabled else '#bdbdbd'
        self.webview.evaluate_javascript(f'window.py_set_all_filters({str(enabled).lower()})')

    def on_webview_load(self, webview):
        self._map_ready = True
        self.load_markers()

    def load_markers(self):
        if not self._map_ready:
            return
        if self.mapa_service is None:
            return
        geojson = self.mapa_service.get_geojson()
        escaped = geojson.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        self.webview.evaluate_javascript(f'window.py_add_markers("{escaped}")')

    def on_marker_click(self, point_json):
        try:
            self.selected_point = json.loads(point_json)
            self.show_bottom_sheet(self.selected_point)
        except Exception as e:
            print(f'Błąd parsowania punktu: {e}')

    def show_bottom_sheet(self, point):
        for child in list(self.bottom_sheet_content.children):
            self.bottom_sheet_content.remove(child)
        
        chain = point.get('siec', '')
        color = self.chain_colors.get(chain, '#1e88e5')
        icon = self.chain_icons.get(chain, '📍')
        
        header = toga.Box(style=Pack(direction=ROW, padding_bottom=12))
        title_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        
        chain_label = toga.Label(f'{icon} {chain}', style=Pack(color=color, font_size=16, font_weight='bold'))
        
        address = point.get('adres_pelny') or f"{point.get('ulica', '')} {point.get('numer', '')}, {point.get('kod', '')} {point.get('miasto', '')}"
        addr_label = toga.Label(address, style=Pack(color='#444', font_size=13, margin_top=2))
        
        title_box.add(chain_label)
        title_box.add(addr_label)
        
        close_btn = toga.Button('✕', on_press=self.hide_bottom_sheet, style=Pack(width=32, height=32, background_color='#f5f5f5', border_radius=16))
        header.add(title_box)
        header.add(close_btn)
        
        typ = point.get('typ_zbiorki_opis') or point.get('typ_zbiorki', '')
        type_icon = '♻️' if point.get('typ_zbiorki') == 'automat' else '🤲'
        type_label = toga.Label(f'{type_icon} {typ}', style=Pack(color='#555', font_size=13, margin_bottom=8))
        
        hours = point.get('godziny', {})
        if hours:
            hours_text = 'Godziny otwarcia:\n' + '\n'.join(f'{d[:3]}: {h}' for d, h in hours.items())
        else:
            hours_text = 'Godziny: brak danych'
        hours_label = toga.Label(hours_text, style=Pack(color='#666', font_size=12, line_height=18, margin_bottom=12))
        
        status = point.get('status', 'aktywny')
        status_color = '#1b5e20' if status == 'aktywny' else '#e65100'
        status_bg = '#e8f5e9' if status == 'aktywny' else '#fff3e0'
        status_label = toga.Label(
            f'● {status.capitalize()}',
            style=Pack(color=status_color, background_color=status_bg, padding=(6, 12), border_radius=16, font_size=12, font_weight='bold', margin_bottom=16)
        )
        
        actions_box = toga.Box(style=Pack(direction=ROW, gap=8, margin_top=8))
        
        btn_navigate = toga.Button(
            '🗺️ Nawiguj',
            on_press=lambda w: self.on_navigate(point),
            style=Pack(flex=1, padding=12, background_color='#1e88e5', color='white', border_radius=8)
        )
        
        btn_report = toga.Button(
            '📝 Zgłoś status',
            on_press=lambda w: self.on_report_status(point),
            style=Pack(flex=1, padding=12, background_color='#ff9800', color='white', border_radius=8)
        )
        
        btn_add = toga.Button(
            '➕ Dodaj brakujący',
            on_press=lambda w: self.on_add_missing(point),
            style=Pack(flex=1, padding=12, background_color='#4caf50', color='white', border_radius=8)
        )
        
        actions_box.add(btn_navigate)
        actions_box.add(btn_report)
        actions_box.add(btn_add)
        
        self.bottom_sheet_content.add(header)
        self.bottom_sheet_content.add(type_label)
        self.bottom_sheet_content.add(hours_label)
        self.bottom_sheet_content.add(status_label)
        self.bottom_sheet_content.add(actions_box)
        
        self.bottom_sheet.style.visibility = 'visible'
        self.bottom_sheet.style.height = 320
        self.bottom_sheet.style.flex = 1

    def hide_bottom_sheet(self, widget):
        self.bottom_sheet.style.visibility = HIDDEN
        self.bottom_sheet.style.height = 0
        self.bottom_sheet.style.flex = 0

    def on_locate(self, widget):
        self.app.main_window.info_dialog('Lokalizacja', 'Funkcja w przygotowaniu')

    def on_refresh(self, widget):
        self.load_markers()

    def on_menu(self, widget):
        self.app.main_window.info_dialog('Menu', 'Ustawienia, informacje o aplikacji - w przygotowaniu')

    def on_ranking(self, widget):
        win = toga.Window(title='🏆 Tygodniowy Ranking')
        win.content = RankingView(self.ranking_service).build()
        win.show()

    def on_navigate(self, point):
        lat = point.get('latitude')
        lon = point.get('longitude')
        if lat and lon:
            webbrowser.open(f'geo:{lat},{lon}?q={lat},{lon}({point.get("siec", "Butelkomat")})')

    def on_report_status(self, point):
        self.app.main_window.info_dialog('Zgłoś status', 'Formularz zgłoszenia - w przygotowaniu')

    def on_add_missing(self, point):
        self.app.main_window.info_dialog('Dodaj automat', 'Formularz dodawania - w przygotowaniu')