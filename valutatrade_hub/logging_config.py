import logging
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> logging.Logger:
    """Настройка журнала логирования"""

    settings = SettingsLoader()

    log_dir = settings.get("LOG_DIR")
    log_file = settings.get("LOG_FILE")

    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(
        getattr(
            logging,
            str(settings.get("LOG_LEVEL", "INFO")).upper(),
            logging.INFO,
        )
    )
    logger.propagate = False

    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        log_file,
        maxBytes=int(settings.get("LOG_MAX_BYTES", 1_000_000)),
        backupCount=int(settings.get("LOG_BACKUP_COUNT", 3)),
        encoding="utf-8",
    )

    handler.setFormatter(
        logging.Formatter(
            settings.get(
                "LOG_FORMAT",
                "%(levelname)s %(asctime)s %(message)s",
            )
        )
    )

    logger.addHandler(handler)
    return logger
