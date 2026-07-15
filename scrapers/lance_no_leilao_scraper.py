"""Scraper for Lance no Leilão (lancenoleilao.com.br)

Auction management platform handling judicial and bank auctions.
Main listing at /leilao.php with category filtering via query parameters.
"""
from .base_scraper import BaseScraper
import config


class LanceNoLeilaoScraper(BaseScraper):

    CATEGORIES = {
        "imoveis": "imoveis",
        "veiculos": "veiculos",
        "diversos": "diversos",
    }

    CARD_SELECTORS = (
        "[class*='card-lote'], [class*='lot-card'], "
        "[class*='auction-card'], article[class*='card'], "
        "div[class*='leilao-item'], div[class*='lote-item'], "
        "div[class*='item-lote'], tr[class*='lote']"
    )
    LINK_PATTERNS = ["/leilao", "/lote/", "/detalhe/", "/imovel/", "/veiculo/"]

    def __init__(self):
        super().__init__("lance_no_leilao", "https://www.lancenoleilao.com.br")

    def scrape(self):
        self.logger.info("Scraping Lance no Leilao...")
        for cat_name, cat_value in self.CATEGORIES.items():
            try:
                self._scrape_category(cat_name, cat_value)
            except Exception as e:
                self.logger.error(f"Error scraping {cat_name}: {e}")

    def _scrape_category(self, cat_name, cat_value):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}/leilao.php?categoria={cat_value}&pagina={page}"
            try:
                resp = self._fetch(url)
                soup = self._parse_html(resp.text)
            except Exception:
                self.logger.info(f"cloudscraper blocked for {cat_name} p{page}, trying Selenium")
                html = self._fetch_with_selenium(
                    url,
                    wait_selector="[class*='card'], [class*='lote'], table, article",
                    wait_timeout=15,
                )
                soup = self._parse_html(html)

            items = self._select_items(
                soup, self.CARD_SELECTORS, self.LINK_PATTERNS
            )
            if not items:
                break

            for item in items:
                auction = self._parse_item(item, cat_name)
                if auction:
                    self.results.append(auction)

            self.logger.info(f"{cat_name} page {page}: {len(items)} items")

    def _parse_item(self, item, category):
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
            city, state = self.parse_location(location_el.get_text()) if location_el else (None, None)

            date_el = item.select_one(
                "[class*='data'], time, [class*='date'], [class*='prazo']"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + "/" + href.lstrip("/")

            img_el = item.select_one("img[src], img[data-src]")
            image_url = (img_el.get("src") or img_el.get("data-src")) if img_el else None

            type_el = item.select_one("[class*='tipo'], [class*='badge'], [class*='type']")
            auction_type = "Judicial"
            if type_el and "extrajudicial" in type_el.get_text().lower():
                auction_type = "Extrajudicial"

            return {
                "title": title,
                "category": self.normalize_category(category),
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": "Lance no Leilao",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
