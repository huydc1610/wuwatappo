import json
import threading
import time
from typing import Any, Callable
from wuwatappo.config import AppConfig
from wuwatappo.services.api_client import ApiClient
from wuwatappo.services.catalog import Catalog
from wuwatappo.storage import Storage

class ChestService:
    def __init__(
        self,
        config: AppConfig,
        storage: Storage,
        api_client: ApiClient,
        catalog: Catalog,
    ) -> None:
        self.config = config
        self.storage = storage
        self.api_client = api_client
        self.catalog = catalog

        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self.opened_count = 0
        self.last_status = "Đã dừng"

        self.on_reward_received: Callable[[dict[str, Any]], None] | None = None
        self.on_status_change: Callable[[str], None] | None = None
        self.on_auth_expired: Callable[[], None] | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self.last_status = "Đang chạy"
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._stop_event.set()
        self.last_status = "Đã dừng bởi người dùng"
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.on_status_change:
            self.on_status_change(self.last_status)

    def _worker_loop(self) -> None:
        while self._running:
            for place in ("left", "right"):
                if not self._running:
                    break
                self._attempt_open_chest(place)
                time.sleep(1.0)

            interval = max(5, self.config.check_interval_seconds)
            for _ in range(interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1.0)

    def _attempt_open_chest(self, place: str) -> None:
        ok, resp, status_code = self.api_client.open_chest(place)

        if status_code in (401, 403):
            self._running = False
            self.last_status = f"Token hết hạn (HTTP {status_code})"
            self.storage.add_log("ERROR", f"Auto claim rương {place}: Token hết hạn")
            if self.on_auth_expired:
                self.on_auth_expired()
            return

        if not ok:
            err_msg = str(resp)
            self.storage.add_log("WARNING", f"Claim rương {place} chưa thành công: {err_msg} (HTTP {status_code})")
            return

        # Phân tích dữ liệu phần quà nhận được
        asset_id = "unknown"
        asset_name = "Phần thưởng"
        cost = 0
        raw_str = ""

        if isinstance(resp, dict):
            raw_str = json.dumps(resp, ensure_ascii=False)
            data = resp.get("data", resp)
            if isinstance(data, dict):
                asset_id = str(data.get("asset_id") or data.get("id") or data.get("item_id") or "1")
                cost = int(data.get("cost") or 0)
            elif isinstance(data, list) and len(data) > 0:
                first = data[0]
                if isinstance(first, dict):
                    asset_id = str(first.get("asset_id") or first.get("id") or "1")
        else:
            raw_str = str(resp)

        resolved = self.catalog.resolve(asset_id)
        asset_name = resolved["name"]

        reward_id = self.storage.add_reward(
            place=place,
            asset_id=asset_id,
            asset_name=asset_name,
            cost=cost,
            status="confirmed",
            raw_json=raw_str,
        )

        self.opened_count += 1
        reward_info = {
            "id": reward_id,
            "place": place,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "cost": cost,
            "status": "confirmed",
        }

        self.storage.add_log("INFO", f"Nhận quà rương {place}: {asset_name} (ID: {asset_id})")
        if self.on_reward_received:
            self.on_reward_received(reward_info)

