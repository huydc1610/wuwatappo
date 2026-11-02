import requests
from typing import Any
from wuwatappo.config import AppConfig

def mask_token(token: str | None) -> str:
    if not token:
        return "None"
    token = token.strip()
    if len(token) <= 8:
        return token[:3] + "..."
    return token[:8] + "..."

class ApiClient:
    def __init__(self, config: AppConfig, token: str | None = None) -> None:
        self.config = config
        self.token = token
        self.session = requests.Session()

    def set_token(self, token: str | None) -> None:
        self.token = token

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "origin": self.config.origin,
            "referer": self.config.referer,
            "user-agent": self.config.user_agent,
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "priority": "u=1, i",
        }
        if self.token:
            headers["authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def post(self, url: str, json_data: dict[str, Any]) -> tuple[bool, Any, int]:
        if not self.token:
            return False, "Chưa có token xác thực", 0

        headers = self._get_headers()
        try:
            resp = self.session.post(
                url=url,
                json=json_data,
                headers=headers,
                timeout=10,
                verify=True,
            )
            status_code = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = resp.text

            is_ok = 200 <= status_code < 300
            return is_ok, data, status_code
        except requests.exceptions.Timeout:
            return False, "Kết nối timeout (10s)", 408
        except requests.exceptions.SSLError:
            return False, "Lỗi xác thực SSL", 495
        except requests.exceptions.ConnectionError:
            return False, "Lỗi kết nối mạng", 503
        except Exception as e:
            return False, f"Lỗi không xác định: {str(e)}", 500

    def open_chest(self, place: str = "left") -> tuple[bool, Any, int]:
        url = self.config.chest_open_url
        body = {"place": place.lower()}
        return self.post(url, body)

    def buff_click(self, click_num: int, place: str = "left") -> tuple[bool, Any, int]:
        url = self.config.click_url
        if not url or url.startswith("TODO"):
            return False, "Chưa cấu hình endpoint Buff Click", 400
        body = {"place": place.lower(), "click_num": int(click_num)}
        return self.post(url, body)

