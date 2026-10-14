import logging
import threading

from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger(__name__)


class RatesScheduler:
    def __init__(
        self,
        updater: RatesUpdater | None = None,
        interval_seconds: int = 300,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("интервал_секунд должен быть положительным")

        self.updater = updater or RatesUpdater()
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def run_once(self) -> dict:
        return self.updater.run_update()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="rates-scheduler",
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("Не удалось обновить запланированные тарифы")

            self._stop_event.wait(self.interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 5)
