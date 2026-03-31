"""
Abstract base class for all auction scrapers.
"""

import abc
import json
import logging
import os
import random
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

import config

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """Base class providing common functionality for auction scrapers."""

    SOURCE_NAME: str = "base"
    BASE_URL: str = ""

    def __init__(self):
        self.session = requests.Session()
        self._rotate_user_agent()
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.results: list[dict] = []

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def _rotate_user_agent(self) -> None:
        ua = random.choice(config.USER_AGENTS)
        self.session.headers.update({"User-Agent": ua})

    def _rate_limit(self) -> None:
        time.sleep(config.REQUEST_DELAY)

    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _get(self, url: str, **kwargs) -> requests.Response:
        self._rotate_user_agent()
        self._rate_limit()
        kwargs.setdefault("timeout", config.TIMEOUT)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def scrape(self) -> list[dict]:
        """Scrape auction data and return a list of dicts."""

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_raw(self, data: list[dict] | None = None) -> str:
        data = data if data is not None else self.results
        os.makedirs(config.RAW_DIR, exist_ok=True)
        path = os.path.join(config.RAW_DIR, f"{self.SOURCE_NAME}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, default=str)
        logger.info("Saved %d items to %s", len(data), path)
        return path

    # ------------------------------------------------------------------
    # Parsing utilities
    # ------------------------------------------------------------------
    @staticmethod
    def parse_price(text: str | None) -> float | None:
        """Parse Brazilian currency string (e.g. 'R$ 1.234.567,89') to float."""
        if not text:
            return None
        cleaned = re.sub(r"[^\d,.]", "", text)
        # Brazilian format uses '.' as thousands separator and ',' as decimal
        if "," in cleaned:
            parts = cleaned.rsplit(",", 1)
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1] if len(parts) > 1 else "0"
            cleaned = f"{integer_part}.{decimal_part}"
        else:
            cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    @staticmethod
    def parse_date(text: str | None) -> str | None:
        """Parse common Brazilian date formats to ISO-8601 string."""
        if not text:
            return None
        text = text.strip()
        formats = [
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt).isoformat()
            except ValueError:
                continue
        return text  # return as-is if unparsable

    @staticmethod
    def parse_location(text: str | None) -> tuple[str | None, str | None]:
        """Try to split 'City - UF' or 'City/UF' into (city, state)."""
        if not text:
            return None, None
        text = text.strip()
        for sep in [" - ", "/", ", "]:
            if sep in text:
                parts = text.rsplit(sep, 1)
                city = parts[0].strip()
                state = parts[1].strip().upper()
                if len(state) == 2 and state in config.BRAZILIAN_STATES:
                    return city, state
        return text, None
