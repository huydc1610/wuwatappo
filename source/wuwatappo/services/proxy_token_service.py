import asyncio
import atexit
import ctypes
import os
import signal
import subprocess
import sys
import threading
import winreg
from typing import Callable
from urllib.parse import parse_qs, urlparse

from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

CA_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDNTCCAh2gAwIBAgIUPUhrqaPQCZy2JHb7A1HxrhVgL1IwDQYJKoZIhvcNAQEL
BQAwKDESMBAGA1UEAwwJbWl0bXByb3h5MRIwEAYDVQQKDAltaXRtcHJveHkwHhcN
MjYxMDI1MTU1NzQ1WhcNMzYxMDI0MTU1NzQ1WjAoMRIwEAYDVQQDDAltaXRtcHJv
eHkxEjAQBgNVBAoMCW1pdG1wcm94eTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCC
AQoCggEBAL24okk0ekfgy5fYNuqVGtZS0uXfKYqzzg3gn0y3sHdqt5YCaHQN+tpT
31Uph8bCGWgfW6iI3kEofwmoTGfx+M2fM5yjWlqIDNxM34mN6QMXThZkvFwjyImG
WxF3eus9HFZTlfS6JcjMUmWwCQENMUeB8NEAP9AnYBiVkDAHXw3esiEjfvSvfWU2
jeQiY3d/tDggXRA7mCRa6ZT8hnOr6CPezDNnqEunh8eLCbP3VQjumVUxMthfd5Sf
wU41mNnYfpkJujQ0HZoXGEOgc7E2P0mOOzBHEHhUjOGddPpsVzM6Lqm+IKEnT/Kg
MAoJ/X5wWuyeuPj6qW8QSmh0T1DgS7sCAwEAAaNXMFUwDwYDVR0TAQH/BAUwAwEB
/zATBgNVHSUEDDAKBggrBgEFBQcDATAOBgNVHQ8BAf8EBAMCAQYwHQYDVR0OBBYE
FIa+z5HJIObK2FGiZCoOQ8SwWKMHMA0GCSqGSIb3DQEBCwUAA4IBAQBa0RX0Ep96
5srM/WwQ7CQprabszbp3JKGd8ZOghzn0+8U8UbzFHzL2FKqZmAdR2eHW0R3NLovH
U9lxFNFBhc0TliJzXzmV1QARUiQkZwqkrzY2VNvHcan5Txqxo4zKfOU7kNmSMUDH
jorTs6yYOTVmXtQxxD0m+2v8IRzOe0BvZGdnxVCtv5SfMSlTLwCHntS9qweIxE4l
GLJstt/andOYGDnJRvIqgcEbc931J4Jv1TUg+FCySmBB3nRHEyhZgBX5n6W5BH1M
Iu3uoNavkhvjDYpFEfXFCAIaLmCFioM72T6diGinFvh7VkFtXwIpkS7glUFk+OQv
Ja8zjVOMBZ78
-----END CERTIFICATE-----
"""

CA_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAvbiiSTR6R+DLl9g26pUa1lLS5d8pirPODeCfTLewd2q3lgJo
dA362lPfVSmHxsIZaB9bqIjeQSh/CahMZ/H4zZ8znKNaWogM3EzfiY3pAxdOFmS8
XCPIiYZbEXd66z0cVlOV9LolyMxSZbAJAQ0xR4Hw0QA/0CdgGJWQMAdfDd6yISN+
9K99ZTaN5CJjd3+0OCBdEDuYJFrplPyGc6voI97MM2eoS6eHx4sJs/dVCO6ZVTEy
2F93lJ/BTjWY2dh+mQm6NDQdmhcYQ6BzsTY/SY47MEcQeFSM4Z10+mxXMzouqb4g
oSdP8qAwCgn9fnBa7J64+PqpbxBKaHRPUOBLuwIDAQABAoIBABYjGBSQogAHE9p4
6ReAJGyDp4YY/wDnMBDgd9X8zQNyGU/Qoh2AkBevl6yZNvWTKmHC3vAQYFacAg6/
a4Lpcg2UGPKbAOz1WQLPmXm0bE7nBj6IrI3XwwuA+NlV5qrSK59LC4FNwyDl7mtd
Gf/caTady9qnO8ru/UCBGxzvj0DP2uvNt93olY+yKDgX7oRBrXEd25lSThm+cRMG
q6vWuQou2hj7F931C8hxXX9Qm+aWI+OpEv2begJA8BtB4WBReFTvH8hEWiGYqT7v
zPWEvzF2SJlnN9rKPEJlSN7G1nK9bhwb78etVgieKGeL2xoYvd07BM93wGhTUZHw
KGTlwDkCgYEA30GY71TI321Lyd/pGHOD0L2K4QVT/PAn/PYcOw7dO8Xcns2W7whG
yiB9gJMPnz6nc6GpiLW2OCPedeKP1hDXA46MHKIi2bolq1zhgCTsljna7usQG4JQ
/9otAkGmwFW6VAtssjMaiqPT9b0lbLmBCPX7CiwgCwV+PSJM/imYJg0CgYEA2Yvt
ZY5pIP0djay1m1rAEzDS25SZfWhWlWWa8J6+PXXhoMyVeWMVbQXsGA2m9UGfaSGJ
hHv2bPHpa/Qq+pXB4r1goj6JkZxK6klvYSzSFu0rYOcdzo/47921XmYo8SrV9lpb
nLVRpJomA0YWl5mnciter1pgbmdNoMQSA692TucCgYEAoNuuyaKZKQKi/M1sMcXp
T9mB2yfvn+uZpFXfeV34YTzq/TC8c3XPK4vFYYKUWvTVyibM9EeZB1Iw01dus5pm
kZV/tpHL8nyA77t4btAr9wGwkTyk2m1G11Hn5BxRfXtHSY8BvlO75/CqpAComnH+
WuqA+o9Ydxh6IKo6N1bY3XECgYBLJUiVogGygXxp6dS5mzlp552Od+AlL5to87X3
k/4G4OdVUhX33kASbs9E58JaSZa1C/6ioudWbqHAxpDqCjz1A5GTuaJvh9tg3oj4
ujC/9qDbUjo7lgPZZ24083kFBVTvSfsHQKK5Bv5GdzlqmIr8pvqH++H/gPORqujG
GR/21QKBgDgrQbUwGh4wvOa6H+FJCnnu/PgsFfpR2GDG5mDqJU3jJuVHStDTvQCm
ZI+XVFa5MfqJV3rIQnkDl318OsQWwcViGb3U1qwzMNyWgyp/EP/Sh5w6TAtHEqCZ
KbXQPBKFdqX5yKKcZolxfQICxXZRYM1hKue9SttZBeAUmIXWd9wt
-----END RSA PRIVATE KEY-----
"""

