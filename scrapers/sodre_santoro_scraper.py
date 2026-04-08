"""Scraper for Sodre Santoro (sodresantoro.com.br)

Real URLs:
  /veiculos/lotes?page=N - vehicles
  /imoveis/lotes?page=N  - real estate
  /materiais/lotes?page=N - materials/equipment

Uses Selenium due to Cloudflare + JS rendering.
"""
from .base_scraper import BaseScraper
import config


class SodreSantoroScraper(BaseScraper):
    REQUIRES_SELENIUM = True

    SEGMENTS = {
        "veiculos": "/veiculos/lotes",
        "imoveis": "/imoveis/lotes",
        "materiais": "/materiais/lotes",
    }

    CARD_SELECTORS = (
        "[class*='vehicle-card'], [class*='lote-card'], "
        "[class*='lot-card'], article[class*='card'], "
        "div[class*='card-lote'], div[class*='auction-card']"
    )
    LINK_PATTERNS = ["/lote/", "/veiculo/", "/imovel/", "/leiloes/"]

    def __init__(self):
        super().__init__("sodre_santoro", "https://www.sodresantoro.com.br")

    def scrape(self):
        self.logger.info("Scraping Sodre Santoro...")
        for segment_name, segment_path in self.SEGMENTS.items():
            try:
                self._scrape_segment(segment_name, segment_path)
            except Exception as e:
                self.logger.error(f"Error scraping {segment_name}: {e}")

    def _scrape_segment(self, segment_name, segment_path):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}{segment_path}?page={page}"
            try:
                html = self._fetch_with_selenium(
                    url,
                    wait_selector="[class*='card'], [class*='lote'], article, [class*='vehicle']",
                    wait_timeout=15,
                )
                soup = self._parse_html(html)

                items = self._select_items(
                    soup, self.CARD_SELECTORS, self.LINK_PATTERNS
                )
                if not items:
                    self.logger.info(f"No items on {segment_name} page {page}")
                    break

                for item in items:
                    auction = self._parse_item(item, segment_name)
                    if auction:
                        self.results.append(auction)

                self.logger.info(f"{segment_name} page {page}: {len(items)} items")

            except Exception as e:
                self.logger.warning(f"{segment_name} page {page} error: {e}")
                break

    def _parse_item(self, item, segment):
        try:
            title_el = item.select_one(
                "h3, h4, [class*='titulo'], [class*='title'], [class*='vehicle-name'], [class*='nome']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                title = self.extract_title_from_element(item)
            if not title:
                return None

            price_el = item.select_one(
                "[class*='preco'], [class*='price'], [class*='lance'], [class*='valor']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(
                "[class*='patio'], [class*='location'], [class*='local'], [class*='cidade']"
            )
            city, state = self.parse_location(location_el.get_text()) if location_el else (None, None)

            date_el = item.select_one(
                "[class*='data'], time, [class*='date'], [class*='auction-date']"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href

            img_el = item.select_one("img[src], img[data-src]")
            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

            category = self.normalize_category(segment)

            return {
                "title": title,
                "category": category,
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": "Extrajudicial",
                "source": "Sodre Santoro",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
