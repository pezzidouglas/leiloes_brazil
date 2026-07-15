"""
Generate a static HTML dashboard from auction data.

Reads data from data/processed/all_auctions.json (or generates demo data)
and produces a self-contained docs/index.html that can be deployed to
static hosting services like Tiiny.host.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "processed" / "all_auctions.json"
OUTPUT_DIR = BASE_DIR / "docs"

CATEGORIES = [
    "Imoveis", "Veiculos", "Maquinas", "Bens de Consumo", "Rural", "Diversos"
]
STATES = [
    "SP", "RJ", "MG", "BA", "PR", "RS", "SC", "GO", "PE", "CE",
    "PA", "MA", "MT", "MS", "DF", "ES", "PB", "RN", "AL", "PI",
    "SE", "RO", "TO", "AC", "AP", "AM", "RR",
]
SOURCES = [
    "Superbid", "Mega Leiloes", "Zuk", "Leiloes Brasil", "Sodre Santoro",
    "Leilao VIP", "Leiloes Judiciais", "E-Leiloes", "Frazao Leiloes",
    "Sold", "Nucleo Leiloes", "Mapa do Leilao",
]
TYPES = ["Judicial", "Extrajudicial", "Venda Direta", "Corporativo"]
CITIES = {
    "SP": ["Sao Paulo", "Campinas", "Santos", "Ribeirao Preto", "Sorocaba"],
    "RJ": ["Rio de Janeiro", "Niteroi", "Petropolis", "Volta Redonda"],
    "MG": ["Belo Horizonte", "Uberlandia", "Juiz de Fora", "Contagem"],
    "BA": ["Salvador", "Feira de Santana", "Vitoria da Conquista"],
    "PR": ["Curitiba", "Londrina", "Maringa", "Foz do Iguacu"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas"],
    "SC": ["Florianopolis", "Joinville", "Blumenau"],
    "GO": ["Goiania", "Aparecida de Goiania"],
    "PE": ["Recife", "Olinda", "Jaboatao"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte"],
}
IMOVEIS_TITLES = [
    "Apartamento 3 quartos", "Casa 2 quartos com garagem", "Terreno 500m2",
    "Sala Comercial 80m2", "Galpao Industrial 1200m2", "Sitio 5 hectares",
    "Cobertura Duplex", "Flat Mobiliado", "Loja Comercial", "Casa de Praia",
    "Apartamento Studio", "Sobrado 4 quartos",
]
VEICULOS_TITLES = [
    "VW Gol 2019", "Fiat Strada 2020", "Toyota Corolla 2021",
    "Honda Civic 2018", "Chevrolet Onix 2022", "Hyundai HB20 2020",
    "Ford Ranger 2019", "Mercedes Sprinter 2018", "Yamaha Factor 150 2021",
    "Honda CG 160 2020", "Scania R450 2017", "Volvo FH 540 2019",
]


def generate_demo_data(n=250):
    """Generate demo auction data when no real data is available."""
    data = []
    for i in range(n):
        cat = random.choice(CATEGORIES)
        state = random.choice(STATES[:15])
        city_list = CITIES.get(state, ["Capital"])
        if cat == "Imoveis":
            titles = IMOVEIS_TITLES
        elif cat == "Veiculos":
            titles = VEICULOS_TITLES
        else:
            titles = [f"Lote {cat} #{i}"]
        base_price = (
            random.uniform(10000, 2000000) if cat == "Imoveis"
            else random.uniform(5000, 300000)
        )
        discount = random.randint(10, 60)
        data.append({
            "title": random.choice(titles),
            "category": cat,
            "current_bid": round(base_price * (1 - discount / 100), 2),
            "minimum_bid": round(base_price * (1 - discount / 100) * 0.8, 2),
            "market_value": round(base_price, 2),
            "discount_percentage": discount,
            "auction_date": (
                datetime.now() + timedelta(days=random.randint(-5, 30))
            ).strftime("%Y-%m-%d"),
            "city": random.choice(city_list),
            "state": state,
            "auction_type": random.choice(TYPES),
            "source": random.choice(SOURCES),
            "source_url": f"https://example.com/lote/{i + 1}",
            "scraped_at": datetime.now().isoformat(),
        })
    return data


def load_data():
    """Load auction data from processed JSON file, or generate demo data."""
    if DATA_PATH.exists():
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data:
                return data
        except Exception:
            pass
    return generate_demo_data(250)


def build_html(data, generated_at):
    """Build a self-contained HTML dashboard string."""
    data_json = json.dumps(data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Leiloes Brazil Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0e1117; color: #fafafa; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 24px 32px; border-bottom: 2px solid #009c3b; }}
.header h1 {{ font-size: 28px; margin-bottom: 4px; }}
.header p {{ color: #b0b0b0; font-size: 14px; }}
.container {{ display: flex; min-height: calc(100vh - 80px); }}
.sidebar {{ width: 280px; background: #161b22; padding: 20px; border-right: 1px solid #30363d; overflow-y: auto; flex-shrink: 0; }}
.sidebar h3 {{ font-size: 16px; margin-bottom: 16px; color: #58a6ff; }}
.filter-group {{ margin-bottom: 16px; }}
.filter-group label {{ display: block; font-size: 13px; color: #b0b0b0; margin-bottom: 6px; font-weight: 600; }}
.filter-group select {{ width: 100%; padding: 8px; background: #0d1117; color: #fafafa; border: 1px solid #30363d; border-radius: 6px; font-size: 13px; }}
.filter-group select[multiple] {{ height: 100px; }}
.filter-group input[type=range] {{ width: 100%; accent-color: #009c3b; }}
.range-labels {{ display: flex; justify-content: space-between; font-size: 11px; color: #888; }}
.main {{ flex: 1; padding: 20px; overflow-y: auto; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
.kpi-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }}
.kpi-card .icon {{ font-size: 24px; }}
.kpi-card .value {{ font-size: 28px; font-weight: 700; color: #58a6ff; margin: 4px 0; }}
.kpi-card .label {{ font-size: 12px; color: #888; }}
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
.chart-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }}
.chart-card h3 {{ font-size: 15px; margin-bottom: 8px; color: #c9d1d9; }}
.divider {{ border: none; border-top: 1px solid #30363d; margin: 20px 0; }}
.table-section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }}
.table-section h3 {{ font-size: 15px; margin-bottom: 12px; color: #c9d1d9; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: #0d1117; color: #58a6ff; padding: 10px 8px; text-align: left; position: sticky; top: 0; cursor: pointer; user-select: none; }}
th:hover {{ color: #79c0ff; }}
td {{ padding: 8px; border-bottom: 1px solid #21262d; }}
tr:hover td {{ background: #1c2128; }}
a {{ color: #58a6ff; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.table-scroll {{ max-height: 500px; overflow-y: auto; }}
.btn {{ display: inline-block; background: #009c3b; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin-top: 12px; }}
.btn:hover {{ background: #00b341; }}
.footer {{ text-align: center; padding: 12px; color: #666; font-size: 12px; border-top: 1px solid #30363d; }}
.warning {{ background: #2d1b00; border: 1px solid #d29922; border-radius: 8px; padding: 16px; color: #d29922; text-align: center; margin: 20px 0; }}
@media (max-width: 900px) {{
  .container {{ flex-direction: column; }}
  .sidebar {{ width: 100%; border-right: none; border-bottom: 1px solid #30363d; }}
  .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  .charts-row {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>\U0001f1e7\U0001f1f7 Leiloes Brazil Dashboard</h1>
  <p><strong>Painel de leiloes do Brasil</strong> &mdash; Dados agregados de 6+ plataformas de leilao</p>
</div>

<div class="container">
  <div class="sidebar">
    <h3>\U0001f50d Filtros</h3>

    <div class="filter-group">
      <label>Categoria</label>
      <select id="filterCategory" multiple></select>
    </div>
    <div class="filter-group">
      <label>Estado</label>
      <select id="filterState" multiple></select>
    </div>
    <div class="filter-group">
      <label>Tipo de Leilao</label>
      <select id="filterType" multiple></select>
    </div>
    <div class="filter-group">
      <label>Fonte</label>
      <select id="filterSource" multiple></select>
    </div>
    <div class="filter-group">
      <label>Preco Maximo (R$)</label>
      <input type="range" id="filterPrice" min="0" max="100" value="100">
      <div class="range-labels"><span id="priceMin">R$ 0</span><span id="priceMax">R$ 0</span></div>
    </div>

    <button class="btn" onclick="applyFilters()" style="width:100%">Aplicar Filtros</button>
    <button class="btn" onclick="resetFilters()" style="width:100%; background:#30363d; margin-top:6px;">Limpar</button>

    <hr class="divider">
    <p style="font-size:12px; color:#666;"><strong>Leiloes Brazil</strong> v1.0</p>
    <p style="font-size:12px; color:#666;">Ultima atualizacao: {generated_at}</p>
  </div>

  <div class="main">
    <div class="kpi-row">
      <div class="kpi-card"><div class="icon">\U0001f4e6</div><div class="value" id="kpiTotal">0</div><div class="label">Total Leiloes</div></div>
      <div class="kpi-card"><div class="icon">\U0001f4b0</div><div class="value" id="kpiDiscount">0%</div><div class="label">Desconto Medio</div></div>
      <div class="kpi-card"><div class="icon">\U0001f4c5</div><div class="value" id="kpiWeek">0</div><div class="label">Esta Semana</div></div>
      <div class="kpi-card"><div class="icon">\U0001f310</div><div class="value" id="kpiSources">0</div><div class="label">Fontes Ativas</div></div>
    </div>

    <div id="warningBox" class="warning" style="display:none;">Nenhum leilao encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.</div>

    <div id="chartsArea">
      <div class="charts-row">
        <div class="chart-card"><h3>Leiloes por Categoria</h3><div id="chartCategory"></div></div>
        <div class="chart-card"><h3>Leiloes por Estado (Top 10)</h3><div id="chartState"></div></div>
      </div>
      <div class="charts-row">
        <div class="chart-card"><h3>Tipos de Leilao</h3><div id="chartType"></div></div>
        <div class="chart-card"><h3>Leiloes por Fonte</h3><div id="chartSource"></div></div>
      </div>
    </div>

    <hr class="divider">
    <div class="table-section">
      <h3>\U0001f4cb Lista de Leiloes</h3>
      <div class="table-scroll">
        <table>
          <thead><tr>
            <th onclick="sortTable(0)">Titulo</th>
            <th onclick="sortTable(1)">Categoria</th>
            <th onclick="sortTable(2)">Lance Atual (R$)</th>
            <th onclick="sortTable(3)">Estado</th>
            <th onclick="sortTable(4)">Cidade</th>
            <th onclick="sortTable(5)">Tipo</th>
            <th onclick="sortTable(6)">Data</th>
            <th onclick="sortTable(7)">Fonte</th>
            <th>Link</th>
          </tr></thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>
      <button class="btn" onclick="exportCSV()">\U0001f4e5 Exportar CSV</button>
    </div>
  </div>
</div>

<div class="footer">Leiloes Brazil &copy; {datetime.now().year} &mdash; Dados atualizados automaticamente</div>

<script>
const RAW_DATA = {data_json};

let filteredData = [];
let globalMin = 0, globalMax = 0;
let sortCol = -1, sortAsc = true;

function init() {{
  // Compute global price range
  const prices = RAW_DATA.filter(d => d.current_bid != null).map(d => d.current_bid);
  globalMin = prices.length ? Math.min(...prices) : 0;
  globalMax = prices.length ? Math.max(...prices) : 1000000;

  // Populate filter options
  populateSelect('filterCategory', unique(RAW_DATA, 'category'));
  populateSelect('filterState', unique(RAW_DATA, 'state'));
  populateSelect('filterType', unique(RAW_DATA, 'auction_type'));
  populateSelect('filterSource', unique(RAW_DATA, 'source'));

  // Price slider
  const slider = document.getElementById('filterPrice');
  slider.min = 0;
  slider.max = 100;
  slider.value = 100;
  updatePriceLabel();
  slider.addEventListener('input', updatePriceLabel);

  applyFilters();
}}

function unique(data, key) {{
  return [...new Set(data.map(d => d[key]).filter(v => v != null))].sort();
}}

function populateSelect(id, options) {{
  const sel = document.getElementById(id);
  sel.innerHTML = '';
  options.forEach(opt => {{
    const o = document.createElement('option');
    o.value = opt;
    o.textContent = opt;
    o.selected = true;
    sel.appendChild(o);
  }});
}}

function getSelected(id) {{
  const sel = document.getElementById(id);
  return [...sel.selectedOptions].map(o => o.value);
}}

function updatePriceLabel() {{
  const v = document.getElementById('filterPrice').value;
  const maxPrice = globalMin + (globalMax - globalMin) * (v / 100);
  document.getElementById('priceMin').textContent = 'R$ ' + fmt(globalMin);
  document.getElementById('priceMax').textContent = 'R$ ' + fmt(Math.round(maxPrice));
}}

function fmt(n) {{
  return n.toLocaleString('pt-BR', {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
}}

function applyFilters() {{
  const cats = getSelected('filterCategory');
  const states = getSelected('filterState');
  const types = getSelected('filterType');
  const sources = getSelected('filterSource');
  const priceSlider = document.getElementById('filterPrice').value;
  const maxPrice = globalMin + (globalMax - globalMin) * (priceSlider / 100);

  filteredData = RAW_DATA.filter(d => {{
    if (cats.length && !cats.includes(d.category)) return false;
    if (states.length && !states.includes(d.state) && !states.includes(d.city)) return false;
    if (types.length && !types.includes(d.auction_type)) return false;
    if (sources.length && !sources.includes(d.source)) return false;
    if (d.current_bid != null && d.current_bid > maxPrice) return false;
    return true;
  }});

  renderKPIs();
  if (filteredData.length === 0) {{
    document.getElementById('warningBox').style.display = 'block';
    document.getElementById('chartsArea').style.display = 'none';
  }} else {{
    document.getElementById('warningBox').style.display = 'none';
    document.getElementById('chartsArea').style.display = 'block';
    renderCharts();
  }}
  renderTable();
}}

function resetFilters() {{
  ['filterCategory','filterState','filterType','filterSource'].forEach(id => {{
    const sel = document.getElementById(id);
    [...sel.options].forEach(o => o.selected = true);
  }});
  document.getElementById('filterPrice').value = 100;
  updatePriceLabel();
  applyFilters();
}}

function renderKPIs() {{
  document.getElementById('kpiTotal').textContent = filteredData.length.toLocaleString();

  const discounts = filteredData.filter(d => d.discount_percentage != null).map(d => d.discount_percentage);
  const avg = discounts.length ? (discounts.reduce((a, b) => a + b, 0) / discounts.length) : 0;
  document.getElementById('kpiDiscount').textContent = Math.round(avg) + '%';

  // This week count
  const now = new Date();
  const weekLater = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  let weekCount = 0;
  filteredData.forEach(d => {{
    if (d.auction_date) {{
      // Handle various date formats
      let dateStr = d.auction_date;
      const match = dateStr.match(/(\\d{{4}})[-/](\\d{{2}})[-/](\\d{{2}})/);
      if (match) {{
        const aDate = new Date(match[1], match[2] - 1, match[3]);
        if (aDate >= now && aDate <= weekLater) weekCount++;
      }}
    }}
  }});
  document.getElementById('kpiWeek').textContent = weekCount.toLocaleString();

  const uniqueSources = new Set(filteredData.map(d => d.source).filter(Boolean));
  document.getElementById('kpiSources').textContent = uniqueSources.size;
}}

function countBy(data, key) {{
  const counts = {{}};
  data.forEach(d => {{
    const v = d[key] || 'N/A';
    counts[v] = (counts[v] || 0) + 1;
  }});
  return Object.entries(counts).sort((a, b) => b[1] - a[1]);
}}

const SET2 = ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854','#ffd92f','#e5c494','#b3b3b3'];
const BOLD = ['#7F3C8D','#11A579','#3969AC','#F2B701','#E73F74','#80BA5A','#E68310','#008695','#CF1C90','#f97b72'];
const PASTEL = ['#b3e2cd','#fdcdac','#cbd5e8','#f4cae4','#e6f5c9','#fff2ae'];

function renderCharts() {{
  // Category bar chart
  const catData = countBy(filteredData, 'category');
  Plotly.newPlot('chartCategory', [{{
    x: catData.map(c => c[0]),
    y: catData.map(c => c[1]),
    type: 'bar',
    marker: {{ color: catData.map((_, i) => SET2[i % SET2.length]) }}
  }}], {{
    height: 320, margin: {{ t: 10, b: 40, l: 40, r: 10 }},
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    font: {{ color: '#c9d1d9' }},
    xaxis: {{ gridcolor: '#30363d' }}, yaxis: {{ gridcolor: '#30363d' }}
  }}, {{ responsive: true }});

  // State bar chart (top 10)
  const stateData = countBy(filteredData, 'state').slice(0, 10);
  Plotly.newPlot('chartState', [{{
    x: stateData.map(c => c[0]),
    y: stateData.map(c => c[1]),
    type: 'bar',
    marker: {{ color: stateData.map(c => c[1]), colorscale: 'Viridis' }}
  }}], {{
    height: 320, margin: {{ t: 10, b: 40, l: 40, r: 10 }},
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    font: {{ color: '#c9d1d9' }},
    xaxis: {{ gridcolor: '#30363d' }}, yaxis: {{ gridcolor: '#30363d' }}
  }}, {{ responsive: true }});

  // Type pie chart
  const typeData = countBy(filteredData, 'auction_type');
  Plotly.newPlot('chartType', [{{
    labels: typeData.map(c => c[0]),
    values: typeData.map(c => c[1]),
    type: 'pie',
    marker: {{ colors: PASTEL }}
  }}], {{
    height: 320, margin: {{ t: 10, b: 10, l: 10, r: 10 }},
    paper_bgcolor: 'transparent',
    font: {{ color: '#c9d1d9' }}
  }}, {{ responsive: true }});

  // Source bar chart
  const srcData = countBy(filteredData, 'source');
  Plotly.newPlot('chartSource', [{{
    x: srcData.map(c => c[0]),
    y: srcData.map(c => c[1]),
    type: 'bar',
    marker: {{ color: srcData.map((_, i) => BOLD[i % BOLD.length]) }}
  }}], {{
    height: 320, margin: {{ t: 10, b: 80, l: 40, r: 10 }},
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    font: {{ color: '#c9d1d9' }},
    xaxis: {{ gridcolor: '#30363d', tickangle: -30 }}, yaxis: {{ gridcolor: '#30363d' }}
  }}, {{ responsive: true }});
}}

function renderTable() {{
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';
  const rows = filteredData.slice(0, 500);  // Limit for performance
  rows.forEach(d => {{
    const tr = document.createElement('tr');
    const bid = d.current_bid != null ? 'R$ ' + d.current_bid.toLocaleString('pt-BR', {{minimumFractionDigits: 2}}) : '-';
    const dateStr = d.auction_date || '-';
    const link = d.source_url ? '<a href="' + escapeHtml(d.source_url) + '" target="_blank" rel="noopener noreferrer">Ver</a>' : '-';
    tr.innerHTML =
      '<td>' + escapeHtml(d.title || '-') + '</td>' +
      '<td>' + escapeHtml(d.category || '-') + '</td>' +
      '<td>' + bid + '</td>' +
      '<td>' + escapeHtml(d.state || d.city || '-') + '</td>' +
      '<td>' + escapeHtml(d.city || '-') + '</td>' +
      '<td>' + escapeHtml(d.auction_type || '-') + '</td>' +
      '<td>' + escapeHtml(dateStr) + '</td>' +
      '<td>' + escapeHtml(d.source || '-') + '</td>' +
      '<td>' + link + '</td>';
    tbody.appendChild(tr);
  }});
}}

function escapeHtml(str) {{
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}}

function sortTable(col) {{
  if (sortCol === col) {{
    sortAsc = !sortAsc;
  }} else {{
    sortCol = col;
    sortAsc = true;
  }}
  const keys = ['title','category','current_bid','state','city','auction_type','auction_date','source'];
  const key = keys[col];
  filteredData.sort((a, b) => {{
    let va = a[key], vb = b[key];
    if (va == null) va = '';
    if (vb == null) vb = '';
    if (typeof va === 'number' && typeof vb === 'number') {{
      return sortAsc ? va - vb : vb - va;
    }}
    va = String(va).toLowerCase();
    vb = String(vb).toLowerCase();
    return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
  }});
  renderTable();
}}

function exportCSV() {{
  const headers = ['title','category','current_bid','minimum_bid','state','city','auction_type','auction_date','source','source_url','discount_percentage'];
  let csv = headers.join(',') + '\\n';
  filteredData.forEach(d => {{
    csv += headers.map(h => {{
      let v = d[h] != null ? String(d[h]) : '';
      if (v.includes(',') || v.includes('"') || v.includes('\\n')) {{
        v = '"' + v.replace(/"/g, '""') + '"';
      }}
      return v;
    }}).join(',') + '\\n';
  }});
  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'leiloes_brazil_filtered.csv';
  a.click();
  URL.revokeObjectURL(url);
}}

document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = build_html(data, generated_at)
    output_path = OUTPUT_DIR / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Static site generated: {output_path}")
    print(f"  - {len(data)} auction records embedded")
    print(f"  - Generated at: {generated_at}")
    print(f"  - Ready to deploy to Tiiny.host!")


if __name__ == "__main__":
    main()
