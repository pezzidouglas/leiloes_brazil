"""Scraper for Frazao Leiloes (frazaoleiloes.com.br)

Real estate focus with bank partnerships (Santander, Itau).
URLs: /sale/searchLot?estado={STATE}&segmento=Residencial&pagina=N
       /lotes/busca/e/{STATE}/{CITY}
"""
from .base_scraper import BaseScraper
import config


class FrazaoLeiloesScraper(BaseScraper):

    SEGMENTS = ["Residencial", "Comercial", "Terreno", "Rural"]
    STATES = ["SP", "RJ", "MG", "BA", "PR", "RS", "SC", "GO", "PE", "CE", "DF"]

    CARD_SELECTORS = (
        "[class*='card-lote'], [class*='lot-card'], "
        "[class*='auction-card'], article[class*='card'], "
        "div[class*='leilao-item'], div[class*='property-card']"
    )
    LINK_PATTERNS = ["/sale/", "/lote/", "/imovel/"]

    def __init__(self):
        super().__init__("frazao_leiloes", "https://www.frazaoleiloes.com.br")

    def scrape(self):
        self.logger.info("Scraping Frazao Leiloes...")
        for state in self.STATES:
            for segment in self.SEGMENTS:
                try:
                    self._scrape_state_segment(state, segment)
                except Exception as e:
                    self.logger.warning(f"Error {state}/{segment}: {e}")

    def _scrape_state_segment(self, state, segment):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}/sale/searchLot?estado={state}&segmento={segment}&pagina={page}"
            try:
                resp = self._fetch(url)
                soup = self._parse_html(resp.text)
            except Exception:
                self.logger.info(f"cloudscraper blocked for {state}/{segment}, trying Selenium")
                html = self._fetch_with_selenium(
                    url,
                    wait_selector="[class*='card'], [class*='lote'], [class*='lot']",
                    wait_timeout=15,
                )
                soup = self._parse_html(html)

            items = self._select_items(
                soup, self.CARD_SELECTORS, self.LINK_PATTERNS
            )
            if not items:
                break

            for item in items:
                auction = self._parse_item(item, state, segment)
                if auction:
                    self.results.append(auction)

            self.logger.info(f"{state}/{segment} page {page}: {len(items)} items")

    def _parse_item(self, item, state, segment):
        try:
            title_el = item.select_one(
                "h3, h4, h2, [class*='titulo'], [class*='title'], [class*='nome']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                title = self.extract_title_from_element(item)
            if not title:
                return None

            price_el = item.select_one(
                "[class*='preco'], [class*='price'], [class*='valor'], [class*='lance']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(
                "[class*='local'], [class*='location'], [class*='cidade'], [class*='endereco']"
            )
            city, state_parsed = self.parse_location(location_el.get_text()) if location_el else (None, None)
            if not state_parsed:
                state_parsed = state

            date_el = item.select_one(
                "[class*='data'], time, [class*='date']"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href

            img_el = item.select_one("img[src], img[data-src]")
            image_url = (img_el.get("src") or img_el.get("data-src")) if img_el else None

            type_el = item.select_one("[class*='tipo'], [class*='badge'], [class*='type']")
            auction_type = "Extrajudicial"
            if type_el and "judicial" in type_el.get_text().lower():
                auction_type = "Judicial"

            return {
                "title": title,
                "category": "Imoveis",
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state_parsed,
                "auction_type": auction_type,
                "source": "Frazao Leiloes",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
