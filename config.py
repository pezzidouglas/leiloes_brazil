"""
Configuration for Leiloes Brazil Scraper
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

for d in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

REQUEST_DELAY = 2
REQUEST_TIMEOUT = 30
MAX_PAGES_PER_SOURCE = 10
MAX_RETRIES = 3

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

ENABLED_SCRAPERS = [
    "superbid", "mega_leiloes", "zuk", "leiloes_brasil", "sodre_santoro", "leilao_vip",
    "leiloes_judiciais", "e_leiloes", "frazao_leiloes", "sold", "nucleo_leiloes", "mapa_do_leilao",
    "freitas_leiloeiro", "lance_no_leilao", "pestana_leiloes", "milani_leiloes", "grupo_lance",
]

CATEGORY_MAP = {
    "imoveis": "Imoveis", "imovel": "Imoveis", "apartamentos": "Imoveis",
    "casas": "Imoveis", "terrenos": "Imoveis", "galpoes": "Imoveis",
    "comerciais": "Imoveis", "rurais": "Imoveis", "real_estate": "Imoveis",
    "veiculos": "Veiculos", "veiculo": "Veiculos", "carros": "Veiculos",
    "motos": "Veiculos", "caminhoes": "Veiculos", "onibus": "Veiculos",
    "aeronaves": "Veiculos", "barcos": "Veiculos", "vehicles": "Veiculos",
    "maquinas": "Maquinas", "equipamentos": "Maquinas", "industriais": "Maquinas",
    "eletrodomesticos": "Bens de Consumo", "eletronicos": "Bens de Consumo",
    "moveis": "Bens de Consumo", "consumer": "Bens de Consumo",
    "animais": "Rural", "cavalos": "Rural", "gado": "Rural", "rural": "Rural",
    "diversos": "Diversos", "materiais": "Diversos", "sucatas": "Diversos",
    "outros": "Diversos", "agro": "Rural", "tecnologia": "Bens de Consumo",
    "industrial": "Maquinas", "caminhoesonibus": "Veiculos", "carrosmotos": "Veiculos",
    "maquinaspesadas": "Maquinas", "residencial": "Imoveis", "comercial": "Imoveis",
    "terreno": "Imoveis",
}

BRAZILIAN_STATES = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
    "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
]

AUCTION_TYPES = ["Judicial", "Extrajudicial", "Venda Direta", "Corporativo", "Administrativo"]
OUTPUT_FORMAT = "json"
COMBINED_OUTPUT_FILE = "all_auctions.json"
