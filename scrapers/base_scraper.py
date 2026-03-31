"""
Base scraper class for all auction site scrapers.
"""
import json
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class BaseScraper(ABC):
    """Abstract base class for auction scrapers."""

    def __init__(self, name, base_url):
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(name)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(config.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.results = []

    def _rate_limit(self):
        delay = config.REQUEST_DELAY + random.uniform(0, 1)
        time.sleep(delay)

    @retry(stop=stop_after_attempt(config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch(self, url, params=None):
        self._rate_limit()
        self.session.headers["User-Agent"] = random.choice(config.USER_AGENTS)
        self.logger.info(f"Fetching: {url}")
        response = self.session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    def _parse_html(self, html_content):
        return BeautifulSoup(html_content, "lxml")

    @staticmethod
    def parse_price(price_str):
        if not price_str:
            return None
        price_str = str(price_str)
        price_str = price_str.replace("R$", "").replace("R\$", "")
        price_str = price_str.replace(".", "").replace(",", ".").strip()
        price_str = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_date(date_str):
        if not date_str:
            return None
        date_str = str(date_str).strip()
        formats = [
            "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d de %B de %Y",
            "%d/%m/%y", "%d-%m-%Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).isoformat()
            except ValueError:
                continue
        return date_str

    @staticmethod
    def parse_location(location_str):
        if not location_str:
            return None, None
        parts = str(location_str).split("-")
        if len(parts) >= 2:
            city = parts[0].strip()
            state = parts[-1].strip().upper()
            if len(state) == 2:
                return city, state
        return location_str.strip(), None

    @staticmethod
    def normalize_category(category_str):
        if not category_str:
            return "Diversos"
        key = category_str.lower().strip()
        key = re.sub(r"[^a-z]", "", key)
        return config.CATEGORY_MAP.get(key, "Diversos")

    @abstractmethod
    def scrape(self):
        pass

    def save_raw(self):
        output_path = config.RAW_DIR / f"{self.name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info(f"Saved {len(self.results)} items to {output_path}")
        return output_path

    def run(self):
        self.logger.info(f"Starting scraper: {self.name}")
        try:
            self.scrape()
            self.save_raw()
            self.logger.info(f"Completed {self.name}: {len(self.results)} items")
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
        return self.results
