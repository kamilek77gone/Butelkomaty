"""
Service do obsługi mapy i danych butelkomatów.
Ładuje bazę JSON, konwertuje do GeoJSON dla Leaflet.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any


class MapaService:
    def __init__(self, resources_path=None):
        if resources_path is not None:
            self.base_path = Path(resources_path)
        else:
            self.base_path = Path(__file__).parent.parent
        self.data_file = self.base_path / "baza_butelkomaty.json"
        self._cache = None
        self._load_error = None

    def load_data(self) -> Dict[str, Any]:
        """Ładuje bazę danych z pliku JSON."""
        if self._cache is not None:
            return self._cache
        if self._load_error is not None:
            raise self._load_error
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
        except FileNotFoundError as exc:
            self._load_error = exc
            raise
        return self._cache

    def get_geojson(self, chains: List[str] = None) -> str:
        """
        Zwraca GeoJSON FeatureCollection z punktami.
        chains: lista sieci do uwzględnienia (None = wszystkie).
        """
        data = self.load_data()
        features = []

        for p in data.get("punkty", []):
            if chains and p.get("siec") not in chains:
                continue
            lat = p.get("latitude")
            lon = p.get("longitude")
            if lat is None or lon is None:
                continue
            # Wszystkie pola punktu trafiają do properties
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": p
            })

        return json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False)

    def get_chains(self) -> List[str]:
        """Zwraca listę unikalnych sieci w bazie."""
        data = self.load_data()
        chains = sorted(set(p.get("siec") for p in data.get("punkty", []) if p.get("siec")))
        return chains

    def get_stats(self) -> Dict[str, int]:
        """Zwraca statystyki per sieć."""
        data = self.load_data()
        stats = {}
        for p in data.get("punkty", []):
            siec = p.get("siec", "Nieznana")
            stats[siec] = stats.get(siec, 0) + 1
        return stats