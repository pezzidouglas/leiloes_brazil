"""Scraper for Grupo Lance (grupolance.com.br)

Nationwide auction platform handling judicial, extrajudicial, and
trabalhista (labor-court) auctions.
Listing URL: /?lotes=1&pagina=N&imoveis=1&veiculos=1&sort=data_inicio
Category pages: /leiloes/judiciais, /leiloes/extrajudiciais
"""
from .base_scraper import BaseScraper
import config


class GrupoLanceScraper(BaseScraper):

    SEGMENTS = {
        "judiciais": "/leiloes/judiciais",
        "extrajudiciais": "/leiloes/extrajudiciais",
    }

    CARD_SELECTORS = (
        "[class*='card-lote'], [class*='lot-card'], "
        "[class*='auction-card'], article[class*='card'], "
        "div[class*='leilao-item'], div[class*='lote-card'], "
        "div[class*='item-lote'], div[class*='lote-item']"
    )
    LINK_PATTERNS = ["/lote/", "/leilao/", "/detalhe/"]

    def __init__(self):
        super().__init__("grupo_lance", "https://www.grupolance.com.br")

    def scrape(self):
        self.logger.info("Scraping Grupo Lance...")
        for seg_name, seg_path in self.SEGMENTS.items():
            try:
                self._scrape_segment(seg_name, seg_path)
            except Exception as e:
                self.logger.error(f"Error scraping {seg_name}: {e}")

    def _scrape_segment(self, seg_name, seg_path):
        for page in range(1, config.MAX_PAGES_PER_SOURCE + 1):
            url = f"{self.base_url}{seg_path}?pagina={page}"
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

            items = self._select_items(
                soup, self.CARD_SELECTORS, self.LINK_PATTERNS
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

            # Determine auction type from the segment name
            if "extrajudicial" in segment:
                auction_type = "Extrajudicial"
            else:
                auction_type = "Judicial"

            # Override with badge info if available
            type_el = item.select_one("[class*='tipo'], [class*='badge'], [class*='type']")
            if type_el:
                text = type_el.get_text().lower()
                if "extrajudicial" in text:
                    auction_type = "Extrajudicial"
                elif "trabalhista" in text:
                    # Labor-court auctions are a sub-type of judicial auctions
                    auction_type = "Judicial"
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
                "source": "Grupo Lance",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None

    def _infer_category(self, title):
        return self.infer_category_from_title(title)
