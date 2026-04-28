from __future__ import annotations

import logging


UVICORN_ERROR_LOGGER_NAME = "uvicorn.error"


def get_logger(name: str = "cycling_trip_planner") -> logging.Logger:
    """
    Centralized logger getter for the app.

    We intentionally return a standard library logger so it integrates with
    uvicorn's default logging handlers in dev.
    """
    # Use uvicorn's configured logger hierarchy so logs show up
    # in the backend terminal without extra configuration.
    return logging.getLogger(f"{UVICORN_ERROR_LOGGER_NAME}.{name}")


def configure_logging(*, level: int = logging.INFO) -> None:
    """
    Configure a basic logging setup for non-uvicorn contexts (tests, scripts).
    Uvicorn will typically configure logging itself.
    """
    root = logging.getLogger()
    if root.handlers:
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

