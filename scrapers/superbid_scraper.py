"""Scraper for Superbid Exchange (superbid.net)"""
from scrapers.base_scraper import BaseScraper
import config


class SuperbidScraper(BaseScraper):
    CATEGORIES = {
        "imoveis": 1, "carros-motos": 2, "caminhoes-onibus": 3,
        "maquinas-pesadas": 4, "industrial": 6, "tecnologia": 8,
        "animais": 7, "moveis-decoracao": 9,
    }

    def __init__(self):
        super().__init__("superbid", "https://www.superbid.net")

    def scrape(self):
        self.logger.info("Scraping Superbid Exchange...")
        for cat_slug, cat_id in self.CATEGORIES.items():
            try:
                self._scrape_category(cat_slug, cat_id)
            except Exception as e:
                self.logger.error(f"Error scraping category {cat_slug}: {e}")
        self.logger.info(f"Superbid: collected {len(self.results)} items")

    def _scrape_category(self, cat_slug, cat_id):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}/todos?categoria={cat_slug}&pagina={page}"
            try:
                response = self._fetch(url)
                soup = self._parse_html(response.text)
                items = soup.select("div.card-lote, div.card-item, article.lot-card")
                if not items:
                    break
                for item in items:
                    auction = self._parse_item(item, cat_slug)
                    if auction:
                        self.results.append(auction)
            except Exception as e:
                self.logger.warning(f"Page {page} error for {cat_slug}: {e}")
                break

    def _parse_item(self, item, category_slug):
        try:
            title_el = item.select_one("h3, h4, .card-title, .lot-title")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            price_el = item.select_one(".price, .valor, .lance-atual, .current-bid")
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(".location, .localizacao, .city")
            city, state = (None, None)
            if location_el:
                city, state = self.parse_location(location_el.get_text())

            date_el = item.select_one(".date, .data, .auction-date, time")
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = link_el["href"] if link_el else None
            if source_url and not source_url.startswith("http"):
                source_url = self.base_url + source_url

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
