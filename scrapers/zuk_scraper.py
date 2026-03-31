"""
Scraper for portalzuk.com.br – focused on judicial and extrajudicial
real-estate auctions with discount percentages.
"""

import logging
import re

from scrapers.base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class ZukScraper(BaseScraper):
    SOURCE_NAME = "zuk"
    BASE_URL = "https://www.portalzuk.com.br"
    SEARCH_URL = f"{BASE_URL}/imoveis"

    def scrape(self) -> list[dict]:
        logger.info("Starting Zuk scraper")
        self.results = []

        for page in range(1, config.MAX_PAGES + 1):
            try:
                url = f"{self.SEARCH_URL}?pagina={page}"
                resp = self._get(url)
                soup = self._soup(resp.text)
                items = soup.select(
                    "div.property-card, div.card-imovel, div.imovel-item, "
                    "div.card, li.property-list-item"
                )

                if not items:
                    logger.info("No more items at page %d", page)
                    break

                for item in items:
                    auction = self._parse_item(item)
                    if auction:
                        self.results.append(auction)

                logger.info("Page %d: found %d items", page, len(items))
            except Exception:
                logger.exception("Error scraping Zuk page %d", page)
                continue

        logger.info("Zuk scraper finished with %d items", len(self.results))
        return self.results

    def _parse_item(self, item) -> dict | None:
        try:
            title_el = item.select_one(
                "h3, h2, .titulo, .property-title, .card-title"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            ptype_el = item.select_one(
                ".tipo-imovel, .property-type, .badge, .tag"
            )
            property_type = ptype_el.get_text(strip=True) if ptype_el else ""

            addr_el = item.select_one(
                ".endereco, .address, .location-detail"
            )
            address = addr_el.get_text(strip=True) if addr_el else ""

            loc_el = item.select_one(
                ".cidade-estado, .location, .local"
            )
            city, state = self.parse_location(
                loc_el.get_text(strip=True) if loc_el else None
            )

            discount_el = item.select_one(
                ".desconto, .discount, .badge-discount, .percentual"
            )
            discount_percentage = None
            if discount_el:
                try:
                    pct_text = re.sub(r"[^\d,.]", "", discount_el.get_text(strip=True))
                    pct_text = pct_text.replace(",", ".")
                    discount_percentage = float(pct_text) if pct_text else None
                except ValueError:
                    discount_percentage = None

            market_el = item.select_one(
                ".valor-mercado, .market-value, .avaliacao"
            )
            market_value = self.parse_price(
                market_el.get_text(strip=True) if market_el else None
            )

            min_el = item.select_one(
                ".lance-minimo, .min-bid, .valor-minimo, .preco"
            )
            minimum_bid = self.parse_price(
                min_el.get_text(strip=True) if min_el else None
            )

            date_el = item.select_one(".data, .date, .auction-date, time")
            auction_date = self.parse_date(
                date_el.get_text(strip=True) if date_el else None
            )

            type_el = item.select_one(
                ".tipo-leilao, .auction-type, .modalidade"
            )
            auction_type = type_el.get_text(strip=True) if type_el else "Judicial"

            link_el = item.select_one("a[href]")
            source_url = ""
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            img_el = item.select_one("img[src]")
            image_url = img_el.get("src", "") if img_el else ""

            return {
                "title": title,
                "description": f"{property_type} - {address}" if property_type else address,
                "category": "Imóveis",
                "property_type": property_type,
                "address": address,
                "current_bid": minimum_bid,
                "minimum_bid": minimum_bid,
                "market_value": market_value,
                "discount_percentage": discount_percentage,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception:
            logger.exception("Error parsing Zuk item")
            return None
