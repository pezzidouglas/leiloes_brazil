"""Scraper for Milani Leilões (milanileiloes.com.br)

Real estate, vehicles, and machinery auctions based in São Paulo.
Main listing uses query-string pagination and sorting:
  /?searchType=opened&pageNumber=N&pageSize=30&orderBy=endDate:asc
Individual lots: /leilao/{auctionId}/lote/{lotId}
"""
from .base_scraper import BaseScraper
import config


class MilaniLeiloesScraper(BaseScraper):

    # The site is a JS SPA — Selenium is required.
    REQUIRES_SELENIUM = True

    CARD_SELECTORS = (
        "[class*='card-lote'], [class*='lot-card'], "
        "[class*='auction-card'], article[class*='card'], "
        "div[class*='leilao-item'], div[class*='lote-card'], "
        "div[class*='item-lote'], div[class*='product-card'], "
        "div[class*='auction-item']"
    )
    LINK_PATTERNS = ["/leilao/", "/lote/"]

    def __init__(self):
        super().__init__("milani_leiloes", "https://www.milanileiloes.com.br")

    def scrape(self):
        self.logger.info("Scraping Milani Leiloes...")
        try:
            self._scrape_listings()
        except Exception as e:
            self.logger.error(f"Error scraping listings: {e}")

    def _scrape_listings(self):
        page_size = 30
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = (
                f"{self.base_url}/"
                f"?searchType=opened"
                f"&preOrderBy=orderByFirstOpenedOffers"
                f"&pageNumber={page}"
                f"&pageSize={page_size}"
                f"&orderBy=endDate:asc"
            )
            html = self._fetch_with_selenium(
                url,
                wait_selector="[class*='card'], [class*='lote'], [class*='auction'], article",
                wait_timeout=15,
            )
            soup = self._parse_html(html)

            items = self._select_items(
                soup, self.CARD_SELECTORS, self.LINK_PATTERNS
            )
            if not items:
                break

            for item in items:
                auction = self._parse_item(item)
                if auction:
                    self.results.append(auction)

            self.logger.info(f"Page {page}: {len(items)} items")

    def _parse_item(self, item):
        try:
            title_el = item.select_one(
                "h3, h4, h2, [class*='titulo'], [class*='title'], [class*='nome']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                title = self.extract_title_from_element(item)
            if not title:
                return None

            category = self._infer_category(title)

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
                source_url = href if href.startswith("http") else self.base_url + href

            img_el = item.select_one("img[src], img[data-src]")
            image_url = (img_el.get("src") or img_el.get("data-src")) if img_el else None

            type_el = item.select_one("[class*='tipo'], [class*='badge'], [class*='type']")
            auction_type = "Judicial"
            if type_el:
                text = type_el.get_text().lower()
                if "extrajudicial" in text:
                    auction_type = "Extrajudicial"
                elif "venda direta" in text:
                    auction_type = "Venda Direta"

            return {
                "title": title,
                "category": category,
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": "Milani Leiloes",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None

    def _infer_category(self, title):
        return self.infer_category_from_title(title)
