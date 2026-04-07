"""Scraper for Sodre Santoro (sodresantoro.com.br) - Vehicle Auctions"""
from .base_scraper import BaseScraper
import config

class SodreSantoroScraper(BaseScraper):
    def __init__(self):
        super().__init__("sodre_santoro", "https://www.sodresantoro.com.br")
    def scrape(self):
        self.logger.info("Scraping Sodre Santoro...")
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            try:
                url = f"{self.base_url}/leiloes?page={page}"
                response = self._fetch(url)
                soup = self._parse_html(response.text)
                items = soup.select(".vehicle-card, .lote-card, .card, article")
                if not items: break
                for item in items:
                    auction = self._parse_item(item)
                    if auction: self.results.append(auction)
            except Exception as e:
                self.logger.warning(f"Page {page} error: {e}")
                break
    def _parse_item(self, item):
        try:
            title_el = item.select_one("h3, h4, .titulo, .vehicle-name")
            title = title_el.get_text(strip=True) if title_el else None
            if not title: return None
            price_el = item.select_one(".preco, .price, .lance")
            price = self.parse_price(price_el.get_text()) if price_el else None
            location_el = item.select_one(".patio, .location, .local")
            city, state = self.parse_location(location_el.get_text()) if location_el else (None, None)
            date_el = item.select_one(".data, time")
            auction_date = self.parse_date(date_el.get_text()) if date_el else None
            link_el = item.select_one("a[href]")
            source_url = link_el["href"] if link_el else None
            if source_url and not source_url.startswith("http"):
                source_url = self.base_url + source_url
            img_el = item.select_one("img")
            image_url = img_el.get("src") if img_el else None
            return {
                "title": title, "category": "Veiculos",
                "current_bid": price, "minimum_bid": price,
                "auction_date": auction_date, "city": city, "state": state,
                "auction_type": "Extrajudicial", "source": "Sodre Santoro",
                "source_url": source_url, "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
