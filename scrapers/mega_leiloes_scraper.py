"""Scraper for Mega Leiloes (megaleiloes.com.br)"""
from .base_scraper import BaseScraper
import config


class MegaLeiloesScraper(BaseScraper):
    CATEGORIES = ["imoveis", "veiculos", "bens-de-consumo", "bens-industriais", "animais", "produtos-diversos"]

    def __init__(self):
        super().__init__("mega_leiloes", "https://www.megaleiloes.com.br")

    def scrape(self):
        self.logger.info("Scraping Mega Leiloes...")
        for category in self.CATEGORIES:
            try:
                self._scrape_category(category)
            except Exception as e:
                self.logger.error(f"Error scraping {category}: {e}")

    def _scrape_category(self, category):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}/pesquisa?categoria={category}&pagina={page}"
            try:
                response = self._fetch(url)
                soup = self._parse_html(response.text)
                items = soup.select(".leilao-item, .lot-card, .card-lote, article")
                if not items:
                    break
                for item in items:
                    auction = self._parse_item(item, category)
                    if auction:
                        self.results.append(auction)
            except Exception as e:
                self.logger.warning(f"Page {page} error: {e}")
                break

    def _parse_item(self, item, category):
        try:
            title_el = item.select_one("h3, h4, .titulo, .title, .card-title")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            price_el = item.select_one(".preco, .price, .valor, .lance")
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(".localizacao, .location, .endereco")
            city, state = (None, None)
            if location_el:
                city, state = self.parse_location(location_el.get_text())

            date_el = item.select_one(".data, .date, time, .encerramento")
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = link_el["href"] if link_el else None
            if source_url and not source_url.startswith("http"):
                source_url = self.base_url + source_url

            img_el = item.select_one("img[src]")
            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

            type_el = item.select_one(".tipo, .badge, .judicial")
            auction_type = "Judicial" if (type_el and "judicial" in type_el.get_text().lower()) else "Extrajudicial"

            return {
                "title": title,
                "category": self.normalize_category(category.replace("-", "")),
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": "Mega Leiloes",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
