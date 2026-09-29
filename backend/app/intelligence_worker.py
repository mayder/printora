from __future__ import annotations

import logging
import os
import signal
import threading

from app.config import get_settings
from app.modules.administration.intelligence import IntelligenceRepository


LOGGER = logging.getLogger("printora.intelligence")


def main() -> None:
    logging.basicConfig(level=os.environ.get("PRINTORA_LOG_LEVEL", "INFO"))
    stopped = threading.Event()

    def stop(_signum, _frame) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    repository = IntelligenceRepository(get_settings().database_path)
    repository.ensure_schema()
    while not stopped.is_set():
        result = repository.process_pending(100)
        if result["processed"] == 0:
            stopped.wait(1.0)
        else:
            LOGGER.info("analytics_processed=%s", result["processed"])


if __name__ == "__main__":
    main()
