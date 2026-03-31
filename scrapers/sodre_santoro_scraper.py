"""
Scraper for sodresantoro.com.br – major vehicle auction house in Brazil.

Extracts vehicle details including make, model, year, plate info.
"""

import logging

from scrapers.base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class SodreSantoroScraper(BaseScraper):
    SOURCE_NAME = "sodre_santoro"
    BASE_URL = "https://www.sodresantoro.com.br"
    SEARCH_URL = f"{BASE_URL}/leiloes"

    def scrape(self) -> list[dict]:
        logger.info("Starting Sodré Santoro scraper")
        self.results = []

        for page in range(1, config.MAX_PAGES + 1):
            try:
                url = f"{self.SEARCH_URL}?pagina={page}"
                resp = self._get(url)
                soup = self._soup(resp.text)
                items = soup.select(
                    "div.lote-card, div.vehicle-card, div.card, "
                    "div.auction-item, li.lote"
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
                logger.exception("Error scraping Sodré Santoro page %d", page)
                continue

        logger.info(
            "Sodré Santoro scraper finished with %d items", len(self.results)
        )
        return self.results

    def _parse_item(self, item) -> dict | None:
        try:
            title_el = item.select_one(
                "h3, h2, .titulo, .vehicle-title, .card-title, .lote-title"
            )
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                return None

            desc_el = item.select_one(
                ".descricao, .description, .vehicle-details, p"
            )
            description = desc_el.get_text(strip=True) if desc_el else ""

            # Try to extract vehicle specifics from title/description
            make = ""
            model = ""
            year = ""
            plate_info = ""

            detail_els = item.select(".detail, .info-item, .spec, dd")
            for detail in detail_els:
                text = detail.get_text(strip=True).lower()
                label_el = detail.find_previous_sibling("dt")
                label = label_el.get_text(strip=True).lower() if label_el else ""

                if "marca" in label or "make" in label:
                    make = detail.get_text(strip=True)
                elif "modelo" in label or "model" in label:
                    model = detail.get_text(strip=True)
                elif "ano" in label or "year" in label:
                    year = detail.get_text(strip=True)
                elif "placa" in label or "plate" in label:
                    plate_info = detail.get_text(strip=True)

            cat_el = item.select_one(
                ".categoria, .category, .badge, .tag"
            )
            category = cat_el.get_text(strip=True) if cat_el else "Veículos"

            bid_el = item.select_one(
                ".preco, .price, .valor, .lance-inicial, .starting-bid"
            )
            starting_bid = self.parse_price(
                bid_el.get_text(strip=True) if bid_el else None
            )

            date_el = item.select_one(".data, .date, .auction-date, time")
            auction_date = self.parse_date(
                date_el.get_text(strip=True) if date_el else None
            )

            loc_el = item.select_one(".local, .location, .cidade-estado")
            city, state = self.parse_location(
                loc_el.get_text(strip=True) if loc_el else None
            )

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
                "make": make,
                "model": model,
                "year": year,
                "plate_info": plate_info,
                "current_bid": starting_bid,
                "minimum_bid": starting_bid,
                "auction_date": auction_date,
                "city": city,
                "state": state,
                "auction_type": "Presencial",
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "image_url": image_url,
            }
        except Exception:
            logger.exception("Error parsing Sodré Santoro item")
            return None
