import json
from pathlib import Path
from typing import Any, Self

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Синглтон абстракция хранилища JSON"""

    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        settings = SettingsLoader()
        self._paths = {
            "users": Path(settings.get("USERS_FILE")),
            "portfolios": Path(settings.get("PORTFOLIOS_FILE")),
            "rates": Path(settings.get("RATES_FILE")),
        }
        self._initialized = True

    def read_json(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """Читает JSON"""

        path = self._get_path(name)

        if not path.exists():
            return default

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                f"Не удалось прочитать {path}: {exc}"
            ) from exc

    def write_json(self, name: str, data: Any) -> None:
        """Пишет в JSON"""

        path = self._get_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(path.suffix + ".tmp")

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
                file.write("\n")

            temporary_path.replace(path)
        except OSError as exc:
            raise RuntimeError(
                f"Не удалось сохранить {path}: {exc}"
            ) from exc
        finally:
            if temporary_path.exists():
                temporary_path.unlink(missing_ok=True)

    def _get_path(self, name: str) -> Path:
        try:
            return self._paths[name]
        except KeyError as exc:
            raise ValueError(
                f"Неизвестное JSON-хранилище: {name}"
            ) from exc
