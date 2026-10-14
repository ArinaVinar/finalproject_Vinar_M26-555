import argparse
import shlex

from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import User
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_portfolio_summary,
    get_rate,
    login_user,
    register_user,
    sell_currency,
)

current_user: User | None = None


def handle_register(args: argparse.Namespace) -> None:
    try:
        user = register_user(args.username, args.password)
        print(
            f"Пользователь '{user.username}' зарегистрирован "
            f"(id={user.user_id}). Войдите: login --username "
            f"{user.username} --password ****"
        )
    except ValueError as error:
        print(error)


def handle_login(args: argparse.Namespace) -> None:
    global current_user

    try:
        current_user = login_user(args.username, args.password)
        print(f"Вы вошли как '{current_user.username}'")
    except ValueError as error:
        print(error)


def handle_show_portfolio(args):
    if current_user is None:
        print("Сначала выполните вход: login")
        return

    try:
        summary = get_portfolio_summary(current_user)

        table = PrettyTable()
        table.field_names = [
            "Валюта",
            "Баланс",
            "Курс к USD",
            "Стоимость в USD",
        ]

        for wallet in summary["wallets"]:
            table.add_row(
                [
                    wallet["currency"],
                    f"{wallet['balance']:.8f}".rstrip("0").rstrip("."),
                    (
                        f"{wallet['usd_rate']:.6f}"
                        if wallet["usd_rate"] is not None
                        else "н/д"
                    ),
                    (
                        f"{wallet['value_usd']:.2f}"
                        if wallet["value_usd"] is not None
                        else "н/д"
                    ),
                ]
            )

        print(table)
        print(f"Общая стоимость портфеля: ${summary['total_usd']:.2f}")
    except (ValueError, KeyError) as error:
        print(error)


def handle_get_rate(args):
    try:
        result = get_rate(args.from_currency, args.to_currency)
        print(
            f"{result['from_currency']} → {result['to_currency']}: {result['rate']:.8f}"
        )
        print(f"Источник: {result['source']}")
        print(f"Время обновления: {result['updated_at']}")
        print(f"Обратный курс: {1 / result['rate']:.8f}")
    except (
        ValueError,
        KeyError,
        ApiRequestError,
        CurrencyNotFoundError,
        InsufficientFundsError,
    ) as error:
        print(error)


def handle_buy(args):
    if current_user is None:
        print("Сначала выполните вход: login")
        return

    try:
        result = buy_currency(
            current_user,
            args.currency,
            args.amount,
        )
        print(f"Покупка выполнена: {result['amount']:g} {result['currency']}")
        if result["value_usd"] is not None:
            print(f"Стоимость в USD: ${result['value_usd']:.2f}")
        print(f"Новый баланс: {result['balance']:g} {result['currency']}")
    except (
        ValueError,
        KeyError,
        ApiRequestError,
        CurrencyNotFoundError,
        InsufficientFundsError,
    ) as error:
        print(error)

def handle_sell(args):
    if current_user is None:
        print("Сначала выполните вход: login")
        return

    try:
        result = sell_currency(
            current_user,
            args.currency,
            args.amount,
        )
        print(f"Продажа выполнена: {result['amount']:g} {result['currency']}")
        if result["value_usd"] is not None:
            print(f"Стоимость в USD: ${result['value_usd']:.2f}")
        print(f"Остаток: {result['balance']:g} {result['currency']}")
    except (
        ValueError,
        KeyError,
        ApiRequestError,
        CurrencyNotFoundError,
        InsufficientFundsError,
    ) as error:
        print(error)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="valutatrade",
        description="Платформа для управления валютным портфелем",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser(
        "register",
        help="Зарегистрировать пользователя",
    )
    register_parser.add_argument("--username", required=True)
    register_parser.add_argument("--password", required=True)
    register_parser.set_defaults(handler=handle_register)

    login_parser = subparsers.add_parser(
        "login",
        help="Войти в систему",
    )
    login_parser.add_argument("--username", required=True)
    login_parser.add_argument("--password", required=True)
    login_parser.set_defaults(handler=handle_login)

    portfolio_parser = subparsers.add_parser(
        "show-portfolio",
        help="Показать валютный портфель",
    )
    portfolio_parser.set_defaults(handler=handle_show_portfolio)

    rate_parser = subparsers.add_parser(
        "get-rate",
        help="Получить курс валюты",
    )
    rate_parser.add_argument("--from", dest="from_currency", required=True)
    rate_parser.add_argument("--to", dest="to_currency", required=True)
    rate_parser.set_defaults(handler=handle_get_rate)

    buy_parser = subparsers.add_parser(
        "buy",
        help="Купить валюту",
    )
    buy_parser.add_argument("--currency", required=True)
    buy_parser.add_argument("--amount", type=float, required=True)
    buy_parser.set_defaults(handler=handle_buy)

    sell_parser = subparsers.add_parser(
        "sell",
        help="Продать валюту",
    )
    sell_parser.add_argument("--currency", required=True)
    sell_parser.add_argument("--amount", type=float, required=True)
    sell_parser.set_defaults(handler=handle_sell)

    return parser


def run_command(command_line: str) -> None:
    """Парсинг и выполнение одной команды"""

    try:
        args = build_parser().parse_args(shlex.split(command_line))
        args.handler(args)
    except SystemExit:
        print("Не удалось разобрать команду. Проверьте её аргументы.")


def main() -> None:
    """Запуск cli интерфейса"""

    print("ValutaTrade Hub. Для выхода введите exit.")

    while True:
        try:
            command_line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nРабота завершена.")
            break

        if command_line.lower() in {"exit", "quit"}:
            print("Работа завершена.")
            break

        if not command_line:
            continue

        run_command(command_line)


if __name__ == "__main__":
    main()
