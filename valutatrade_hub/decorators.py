import functools
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from valutatrade_hub.logging_config import setup_logging

logger = setup_logging()


def log_action(
    action: str | None = None,
    verbose: bool = False,
) -> Callable:
    """Записывает успешные операции и исключения"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation = (
                action or func.__name__.replace("_currency", "").upper()
            )


            user = kwargs.get("user")
            if user is None and args and func.__name__ in {
                "buy_currency",
                "sell_currency",
            }:
                user = args[0]

            currency = kwargs.get(
                "currency_code",
                kwargs.get("currency", kwargs.get("code", "-")),
            )
            amount = kwargs.get("amount", "-")
            base = kwargs.get("base", "USD")
            rate = kwargs.get("rate", "-")

            if func.__name__ in {"buy_currency", "sell_currency"}:
                if len(args) > 1:
                    currency = kwargs.get("currency", args[1])
                if len(args) > 2:
                    amount = kwargs.get("amount", args[2])

            elif func.__name__ == "get_rate":
                if args:
                    currency = kwargs.get("from_currency", args[0])
                if len(args) > 1:
                    base = kwargs.get("to_currency", args[1])

            context = {
                "username": getattr(
                    user, "username", kwargs.get("username", "-")
                ),
                "user_id": getattr(
                    user, "user_id", kwargs.get("user_id", "-")
                ),
                "currency_code": currency,
                "amount": amount,
                "rate": rate,
                "base": base,
            }

            timestamp = datetime.now(UTC).isoformat()

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                logger.info(
                    "timestamp=%s action=%s username=%r user_id=%r "
                    "currency=%r amount=%r rate=%r base=%r "
                    "result=ERROR error_type=%s error_message=%r",
                    timestamp,
                    operation,
                    context["username"],
                    context["user_id"],
                    context["currency_code"],
                    context["amount"],
                    context["rate"],
                    context["base"],
                    type(exc).__name__,
                    str(exc),
                )
                raise

            logger.info(
                "timestamp=%s action=%s username=%r user_id=%r "
                "currency=%r amount=%r rate=%r base=%r result=OK",
                timestamp,
                operation,
                context["username"],
                context["user_id"],
                context["currency_code"],
                context["amount"],
                context["rate"],
                context["base"],
            )

            if verbose:
                logger.debug(
                    "action=%s function=%s result_type=%s",
                    operation,
                    func.__name__,
                    type(result).__name__,
                )

            return result

        return wrapper

    return decorator
