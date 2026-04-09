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

import cloudscraper
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class BaseScraper(ABC):
    """Abstract base class for auction scrapers."""

    # Subclasses can set this to True to use Selenium instead of cloudscraper
    REQUIRES_SELENIUM = False

    def __init__(self, name, base_url):
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(name)
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False},
        )
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.results = []
        self._driver = None

    def _rate_limit(self):
        delay = config.REQUEST_DELAY + random.uniform(0, 1)
        time.sleep(delay)

    @retry(stop=stop_after_attempt(config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch(self, url, params=None):
        self._rate_limit()
        self.logger.info(f"Fetching: {url}")
        response = self.session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    def _parse_html(self, html_content):
        return BeautifulSoup(html_content, "lxml")

    # --- Selenium helpers for JS-rendered sites ---

    def _get_driver(self):
        """Lazily create a Selenium WebDriver."""
        if self._driver is None:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"--user-agent={random.choice(config.USER_AGENTS)}")
            options.add_argument("--lang=pt-BR")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            try:
                service = Service(ChromeDriverManager().install())
                self._driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                # Fall back to system chromedriver if webdriver-manager fails
                self.logger.warning(f"webdriver-manager failed ({e}), falling back to system chromedriver")
                self._driver = webdriver.Chrome(options=options)
            self._driver.set_page_load_timeout(config.REQUEST_TIMEOUT)
        return self._driver

    def _fetch_with_selenium(self, url, wait_selector=None, wait_timeout=15):
        """Fetch a page using Selenium, optionally waiting for a CSS selector."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self._rate_limit()
        driver = self._get_driver()
        self.logger.info(f"Fetching (Selenium): {url}")
        driver.get(url)

        if wait_selector:
            try:
                WebDriverWait(driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
            except Exception:
                self.logger.warning(f"Timeout waiting for '{wait_selector}' on {url}")

        return driver.page_source

    def _close_driver(self):
        """Close the Selenium WebDriver if open."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    # --- Parsing helpers ---

    @staticmethod
    def parse_price(price_str):
        if not price_str:
            return None
        price_str = str(price_str)
        price_str = price_str.replace("R$", "")
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
        # Remove common prefixes like "1a Praca: " or "2a Praca: "
        date_str = re.sub(r"^\d+a?\s*Pra[cç]a\s*:\s*", "", date_str, flags=re.IGNORECASE)
        date_str = date_str.replace(" as ", " ").replace(" às ", " ")
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
        text = str(location_str).strip()
        # Try "City - ST" or "City/ST" or "City, ST"
        for sep in [" - ", "/", ", "]:
            parts = text.rsplit(sep, 1)
            if len(parts) == 2:
                city = parts[0].strip()
                state = parts[1].strip().upper()
                if len(state) == 2 and state.isalpha():
                    return city, state
        return text, None

    @staticmethod
    def normalize_category(category_str):
        if not category_str:
            return "Diversos"
        key = category_str.lower().strip()
        key = re.sub(r"[^a-z]", "", key)
        return config.CATEGORY_MAP.get(key, "Diversos")

    # --- Adaptive item detection ---

    def _select_items(self, soup, card_selectors, link_patterns=None):
        """Select auction items from soup using card selectors with link-based fallback.

        Args:
            soup: BeautifulSoup object
            card_selectors: CSS selector string for card elements
            link_patterns: list of href substrings to match for fallback
                           (e.g., ['/lote/', '/oferta/'])

        Returns:
            list of BeautifulSoup Tag elements
        """
        # First try the explicit card selectors
        items = soup.select(card_selectors)
        if items:
            return items

        # Fallback: detect items by link URL patterns
        if not link_patterns:
            return []

        seen_hrefs = set()
        seen_containers = set()
        containers = []

        for pattern in link_patterns:
            for a_tag in soup.select(f"a[href*='{pattern}']"):
                href = a_tag.get("href", "")
                if not href or href in seen_hrefs:
                    continue

                seen_hrefs.add(href)

                # Walk up to find the card-like container
                container = self._find_card_container(a_tag)
                container_id = id(container)
                if container_id not in seen_containers:
                    seen_containers.add(container_id)
                    containers.append(container)

        return containers

    @staticmethod
    def _find_card_container(element):
        """Find the closest card-like ancestor of an element."""
        for parent in element.parents:
            if parent.name in ('div', 'article', 'li', 'section', 'tr'):
                # A "card" typically has a few direct child elements
                children_count = len([c for c in parent.children if c.name])
                if children_count >= 2:
                    return parent
        return element.parent

    @staticmethod
    def extract_title_from_element(item):
        """Try multiple strategies to extract a title from an element.

        Tries heading tags, common class patterns, then falls back to
        the first <a> tag with meaningful text.
        """

        def _is_valid_title(text):
            """Return True if text looks like a real title, not a price/date."""
            if not text or len(text) < 3:
                return False
            # Skip text that is purely a price (e.g. "R$ 100.000,00")
            cleaned = re.sub(r"R\$|[\s.,\d]", "", text)
            if not cleaned:
                return False
            return True

        # Strategy 1: heading tags and common title classes
        for selector in [
            "h2", "h3", "h4",
            "[class*='title']", "[class*='titulo']",
            "[class*='nome']", "[class*='name']",
        ]:
            el = item.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if _is_valid_title(text):
                    return text

        # Strategy 2: first <a> with meaningful text
        for a_tag in item.select("a[href]"):
            text = a_tag.get_text(strip=True)
            if _is_valid_title(text) and len(text) >= 5:
                return text

        return None

    @staticmethod
    def infer_category_from_title(title):
        """Infer auction category from item title keywords.

        Returns a normalized category string suitable for the output schema.
        """
        lower = title.lower()
        property_kw = [
            "apartamento", "casa", "terreno", "galpão", "galpao",
            "sala", "loja", "prédio", "predio", "imóvel", "imovel", "sítio", "sitio",
        ]
        vehicle_kw = [
            "carro", "moto", "veículo", "veiculo", "caminhão",
            "caminhao", "ônibus", "onibus", "van", "pickup",
        ]
        machine_kw = [
            "máquina", "maquina", "equipamento", "trator",
            "escavadeira", "empilhadeira",
        ]

        for kw in property_kw:
            if kw in lower:
                return "Imoveis"
        for kw in vehicle_kw:
            if kw in lower:
                return "Veiculos"
        for kw in machine_kw:
            if kw in lower:
                return "Maquinas"
        return "Diversos"

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
        finally:
            self._close_driver()
        return self.results
