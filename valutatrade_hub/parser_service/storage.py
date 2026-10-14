import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PAIR_PATTERN = re.compile(r"^[A-Z]{2,5}_[A-Z]{2,5}$")


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_utc(value: datetime | None = None) -> str:
    value = value or utc_now()
    return value.astimezone(UTC).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


class RatesStorage:
    def __init__(
        self,
        rates_path: str | Path,
        history_path: str | Path,
    ) -> None:
        self.rates_path = Path(rates_path)
        self.history_path = Path(history_path)

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Не возможно прочитать JSON {path}: {exc}") from exc

    @staticmethod
    def _atomic_write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_name = file.name
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_name, path)
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)


    def load_cache(self):
        data = self._read_json(
            self.rates_path,
            {"pairs": {}, "last_refresh": None},
        )

        if not isinstance(data, dict):
            raise TypeError(
                f"Недопустимый формат кэша ставок: {self.rates_path}"
            )

        if isinstance(data.get("pairs"), dict):
            data.setdefault("last_refresh", None)
            return data

        metadata_keys = {"source", "last_refresh"}
        pairs = {
            key: value
            for key, value in data.items()
            if key not in metadata_keys
        }

        for pair, item in pairs.items():
            if not isinstance(pair, str) or not PAIR_PATTERN.fullmatch(pair):
                raise TypeError(
                    f"Недопустимый формат пары валют: {pair!r}"
                )
            if not isinstance(item, dict) or "rate" not in item:
                raise TypeError(
                    f"Недопустимая запись курса: {pair}"
                )

        return {
            "pairs": pairs,
            "last_refresh": data.get("last_refresh"),
        }

    def load_history(self) -> list[dict]:
        data = self._read_json(self.history_path, [])
        if not isinstance(data, list):
            raise TypeError(f"Недопустимый формат истории: {self.history_path}")
        return data

    def save_updates(self, updates: dict[str, dict]) -> dict:
        """Проверка обновления, добавление истории и обновление кэша"""

        cache = self.load_cache()
        history = self.load_history()
        now = utc_now()
        timestamp = iso_utc(now)

        for pair, item in updates.items():
            if not PAIR_PATTERN.fullmatch(pair):
                raise ValueError(f"Недопустимая валютная пара: {pair}")

            rate = item.get("rate")
            source = item.get("source")
            if (
                not isinstance(rate, (int, float))
                or isinstance(rate, bool)
                or rate <= 0
                or not source
            ):
                raise ValueError(f"Неверная запись о ставке для {pair}")

            from_currency, to_currency = pair.split("_", maxsplit=1)
            record = {
                "id": f"{pair}_{timestamp}",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": float(rate),
                "timestamp": timestamp,
                "source": source,
                "meta": item.get("meta", {}),
            }
            history.append(record)

            previous = cache["pairs"].get(pair)
            previous_timestamp = previous.get("updated_at") if previous else None
            if not previous_timestamp or timestamp >= previous_timestamp:
                cache["pairs"][pair] = {
                    "rate": float(rate),
                    "updated_at": timestamp,
                    "source": source,
                }

        cache["last_refresh"] = timestamp

        self._atomic_write(self.history_path, history)
        self._atomic_write(self.rates_path, cache)
        return cache
