import json
import os


class MapaService:
    def __init__(self):
        # Pobieranie katalogu, w którym znajduje się ten plik usług
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.sklepy_path = os.path.join(self.base_dir, "..", "sklepy_mapa.json")

    def pobierz_sklepy(self):
        try:
            if os.path.exists(self.sklepy_path):
                with open(self.sklepy_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Błąd podczas wczytywania mapy sklepów: {e}")
        return []
