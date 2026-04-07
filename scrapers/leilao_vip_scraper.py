"""Scraper for Leilao VIP (leilaovip.com.br)

Real URLs:
  /pesquisa/ with query params: ?estado=N&subclasse=N&ordenacao=N
  /pesquisa/{class}/{state}/{city} positional format
  /evento/anuncio/{slug}-{id} for individual listings

Uses cloudscraper with Selenium fallback.
"""
from .base_scraper import BaseScraper
import config


class LeilaoVipScraper(BaseScraper):

    # State IDs discovered from indexed URLs
    STATE_IDS = {
        "SP": 26, "RJ": 20, "MG": 14, "BA": 5, "PR": 17,
        "RS": 22, "SC": 25, "GO": 9, "PE": 16, "CE": 6,
    }

    def __init__(self):
        super().__init__("leilao_vip", "https://www.leilaovip.com.br")

    def scrape(self):
        self.logger.info("Scraping Leilao VIP...")

        # Scrape the main search page, then by state
        for state_name, state_id in self.STATE_IDS.items():
            try:
                self._scrape_state(state_name, state_id)
            except Exception as e:
                self.logger.error(f"Error scraping state {state_name}: {e}")

    def _scrape_state(self, state_name, state_id):
        url = f"{self.base_url}/pesquisa/?estado={state_id}&ordenacao=1"

        # Try cloudscraper first
        try:
            resp = self._fetch(url)
            html = resp.text
        except Exception:
            self.logger.info(f"cloudscraper blocked for {state_name}, trying Selenium")
            html = self._fetch_with_selenium(
                url,
                wait_selector="[class*='card'], [class*='lote'], [class*='anuncio'], article",
                wait_timeout=15,
            )

        soup = self._parse_html(html)

        items = soup.select(
            "[class*='lot-card'], [class*='card'], article, "
            "[class*='item-lote'], [class*='anuncio-card'], "
            "div[class*='leilao'], div[class*='lote']"
        )
        if not items:
            self.logger.info(f"No items for state {state_name}")
            return

        for item in items:
            auction = self._parse_item(item, state_name)
            if auction:
                self.results.append(auction)

        self.logger.info(f"State {state_name}: {len(items)} items")

    def _parse_item(self, item, state_hint):
        try:
            title_el = item.select_one(
                "h3, h4, [class*='titulo'], [class*='title'], [class*='nome']"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            price_el = item.select_one(
                "[class*='preco'], [class*='price'], [class*='valor'], [class*='lance']"
            )
            price = self.parse_price(price_el.get_text()) if price_el else None

            location_el = item.select_one(
                "[class*='localizacao'], [class*='location'], [class*='cidade'], [class*='local']"
            )
            city, state = self.parse_location(location_el.get_text()) if location_el else (None, None)
            if not state:
                state = state_hint

            date_el = item.select_one(
                "[class*='data'], time, [class*='date'], [class*='prazo']"
            )
            auction_date = self.parse_date(date_el.get_text()) if date_el else None

            link_el = item.select_one("a[href]")
            source_url = None
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href

            img_el = item.select_one("img")
            image_url = img_el.get("src") if img_el else None

            # Try to guess category from title
            title_lower = title.lower() if title else ""
            if any(w in title_lower for w in ["apartamento", "casa", "terreno", "imovel", "sala", "galpao"]):
                category = "Imoveis"
            elif any(w in title_lower for w in ["veiculo", "carro", "moto", "caminhao", "onibus"]):
                category = "Veiculos"
            else:
                category = "Diversos"

            return {
                "title": title,
                "category": category,
                "current_bid": price,
                "minimum_bid": price,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": "Judicial",
                "source": "Leilao VIP",
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception as e:
            self.logger.debug(f"Parse error: {e}")
            return None
