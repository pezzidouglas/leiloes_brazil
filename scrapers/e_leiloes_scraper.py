"""Scraper for E-Leiloes (e-leiloes.com.br)

Large platform handling Federal Police seizure auctions and more.
URLs: /lojas?page=N&tipoLeilao=veiculos, /eventos/leilao/{ID}/{SLUG}
"""
from .base_scraper import BaseScraper
import config


class ELeiloesScraper(BaseScraper):

    SEGMENTS = {
        "veiculos": "/lojas?tipoLeilao=veiculos",
        "imoveis": "/lojas?tipoLeilao=imoveis",
        "agro": "/lojas?tipoLeilao=agro",
        "maquinas": "/lojas?tipoLeilao=maquinas",
    }

    def __init__(self):
        super().__init__("e_leiloes", "https://www.e-leiloes.com.br")

    def scrape(self):
        self.logger.info("Scraping E-Leiloes...")
        for seg_name, seg_path in self.SEGMENTS.items():
            try:
                self._scrape_segment(seg_name, seg_path)
            except Exception as e:
                self.logger.error(f"Error scraping {seg_name}: {e}")

    def _scrape_segment(self, seg_name, seg_path):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}{seg_path}&page={page}"
            try:
                resp = self._fetch(url)
                soup = self._parse_html(resp.text)
            except Exception:
                self.logger.info(f"cloudscraper blocked for {seg_name} p{page}, trying Selenium")
                html = self._fetch_with_selenium(
                    url,
                    wait_selector="[class*='card'], [class*='lote'], article",
                    wait_timeout=15,
                )
                soup = self._parse_html(html)

            items = soup.select(
                "[class*='card-lote'], [class*='lot-card'], "
                "[class*='auction-card'], article[class*='card'], "
                "div[class*='leilao-item'], div[class*='product-card']"
            )
            if not items:
                break

            for item in items:
                auction = self._parse_item(item, seg_name)
                if auction:
                    self.results.append(auction)

            self.logger.info(f"{seg_name} page {page}: {len(items)} items")

    def _parse_item(self, item, segment):
        try:
            title_el = item.select_one(
                "h3, h4, h2, [class*='titulo'], [class*='title'], [class*='nome']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            price_el = item.select_one(
                "[class*='preco'], [class*='price'], [class*='valor'], [class*='lance']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(
                "[class*='local'], [class*='location'], [class*='cidade'], [class*='endereco']"
            )
            city, state = self.parse_location(location_el.get_text()) if location_el else (None, None)

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

            return {
                "title": title,
                "category": self.normalize_category(segment),
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": "Judicial",
                "source": "E-Leiloes",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
