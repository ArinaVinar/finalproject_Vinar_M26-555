import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ParserConfig:
    EXCHANGERATE_API_KEY: str = field(
        default_factory=lambda: os.getenv(
            "EXCHANGERATE_API_KEY", ""
        ).strip()
    )

    COINGECKO_URL: str = (
        "https://api.coingecko.com/api/v3/simple/price"
    )
    EXCHANGERATE_API_URL: str = (
        "https://v6.exchangerate-api.com/v6"
    )

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple[str, ...] = ("BTC", "ETH", "SOL")

    CRYPTO_ID_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }
    )

    REQUEST_TIMEOUT: int = 10

    RATES_FILE_PATH: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "rates.json"
    )
    HISTORY_FILE_PATH: Path = field(
        default_factory=lambda: (
            PROJECT_ROOT / "data" / "exchange_rates.json"
        )
    )


def get_config() -> ParserConfig:
    return ParserConfig()
