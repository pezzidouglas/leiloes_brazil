"""
Scraper for leilaovip.com.br (HastaVip).

Categories: Imóveis, Materiais, Veículos, Diversos, Remanescentes.
"""

import logging

from scrapers.base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class LeilaoVipScraper(BaseScraper):
    SOURCE_NAME = "leilao_vip"
    BASE_URL = "https://www.leilaovip.com.br"
    SEARCH_URL = f"{BASE_URL}/leiloes"

    CATEGORIES = [
        "Imóveis",
        "Materiais",
        "Veículos",
        "Diversos",
        "Remanescentes",
    ]

    def scrape(self) -> list[dict]:
        logger.info("Starting Leilão VIP scraper")
        self.results = []

        for page in range(1, config.MAX_PAGES + 1):
            try:
                url = f"{self.SEARCH_URL}?page={page}"
                resp = self._get(url)
                soup = self._soup(resp.text)
                items = soup.select(
                    "div.leilao-card, div.auction-item, div.card, "
                    "div.item-leilao, li.auction"
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
                logger.exception("Error scraping Leilão VIP page %d", page)
                continue

        logger.info("Leilão VIP scraper finished with %d items", len(self.results))
        return self.results

    def _parse_item(self, item) -> dict | None:
        try:
            title_el = item.select_one(
                "h3, h2, .titulo, .title, .card-title"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            desc_el = item.select_one(".descricao, .description, p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            cat_el = item.select_one(
                ".categoria, .category, .badge, .tag"
            )
            category = cat_el.get_text(strip=True) if cat_el else "Diversos"

            bid_el = item.select_one(
                ".preco, .price, .valor, .lance-atual"
            )
            current_bid = self.parse_price(
                bid_el.get_text(strip=True) if bid_el else None
            )

            min_el = item.select_one(".lance-minimo, .min-bid, .valor-minimo")
            minimum_bid = self.parse_price(
                min_el.get_text(strip=True) if min_el else None
            )

            date_el = item.select_one(".data, .date, .auction-date, time")
            auction_date = self.parse_date(
                date_el.get_text(strip=True) if date_el else None
            )

            loc_el = item.select_one(".local, .location, .cidade-estado")
            city, state = self.parse_location(
                loc_el.get_text(strip=True) if loc_el else None
            )

            type_el = item.select_one(".tipo, .auction-type, .modalidade")
            auction_type = type_el.get_text(strip=True) if type_el else "Online"

            link_el = item.select_one("a[href]")
            source_url = ""
            if link_el:
                href = link_el.get("href", "")
                source_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            img_el = item.select_one("img[src]")
            image_url = img_el.get("src", "") if img_el else ""

            return {
                "title": title,
                "description": description,
                "category": category,
                "current_bid": current_bid,
                "minimum_bid": minimum_bid,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": auction_type,
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception:
            logger.exception("Error parsing Leilão VIP item")
            return None
