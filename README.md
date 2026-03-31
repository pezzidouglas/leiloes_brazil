# 🇧🇷 Leilões Brazil - Auction Scraper & Dashboard

A comprehensive web scraper and dashboard for Brazilian auctions (leilões). Scrapes data from major auction platforms across Brazil and presents it in a beautiful, interactive Streamlit dashboard.

## 🎯 Features

- **Multi-source scraping**: Collects auction data from 6+ major Brazilian auction platforms
- - **Unified data format**: Normalizes data from different sources into a consistent schema
  - - **Interactive dashboard**: Filter by category, state, price range, and auction date
    - - **Auto-refresh**: GitHub Actions workflow runs daily to keep data fresh
      - - **Export**: Download filtered results as CSV
       
        - ## 📊 Supported Auction Sources
       
        - | Source | URL | Categories |
        - |--------|-----|------------|
        - | Superbid | superbid.net | Vehicles, Real Estate, Industrial, Rural |
        - | Mega Leilões | megaleiloes.com.br | Real Estate, Vehicles, Consumer Goods |
        - | Zuk Leilões | portalzuk.com.br | Real Estate (Judicial & Extrajudicial) |
        - | Leilões Brasil | leiloesbrasil.com.br | Vehicles, Real Estate, Judicial |
        - | Sodré Santoro | sodresantoro.com.br | Vehicles, Electronics, Furniture |
        - | Leilão VIP | leilaovip.com.br | Real Estate, Vehicles, Materials |
       
        - ## 🏗️ Project Structure
       
        - ```
          leiloes_brazil/
          ├── README.md
          ├── requirements.txt
          ├── config.py                # Configuration & constants
          ├── scrapers/
          │   ├── __init__.py
          │   ├── base_scraper.py      # Abstract base scraper class
          │   ├── superbid_scraper.py  # Superbid Exchange scraper
          │   ├── mega_leiloes_scraper.py  # Mega Leilões scraper
          │   ├── zuk_scraper.py       # Zuk Portal scraper
          │   ├── leiloes_brasil_scraper.py  # Leilões Brasil scraper
          │   ├── sodre_santoro_scraper.py   # Sodré Santoro scraper
          │   └── leilao_vip_scraper.py     # Leilão VIP scraper
          ├── data/
          │   ├── raw/                 # Raw scraped data per source
          │   └── processed/           # Unified processed data
          ├── pipeline.py              # Data processing pipeline
          ├── run_scrapers.py          # Main scraper orchestrator
          ├── dashboard.py             # Streamlit dashboard
          └── .github/
              └── workflows/
                  └── scrape.yml       # Daily scraping workflow
          ```

          ## 🚀 Quick Start

          ### 1. Install dependencies
          ```bash
          pip install -r requirements.txt
          ```

          ### 2. Run the scrapers
          ```bash
          python run_scrapers.py
          ```

          ### 3. Launch the dashboard
          ```bash
          streamlit run dashboard.py
          ```

          ## ⚙️ Configuration

          Edit `config.py` to customize:
          - Which scrapers to enable/disable
          - - Number of pages to scrape per source
            - - Request delays and timeouts
              - - Output data format
               
                - ## 📦 Requirements
               
                - - Python 3.9+
                  - - See `requirements.txt` for full dependency list
                   
                    - ## 📄 License
                   
                    - MIT License
