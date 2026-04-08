"""Scraper for leiloesbrasil.com.br

Real URLs use category paths: /veiculos/, /imoveis/, /diversos/, /materiais/
Individual lots: /lote/{id} or /{category}/lote/{id}
Uses cloudscraper to handle Cloudflare. Falls back to Selenium if needed.
"""
import logging

from .base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class LeiloesBrasilScraper(BaseScraper):

    CATEGORIES = {
        "veiculos": "/veiculos/",
        "imoveis": "/imoveis/",
        "materiais": "/materiais/",
        "diversos": "/diversos/",
    }

    CARD_SELECTORS = (
        "[class*='leilao-item'], [class*='auction-card'], "
        "[class*='card-lote'], [class*='lote-card'], "
        "div[class*='card'], article[class*='lot'], "
        "tr[class*='auction'], li[class*='leilao']"
    )
    LINK_PATTERNS = ["/lote/", "/leilao/"]

    def __init__(self):
        super().__init__("leiloes_brasil", "https://www.leiloesbrasil.com.br")

    def scrape(self):
        logger.info("Starting Leiloes Brasil scraper")
        self.results = []

        for cat_name, cat_path in self.CATEGORIES.items():
            try:
                self._scrape_category(cat_name, cat_path)
            except Exception as e:
                logger.error(f"Error scraping {cat_name}: {e}")

        logger.info(f"Leiloes Brasil: collected {len(self.results)} items")
        return self.results

    def _scrape_category(self, cat_name, cat_path):
        url = f"{self.base_url}{cat_path}"

        # Try cloudscraper first, fall back to Selenium
        try:
            resp = self._fetch(url)
            html = resp.text
        except Exception:
            logger.info(f"cloudscraper blocked for {cat_name}, trying Selenium")
            html = self._fetch_with_selenium(
                url,
                wait_selector="[class*='card'], [class*='lote'], [class*='leilao'], article",
                wait_timeout=15,
            )

        soup = self._parse_html(html)

        items = self._select_items(
            soup, self.CARD_SELECTORS, self.LINK_PATTERNS
        )

        if not items:
            logger.info(f"No items found for {cat_name}")
            return

        for item in items:
            auction = self._parse_item(item, cat_name)
            if auction:
                self.results.append(auction)

        logger.info(f"{cat_name}: {len(items)} items found")

    def _parse_item(self, item, category):
        try:
            title_el = item.select_one(
                "h3, h2, h4, [class*='titulo'], [class*='title'], [class*='card-title']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                title = self.extract_title_from_element(item)
            if not title:
                return None

            desc_el = item.select_one("[class*='descricao'], [class*='description'], p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            bid_el = item.select_one(
                "[class*='preco'], [class*='price'], [class*='valor'], [class*='lance']"
            )
            current_bid = self.parse_price(bid_el.get_text(strip=True) if bid_el else None)

            min_el = item.select_one(
                "[class*='lance-minimo'], [class*='min-bid'], [class*='valor-minimo']"
            )
            minimum_bid = self.parse_price(min_el.get_text(strip=True) if min_el else None)

            date_el = item.select_one(
                "[class*='data'], [class*='date'], time, [class*='auction-date']"
            )
            auction_date = self.parse_date(date_el.get_text(strip=True) if date_el else None)

            loc_el = item.select_one(
                "[class*='local'], [class*='location'], [class*='cidade']"
            )
            city, state = self.parse_location(loc_el.get_text(strip=True) if loc_el else None)

            type_el = item.select_one("[class*='tipo'], [class*='auction-type'], [class*='modalidade']")
            auction_type = type_el.get_text(strip=True) if type_el else "Online"

            link_el = item.select_one("a[href]")
            source_url = ""
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else f"{self.base_url}{href}"

            img_el = item.select_one("img[src]")
            image_url = img_el.get("src", "") if img_el else ""

            return {
                "title": title,
                "description": description,
                "category": self.normalize_category(category),
                "current_bid": current_bid,
                "minimum_bid": minimum_bid,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": "Leiloes Brasil",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception:
            logger.exception("Error parsing Leiloes Brasil item")
            return None
