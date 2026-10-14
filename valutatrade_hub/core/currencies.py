from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный класс для валют"""

    def __init__(self, name: str, code: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Название валюты не должно быть пустым")

        if (
            not isinstance(code, str)
            or not 2 <= len(code) <= 5
            or not code.isascii()
            or not code.isalpha()
            or code != code.upper()
        ):
            raise ValueError(
                "Код валюты должен содержать 2–5 латинских "
                "букв в верхнем регистре"
            )

        self.name = name.strip()
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает описание валюты"""


class FiatCurrency(Currency):
    """Fiat-валюта, выпущенная страной"""

    def __init__(
        self,
        name: str,
        code: str,
        issuing_country: str,
    ) -> None:
        super().__init__(name, code)

        if (
            not isinstance(issuing_country, str)
            or not issuing_country.strip()
        ):
            raise ValueError("Страна эмиссии не должна быть пустой")

        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    """Криптовалюта со своим алгоритмом"""

    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        super().__init__(name, code)

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("Алгоритм не должен быть пустым")

        if (
            isinstance(market_cap, bool)
            or not isinstance(market_cap, (int, float))
            or market_cap < 0
        ):
            raise ValueError(
                "Капитализация должна быть неотрицательным числом"
            )

        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


_CURRENCIES: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.0e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of Stake", 8.0e10),
}


def get_currency(code: str) -> Currency:
    """Возвращает зарегистрированную валюту по коду"""

    if not isinstance(code, str):
        raise CurrencyNotFoundError(str(code))

    normalized_code = code.strip().upper()

    currency = _CURRENCIES.get(normalized_code)
    if currency is None:
        raise CurrencyNotFoundError(normalized_code)

    return currency


def get_supported_currencies() -> dict[str, Currency]:
    """Возвращает реестр поддерживаемых валют"""

    return _CURRENCIES.copy()
