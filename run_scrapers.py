"""Main orchestrator to run all scrapers and pipeline."""
import logging
import time
from datetime import datetime

import config
from pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("orchestrator")

SCRAPER_MAP = {
    "superbid": ("scrapers.superbid_scraper", "SuperbidScraper"),
    "mega_leiloes": ("scrapers.mega_leiloes_scraper", "MegaLeiloesScraper"),
    "zuk": ("scrapers.zuk_scraper", "ZukScraper"),
    "leiloes_brasil": ("scrapers.leiloes_brasil_scraper", "LeiloesBrasilScraper"),
    "sodre_santoro": ("scrapers.sodre_santoro_scraper", "SodreSantoroScraper"),
    "leilao_vip": ("scrapers.leilao_vip_scraper", "LeilaoVipScraper"),
}


def run_all_scrapers():
    logger.info(f"Starting scraper run at {datetime.now().isoformat()}")
    logger.info(f"Enabled scrapers: {config.ENABLED_SCRAPERS}")
    results_summary = {}
    for scraper_name in config.ENABLED_SCRAPERS:
        if scraper_name not in SCRAPER_MAP:
            logger.warning(f"Unknown scraper: {scraper_name}")
            continue
        module_path, class_name = SCRAPER_MAP[scraper_name]
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {scraper_name}")
        logger.info(f"{'='*50}")
        try:
            import importlib
            module = importlib.import_module(module_path)
            scraper_class = getattr(module, class_name)
            scraper = scraper_class()
            results = scraper.run()
            results_summary[scraper_name] = len(results)
            logger.info(f"{scraper_name}: {len(results)} items collected")
        except Exception as e:
            logger.error(f"Failed to run {scraper_name}: {e}")
            results_summary[scraper_name] = 0
    # Run pipeline
    logger.info(f"\n{'='*50}")
    logger.info("Running data pipeline...")
    logger.info(f"{'='*50}")
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
    # Print final summary
    logger.info(f"\n{'='*50}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*50}")
    total = 0
    for name, count in results_summary.items():
        logger.info(f"  {name}: {count} items")
        total += count
    logger.info(f"  TOTAL: {total} items")
    logger.info(f"Completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    run_all_scrapers()
