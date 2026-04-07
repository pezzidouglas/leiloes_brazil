"""Scraper for Mega Leiloes (megaleiloes.com.br)

Uses Selenium because the site is JS-rendered behind Cloudflare.
CSS selectors confirmed from multiple open-source GitHub scrapers.
"""
import re
from .base_scraper import BaseScraper
import config


class MegaLeiloesScraper(BaseScraper):
    REQUIRES_SELENIUM = True

    # Real URL segments for categories
    CATEGORIES = {
        "imoveis": "/imoveis",
        "veiculos": "/veiculos",
        "outros": "/outros",
    }

    COOKIE_ACCEPT_SELECTOR = "#adopt-accept-all-button"
    CARDS_SELECTOR = "div.cards-container div[data-key]"

    def __init__(self):
        super().__init__("mega_leiloes", "https://www.megaleiloes.com.br")

    def scrape(self):
        self.logger.info("Scraping Mega Leiloes...")
        self._dismiss_cookies = True
        for cat_name, cat_path in self.CATEGORIES.items():
            try:
                self._scrape_category(cat_name, cat_path)
            except Exception as e:
                self.logger.error(f"Error scraping {cat_name}: {e}")
        self.logger.info(f"Mega Leiloes: collected {len(self.results)} items")

    def _scrape_category(self, cat_name, cat_path):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}{cat_path}?pagina={page}"
            try:
                html = self._fetch_with_selenium(
                    url,
                    wait_selector=self.CARDS_SELECTOR,
                    wait_timeout=15,
                )
                # Dismiss cookie banner on first load
                if self._dismiss_cookies:
                    self._try_dismiss_cookies()
                    self._dismiss_cookies = False

                soup = self._parse_html(html)
                items = soup.select(self.CARDS_SELECTOR)
                if not items:
                    self.logger.info(f"No items on {cat_name} page {page}, stopping")
                    break

                for item in items:
                    auction = self._parse_item(item, cat_name)
                    if auction:
                        self.results.append(auction)

                self.logger.info(f"{cat_name} page {page}: {len(items)} items")

                # Check if there's a next page
                if not soup.select_one("li.next:not(.disabled)"):
                    break

            except Exception as e:
                self.logger.warning(f"{cat_name} page {page} error: {e}")
                break

    def _try_dismiss_cookies(self):
        """Click the cookie accept button if present."""
        try:
            from selenium.webdriver.common.by import By
            driver = self._get_driver()
            btn = driver.find_elements(By.CSS_SELECTOR, self.COOKIE_ACCEPT_SELECTOR)
            if btn:
                btn[0].click()
                import time
                time.sleep(1)
        except Exception:
            pass

    def _parse_item(self, item, category):
        try:
            # Title
            title_el = item.select_one("a.card-title")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            # Detail link
            source_url = None
            if title_el and title_el.get("href"):
                href = title_el["href"]
                source_url = href if href.startswith("http") else self.base_url + href

            # Price (current display price)
            price_el = item.select_one("div.card-price")
            price = self.parse_price(price_el.get_text()) if price_el else None

            # Auction dates
            first_date_el = item.select_one("span.card-first-instance-date")
            second_date_el = item.select_one("span.card-second-instance-date")
            auction_date = None
            if first_date_el:
                auction_date = self.parse_date(first_date_el.get_text())
            elif second_date_el:
                auction_date = self.parse_date(second_date_el.get_text())

            # Auction values (1st and 2nd praca)
            value_els = item.select("span.card-instance-value")
            minimum_bid = None
            if value_els:
                # Last value is typically the 2nd praca (lower) value
                minimum_bid = self.parse_price(value_els[-1].get_text())

            # Status
            status_el = item.select_one("div.card-status")
            status = status_el.get_text(strip=True) if status_el else None

            # Lot number
            lot_el = item.select_one("div.card-number")
            lot_number = lot_el.get_text(strip=True) if lot_el else None

            # Image
            img_el = item.select_one("a.card-image")
            image_url = None
            if img_el:
                image_url = img_el.get("data-bg") or img_el.get("style", "")
                if "url(" in str(image_url):
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", image_url)
                    image_url = match.group(1) if match else None

            # Parse location from title (often "Apartamento 54m2 - Bairro - City/ST")
            city, state = None, None
            if title:
                city, state = self.parse_location(title.split(" - ")[-1] if " - " in title else None)

            # Determine auction type from status/context
            auction_type = "Judicial"
            batch_el = item.select_one("div.batch-type")
            if batch_el:
                text = batch_el.get_text(strip=True).lower()
                if "extrajudicial" in text:
                    auction_type = "Extrajudicial"

            return {
                "title": title,
                "category": self.normalize_category(category),
                "current_bid": price,
                "minimum_bid": minimum_bid or price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": "Mega Leiloes",
                "source_url": source_url,
                "image_url": image_url,
                "lot_number": lot_number,
                "status": status,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
