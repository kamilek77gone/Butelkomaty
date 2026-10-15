import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


class RankingService:
    def __init__(self, data_file=None):
        if data_file is None:
            self.data_file = Path(__file__).parent.parent / "data" / "ranking.json"
        else:
            self.data_file = Path(data_file)
        self._cache = None

    def _load(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
        else:
            self._cache = {"zwroty": [], "uzytkownicy": {}}
        return self._cache

    def _save(self) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def zapisz_zwrot(self, user_id: str, user_name: str, ilosc: int, data: str = None) -> Dict[str, Any]:
        data = self._load()
        if data is None:
            data = self._cache
        zwrot = {
            "user_id": user_id,
            "user_name": user_name,
            "ilosc": ilosc,
            "data": data or datetime.now().isoformat()
        }
        data["zwroty"].append(zwrot)
        uzytkownicy = data.setdefault("uzytkownicy", {})
        if user_id not in uzytkownicy:
            uzytkownicy[user_id] = {"name": user_name, "razem": 0}
        uzytkownicy[user_id]["razem"] += ilosc
        uzytkownicy[user_id]["name"] = user_name
        self._cache = data
        self._save()
        return zwrot

    def ranking_tygodniowy(self) -> List[Dict[str, Any]]:
        data = self._load()
        teraz = datetime.now()
        poczatek_tygodnia = teraz - timedelta(days=teraz.weekday())
        poczatek_tygodnia = poczatek_tygodnia.replace(hour=0, minute=0, second=0, microsecond=0)

        tygodniowe: Dict[str, int] = {}
        for z in data.get("zwroty", []):
            try:
                dzien = datetime.fromisoformat(z["data"])
            except Exception:
                continue
            if dzien >= poczatek_tygodnia:
                uid = z["user_id"]
                tygodniowe[uid] = tygodniowe.get(uid, 0) + z["ilosc"]

        wynik = sorted(tygodniowe.items(), key=lambda x: x[1], reverse=True)
        uzytkownicy = data.get("uzytkownicy", {})
        return [
            {
                "pozycja": i + 1,
                "user_id": uid,
                "user_name": uzytkownicy.get(uid, {}).get("name", uid),
                "ilosc": ilosc,
            }
            for i, (uid, ilosc) in enumerate(wynik)
        ]

    def znizki(self, top_n: int = 3) -> List[Dict[str, Any]]:
        ranking = self.ranking_tygodniowy()
        poziomy = {1: "10%", 2: "7%", 3: "5%"}
        return [
            {
                "pozycja": r["pozycja"],
                "user_name": r["user_name"],
                "znizka": poziomy.get(r["pozycja"], "0%"),
            }
            for r in ranking[:top_n]
        ]
