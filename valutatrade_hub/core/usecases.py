import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from valutatrade_hub.core.models import Portfolio, User, Wallet

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"

STUB_RATES = {
    "EUR_USD": 1.0786,
    "GBP_USD": 1.2650,
    "RUB_USD": 0.01016,
    "BTC_USD": 59337.21,
    "ETH_USD": 3720.0,
}
RATE_CACHE_TTL = timedelta(minutes=5)


def _read_json(path: Path, default: object) -> object:
    """Читает JSON-файл"""

    if not path.exists() or path.stat().st_size == 0:
        return default

    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _write_json(path: Path, data: object) -> None:
    """Пишет в JSON-файл"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _load_users() -> list[dict]:
    """Подгружает данные о пользователях"""

    return _read_json(USERS_FILE, [])


def _load_portfolios() -> list[dict]:
    """Подгружает данные о портфолио"""

    return _read_json(PORTFOLIOS_FILE, [])


def _save_users(users: list[dict]) -> None:
    """Сохраняет пользователей"""

    _write_json(USERS_FILE, users)


def _save_portfolios(portfolios: list[dict]) -> None:
    """Сохраняет портфолио"""

    _write_json(PORTFOLIOS_FILE, portfolios)


def register_user(username: str, password: str) -> User:
    """Регистрирует пользователя и создаёт портфолио"""

    username = username.strip()

    if not username:
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = _load_users()

    if any(item["username"].casefold() == username.casefold() for item in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((item["user_id"] for item in users), default=0) + 1

    user = User(user_id=user_id, username=username)
    user.change_password(password)

    users.append(
        {
            "user_id": user.user_id,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "salt": user.salt,
            "registration_date": user.registration_date.isoformat(),
        }
    )
    _save_users(users)

    portfolios = _load_portfolios()
    portfolios.append({"user_id": user_id, "wallets": {}})
    _save_portfolios(portfolios)

    return user


def login_user(username: str, password: str) -> User:
    """Аутентификация пользователя"""

    for item in _load_users():
        if item["username"].casefold() == username.strip().casefold():
            user = User(
                user_id=item["user_id"],
                username=item["username"],
                hashed_password=item["hashed_password"],
                salt=item["salt"],
            )
            if user.verify_password(password):
                return user
            raise ValueError("Неверный пароль")

    raise ValueError(f"Пользователь '{username}' не найден")


def load_portfolio(user: User) -> Portfolio:
    """Загружает портфолио пользователя"""

    for item in _load_portfolios():
        if item["user_id"] == user.user_id:
            wallets = {
                code: Wallet(code, details["balance"])
                for code, details in item["wallets"].items()
            }
            return Portfolio(user_id=user.user_id, wallets=wallets, user=user)

    portfolio = Portfolio(user_id=user.user_id, user=user)
    save_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio: Portfolio) -> None:
    """Сохраняет портфолио"""

    portfolios = _load_portfolios()
    user_id = portfolio.user_id

    record = {
        "user_id": user_id,
        "wallets": {
            code: {"balance": wallet.balance}
            for code, wallet in portfolio.wallets.items()
        },
    }

    for index, item in enumerate(portfolios):
        if item["user_id"] == user_id:
            portfolios[index] = record
            break
    else:
        portfolios.append(record)

    _save_portfolios(portfolios)


def _get_usd_rate(currency: str) -> float:
    """Возвращает курс валюты в долларах США"""

    if currency == "USD":
        return 1.0

    key = f"{currency}_USD"
    rates = _read_json(RATES_FILE, {})
    cached = rates.get(key)

    if cached:
        updated_at = datetime.fromisoformat(cached["updated_at"])
        now = datetime.now(UTC)

        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)

        if now - updated_at < RATE_CACHE_TTL:
            return float(cached["rate"])

    if key not in STUB_RATES:
        raise ValueError(f"Курс валюты {currency} пока недоступен")

    rate = STUB_RATES[key]
    rates[key] = {
        "rate": rate,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    rates["source"] = "stub"
    rates["last_refresh"] = datetime.now(UTC).isoformat()
    _write_json(RATES_FILE, rates)

    return rate


def get_rate(from_currency: str, to_currency: str) -> dict:
    """Получить обменный курс между двумя валютами"""

    from_currency = from_currency.strip().upper()
    to_currency = to_currency.strip().upper()

    if not from_currency or not to_currency:
        raise ValueError("Укажите обе валюты")

    if from_currency == to_currency:
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": 1.0,
            "updated_at": datetime.now(UTC).isoformat(),
            "source": "stub",
        }

    from_usd = _get_usd_rate(from_currency)
    to_usd = _get_usd_rate(to_currency)
    rate = from_usd / to_usd

    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate,
        "updated_at": datetime.now(UTC).isoformat(),
        "source": "stub",
    }


def get_portfolio_summary(user: User) -> dict:
    """Возвращает кошельки пользователей"""

    portfolio = load_portfolio(user)
    wallets = []

    total_usd = 0.0

    for currency, wallet in portfolio.wallets.items():
        balance = wallet.balance

        try:
            usd_rate = _get_usd_rate(currency)
            value_usd = balance * usd_rate
        except ValueError:
            usd_rate = None
            value_usd = None

        if value_usd is not None:
            total_usd += value_usd

        wallets.append(
            {
                "currency": currency,
                "balance": balance,
                "usd_rate": usd_rate,
                "value_usd": value_usd,
            }
        )

    return {
        "username": user.username,
        "wallets": wallets,
        "total_usd": total_usd,
    }


def buy_currency(user: User, currency: str, amount: float) -> dict:
    """Покупка валюты на указанную стоимость"""

    currency = currency.strip().upper()

    if not currency:
        raise ValueError("Укажите код валюты")

    if amount <= 0:
        raise ValueError("Количество должно быть больше нуля")

    portfolio = load_portfolio(user)
    portfolio.add_currency(currency)
    wallet = portfolio.get_wallet(currency)
    wallet.deposit(amount)
    save_portfolio(portfolio)

    try:
        usd_rate = _get_usd_rate(currency)
        value_usd = amount * usd_rate
    except ValueError:
        usd_rate = None
        value_usd = None

    return {
        "currency": currency,
        "amount": amount,
        "usd_rate": usd_rate,
        "value_usd": value_usd,
        "balance": wallet.balance,
    }


def sell_currency(user: User, currency: str, amount: float) -> dict:
    """Продажа валюты на указанную стоимость"""

    currency = currency.strip().upper()

    if not currency:
        raise ValueError("Укажите код валюты")

    if amount <= 0:
        raise ValueError("Количество должно быть больше нуля")

    portfolio = load_portfolio(user)
    wallet = portfolio.get_wallet(currency)

    if wallet is None:
        raise ValueError(f"У вас нет кошелька {currency}")

    if wallet.balance < amount:
        raise ValueError(
            f"Недостаточно средств: доступно {wallet.balance:g} {currency}"
        )

    wallet.withdraw(amount)
    save_portfolio(portfolio)

    try:
        usd_rate = _get_usd_rate(currency)
        value_usd = amount * usd_rate
    except ValueError:
        usd_rate = None
        value_usd = None

    return {
        "currency": currency,
        "amount": amount,
        "usd_rate": usd_rate,
        "value_usd": value_usd,
        "balance": wallet.balance,
    }
