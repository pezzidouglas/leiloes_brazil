"""Scraper for Mapa do Leilao (mapadoleilao.com.br)

Aggregator with auctions from verified official auctioneers.
URLs: /mapa/estado/{state-slug}, /leiloeiro/{slug}
"""
from .base_scraper import BaseScraper
import config


class MapaDoLeilaoScraper(BaseScraper):

    STATE_SLUGS = {
        "SP": "sao-paulo", "RJ": "rio-de-janeiro", "MG": "minas-gerais",
        "BA": "bahia", "PR": "parana", "RS": "rio-grande-do-sul",
        "SC": "santa-catarina", "GO": "goias", "PE": "pernambuco",
        "CE": "ceara", "DF": "distrito-federal", "PA": "para",
    }

    CARD_SELECTORS = (
        "[class*='card-leilao'], [class*='auction-card'], "
        "[class*='lot-card'], [class*='property-card'], "
        "article[class*='card'], div[class*='leilao-item']"
    )
    LINK_PATTERNS = ["/leilao/", "/leiloeiro/", "/lote/"]

    def __init__(self):
        super().__init__("mapa_do_leilao", "https://www.mapadoleilao.com.br")

    def scrape(self):
        self.logger.info("Scraping Mapa do Leilao (aggregator)...")
        for state_code, state_slug in self.STATE_SLUGS.items():
            try:
                self._scrape_state(state_code, state_slug)
            except Exception as e:
                self.logger.warning(f"Error scraping {state_code}: {e}")

    def _scrape_state(self, state_code, state_slug):
        url = f"{self.base_url}/mapa/estado/{state_slug}"
        try:
            resp = self._fetch(url)
            soup = self._parse_html(resp.text)
        except Exception:
            self.logger.info(f"cloudscraper blocked for {state_code}, trying Selenium")
            html = self._fetch_with_selenium(
                url,
                wait_selector="[class*='card'], [class*='leilao'], [class*='auction'], article",
                wait_timeout=15,
            )
            soup = self._parse_html(html)

        items = self._select_items(
            soup, self.CARD_SELECTORS, self.LINK_PATTERNS
        )
        if not items:
            self.logger.info(f"No items for {state_code}")
            return

        for item in items:
            auction = self._parse_item(item, state_code)
            if auction:
                self.results.append(auction)

        self.logger.info(f"{state_code}: {len(items)} items")

    def _parse_item(self, item, state_hint):
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
            if not state:
                state = state_hint

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

            # Try to infer category from title
            title_lower = title.lower()
            if any(w in title_lower for w in ["apartamento", "casa", "terreno", "imovel", "sala", "galpao", "sitio"]):
                category = "Imoveis"
            elif any(w in title_lower for w in ["carro", "moto", "veiculo", "caminhao", "onibus", "van"]):
                category = "Veiculos"
            elif any(w in title_lower for w in ["maquina", "equipamento", "trator"]):
                category = "Maquinas"
            else:
                category = "Diversos"

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
                "source": "Mapa do Leilao",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
