# Project Instructions & Guidelines

## 1. Directory Structure
- `docs/`: Chứa tài liệu kỹ thuật, context và hướng dẫn dự án.
- `agentlog/`: Chứa nhật ký phiên làm việc, tổng hợp thay đổi của agent.
- `source/`: Chứa toàn bộ mã nguồn của dự án (`source/wuwatappo`, `source/main.py`).
- Root level: Môi trường `uv` độc lập (`.venv`, `pyproject.toml`, `uv.lock`), cấu hình gốc.

## 2. Environment & Package Management
- Sử dụng `uv` độc quyền để quản lý môi trường và gói thư viện.
- Môi trường ảo độc lập đặt tại `.venv` ở thư mục gốc.
- Lệnh chạy:
  - Cài đặt / cập nhật dependencies: `uv sync`
  - Thêm thư viện: `uv add <package>`
  - Chạy chương trình: `uv run source/main.py` hoặc `uv run <command>`

## 3. Coding & Communication Rules
- Ngôn ngữ phản hồi: Tiếng Việt.
- Đi thẳng vào code, giải thích ngắn gọn, súc tích.
- Hạn chế comment mã nguồn, chỉ comment các logic phức tạp bằng cụm từ tiếng Việt siêu ngắn.
- Dọn dẹp toàn bộ file test/mock tạm thời sau khi xác minh xong.
- Sau mỗi phiên làm việc hoặc cập nhật mới, ghi log vào `agentlog/`.
