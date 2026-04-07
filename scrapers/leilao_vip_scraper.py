"""Scraper for Leilao VIP / HastaVip (leilaovip.com.br)"""
from .base_scraper import BaseScraper
import config

class LeilaoVipScraper(BaseScraper):
    CATEGORIES = ["imoveis", "materiais", "veiculos", "diversos", "remanescentes"]
    def __init__(self):
        super().__init__("leilao_vip", "https://www.leilaovip.com.br")
    def scrape(self):
        self.logger.info("Scraping Leilao VIP...")
        for cat in self.CATEGORIES:
            try:
                self._scrape_category(cat)
            except Exception as e:
                self.logger.error(f"Error scraping {cat}: {e}")
    def _scrape_category(self, category):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}/leiloes/{category}?page={page}"
            try:
                response = self._fetch(url)
                soup = self._parse_html(response.text)
                items = soup.select(".lot-card, .card, article, .item-lote")
                if not items: break
                for item in items:
                    auction = self._parse_item(item, category)
                    if auction: self.results.append(auction)
            except Exception as e:
                self.logger.warning(f"Page {page} error: {e}")
                break
    def _parse_item(self, item, category):
        try:
            title_el = item.select_one("h3, h4, .titulo, .title")
            title = title_el.get_text(strip=True) if title_el else None
            if not title: return None
            price_el = item.select_one(".preco, .price, .valor")
            price = self.parse_price(price_el.get_text()) if price_el else None
            location_el = item.select_one(".localizacao, .location")
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
                "title": title, "category": self.normalize_category(category),
                "current_bid": price, "minimum_bid": price,
                "auction_date": auction_date, "city": city, "state": state,
                "auction_type": "Judicial", "source": "Leilao VIP",
                "source_url": source_url, "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
