# Hướng Dẫn Build & Chạy WuwaTappo UI EXE

## 1. Yêu cầu hệ thống
- Hệ điều hành: Windows 10/11 64-bit.
- Công cụ quản lý môi trường: `uv` (Fast Python package manager).

## 2. Cài đặt môi trường phát triển
```bash
# Đồng bộ môi trường và dependencies
uv sync
```

## 3. Chạy trực tiếp từ mã nguồn
```bash
# Chạy app giao diện CustomTkinter
uv run source/main.py
```

## 4. Đóng gói thành file EXE (Dạng onedir)
```bash
# Thực thi script build PyInstaller
uv run python build_exe.py
```
Sau khi build xong:
- Thư mục phân phối: `dist/WuwaTappo/`
- File thực thi: `dist/WuwaTappo/WuwaTappo.exe`

## 5. Quy tắc an toàn & Lưu ý
- Không chứa token thật trong repo.
- Token được mã hoá cục bộ bằng Fernet key trên máy người dùng.
- Luôn đóng app official trước khi bật tính năng Auto Claim để tránh xung đột rương.

