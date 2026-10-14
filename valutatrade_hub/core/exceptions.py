class InsufficientFundsError(Exception):
    """Исключение, когда на кошельке нет средств"""

    def __init__(
        self,
        available: float,
        required: float,
        code: str,
    ) -> None:
        self.available = available
        self.required = required
        self.code = code
        super().__init__(
            f"Недостаточно средств: доступно {available:g} {code}, "
            f"требуется {required:g} {code}"
        )


class CurrencyNotFoundError(Exception):
    """Исключение, когда код валюты не известен"""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Исключение при ошибке API"""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            f"Ошибка при обращении к внешнему API: {reason}"
        )
