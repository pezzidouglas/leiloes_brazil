"""
Main orchestrator – runs every enabled scraper, then the processing pipeline.
"""

import importlib
import logging
import sys

import config
from pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_all_scrapers() -> dict[str, int]:
    """Import and run each enabled scraper, returning item counts per source."""
    stats: dict[str, int] = {}

    for module_path, class_name in config.ENABLED_SCRAPERS:
        try:
            logger.info("Running %s.%s …", module_path, class_name)
            module = importlib.import_module(module_path)
            scraper_cls = getattr(module, class_name)
            scraper = scraper_cls()
            items = scraper.scrape()
            scraper.save_raw(items)
            stats[scraper.SOURCE_NAME] = len(items)
            logger.info("%s: %d items scraped", scraper.SOURCE_NAME, len(items))
        except Exception:
            logger.exception("Scraper %s.%s failed – continuing", module_path, class_name)
            stats[f"{module_path} (FAILED)"] = 0

    return stats


def print_summary(scraper_stats: dict[str, int], df) -> None:
    """Print a human-readable summary of the scraping run."""
    print("\n" + "=" * 60)
    print("  Leilões Brazil – Scraping Summary")
    print("=" * 60)

    total_scraped = sum(scraper_stats.values())
    print(f"\n  Total items scraped : {total_scraped}")
    print(f"  Items after pipeline: {len(df)}")

    print("\n  Per source:")
    for source, count in sorted(scraper_stats.items()):
        print(f"    {source:30s} {count:>6d}")

    if not df.empty and "category" in df.columns:
        print("\n  Per category:")
        for cat, count in df["category"].value_counts().items():
            print(f"    {cat:30s} {count:>6d}")

    print("\n" + "=" * 60 + "\n")


def main() -> None:
    logger.info("Starting scraping run")

    scraper_stats = run_all_scrapers()

    logger.info("Running processing pipeline")
    df = run_pipeline()

    print_summary(scraper_stats, df)


if __name__ == "__main__":
    main()
