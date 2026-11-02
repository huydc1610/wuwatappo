import re
import threading
import time
from enum import Enum
from typing import Callable
from wuwatappo.config import AppConfig
from wuwatappo.services.api_client import ApiClient, mask_token
from wuwatappo.storage import Storage

class TokenStatus(str, Enum):
    NO_TOKEN = "Chưa có"
    WAITING = "Đang chờ phát hiện..."
    DETECTED_WAITING_CONFIRM = "Đã bắt được, chờ xác nhận"
    CONFIRMED = "Đã xác nhận"
    EXPIRED = "Hết hạn"

TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{32,256}$")

class TokenService:
    def __init__(self, config: AppConfig, storage: Storage, api_client: ApiClient) -> None:
        self.config = config
        self.storage = storage
        self.api_client = api_client
        self.status = TokenStatus.NO_TOKEN
        self.current_token: str | None = None
        self.pending_token: str | None = None

        self.on_status_change: Callable[[TokenStatus, str], None] | None = None
        self.on_token_detected: Callable[[str], None] | None = None

        self._running = False
        self._thread: threading.Thread | None = None

        self._load_initial_token()

    def _load_initial_token(self) -> None:
        saved_token = self.storage.load_token()
        if saved_token:
            self.current_token = saved_token
            self.status = TokenStatus.CONFIRMED
            self.api_client.set_token(saved_token)
        else:
            self.status = TokenStatus.NO_TOKEN

    def start_background_listener(self) -> None:
        if self._running:
            return
        self._running = True
        if self.status != TokenStatus.CONFIRMED:
            self.status = TokenStatus.WAITING
            self._notify_status()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop_background_listener(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.status == TokenStatus.WAITING:
            self.status = TokenStatus.NO_TOKEN
            self._notify_status()

    def _notify_status(self) -> None:
        if self.on_status_change:
            self.on_status_change(self.status, mask_token(self.current_token))

    def _worker_loop(self) -> None:
        last_checked = ""
        while self._running:
            try:
                # Kiểm tra clipboard an toàn
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                clip_text = ""
                try:
                    clip_text = root.clipboard_get()
                except Exception:
                    pass
                root.destroy()

                clip_text = clip_text.strip()
                if clip_text and clip_text != last_checked:
                    last_checked = clip_text
                    clean_token = clip_text
                    if clean_token.lower().startswith("bearer "):
                        clean_token = clean_token[7:].strip()

                    if TOKEN_PATTERN.match(clean_token) and clean_token != self.current_token:
                        self.pending_token = clean_token
                        self.status = TokenStatus.DETECTED_WAITING_CONFIRM
                        self._notify_status()
                        if self.on_token_detected:
                            self.on_token_detected(mask_token(clean_token))
            except Exception:
                pass
            time.sleep(2.0)

    def confirm_token(self) -> bool:
        if not self.pending_token:
            return False
        self.current_token = self.pending_token
        self.pending_token = None
        self.storage.save_token(self.current_token)
        self.api_client.set_token(self.current_token)
        self.status = TokenStatus.CONFIRMED
        self._notify_status()
        return True

    def reject_token(self) -> None:
        self.pending_token = None
        if self.current_token:
            self.status = TokenStatus.CONFIRMED
        else:
            self.status = TokenStatus.WAITING if self._running else TokenStatus.NO_TOKEN
        self._notify_status()

    def manual_set_token(self, token_str: str) -> bool:
        clean = token_str.strip()
        if clean.lower().startswith("bearer "):
            clean = clean[7:].strip()
        if not clean:
            return False

        self.current_token = clean
        self.pending_token = None
        self.storage.save_token(self.current_token)
        self.api_client.set_token(self.current_token)
        self.status = TokenStatus.CONFIRMED
        self._notify_status()
        return True

    def delete_token(self) -> None:
        self.current_token = None
        self.pending_token = None
        self.storage.delete_token()
        self.api_client.set_token(None)
        self.status = TokenStatus.NO_TOKEN
        self._notify_status()

    def mark_expired(self) -> None:
        self.status = TokenStatus.EXPIRED
        self._notify_status()

