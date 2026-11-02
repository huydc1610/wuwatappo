import sys
import time
from wuwatappo.config import AppConfig
from wuwatappo.services.proxy_token_service import ProxyTokenService
from wuwatappo.storage import Storage

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main() -> None:
    print("=== DỊCH VỤ TỰ ĐỘNG BẮT TOKEN QUA PROXY ===")
    config = AppConfig.load()
    storage = Storage(config)
    proxy_service = ProxyTokenService(port=8889)

    captured_token = None

    def on_captured(token: str) -> None:
        nonlocal captured_token
        captured_token = token
        storage.save_token(token)
        print(f"\n[+] ĐÃ BẮT ĐƯỢC TOKEN: {token[:8]}...")
        print("[+] Proxy đã tự động TẮT và khôi phục cài đặt mạng Windows ban đầu.")

    def on_status(msg: str) -> None:
        print(f"[*] {msg}")

    print("[*] Đang thiết lập proxy...")
    if not proxy_service.start(on_token_captured=on_captured, on_status=on_status):
        print("[!] Không thể bật proxy.")
        return

    print("\n>>> HÃY VÀO GAME VÀ MỞ SỰ KIỆN WUWA TAPPO ĐỂ BẮT TOKEN <<<")
    print(">>> Nhấn Ctrl+C để hủy và tắt proxy bất cứ lúc nào <<<\n")

    try:
        while not captured_token:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[*] Đang hủy và tắt proxy...")
    finally:
        proxy_service.stop()
        print("[*] Hoàn tất.")

if __name__ == "__main__":
    main()
