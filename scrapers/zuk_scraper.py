"""Scraper for Zuk Leiloes (portalzuk.com.br) - Real Estate Focus

Real URLs: /leilao-de-imoveis/u/todos-imoveis/{state}
Uses Selenium because site is JS-rendered behind Cloudflare.
"""
from .base_scraper import BaseScraper
import config
import re


class ZukScraper(BaseScraper):
    REQUIRES_SELENIUM = True

    # Property type URL segments
    PROPERTY_TYPES = ["todos-imoveis"]

    # Top states by auction volume
    STATES = ["sp", "rj", "mg", "ba", "pr", "rs", "sc", "go", "pe", "ce"]

    def __init__(self):
        super().__init__("zuk", "https://www.portalzuk.com.br")

    def scrape(self):
        self.logger.info("Scraping Zuk Leiloes...")
        for state in self.STATES:
            try:
                self._scrape_state(state)
            except Exception as e:
                self.logger.warning(f"Error scraping state {state}: {e}")

    def _scrape_state(self, state):
        url = f"{self.base_url}/leilao-de-imoveis/u/todos-imoveis/{state}"
        try:
            html = self._fetch_with_selenium(
                url,
                wait_selector="[class*='card'], [class*='property'], article, [class*='imovel']",
                wait_timeout=15,
            )
            soup = self._parse_html(html)

            # Try multiple card selectors
            items = soup.select(
                "[class*='property-card'], [class*='card-imovel'], "
                "[class*='lot-item'], article[class*='card'], "
                "div[class*='auction-card'], div[class*='leilao-card']"
            )
            if not items:
                self.logger.info(f"No items for state {state}")
                return

            for item in items:
                auction = self._parse_item(item, state)
                if auction:
                    self.results.append(auction)

            self.logger.info(f"State {state}: {len(items)} items")

        except Exception as e:
            self.logger.warning(f"State {state} error: {e}")

    def _parse_item(self, item, state):
        try:
            title_el = item.select_one(
                "h3, h4, [class*='title'], [class*='titulo'], [class*='nome']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            price_el = item.select_one(
                "[class*='preco'], [class*='price'], [class*='valor'], [class*='lance']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            discount_el = item.select_one(
                "[class*='desconto'], [class*='discount'], [class*='badge']"
            )
            discount = None
            if discount_el:
                match = re.search(r"(\d+)", discount_el.get_text())
                discount = int(match.group(1)) if match else None

            location_el = item.select_one(
                "[class*='localizacao'], [class*='endereco'], [class*='address'], "
                "[class*='location'], [class*='cidade']"
            )
            city, state_code = (None, None)
            if location_el:
                city, state_code = self.parse_location(location_el.get_text())
            if not state_code:
                state_code = state.upper()

            date_el = item.select_one(
                "[class*='data'], time, [class*='date'], [class*='praca']"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href

            img_el = item.select_one("img[src], img[data-src]")
            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

            type_el = item.select_one("[class*='tipo'], [class*='badge'], [class*='type']")
            auction_type = "Judicial"
            if type_el and "extrajudicial" in type_el.get_text().lower():
                auction_type = "Extrajudicial"

            return {
                "title": title,
                "category": "Imoveis",
                "current_bid": price,
                "minimum_bid": price,
                "discount_percentage": discount,
                "auction_date": auction_date,
                "city": city,
                "state": state_code,
                "auction_type": auction_type,
                "source": "Zuk",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
