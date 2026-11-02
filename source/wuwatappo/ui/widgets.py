import customtkinter as ctk
from typing import Callable

class ConfirmTokenDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent: ctk.CTk,
        masked_token: str,
        on_confirm: Callable[[], None],
        on_reject: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.title("Phát hiện Token Mới")
        self.geometry("450x220")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.on_confirm = on_confirm
        self.on_reject = on_reject

        label_title = ctk.CTkLabel(
            self,
            text="🔔 Đã phát hiện token mới ngầm!",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        label_title.pack(pady=(15, 5))

        label_desc = ctk.CTkLabel(
            self,
            text=f"Token: {masked_token}\n\nToken này CHƯA được dùng cho đến khi bạn xác nhận.\nBạn có muốn dùng token này không?",
            font=ctk.CTkFont(size=12),
            justify="center",
        )
        label_desc.pack(pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(10, 15))

        btn_confirm = ctk.CTkButton(
            btn_frame,
            text="Xác nhận dùng",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._confirm,
        )
        btn_confirm.pack(side="left", padx=10)

        btn_reject = ctk.CTkButton(
            btn_frame,
            text="Từ chối / Bỏ qua",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._reject,
        )
        btn_reject.pack(side="left", padx=10)

    def _confirm(self) -> None:
        self.on_confirm()
        self.destroy()

    def _reject(self) -> None:
        self.on_reject()
        self.destroy()

