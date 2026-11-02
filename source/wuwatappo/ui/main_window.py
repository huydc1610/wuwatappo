import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime

from wuwatappo.config import AppConfig
from wuwatappo.services.api_client import ApiClient, mask_token
from wuwatappo.services.catalog import Catalog
from wuwatappo.services.chest_service import ChestService
from wuwatappo.services.click_service import ClickService
from wuwatappo.services.proxy_token_service import ProxyTokenService
from wuwatappo.services.token_service import TokenService, TokenStatus
from wuwatappo.storage import Storage

class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("WuwaTappo UI EXE — Buff Click & Auto Claim")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Khởi tạo modules và services
        self.config = AppConfig.load()
        self.storage = Storage(self.config)
        self.api_client = ApiClient(self.config)
        self.catalog = Catalog()
        self.token_service = TokenService(self.config, self.storage, self.api_client)
        self.click_service = ClickService(self.api_client)
        self.chest_service = ChestService(self.config, self.storage, self.api_client, self.catalog)
        self.proxy_token_service = ProxyTokenService()

        # Đăng ký callbacks
        self.token_service.on_status_change = self._on_token_status_changed
        self.click_service.on_progress = self._on_click_progress
        self.click_service.on_finished = self._on_click_finished
        self.click_service.on_auth_expired = self._on_auth_expired
        self.chest_service.on_reward_received = self._on_reward_received
        self.chest_service.on_status_change = self._on_chest_status_changed
        self.chest_service.on_auth_expired = self._on_auth_expired

        self._build_ui()
        self._refresh_token_display()
        self._load_rewards_table()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self) -> None:
        # Header Frame
        header = ctk.CTkFrame(self, fg_color="#1e1e2d", corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)

        app_title = ctk.CTkLabel(
            title_box,
            text="WuwaTappo Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        app_title.pack(anchor="w")

        # Cảnh báo rủi ro bắt buộc
        warning_lbl = ctk.CTkLabel(
            header,
            text="⚠️ Cảnh báo: Sử dụng bot liên tục có nguy cơ bị khoá nick. Đóng app official trước khi bật auto claim!",
            text_color="#f39c12",
            font=ctk.CTkFont(size=11),
        )
        warning_lbl.pack(side="left", padx=20, pady=10)

        # Nút Dừng Tất Cả khẩn cấp
        btn_stop_all = ctk.CTkButton(
            header,
            text="🛑 DỪNG TẤT CẢ",
            fg_color="#c0392b",
            hover_color="#e74c3c",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=130,
            height=36,
            command=self.emergency_stop,
        )
        btn_stop_all.pack(side="right", padx=15, pady=10)

        # Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=8)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(10, 5))

        self.tab_click = self.tabview.add("Buff Click")
        self.tab_claim = self.tabview.add("Auto Claim")
        self.tab_rewards = self.tabview.add("Phần Quà")
        self.tab_settings = self.tabview.add("Cài Đặt")
        self.tab_logs = self.tabview.add("Nhật Ký")

        self._build_tab_click()
        self._build_tab_claim()
        self._build_tab_rewards()
        self._build_tab_settings()
        self._build_tab_logs()

        # Status Bar
        self.status_bar = ctk.CTkFrame(self, height=28, corner_radius=0)
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status_token = ctk.CTkLabel(
            self.status_bar,
            text="Token: Chưa có",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_status_token.pack(side="left", padx=15)

        self.lbl_status_click = ctk.CTkLabel(
            self.status_bar,
            text="Buff Click: Đã dừng",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_status_click.pack(side="left", padx=20)

        self.lbl_status_chest = ctk.CTkLabel(
            self.status_bar,
            text="Auto Claim: Đã dừng",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_status_chest.pack(side="left", padx=20)

    # --- TAB BUFF CLICK ---
    def _build_tab_click(self) -> None:
        frame = ctk.CTkFrame(self.tab_click)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(
            frame,
            text="Buff Click Tự Động",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl.pack(anchor="w", padx=20, pady=(20, 5))

        desc = ctk.CTkLabel(
            frame,
            text="Nhập số lượng click cần buff và nhấn Bắt đầu. Hệ thống sẽ tự động gửi request đến server.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        desc.pack(anchor="w", padx=20, pady=(0, 20))

        # Ô nhập số lượng click (Yêu cầu chính)
        input_box = ctk.CTkFrame(frame, fg_color="transparent")
        input_box.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(input_box, text="Số lượng click:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 15))
        self.entry_click_num = ctk.CTkEntry(input_box, width=200, font=ctk.CTkFont(size=14), placeholder_text="Ví dụ: 43926")
        self.entry_click_num.insert(0, str(self.config.default_click_num))
        self.entry_click_num.pack(side="left")

        # Chọn vị trí
        place_box = ctk.CTkFrame(frame, fg_color="transparent")
        place_box.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(place_box, text="Vị trí rương:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 15))
        self.var_click_place = ctk.StringVar(value="left")
        ctk.CTkRadioButton(place_box, text="Trái (left)", variable=self.var_click_place, value="left").pack(side="left", padx=10)
        ctk.CTkRadioButton(place_box, text="Phải (right)", variable=self.var_click_place, value="right").pack(side="left", padx=10)

        # Buttons
        btn_box = ctk.CTkFrame(frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=20)

        self.btn_start_click = ctk.CTkButton(
            btn_box,
            text="🚀 Bắt Đầu Buff Click",
            fg_color="#2980b9",
            hover_color="#3498db",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_start_click,
        )
        self.btn_start_click.pack(side="left", padx=(0, 15))

        self.btn_stop_click = ctk.CTkButton(
            btn_box,
            text="⏹ Dừng",
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._on_stop_click,
        )
        self.btn_stop_click.pack(side="left")

        # Thống kê click
        self.lbl_click_stat = ctk.CTkLabel(
            frame,
            text="Trạng thái: Sẵn sàng | Đã gửi: 0 click",
            font=ctk.CTkFont(size=13),
        )
        self.lbl_click_stat.pack(anchor="w", padx=20, pady=10)

    # --- TAB AUTO CLAIM ---
    def _build_tab_claim(self) -> None:
        frame = ctk.CTkFrame(self.tab_claim)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(
            frame,
            text="Tự Động Mở Rương (Auto Claim)",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl.pack(anchor="w", padx=20, pady=(20, 5))

        desc = ctk.CTkLabel(
            frame,
            text="Tự động kiểm tra và mở rương trái/phải theo chu kỳ định sẵn khi đủ điều kiện.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        desc.pack(anchor="w", padx=20, pady=(0, 20))

        # Switch Bật/Tắt Auto Claim
        self.var_auto_claim = ctk.BooleanVar(value=False)
        self.switch_auto_claim = ctk.CTkSwitch(
            frame,
            text="Bật Auto Claim",
            font=ctk.CTkFont(size=14, weight="bold"),
            variable=self.var_auto_claim,
            command=self._on_toggle_auto_claim,
        )
        self.switch_auto_claim.pack(anchor="w", padx=20, pady=10)

        # Chu kỳ kiểm tra
        interval_box = ctk.CTkFrame(frame, fg_color="transparent")
        interval_box.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(interval_box, text="Chu kỳ kiểm tra (giây):", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 15))
        self.entry_interval = ctk.CTkEntry(interval_box, width=120)
        self.entry_interval.insert(0, str(self.config.check_interval_seconds))
        self.entry_interval.pack(side="left")

        # Chế độ im lặng khi nhận rương (Yêu cầu bắt buộc)
        self.var_silent_reward = ctk.BooleanVar(value=self.config.silent_on_reward)
        self.switch_silent = ctk.CTkSwitch(
            frame,
            text="Im lặng khi nhận rương (Không mở popup thông báo rương)",
            font=ctk.CTkFont(size=13),
            variable=self.var_silent_reward,
            command=self._on_toggle_silent,
        )
        self.switch_silent.pack(anchor="w", padx=20, pady=15)

        # Thống kê rương
        self.lbl_chest_stat = ctk.CTkLabel(
            frame,
            text="Số rương đã mở phiên này: 0 | Trạng thái: Đã dừng",
            font=ctk.CTkFont(size=13),
        )
        self.lbl_chest_stat.pack(anchor="w", padx=20, pady=10)

    # --- TAB PHẦN QUÀ ---
    def _build_tab_rewards(self) -> None:
        top_filter = ctk.CTkFrame(self.tab_rewards, fg_color="transparent")
        top_filter.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_filter, text="Rương:").pack(side="left", padx=5)
        self.opt_place_filter = ctk.CTkOptionMenu(
            top_filter,
            values=["Tất cả", "Trái (left)", "Phải (right)"],
            width=120,
            command=lambda _: self._load_rewards_table(),
        )
        self.opt_place_filter.pack(side="left", padx=5)

        ctk.CTkLabel(top_filter, text="Thời gian:").pack(side="left", padx=5)
        self.opt_date_filter = ctk.CTkOptionMenu(
            top_filter,
            values=["Tất cả", "Hôm nay", "7 ngày qua"],
            width=120,
            command=lambda _: self._load_rewards_table(),
        )
        self.opt_date_filter.pack(side="left", padx=5)

        self.entry_search_reward = ctk.CTkEntry(top_filter, placeholder_text="Tìm kiếm tên quà...", width=160)
        self.entry_search_reward.pack(side="left", padx=10)
        btn_search = ctk.CTkButton(top_filter, text="Tìm", width=60, command=self._load_rewards_table)
        btn_search.pack(side="left")

        btn_refresh = ctk.CTkButton(top_filter, text="🔄 Làm mới", width=80, command=self._load_rewards_table)
        btn_refresh.pack(side="right", padx=5)

        btn_clear = ctk.CTkButton(
            top_filter,
            text="🗑 Xoá lịch sử",
            fg_color="#7f8c8d",
            width=80,
            command=self._clear_rewards_table,
        )
        btn_clear.pack(side="right", padx=5)

        # Bảng danh sách cuộn
        self.rewards_scroll = ctk.CTkScrollableFrame(self.tab_rewards, corner_radius=6)
        self.rewards_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # --- TAB CÀI ĐẶT & TOKEN ---
    def _build_tab_settings(self) -> None:
        frame = ctk.CTkFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(frame, text="Quản Lý Token & Kết Nối", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(anchor="w", padx=20, pady=(20, 10))

        # Token input thủ công
        token_box = ctk.CTkFrame(frame, fg_color="transparent")
        token_box.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(token_box, text="Token thủ công:").pack(anchor="w")
        input_line = ctk.CTkFrame(token_box, fg_color="transparent")
        input_line.pack(fill="x", pady=5)

        self.entry_token = ctk.CTkEntry(input_line, show="*", width=450, placeholder_text="Dán Bearer token vào đây...")
        self.entry_token.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_toggle_eye = ctk.CTkButton(input_line, text="👁", width=40, command=self._toggle_token_visibility)
        self.btn_toggle_eye.pack(side="left", padx=(0, 10))

        btn_save_token = ctk.CTkButton(input_line, text="Lưu & Xác nhận", fg_color="#27ae60", width=120, command=self._on_save_manual_token)
        btn_save_token.pack(side="left")

        # Nút xoá token
        token_act_box = ctk.CTkFrame(frame, fg_color="transparent")
        token_act_box.pack(fill="x", padx=20, pady=10)

        self.lbl_current_token = ctk.CTkLabel(token_act_box, text="Token hiện tại: Chưa có", font=ctk.CTkFont(size=13))
        self.lbl_current_token.pack(side="left")

        btn_delete_token = ctk.CTkButton(
            token_act_box,
            text="Đăng xuất / Xoá token",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=150,
            command=self._on_delete_token,
        )
        btn_delete_token.pack(side="right")

        # Auto Proxy Token Extractor
        ctk.CTkLabel(frame, text="Tự Động Lấy Token Qua Proxy", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(25, 5))
        ctk.CTkLabel(
            frame,
            text="Nhấn Bắt đầu để tự động bật Proxy và cài chứng chỉ. Sau đó vào game mở sự kiện Tappo.\nKhi bắt được token, proxy sẽ TỰ ĐỘNG TẮT ngay lập tức và khôi phục cài đặt mạng.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 10))

        proxy_btn_box = ctk.CTkFrame(frame, fg_color="transparent")
        proxy_btn_box.pack(fill="x", padx=20, pady=5)

        self.btn_start_proxy = ctk.CTkButton(
            proxy_btn_box,
            text="🌐 Bắt Đầu Lấy Token Qua Proxy",
            fg_color="#2980b9",
            hover_color="#3498db",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_start_proxy_token,
        )
        self.btn_start_proxy.pack(side="left", padx=(0, 10))

        self.btn_stop_proxy = ctk.CTkButton(
            proxy_btn_box,
            text="❌ Hủy / Đóng Proxy",
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._on_stop_proxy_token,
        )
        self.btn_stop_proxy.pack(side="left")

        self.lbl_proxy_status = ctk.CTkLabel(
            frame,
            text="Trạng thái Proxy: Đang tắt",
            font=ctk.CTkFont(size=12),
            text_color="#95a5a6",
        )
        self.lbl_proxy_status.pack(anchor="w", padx=20, pady=10)

    # --- TAB NHẬT KÝ ---
    def _build_tab_logs(self) -> None:
        log_box = ctk.CTkFrame(self.tab_logs, fg_color="transparent")
        log_box.pack(fill="x", padx=10, pady=10)

        btn_refresh_log = ctk.CTkButton(log_box, text="🔄 Làm mới log", width=100, command=self._refresh_logs)
        btn_refresh_log.pack(side="left", padx=5)

        btn_clear_log = ctk.CTkButton(log_box, text="🗑 Xoá log", width=80, fg_color="#7f8c8d", command=self._clear_logs)
        btn_clear_log.pack(side="left", padx=5)

        self.txt_logs = ctk.CTkTextbox(self.tab_logs, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_logs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._refresh_logs()

    # --- EVENT HANDLERS ---
    def emergency_stop(self) -> None:
        self.click_service.stop()
        self.chest_service.stop()
        self.var_auto_claim.set(False)
        self.storage.add_log("WARNING", "ĐÃ BẤM DỪNG TẤT CẢ KHẨN CẤP")
        self.lbl_status_click.configure(text="Buff Click: Đã dừng")
        self.lbl_status_chest.configure(text="Auto Claim: Đã dừng")
        self._log_to_view("[EMERGENCY STOP] Toàn bộ tác vụ buff click và auto claim đã dừng!")

    def _on_start_click(self) -> None:
        if self.token_service.status != TokenStatus.CONFIRMED:
            messagebox.showwarning("Thiếu Token", "Vui lòng nhập hoặc xác nhận token trước khi buff click!")
            return

        try:
            val = int(self.entry_click_num.get().strip())
        except ValueError:
            messagebox.showerror("Lỗi nhập liệu", "Số lượng click phải là số nguyên hợp lệ!")
            return

        place = self.var_click_place.get()
        self.click_service.start(total_clicks=val, place=place)
        self.lbl_status_click.configure(text="Buff Click: Đang chạy")
        self.storage.add_log("INFO", f"Bắt đầu buff click: {val} lượt vào rương {place}")

    def _on_stop_click(self) -> None:
        self.click_service.stop()
        self.lbl_status_click.configure(text="Buff Click: Đã dừng")

    def _on_toggle_auto_claim(self) -> None:
        enabled = self.var_auto_claim.get()
        if enabled:
            if self.token_service.status != TokenStatus.CONFIRMED:
                self.var_auto_claim.set(False)
                messagebox.showwarning("Thiếu Token", "Vui lòng nhập hoặc xác nhận token trước khi bật auto claim!")
                return
            try:
                interval = int(self.entry_interval.get().strip())
                self.config.check_interval_seconds = interval
                self.config.save()
            except Exception:
                pass
            self.chest_service.start()
            self.lbl_status_chest.configure(text="Auto Claim: Đang chạy")
            self.storage.add_log("INFO", f"Bật auto claim với chu kỳ {self.config.check_interval_seconds}s")
        else:
            self.chest_service.stop()
            self.lbl_status_chest.configure(text="Auto Claim: Đã dừng")

    def _on_toggle_silent(self) -> None:
        self.config.silent_on_reward = self.var_silent_reward.get()
        self.config.save()

    def _on_save_manual_token(self) -> None:
        token = self.entry_token.get().strip()
        if not token:
            messagebox.showwarning("Trống", "Vui lòng nhập token!")
            return
        if self.token_service.manual_set_token(token):
            self.entry_token.delete(0, "end")
            messagebox.showinfo("Thành công", "Đã lưu và xác nhận token an toàn!")
            self._refresh_token_display()
        else:
            messagebox.showerror("Lỗi", "Định dạng token không hợp lệ!")

    def _on_delete_token(self) -> None:
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xoá token đã lưu và đăng xuất?"):
            self.token_service.delete_token()
            self.emergency_stop()
            self._refresh_token_display()

    def _toggle_token_visibility(self) -> None:
        current = self.entry_token.cget("show")
        if current == "*":
            self.entry_token.configure(show="")
            self.btn_toggle_eye.configure(text="🙈")
        else:
            self.entry_token.configure(show="*")
            self.btn_toggle_eye.configure(text="👁")

    def _on_start_proxy_token(self) -> None:
        def on_captured(token: str) -> None:
            self.after(
                0,
                lambda: self._handle_proxy_captured_token(token),
            )

        def on_status(msg: str) -> None:
            self.after(
                0,
                lambda: self.lbl_proxy_status.configure(text=f"Trạng thái Proxy: {msg}"),
            )

        ok = self.proxy_token_service.start(on_token_captured=on_captured, on_status=on_status)
        if not ok:
            messagebox.showerror("Lỗi", "Không thể khởi động Proxy hoặc cài đặt chứng chỉ!")

    def _on_stop_proxy_token(self) -> None:
        self.proxy_token_service.stop()
        self.lbl_proxy_status.configure(text="Trạng thái Proxy: Đã tắt và khôi phục cài đặt mạng")

    def _handle_proxy_captured_token(self, token: str) -> None:
        self.token_service.manual_set_token(token)
        self._refresh_token_display()
        self.lbl_proxy_status.configure(text="Trạng thái Proxy: Đã bắt được token! Proxy đã tự động tắt.")
        messagebox.showinfo(
            "Bắt Token Thành Công",
            "Đã lấy được token từ game thành công!\nProxy đã tự động tắt và khôi phục cài đặt mạng Windows ban đầu.",
        )

    def _on_token_status_changed(self, status: TokenStatus, masked_token: str) -> None:
        self.after(0, lambda: self._update_token_status_ui(status, masked_token))

    def _update_token_status_ui(self, status: TokenStatus, masked_token: str) -> None:
        self.lbl_status_token.configure(text=f"Token: {status.value}")
        if status == TokenStatus.CONFIRMED:
            self.lbl_current_token.configure(text=f"Token hiện tại: {masked_token} (Đã xác nhận)")
        else:
            self.lbl_current_token.configure(text=f"Token hiện tại: {status.value}")

    def _refresh_token_display(self) -> None:
        status = self.token_service.status
        masked = mask_token(self.token_service.current_token)
        self._update_token_status_ui(status, masked)

    def _on_click_progress(self, sent: int, status_str: str) -> None:
        self.after(
            0,
            lambda: self.lbl_click_stat.configure(
                text=f"Trạng thái: {status_str} | Đã gửi: {sent:,} click"
            ),
        )

    def _on_click_finished(self, msg: str) -> None:
        self.after(
            0,
            lambda: (
                self.lbl_status_click.configure(text="Buff Click: Đã dừng"),
                self._log_to_view(f"[BUFF CLICK] {msg}"),
            ),
        )

    def _on_chest_status_changed(self, status_str: str) -> None:
        self.after(
            0,
            lambda: self.lbl_chest_stat.configure(
                text=f"Số rương đã mở: {self.chest_service.opened_count} | Trạng thái: {status_str}"
            ),
        )

    def _on_reward_received(self, info: dict) -> None:
        self.after(0, lambda: self._handle_new_reward(info))

    def _handle_new_reward(self, info: dict) -> None:
        self.lbl_chest_stat.configure(
            text=f"Số rương đã mở: {self.chest_service.opened_count} | Vừa nhận: {info['asset_name']}"
        )
        self._load_rewards_table()
        self._log_to_view(f"[REWARD] Rương {info['place']}: Nhận {info['asset_name']} (ID: {info['asset_id']})")
        if not self.config.silent_on_reward:
            messagebox.showinfo("Nhận Rương Thành Công", f"Rương {info['place']}:\n{info['asset_name']}")

    def _on_auth_expired(self) -> None:
        self.after(
            0,
            lambda: (
                self.emergency_stop(),
                self.token_service.mark_expired(),
                messagebox.showerror("Hết Hạn", "Token đã hết hạn hoặc bị từ chối bởi server! Vui lòng cập nhật token mới."),
            ),
        )

    def _load_rewards_table(self) -> None:
        for child in self.rewards_scroll.winfo_children():
            child.destroy()

        place_opt = self.opt_place_filter.get()
        place = None
        if "Trái" in place_opt:
            place = "left"
        elif "Phải" in place_opt:
            place = "right"

        date_opt = self.opt_date_filter.get()
        date_filter = None
        if "Hôm nay" in date_opt:
            date_filter = "today"
        elif "7 ngày" in date_opt:
            date_filter = "7days"

        search = self.entry_search_reward.get().strip() or None
        rewards = self.storage.get_rewards(place=place, date_filter=date_filter, search_query=search)

        if not rewards:
            ctk.CTkLabel(self.rewards_scroll, text="Chưa có phần quà nào được ghi nhận.", text_color="gray").pack(pady=20)
            return

        for r in rewards:
            card = ctk.CTkFrame(self.rewards_scroll, fg_color="#2b2b36", corner_radius=6)
            card.pack(fill="x", padx=5, pady=4)

            # Cột trái: thời gian & rương
            col_left = ctk.CTkFrame(card, fg_color="transparent")
            col_left.pack(side="left", padx=10, pady=8)

            badge_color = "#3498db" if r["place"] == "left" else "#9b59b6"
            badge = ctk.CTkLabel(
                col_left,
                text=f"Rương {r['place'].upper()}",
                text_color=badge_color,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            badge.pack(anchor="w")

            time_lbl = ctk.CTkLabel(col_left, text=r["received_at"], font=ctk.CTkFont(size=10), text_color="gray")
            time_lbl.pack(anchor="w")

            # Cột giữa: Tên quà
            col_mid = ctk.CTkFrame(card, fg_color="transparent")
            col_mid.pack(side="left", fill="x", expand=True, padx=15, pady=8)

            name_lbl = ctk.CTkLabel(
                col_mid,
                text=r["asset_name"] or f"Vật phẩm #{r['asset_id']}",
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            name_lbl.pack(anchor="w")

            id_lbl = ctk.CTkLabel(col_mid, text=f"Asset ID: {r['asset_id']}", font=ctk.CTkFont(size=11), text_color="gray")
            id_lbl.pack(anchor="w")

            # Cột phải: Chi phí & Status
            col_right = ctk.CTkFrame(card, fg_color="transparent")
            col_right.pack(side="right", padx=10, pady=8)

            status_lbl = ctk.CTkLabel(col_right, text="Đã xác nhận", text_color="#2ecc71", font=ctk.CTkFont(size=11))
            status_lbl.pack(anchor="e")

    def _clear_rewards_table(self) -> None:
        if messagebox.askyesno("Xác nhận", "Xoá toàn bộ lịch sử phần quà local?"):
            self.storage.clear_rewards()
            self._load_rewards_table()

    def _log_to_view(self, text: str) -> None:
        now_str = datetime.now().strftime("%H:%M:%S")
        self.txt_logs.insert("end", f"[{now_str}] {text}\n")
        self.txt_logs.see("end")

    def _refresh_logs(self) -> None:
        self.txt_logs.delete("1.0", "end")
        logs = self.storage.get_logs(limit=150)
        for log in reversed(logs):
            self.txt_logs.insert("end", f"[{log['created_at']}] [{log['level']}] {log['message']}\n")
        self.txt_logs.see("end")

    def _clear_logs(self) -> None:
        self.storage.clear_logs()
        self._refresh_logs()

    def _on_closing(self) -> None:
        self.emergency_stop()
        self.proxy_token_service.stop()
        self.destroy()

def main() -> None:
    app = MainWindow()
    app.mainloop()

