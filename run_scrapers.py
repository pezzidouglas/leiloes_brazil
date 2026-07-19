"""Main orchestrator to run all scrapers and pipeline."""
import logging
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
    "leiloes_judiciais": ("scrapers.leiloes_judiciais_scraper", "LeiloesJudiciaisScraper"),
    "e_leiloes": ("scrapers.e_leiloes_scraper", "ELeiloesScraper"),
    "frazao_leiloes": ("scrapers.frazao_leiloes_scraper", "FrazaoLeiloesScraper"),
    "sold": ("scrapers.sold_scraper", "SoldScraper"),
    "nucleo_leiloes": ("scrapers.nucleo_leiloes_scraper", "NucleoLeiloesScraper"),
    "mapa_do_leilao": ("scrapers.mapa_do_leilao_scraper", "MapaDoLeilaoScraper"),
    "freitas_leiloeiro": ("scrapers.freitas_leiloeiro_scraper", "FreitasLeiloeiroScraper"),
    "lance_no_leilao": ("scrapers.lance_no_leilao_scraper", "LanceNoLeilaoScraper"),
    "pestana_leiloes": ("scrapers.pestana_leiloes_scraper", "PestanaLeiloesScraper"),
    "milani_leiloes": ("scrapers.milani_leiloes_scraper", "MilaniLeiloesScraper"),
    "grupo_lance": ("scrapers.grupo_lance_scraper", "GrupoLanceScraper"),
}


def run_all_scrapers():
    logger.info("Starting scraper run at %s", datetime.now().isoformat())
    logger.info("Enabled scrapers: %s", config.ENABLED_SCRAPERS)
    results_summary = {}
    failed_scrapers = []

    for scraper_name in config.ENABLED_SCRAPERS:
        if scraper_name not in SCRAPER_MAP:
            logger.warning("Unknown scraper: %s", scraper_name)
            failed_scrapers.append(scraper_name)
            continue

        module_path, class_name = SCRAPER_MAP[scraper_name]
        logger.info("\n%s", "=" * 50)
        logger.info("Running: %s", scraper_name)
        logger.info("%s", "=" * 50)
        try:
            import importlib

            module = importlib.import_module(module_path)
            scraper_class = getattr(module, class_name)
            scraper = scraper_class()
            results = scraper.run()
            results_summary[scraper_name] = len(results)
            logger.info("%s: %s items collected", scraper_name, len(results))
        except Exception as exc:
            logger.error("Failed to run %s: %s", scraper_name, exc)
            results_summary[scraper_name] = 0
            failed_scrapers.append(scraper_name)

    logger.info("\n%s", "=" * 50)
    logger.info("Running data pipeline...")
    logger.info("%s", "=" * 50)
    pipeline_ok = True
    try:
        pipeline_result = run_pipeline()
        if pipeline_result is None:
            pipeline_ok = False
    except Exception as exc:
        logger.error("Pipeline error: %s", exc)
        pipeline_ok = False

    logger.info("\n%s", "=" * 50)
    logger.info("FINAL SUMMARY")
    logger.info("%s", "=" * 50)
    total = 0
    for name, count in results_summary.items():
        logger.info("  %s: %s items", name, count)
        total += count
    logger.info("  TOTAL: %s items", total)
    if failed_scrapers:
        logger.warning("Scrapers with errors: %s", ", ".join(failed_scrapers))
    logger.info("Completed at %s", datetime.now().isoformat())

    if total == 0:
        logger.error("No auction records were collected; refusing to report a successful run.")
        return 1
    if not pipeline_ok:
        logger.error("Data processing failed; refusing to report a successful run.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all_scrapers())
