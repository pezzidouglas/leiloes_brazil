"""Scraper for Superbid Exchange (superbid.net)

Superbid is a JavaScript SPA behind Cloudflare. Uses Selenium to render pages.
Real URLs: /todas-ofertas, /categorias/{slug}, /evento/{slug}, /oferta/{slug}
"""
from .base_scraper import BaseScraper
import config


class SuperbidScraper(BaseScraper):
    REQUIRES_SELENIUM = True

    CATEGORIES = {
        "imoveis": "/categorias/imoveis",
        "carros-motos": "/categorias/carros-motos",
        "caminhoes-onibus": "/categorias/caminhoes-onibus",
        "maquinas-pesadas": "/categorias/maquinas-pesadas",
        "industrial": "/categorias/industrial",
        "tecnologia": "/categorias/tecnologia",
        "animais": "/categorias/animais",
    }

    def __init__(self):
        super().__init__("superbid", "https://www.superbid.net")

    def scrape(self):
        self.logger.info("Scraping Superbid Exchange...")
        for cat_slug, cat_path in self.CATEGORIES.items():
            try:
                self._scrape_category(cat_slug, cat_path)
            except Exception as e:
                self.logger.error(f"Error scraping category {cat_slug}: {e}")
        self.logger.info(f"Superbid: collected {len(self.results)} items")

    def _scrape_category(self, cat_slug, cat_path):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}{cat_path}?pageNumber={page}&pageSize=30"
            try:
                # Wait for cards to render - try common SPA card selectors
                html = self._fetch_with_selenium(
                    url,
                    wait_selector="[class*='card'], [class*='lot'], [class*='offer'], article",
                    wait_timeout=15,
                )
                soup = self._parse_html(html)

                # Try multiple possible card selectors (SPA - selectors may vary)
                items = soup.select(
                    "[class*='card-lote'], [class*='card-item'], "
                    "[class*='lot-card'], [class*='offer-card'], "
                    "article[class*='card'], div[class*='auction-card']"
                )
                if not items:
                    self.logger.info(f"No items on {cat_slug} page {page}")
                    break

                for item in items:
                    auction = self._parse_item(item, cat_slug)
                    if auction:
                        self.results.append(auction)

                self.logger.info(f"{cat_slug} page {page}: {len(items)} items")

            except Exception as e:
                self.logger.warning(f"Page {page} error for {cat_slug}: {e}")
                break

    def _parse_item(self, item, category_slug):
        try:
            # Title - try multiple selectors
            title_el = item.select_one(
                "h3, h4, [class*='title'], [class*='nome'], [class*='name']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            # Price
            price_el = item.select_one(
                "[class*='price'], [class*='valor'], [class*='lance'], [class*='bid']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            # Location
            location_el = item.select_one(
                "[class*='location'], [class*='local'], [class*='city'], [class*='cidade']"
            )
            city, state = (None, None)
            if location_el:
                city, state = self.parse_location(location_el.get_text())

            # Date
            date_el = item.select_one(
                "[class*='date'], [class*='data'], time, [class*='prazo']"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            # Link
            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href

            # Image
            img_el = item.select_one("img[src]")
            image_url = img_el["src"] if img_el else None

            return {
                "title": title,
                "category": self.normalize_category(category_slug.replace("-", "")),
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": "Corporativo",
                "source": "Superbid",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
