"""Data processing pipeline for Leiloes Brazil"""
import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline")


def load_raw_data():
    all_data = []
    for json_file in config.RAW_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                    logger.info(f"Loaded {len(data)} items from {json_file.name}")
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
    return all_data


def normalize_categories(df):
    if "category" in df.columns:
        df["category"] = df["category"].apply(
            lambda x: config.CATEGORY_MAP.get(str(x).lower().strip(), x) if pd.notna(x) else "Diversos"
        )
    return df


def clean_prices(df):
    for col in ["current_bid", "minimum_bid"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_discounts(df):
    if "current_bid" in df.columns and "minimum_bid" in df.columns:
        has_both = df["current_bid"].notna() & df["minimum_bid"].notna() & (df["minimum_bid"] > 0)
        if "discount_percentage" not in df.columns:
            df["discount_percentage"] = None
        df.loc[has_both & df["discount_percentage"].isna(), "discount_percentage"] = (
            ((df["minimum_bid"] - df["current_bid"]) / df["minimum_bid"] * 100)
            .clip(lower=0, upper=100)
            .round(1)
        )
    return df


def deduplicate(df):
    if "source_url" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["source_url"], keep="last")
        logger.info(f"Deduplicated: {before} -> {len(df)} items")
    return df


def run_pipeline():
    logger.info("Starting data pipeline...")
    raw_data = load_raw_data()
    if not raw_data:
        logger.warning("No raw data found. Pipeline complete with no output.")
        return None
    df = pd.DataFrame(raw_data)
    df["scraped_at"] = datetime.now().isoformat()
    df = normalize_categories(df)
    df = clean_prices(df)
    df = compute_discounts(df)
    df = deduplicate(df)
    # Save processed data
    output_json = config.PROCESSED_DIR / config.COMBINED_OUTPUT_FILE
    df.to_json(output_json, orient="records", force_ascii=False, indent=2)
    logger.info(f"Saved {len(df)} items to {output_json}")
    output_csv = config.PROCESSED_DIR / "all_auctions.csv"
    df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info(f"Saved CSV to {output_csv}")
    # Print summary
    logger.info("\n=== Pipeline Summary ===")
    if "source" in df.columns:
        logger.info(f"\nBy Source:\n{df['source'].value_counts().to_string()}")
    if "category" in df.columns:
        logger.info(f"\nBy Category:\n{df['category'].value_counts().to_string()}")
    if "state" in df.columns:
        logger.info(f"\nBy State (top 10):\n{df['state'].value_counts().head(10).to_string()}")
    return df


if __name__ == "__main__":
    run_pipeline()
