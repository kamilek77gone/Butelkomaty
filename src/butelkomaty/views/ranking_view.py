import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class RankingView:
    def __init__(self, ranking_service):
        self.ranking_service = ranking_service

    def build(self):
        box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        title = toga.Label(
            "🏆 Tygodniowy Ranking",
            style=Pack(font_size=20, font_weight='bold', margin_bottom=10)
        )
        box.add(title)

        subtitle = toga.Label(
            "Kto najwięcej zwrócił w tym tygodniu:",
            style=Pack(font_size=14, margin_bottom=8)
        )
        box.add(subtitle)

        ranking = self.ranking_service.ranking_tygodniowy()

        if not ranking:
            empty = toga.Label(
                "Brak zwrotów w tym tygodniu. Bądź pierwszy!",
                style=Pack(color='#666', margin_bottom=10)
            )
            box.add(empty)
        else:
            for r in ranking:
                row = toga.Box(
                    style=Pack(
                        direction=ROW,
                        padding=4,
                        background_color='#f5f5f5' if r['pozycja'] % 2 == 0 else 'white',
                    )
                )
                pos = toga.Label(
                    f"{r['pozycja']}.",
                    style=Pack(width=30, font_weight='bold')
                )
                name = toga.Label(r['user_name'], style=Pack(flex=1))
                cnt = toga.Label(
                    f"{r['ilosc']} szt.",
                    style=Pack(width=80, text_align='right')
                )
                row.add(pos)
                row.add(name)
                row.add(cnt)
                box.add(row)

        box.add(toga.Label("", style=Pack(flex=1)))

        znizki = self.ranking_service.znizki()
        if znizki:
            nagroda = toga.Label(
                "🎟️ Zniżki dla najlepszych:",
                style=Pack(font_size=14, font_weight='bold', margin_top=10, margin_bottom=5)
            )
            box.add(nagroda)
            for z in znizki:
                zrow = toga.Box(style=Pack(direction=ROW, padding=4))
                zrow.add(
                    toga.Label(f"{z['pozycja']}. {z['user_name']}", style=Pack(flex=1))
                )
                zrow.add(
                    toga.Label(
                        f"Zniżka: {z['znizka']}",
                        style=Pack(font_weight='bold', color='#1e88e5')
                    )
                )
                box.add(zrow)

        return box
