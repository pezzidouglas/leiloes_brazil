"""
Data processing pipeline.

Loads raw JSON files from data/raw/, normalises categories, cleans prices
and dates, deduplicates by source_url, and writes the unified dataset to
data/processed/all_auctions.json and all_auctions.csv.
"""

import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

import config

logger = logging.getLogger(__name__)


def load_raw_data() -> list[dict]:
    """Load every JSON file found in data/raw/ and combine into one list."""
    all_items: list[dict] = []
    if not os.path.isdir(config.RAW_DIR):
        logger.warning("Raw data directory does not exist: %s", config.RAW_DIR)
        return all_items

    for filename in os.listdir(config.RAW_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(config.RAW_DIR, filename)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                all_items.extend(data)
                logger.info("Loaded %d items from %s", len(data), filename)
        except Exception:
            logger.exception("Failed to load %s", path)

    logger.info("Total raw items loaded: %d", len(all_items))
    return all_items


def normalize_category(category: str | None) -> str:
    """Map a raw category string to a unified category via config.CATEGORY_MAP."""
    if not category:
        return "Diversos"
    key = category.strip().lower()
    return config.CATEGORY_MAP.get(key, "Diversos")


def clean_price(value) -> float | None:
    """Ensure a price value is a float or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        from scrapers.base_scraper import BaseScraper
        return BaseScraper.parse_price(value)
    return None


def parse_date_field(value) -> str | None:
    """Ensure a date value is an ISO-formatted string or None."""
    if value is None:
        return None
    if isinstance(value, str):
        from scrapers.base_scraper import BaseScraper
        return BaseScraper.parse_date(value)
    return str(value)


def run_pipeline() -> pd.DataFrame:
    """Execute the full pipeline and return the processed DataFrame."""
    items = load_raw_data()

    if not items:
        logger.warning("No raw data to process.")
        return pd.DataFrame()

    df = pd.DataFrame(items)

    # Normalise categories
    if "category" in df.columns:
        df["category"] = df["category"].apply(normalize_category)

    # Clean prices
    for col in ["current_bid", "minimum_bid", "market_value"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_price)

    # Parse dates
    if "auction_date" in df.columns:
        df["auction_date"] = df["auction_date"].apply(parse_date_field)

    # Deduplicate by source_url (keep first)
    if "source_url" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["source_url"], keep="first")
        logger.info("Deduplicated: %d -> %d items", before, len(df))

    # Add scraped_at timestamp
    df["scraped_at"] = datetime.now(timezone.utc).isoformat()

    # Save outputs
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)

    json_path = os.path.join(config.PROCESSED_DIR, "all_auctions.json")
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    logger.info("Saved JSON to %s", json_path)

    csv_path = os.path.join(config.PROCESSED_DIR, "all_auctions.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info("Saved CSV to %s", csv_path)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = run_pipeline()
    print(f"Pipeline complete – {len(df)} auctions processed.")
