import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def build() -> None:
    root = Path(__file__).parent.resolve()
    main_script = root / "source" / "main.py"
    dist_dir = root / "dist"
    build_dir = root / "build"

    print("=== BẮT ĐẦU ĐÓNG GÓI WUWATAPPO UI EXE (ONEDIR) ===")
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "WuwaTappo",
        "--collect-all",
        "customtkinter",
        "--paths",
        str(root / "source"),
        str(main_script),
    ]

    print("Lệnh chạy:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=root)
    if res.returncode == 0:
        print("\n=== ĐÓNG GÓI THÀNH CÔNG ===")
        print(f"Thư mục EXE: {dist_dir / 'WuwaTappo'}")
        print(f"File chạy: {dist_dir / 'WuwaTappo' / 'WuwaTappo.exe'}")
    else:
        print(f"\n[LỖI] Build thất bại với mã: {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
