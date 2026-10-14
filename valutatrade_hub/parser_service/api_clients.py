from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig, get_config


class BaseApiClient(ABC):
    source = "unknown"

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or get_config()

    @abstractmethod
    def fetch_rates(self) -> dict[str, dict[str, Any]]:
        """Коэффициенты возврата задаются по парам"""

    def _get_json(self, url: str, params: dict | None = None) -> tuple[dict, dict]:
        started = perf_counter()
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            request_ms = round((perf_counter() - started) * 1000, 2)
            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, dict):
                raise TypeError("Ответ API должен быть объектом JSON")

            meta = {
                "raw_id": response.headers.get("X-Request-Id"),
                "request_ms": request_ms,
                "status_code": response.status_code,
                "etag": response.headers.get("ETag"),
            }
            return payload, meta
        except (requests.RequestException, ValueError) as exc:
            raise ApiRequestError(
                f"{self.source}: не удалось выполнить анализ запроса: {exc}"
            ) from exc


class CoinGeckoClient(BaseApiClient):
    source = "CoinGecko"

    def fetch_rates(self) -> dict[str, dict[str, Any]]:
        params = {
            "ids": ",".join(self.config.CRYPTO_ID_MAP.values()),
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }
        payload, meta = self._get_json(self.config.COINGECKO_URL, params)

        result: dict[str, dict[str, Any]] = {}
        base = self.config.BASE_CURRENCY.upper()

        for code, coin_id in self.config.CRYPTO_ID_MAP.items():
            coin_data = payload.get(coin_id)
            if not isinstance(coin_data, dict):
                continue

            rate = coin_data.get(base.lower())
            if (
                    isinstance(rate, (int, float))
                    and not isinstance(rate, bool)
                    and rate > 0
            ):
                pair = f"{code.upper()}_{base}"
                result[pair] = {
                    "rate": float(rate),
                    "source": self.source,
                    "meta": dict(meta),
                }

        if not result:
            raise ApiRequestError("CoinGecko вернул недействительные тарифы")

        return result


class ExchangeRateApiClient(BaseApiClient):
    source = "ExchangeRate-API"

    def fetch_rates(self) -> dict[str, dict[str, Any]]:
        key = self.config.EXCHANGERATE_API_KEY
        if not key:
            raise ApiRequestError(
                "EXCHANGERATE_API_KEY не задан в окружающей среде"
            )

        base = self.config.BASE_CURRENCY.upper()
        url = f"{self.config.EXCHANGERATE_API_URL}/{key}/latest/{base}"
        payload, meta = self._get_json(url)

        if payload.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API вернул неудачный результат: "
                f"{payload.get('error-type', 'unknown error')}"
            )

        rates = payload.get("conversion_rates")
        if not isinstance(rates, dict):
            raise ApiRequestError("ExchangeRate-API ответ не имеет значения conversion_rates")

        result: dict[str, dict[str, Any]] = {}

        for code in self.config.FIAT_CURRENCIES:
            if code.upper() == base:
                continue

            base_to_foreign = rates.get(code.upper())
            if (
                isinstance(base_to_foreign, (int, float))
                and not isinstance(base_to_foreign, bool)
                and base_to_foreign > 0
            ):
                pair = f"{code.upper()}_{base}"
                result[pair] = {
                    "rate": 1.0 / float(base_to_foreign),
                    "source": self.source,
                    "meta": {
                        **meta,
                        "raw_id": payload.get("time_last_update_utc"),
                    },
                }

        if not result:
            raise ApiRequestError("ExchangeRate-API возвращены недействительные фиатные курсы")

        return result
