"""
Aplikacja do mapowania i śledzenia automatów recyklingowych w Polsce
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN


class Butelkomaty(toga.App):

    def startup(self):

        tekst = toga.Label(
            "🚀 Butelkomaty\n\nPierwsza wersja działa!",
            style=Pack(padding=20)
        )

        main_box = toga.Box(
            style=Pack(direction=COLUMN)
        )

        main_box.add(tekst)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return Butelkomaty()