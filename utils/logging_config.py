"""Logging and optional error tracking.

Logs go to stdout in a single readable line so any host (Streamlit Cloud,
Docker, Render) can collect them. Sentry is only switched on when SENTRY_DSN
is set and the sentry-sdk package is installed.
"""
import logging
import sys

from utils.config import get_setting

_configured = False


def setup_logging():
    global _configured
    if _configured:
        return
    level_name = (get_setting("LOG_LEVEL", "INFO") or "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger("lumi")
    root.setLevel(getattr(logging, level_name, logging.INFO))
    if not root.handlers:
        root.addHandler(handler)
    root.propagate = False
    _init_sentry(root)
    _configured = True


def _init_sentry(logger):
    dsn = get_setting("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            environment=get_setting("APP_ENV", "production"),
            traces_sample_rate=0.0,
            send_default_pii=False,
        )
        logger.info("Error tracking enabled")
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed")
    except Exception:
        logger.exception("Could not start Sentry")


def get_logger(name):
    return logging.getLogger(f"lumi.{name}")


def report_error(logger, message, exc):
    """Log the error and forward it to Sentry when it is enabled."""
    logger.error("%s: %s", message, exc, exc_info=exc)
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except Exception:
        pass
