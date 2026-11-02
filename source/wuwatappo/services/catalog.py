import json
from pathlib import Path
from typing import Any

class Catalog:
    def __init__(self, cache_file_path: Path | None = None) -> None:
        self.cache_file_path = cache_file_path
        self._items: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file_path and self.cache_file_path.exists():
            try:
                data = json.loads(self.cache_file_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._items = data
            except Exception:
                self._items = {}

    def resolve(self, asset_id: str | int) -> dict[str, Any]:
        key = str(asset_id)
        if key in self._items:
            item = self._items[key]
            return {
                "name": item.get("name", f"Asset {key}"),
                "type": item.get("type", "Vật phẩm"),
                "rarity": item.get("rarity", 1),
            }
        return {
            "name": f"Vật phẩm #{key}",
            "type": "Chưa rõ",
            "rarity": 1,
        }

