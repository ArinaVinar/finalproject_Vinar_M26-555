import logging
from collections.abc import Iterable

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import get_config
from valutatrade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger(__name__)


class RatesUpdater:
    def __init__(
        self,
        clients: Iterable[BaseApiClient] | None = None,
        storage: RatesStorage | None = None,
    ) -> None:
        config = get_config()
        self.clients = list(clients) if clients is not None else [
            CoinGeckoClient(config),
            ExchangeRateApiClient(config),
        ]
        self.storage = storage or RatesStorage(
            config.RATES_FILE_PATH,
            config.HISTORY_FILE_PATH,
        )

    def run_update(self, source: str = "all") -> dict:
        source = source.lower()
        allowed = {"all", "coingecko", "exchangerate"}
        if source not in allowed:
            raise ValueError(
                "источник должен быть 'all', 'coingecko' или 'exchangerate'"
            )

        logger.info("Начато обновление ставок; источник=%s", source)
        combined: dict[str, dict] = {}
        failures: list[str] = []

        for client in self.clients:
            client_name = client.source.lower().replace("-", "")
            if source != "all" and source not in client_name:
                continue

            try:
                rates = client.fetch_rates()
                combined.update(rates)
                logger.info(
                    "Ставки получены успешно; источник=%s количество=%d",
                    client.source,
                    len(rates),
                )
            except (ApiRequestError, ValueError, TypeError) as exc:
                failures.append(f"{client.source}: {exc}")
                logger.exception("Ошибка поставщика тарифов: %s", client.source)

        if combined:
            cache = self.storage.save_updates(combined)
        else:
            cache = self.storage.load_cache()

        logger.info(
            "Обновление ставок завершено; обновлено=%d сбоев=%d",
            len(combined),
            len(failures),
        )

        return {
            "updated": len(combined),
            "pairs": sorted(combined),
            "failures": failures,
            "last_refresh": cache.get("last_refresh"),
        }
