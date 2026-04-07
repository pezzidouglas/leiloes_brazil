"""Scraper for Sold Leiloes (sold.com.br)

Major platform (since 2008) with general auctions.
URLs: /todas-categorias, /categorias/{slug}, /lote/lista?filter=categoria:{ID}
"""
from .base_scraper import BaseScraper
import config


class SoldScraper(BaseScraper):
    REQUIRES_SELENIUM = True

    CATEGORIES = {
        "imoveis": "/categorias/imoveis",
        "carros-motos": "/categorias/carros-motos",
        "caminhoes-onibus": "/categorias/caminhoes-onibus",
        "maquinas": "/categorias/maquinas-pesadas",
        "industrial": "/categorias/industrial",
        "tecnologia": "/categorias/tecnologia",
    }

    def __init__(self):
        super().__init__("sold", "https://www.sold.com.br")

    def scrape(self):
        self.logger.info("Scraping Sold Leiloes...")
        for cat_name, cat_path in self.CATEGORIES.items():
            try:
                self._scrape_category(cat_name, cat_path)
            except Exception as e:
                self.logger.error(f"Error scraping {cat_name}: {e}")

    def _scrape_category(self, cat_name, cat_path):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}{cat_path}?pageNumber={page}&pageSize=30"
            try:
                html = self._fetch_with_selenium(
                    url,
                    wait_selector="[class*='card'], [class*='lot'], [class*='offer'], article",
                    wait_timeout=15,
                )
                soup = self._parse_html(html)

                items = soup.select(
                    "[class*='card-lote'], [class*='card-item'], "
                    "[class*='lot-card'], [class*='offer-card'], "
                    "article[class*='card'], div[class*='auction-card']"
                )
                if not items:
                    break

                for item in items:
                    auction = self._parse_item(item, cat_name)
                    if auction:
                        self.results.append(auction)

                self.logger.info(f"{cat_name} page {page}: {len(items)} items")

            except Exception as e:
                self.logger.warning(f"{cat_name} page {page} error: {e}")
                break

    def _parse_item(self, item, category):
        try:
            title_el = item.select_one(
                "h3, h4, [class*='title'], [class*='nome'], [class*='name']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            price_el = item.select_one(
                "[class*='price'], [class*='valor'], [class*='lance'], [class*='bid']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(
                "[class*='location'], [class*='local'], [class*='city'], [class*='cidade']"
            )
            city, state = self.parse_location(location_el.get_text()) if location_el else (None, None)

            date_el = item.select_one(
                "[class*='date'], [class*='data'], time"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href

            img_el = item.select_one("img[src]")
            image_url = img_el["src"] if img_el else None

            return {
                "title": title,
                "category": self.normalize_category(category.replace("-", "")),
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": "Corporativo",
                "source": "Sold",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
