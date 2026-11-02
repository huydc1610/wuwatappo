import contextlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from cryptography.fernet import Fernet
from wuwatappo.config import AppConfig

class Storage:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._key: bytes | None = None
        self._init_db()

    def _get_cipher(self) -> Fernet:
        key_file = self.config.key_file_path
        if not key_file.exists():
            new_key = Fernet.generate_key()
            key_file.write_bytes(new_key)
            self._key = new_key
        elif self._key is None:
            self._key = key_file.read_bytes()
        return Fernet(self._key)

    def save_token(self, token: str) -> None:
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(token.strip().encode("utf-8"))
        self.config.token_file_path.write_bytes(encrypted)

    def load_token(self) -> str | None:
        token_file = self.config.token_file_path
        if not token_file.exists():
            return None
        try:
            cipher = self._get_cipher()
            decrypted = cipher.decrypt(token_file.read_bytes())
            return decrypted.decode("utf-8")
        except Exception:
            return None

    def delete_token(self) -> None:
        token_file = self.config.token_file_path
        if token_file.exists():
            token_file.unlink()

    @contextlib.contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.config.db_file_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    received_at TEXT NOT NULL,
                    place TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    asset_name TEXT,
                    cost INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    raw_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_reward(
        self,
        place: str,
        asset_id: str,
        asset_name: str | None = None,
        cost: int = 0,
        status: str = "confirmed",
        raw_json: str | None = None,
    ) -> int:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO rewards (received_at, place, asset_id, asset_name, cost, status, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (now_str, place, asset_id, asset_name, cost, status, raw_json),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_rewards(
        self,
        place: str | None = None,
        date_filter: str | None = None,
        search_query: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM rewards WHERE 1=1"
        params: list[Any] = []

        if place and place.lower() in ("left", "right"):
            query += " AND place = ?"
            params.append(place.lower())

        if date_filter == "today":
            today_str = datetime.now().strftime("%Y-%m-%d")
            query += " AND received_at LIKE ?"
            params.append(f"{today_str}%")
        elif date_filter == "7days":
            query += " AND received_at >= datetime('now', '-7 days')"

        if search_query:
            query += " AND (asset_name LIKE ? OR asset_id LIKE ?)"
            params.append(f"%{search_query}%")
            params.append(f"%{search_query}%")

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_rewards(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rewards")
            conn.commit()

    def add_log(self, level: str, message: str) -> None:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO session_logs (created_at, level, message) VALUES (?, ?, ?)",
                (now_str, level.upper(), message),
            )
            conn.commit()

    def get_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM session_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_logs(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session_logs")
            conn.commit()
