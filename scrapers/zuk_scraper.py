"""Scraper for Zuk Leiloes (portalzuk.com.br) - Real Estate Focus"""
from scrapers.base_scraper import BaseScraper
import config


class ZukScraper(BaseScraper):
    def __init__(self):
        super().__init__("zuk", "https://www.portalzuk.com.br")

    def scrape(self):
        self.logger.info("Scraping Zuk Leiloes...")
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            try:
                url = f"{self.base_url}/imoveis?pagina={page}"
                response = self._fetch(url)
                soup = self._parse_html(response.text)
                items = soup.select(".property-card, .card-imovel, .lot-item, article.card")
                if not items:
                    break
                for item in items:
                    auction = self._parse_item(item)
                    if auction:
                        self.results.append(auction)
            except Exception as e:
                self.logger.warning(f"Page {page} error: {e}")
                break

    def _parse_item(self, item):
        try:
            title_el = item.select_one("h3, h4, .titulo, .property-title")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None
            price_el = item.select_one(".preco, .price, .valor-lance")
            price = self.parse_price(price_el.get_text()) if price_el else None
            discount_el = item.select_one(".desconto, .discount, .badge-discount")
            discount = None
            if discount_el:
                import re
                match = re.search(r"(\d+)", discount_el.get_text())
                discount = int(match.group(1)) if match else None
            location_el = item.select_one(".localizacao, .endereco, .address")
            city, state = (None, None)
            if location_el:
                city, state = self.parse_location(location_el.get_text())
            date_el = item.select_one(".data, time, .auction-date")
            auction_date = self.parse_date(date_el.get_text()) if date_el else None
            link_el = item.select_one("a[href]")
            source_url = link_el["href"] if link_el else None
            if source_url and not source_url.startswith("http"):
                source_url = self.base_url + source_url
            img_el = item.select_one("img[src], img[data-src]")
            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None
            type_el = item.select_one(".tipo, .badge")
            auction_type = "Judicial"
            if type_el and "extrajudicial" in type_el.get_text().lower():
                auction_type = "Extrajudicial"
            return {
                "title": title, "category": "Imoveis",
                "current_bid": price, "minimum_bid": price,
                "discount_percentage": discount,
                "auction_date": auction_date,
                "city": city, "state": state,
                "auction_type": auction_type, "source": "Zuk",
                "source_url": source_url, "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
