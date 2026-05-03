"""Logging helpers for structlog."""

from __future__ import annotations

import logging

import structlog


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "rss-news-reader") -> structlog.stdlib.BoundLogger:
    """Return a configured logger."""

    configure_logging()
    return structlog.get_logger(name)
