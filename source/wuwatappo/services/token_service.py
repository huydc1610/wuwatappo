from enum import Enum
from typing import Callable
from wuwatappo.config import AppConfig
from wuwatappo.services.api_client import ApiClient, mask_token
from wuwatappo.storage import Storage

class TokenStatus(str, Enum):
    NO_TOKEN = "Chưa có"
    CONFIRMED = "Đã cấu hình"
    EXPIRED = "Hết hạn"

class TokenService:
    def __init__(self, config: AppConfig, storage: Storage, api_client: ApiClient) -> None:
        self.config = config
        self.storage = storage
        self.api_client = api_client
        self.status = TokenStatus.NO_TOKEN
        self.current_token: str | None = None

        self.on_status_change: Callable[[TokenStatus, str], None] | None = None
        self._load_initial_token()

    def _load_initial_token(self) -> None:
        saved_token = self.storage.load_token()
        if saved_token:
            self.current_token = saved_token
            self.status = TokenStatus.CONFIRMED
            self.api_client.set_token(saved_token)
        else:
            self.status = TokenStatus.NO_TOKEN

    def _notify_status(self) -> None:
        if self.on_status_change:
            self.on_status_change(self.status, mask_token(self.current_token))

    def manual_set_token(self, token_str: str) -> bool:
        clean = token_str.strip()
        if clean.lower().startswith("bearer "):
            clean = clean[7:].strip()
        if not clean:
            return False

        self.current_token = clean
        self.storage.save_token(self.current_token)
        self.api_client.set_token(self.current_token)
        self.status = TokenStatus.CONFIRMED
        self._notify_status()
        return True

    def delete_token(self) -> None:
        self.current_token = None
        self.storage.delete_token()
        self.api_client.set_token(None)
        self.status = TokenStatus.NO_TOKEN
        self._notify_status()

    def mark_expired(self) -> None:
        self.status = TokenStatus.EXPIRED
        self._notify_status()
