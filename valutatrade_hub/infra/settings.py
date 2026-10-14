import tomllib
from pathlib import Path
from typing import Any, Self

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SettingsLoader:
    """Синглтон отвечает за настройку приложения"""

    _instance: "SettingsLoader | None" = None
    _initialized = False

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self.__class__._initialized:
            return

        self._config: dict[str, Any] = {
            "DATA_DIR": PROJECT_ROOT / "data",
            "USERS_FILE": PROJECT_ROOT / "data" / "users.json",
            "PORTFOLIOS_FILE": PROJECT_ROOT / "data" / "portfolios.json",
            "RATES_FILE": PROJECT_ROOT / "data" / "rates.json",
            "RATES_TTL_SECONDS": 300,
            "BASE_CURRENCY": "USD",
            "LOG_DIR": PROJECT_ROOT / "logs",
            "LOG_FILE": PROJECT_ROOT / "logs" / "actions.log",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "%(levelname)s %(asctime)s %(message)s",
            "LOG_MAX_BYTES": 1_000_000,
            "LOG_BACKUP_COUNT": 3,
        }

        self._load_project_config()
        self.__class__._initialized = True

    def _load_project_config(self) -> None:
        config_path = PROJECT_ROOT / "pyproject.toml"

        if not config_path.exists():
            return

        with config_path.open("rb") as config_file:
            project_config = tomllib.load(config_file)

        custom_config = (
            project_config.get("tool", {}).get("valutatrade", {})
        )

        for key, value in custom_config.items():
            if key in self._config:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает настройку или дефолтное значение"""

        return self._config.get(key, default)

    def reload(self) -> None:
        """Перезагрузка конфигурации проекта"""

        self.__class__._initialized = False
        self.__class__._instance = None
        new_settings = self.__class__()
        self._config = new_settings._config
        self.__class__._instance = self
        self.__class__._initialized = True
