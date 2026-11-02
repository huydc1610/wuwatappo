import configparser
from dataclasses import dataclass, field
from pathlib import Path
import os

DEFAULT_CHEST_URL = "https://api-wutheringwaves-wuwatappo.kurogames-global.com/api/frontend/chests/open"
DEFAULT_CLICK_URL = "https://api-wutheringwaves-wuwatappo.kurogames-global.com/api/frontend/chests/open"
DEFAULT_ORIGIN = "http://tauri.localhost"
DEFAULT_REFERER = "http://tauri.localhost/"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36 Edg/155.0.0.0"
DEFAULT_GAME_APP_PATH = r"C:\Program Files\WuwaTappoGlobal\WuwaTappo.exe"

@dataclass
class AppConfig:
    chest_open_url: str = DEFAULT_CHEST_URL
    click_url: str = DEFAULT_CLICK_URL
    origin: str = DEFAULT_ORIGIN
    referer: str = DEFAULT_REFERER
    user_agent: str = DEFAULT_USER_AGENT
    game_app_path: str = DEFAULT_GAME_APP_PATH
    default_place: str = "left"
    default_click_num: int = 1000
    check_interval_seconds: int = 60
    silent_on_reward: bool = True
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WuwaTappo")

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config_file_path(self) -> Path:
        return self.data_dir / "config.ini"

    @property
    def db_file_path(self) -> Path:
        return self.data_dir / "wuwatappo.db"

    @property
    def token_file_path(self) -> Path:
        return self.data_dir / "token.enc"

    @property
    def key_file_path(self) -> Path:
        return self.data_dir / "secret.key"

    @classmethod
    def load(cls) -> "AppConfig":
        cfg = cls()
        path = cfg.config_file_path
        if not path.exists():
            cfg.save()
            return cfg

        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")

        if "api" in parser:
            cfg.chest_open_url = parser["api"].get("chest_open_url", cfg.chest_open_url)
            cfg.click_url = parser["api"].get("click_url", cfg.click_url)
            cfg.origin = parser["api"].get("origin", cfg.origin)
            cfg.referer = parser["api"].get("referer", cfg.referer)
            cfg.user_agent = parser["api"].get("user_agent", cfg.user_agent)

        if "app" in parser:
            cfg.game_app_path = parser["app"].get("game_app_path", cfg.game_app_path)

        if "click" in parser:
            cfg.default_place = parser["click"].get("default_place", cfg.default_place)
            cfg.default_click_num = parser["click"].getint("default_click_num", cfg.default_click_num)

        if "chest" in parser:
            cfg.check_interval_seconds = parser["chest"].getint("check_interval_seconds", cfg.check_interval_seconds)
            cfg.silent_on_reward = parser["chest"].getboolean("silent_on_reward", cfg.silent_on_reward)

        return cfg

    def save(self) -> None:
        parser = configparser.ConfigParser()
        parser["api"] = {
            "chest_open_url": self.chest_open_url,
            "click_url": self.click_url,
            "origin": self.origin,
            "referer": self.referer,
            "user_agent": self.user_agent,
        }
        parser["app"] = {
            "game_app_path": self.game_app_path,
        }
        parser["click"] = {
            "default_place": self.default_place,
            "default_click_num": str(self.default_click_num),
        }
        parser["chest"] = {
            "check_interval_seconds": str(self.check_interval_seconds),
            "silent_on_reward": str(self.silent_on_reward).lower(),
        }

        with open(self.config_file_path, "w", encoding="utf-8") as f:
            parser.write(f)