INTERNET_SETTINGS = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

class ProxyController:
    def __init__(self, host: str = "127.0.0.1", port: int = 8889) -> None:
        self.proxy_addr = f"{host}:{port}"
        self.is_enabled = False
        self.original_enable = 0
        self.original_server = ""
        self._record_original_state()

    def _record_original_state(self) -> None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS, 0, winreg.KEY_READ) as key:
                self.original_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                try:
                    self.original_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                except FileNotFoundError:
                    self.original_server = ""
        except Exception:
            self.original_enable = 0
            self.original_server = ""

    def _refresh(self) -> None:
        try:
            internet_set_option = ctypes.windll.wininet.InternetSetOptionW
            internet_set_option(0, 39, 0, 0)
            internet_set_option(0, 37, 0, 0)
        except Exception:
            pass

    def enable(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, self.proxy_addr)
            self._refresh()
            self.is_enabled = True
            return True
        except Exception:
            return False

    def disable(self) -> None:
        if not self.is_enabled:
            return
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, self.original_enable if self.original_enable == 1 else 0)
                if self.original_server:
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, self.original_server)
                else:
                    try:
                        winreg.DeleteValue(key, "ProxyServer")
                    except Exception:
                        pass
            self._refresh()
            self.is_enabled = False
        except Exception:
            pass

def ensure_ca_installed() -> str:
    mitm_dir = os.path.expanduser("~/.mitmproxy")
    os.makedirs(mitm_dir, exist_ok=True)

    cert_path = os.path.join(mitm_dir, "mitmproxy-ca-cert.cer")
    key_path = os.path.join(mitm_dir, "mitmproxy-ca.pem")

    if not os.path.exists(cert_path):
        with open(cert_path, "w", encoding="utf-8") as f:
            f.write(CA_CERT_PEM)

    if not os.path.exists(key_path):
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(CA_KEY_PEM + "\n" + CA_CERT_PEM)

    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        res = subprocess.run(
            ["certutil", "-user", "-verifystore", "Root", "mitmproxy"],
            capture_output=True,
            text=True,
            creationflags=flags,
        )
        if "Certificate is valid" not in res.stdout:
            subprocess.run(["certutil", "-user", "-addstore", "Root", cert_path], creationflags=flags)
    except Exception:
        pass

    return mitm_dir

class TokenCaptureAddon:
    def __init__(self, on_token: Callable[[str], None]) -> None:
        self.on_token = on_token
        self.captured = False

    def request(self, flow: http.HTTPFlow) -> None:
        if self.captured:
            return

        host = flow.request.pretty_host
        if "wuwatappo.kurogames-global.com" not in host:
            return

        token = None
        query_params = parse_qs(urlparse(flow.request.url).query)
        if "token" in query_params:
            token = query_params["token"][0]

        if not token:
            auth = flow.request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth.replace("Bearer ", "").strip()

        if token and not self.captured:
            self.captured = True
            self.on_token(token)

class ProxyTokenService:
    def __init__(self, port: int = 8889) -> None:
        self.port = port
        self.proxy_ctrl = ProxyController(port=port)
        self.is_running = False
        self._master: DumpMaster | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

        atexit.register(self.stop)

    def start(self, on_token_captured: Callable[[str], None], on_status: Callable[[str], None] | None = None) -> bool:
        if self.is_running:
            return True

        if on_status:
            on_status("Đang cài đặt chứng chỉ & kích hoạt Proxy...")

        confdir = ensure_ca_installed()
        if not self.proxy_ctrl.enable():
            if on_status:
                on_status("Không thể thiết lập Proxy hệ thống Windows!")
            return False

        self.is_running = True
        self._loop = asyncio.new_event_loop()
        opts = options.Options(
            listen_host="127.0.0.1",
            listen_port=self.port,
            confdir=confdir,
        )
        self._master = DumpMaster(opts, loop=self._loop)

        def _handle_token(token: str) -> None:
            # Tự động tắt proxy và ngắt master ngay khi bắt được token
            self.stop()
            if on_status:
                on_status("Đã bắt được token! Proxy đã tự động đóng.")
            on_token_captured(token)

        self._master.addons.add(TokenCaptureAddon(_handle_token))

        def _run() -> None:
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._master.run())
            except Exception:
                pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

        if on_status:
            on_status(f"Proxy đang chạy (127.0.0.1:{self.port}). Hãy mở sự kiện Tappo trong game để lấy token.")
        return True

    def stop(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        self.proxy_ctrl.disable()

        if self._master and self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._master.shutdown)
