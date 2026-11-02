import random
import threading
import time
from typing import Callable
from wuwatappo.services.api_client import ApiClient

class ClickService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client
        self._running = False
        self._thread: threading.Thread | None = None
        self.total_sent = 0
        self.last_status = "Đã dừng"

        self.on_progress: Callable[[int, str], None] | None = None
        self.on_finished: Callable[[str], None] | None = None
        self.on_auth_expired: Callable[[], None] | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, total_clicks: int, place: str = "left", batch_size: int = 1000) -> None:
        if self._running:
            return
        if total_clicks <= 0:
            if self.on_finished:
                self.on_finished("Số lượng click phải lớn hơn 0")
            return

        self._running = True
        self.total_sent = 0
        self.last_status = "Đang chạy"
        self._thread = threading.Thread(
            target=self._worker,
            args=(total_clicks, place, batch_size),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self.last_status = "Đã dừng bởi người dùng"
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.on_progress:
            self.on_progress(self.total_sent, self.last_status)

    def _worker(self, total_clicks: int, place: str, batch_size: int) -> None:
        remaining = total_clicks
        msg = "Hoàn thành"

        # Nếu tổng số click nhỏ hơn hoặc bằng batch_size thì gửi 1 lần duy nhất
        while self._running and remaining > 0:
            current_batch = min(remaining, batch_size) if total_clicks > batch_size else total_clicks
            ok, resp_data, status_code = self.api_client.buff_click(click_num=current_batch, place=place)

            if status_code in (401, 403):
                self._running = False
                msg = f"Token hết hạn hoặc không hợp lệ (HTTP {status_code})"
                if self.on_auth_expired:
                    self.on_auth_expired()
                break

            if not ok:
                self._running = False
                msg = f"Lỗi gửi click: {resp_data} (HTTP {status_code})"
                break

            self.total_sent += current_batch
            remaining -= current_batch
            self.last_status = f"Đã gửi {self.total_sent}/{total_clicks} (HTTP {status_code})"

            if self.on_progress:
                self.on_progress(self.total_sent, self.last_status)

            if remaining <= 0:
                break

            jitter = random.uniform(0.1, 0.4)
            time.sleep(jitter)

        self._running = False
        if self.on_finished:
            self.on_finished(msg)

