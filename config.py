"""
Configuration for Leilões Brazil scraper and dashboard.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# ---------------------------------------------------------------------------
# Scraper settings
# ---------------------------------------------------------------------------
REQUEST_DELAY = 2          # seconds between requests
TIMEOUT = 30               # request timeout in seconds
MAX_PAGES = 10             # max pages to scrape per source
MAX_RETRIES = 3            # retry attempts for failed requests

# ---------------------------------------------------------------------------
# User-agent strings for rotation
# ---------------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
]

# ---------------------------------------------------------------------------
# Enabled scrapers  (module_name, class_name)
# ---------------------------------------------------------------------------
ENABLED_SCRAPERS = [
    ("scrapers.superbid_scraper", "SuperbidScraper"),
    ("scrapers.mega_leiloes_scraper", "MegaLeiloesScraper"),
    ("scrapers.zuk_scraper", "ZukScraper"),
    ("scrapers.leiloes_brasil_scraper", "LeiloesBrasilScraper"),
    ("scrapers.sodre_santoro_scraper", "SodreSantoroScraper"),
    ("scrapers.leilao_vip_scraper", "LeilaoVipScraper"),
]

# ---------------------------------------------------------------------------
# Category mapping – normalises Portuguese auction categories from every
# source into a unified set.
# ---------------------------------------------------------------------------
CATEGORY_MAP: dict[str, str] = {
    # Imóveis
    "imoveis": "Imóveis",
    "imóveis": "Imóveis",
    "imovel": "Imóveis",
    "imóvel": "Imóveis",
    "real estate": "Imóveis",
    "apartamento": "Imóveis",
    "apartamentos": "Imóveis",
    "casa": "Imóveis",
    "casas": "Imóveis",
    "terreno": "Imóveis",
    "terrenos": "Imóveis",
    "comercial": "Imóveis",
    "rural property": "Imóveis",
    # Veículos
    "veiculos": "Veículos",
    "veículos": "Veículos",
    "veiculo": "Veículos",
    "veículo": "Veículos",
    "carros": "Veículos",
    "carro": "Veículos",
    "motos": "Veículos",
    "moto": "Veículos",
    "carros & motos": "Veículos",
    "caminhões & ônibus": "Veículos",
    "caminhoes": "Veículos",
    "caminhões": "Veículos",
    "onibus": "Veículos",
    "ônibus": "Veículos",
    "vehicles": "Veículos",
    # Máquinas & Equipamentos
    "maquinas": "Máquinas & Equipamentos",
    "máquinas": "Máquinas & Equipamentos",
    "máquinas pesadas & agrícolas": "Máquinas & Equipamentos",
    "maquinas pesadas": "Máquinas & Equipamentos",
    "equipamentos": "Máquinas & Equipamentos",
    "industrial": "Máquinas & Equipamentos",
    "bens industriais": "Máquinas & Equipamentos",
    # Bens de Consumo
    "eletronicos": "Bens de Consumo",
    "eletrônicos": "Bens de Consumo",
    "tecnologia": "Bens de Consumo",
    "bens de consumo": "Bens de Consumo",
    "materiais": "Bens de Consumo",
    "consumer goods": "Bens de Consumo",
    # Rural & Animais
    "animais": "Rural & Animais",
    "rural": "Rural & Animais",
    "agro": "Rural & Animais",
    "gado": "Rural & Animais",
    # Diversos
    "diversos": "Diversos",
    "outros": "Diversos",
    "produtos diversos": "Diversos",
    "remanescentes": "Diversos",
    "judiciais": "Diversos",
    "other": "Diversos",
}

# ---------------------------------------------------------------------------
# Brazilian states (UF codes)
# ---------------------------------------------------------------------------
BRAZILIAN_STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

# ---------------------------------------------------------------------------
# Auction types
# ---------------------------------------------------------------------------
AUCTION_TYPES = [
    "Judicial",
    "Extrajudicial",
    "Online",
    "Presencial",
    "Misto",
]
