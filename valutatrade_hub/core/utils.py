import math

from valutatrade_hub.core.currencies import get_currency


def validate_amount(amount: float) -> float:
    """Проверка на положительную сумму"""

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError("Сумма должна быть числом")

    value = float(amount)

    if not math.isfinite(value) or value <= 0:
        raise ValueError("Сумма должна быть положительным числом")

    return value


def validate_currency_code(code: str) -> str:
    """Проверка кода валюты"""

    if not isinstance(code, str):
        raise TypeError("Код валюты должен быть строкой")

    normalized_code = code.strip().upper()

    if not normalized_code:
        raise ValueError("Код валюты не должен быть пустым")

    get_currency(normalized_code)
    return normalized_code


def convert_currency(
    amount: float,
    rate: float,
) -> float:
    """Конвертация суммы по обменному курсу"""

    validated_amount = validate_amount(amount)

    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
        or rate <= 0
    ):
        raise ValueError("Курс должен быть положительным числом")

    return validated_amount * float(rate)
