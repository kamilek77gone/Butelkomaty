import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from butelkomaty.views.main_view import MainView


class Butelkomaty(toga.App):
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main window.
        """
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Inicjalizacja głównego widoku aplikacji
        self.main_view = MainView(self)
        
        self.main_window.content = self.main_view.container
        self.main_window.show()


def main():
    return Butelkomaty()
