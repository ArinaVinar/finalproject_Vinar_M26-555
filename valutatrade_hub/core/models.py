import hashlib
import secrets
from datetime import datetime


class User:
    """Класс зарегистрированного пользователя"""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str = "",
        salt: str = "",
        registration_date: datetime | None = None,
    ) -> None:
        self._user_id = user_id
        self._username = username
        self._salt = salt or secrets.token_hex(16)
        self._hashed_password = hashed_password
        self._registration_date = registration_date or datetime.now()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def change_password(self, new_password: str) -> None:
        """Хэширует и сохраняет новый пароль"""

        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        self._hashed_password = hashlib.sha256(
            (new_password + self._salt).encode("utf-8")
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверяет соответствует ли указанный пароль"""

        candidate = hashlib.sha256((password + self._salt).encode("utf-8")).hexdigest()
        return secrets.compare_digest(candidate, self._hashed_password)

    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе"""

        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date,
        }


class Wallet:
    """Класс сохранения баланса в одной валюте"""

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        self.currency_code = currency_code.strip().upper()
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополняет кошелёк"""
        self._validate_amount(amount)
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Вывод средств"""

        self._validate_amount(amount)
        if amount > self.balance:
            raise ValueError("Недостаточно средств")
        self.balance -= amount

    @staticmethod
    def _validate_amount(amount: float) -> None:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

    def get_balance_info(self) -> dict:
        """Возвращает информацию о балансе"""

        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
        }


class Portfolio:
    """Класс для управления валютными кошельками"""

    def __init__(
        self,
        user_id: int,
        wallets: dict[str, Wallet] | None = None,
        user: User | None = None,
    ) -> None:
        self._user_id = user_id
        self._user = user
        self._wallets = dict(wallets or {})

    @property
    def user(self) -> User | None:
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """Создать кошелёк"""

        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        code = currency_code.strip().upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк {code} уже существует")

        wallet = Wallet(code)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает кошелёк по коду валюты"""

        code = currency_code.strip().upper()
        try:
            return self._wallets[code]
        except KeyError:
            raise KeyError(f"Кошелёк {code} не найден") from None

    def get_total_value(
        self,
        base_currency: str = "USD",
        exchange_rates: dict[str, float] | None = None,
    ) -> float:
        """Возвращает общую стоимость всех валют"""

        base = base_currency.strip().upper()
        rates = exchange_rates or {}

        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
            else:
                rate = rates.get(f"{code}_{base}")
                if rate is None:
                    raise ValueError(f"Неизвестный курс {code} к {base}")
                total += wallet.balance * rate

        return total
