"""Streamlit Dashboard for Leiloes Brazil"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import config

st.set_page_config(page_title="Leiloes Brazil Dashboard", page_icon="🇧🇷", layout="wide")

CATEGORIES = ["Imoveis", "Veiculos", "Maquinas", "Bens de Consumo", "Rural", "Diversos"]
STATES = ["SP","RJ","MG","BA","PR","RS","SC","GO","PE","CE","PA","MA","MT","MS","DF","ES","PB","RN","AL","PI","SE","RO","TO","AC","AP","AM","RR"]
SOURCES = ["Superbid", "Mega Leiloes", "Zuk", "Leiloes Brasil", "Sodre Santoro", "Leilao VIP",
    "Leiloes Judiciais", "E-Leiloes", "Frazao Leiloes", "Sold", "Nucleo Leiloes", "Mapa do Leilao"]
TYPES = ["Judicial", "Extrajudicial", "Venda Direta", "Corporativo"]
CITIES = {"SP": ["Sao Paulo","Campinas","Santos","Ribeirao Preto","Sorocaba"],
    "RJ": ["Rio de Janeiro","Niteroi","Petropolis","Volta Redonda"],
    "MG": ["Belo Horizonte","Uberlandia","Juiz de Fora","Contagem"],
    "BA": ["Salvador","Feira de Santana","Vitoria da Conquista"],
    "PR": ["Curitiba","Londrina","Maringa","Foz do Iguacu"],
    "RS": ["Porto Alegre","Caxias do Sul","Pelotas"],
    "SC": ["Florianopolis","Joinville","Blumenau"],
    "GO": ["Goiania","Aparecida de Goiania"],
    "PE": ["Recife","Olinda","Jaboatao"],
    "CE": ["Fortaleza","Caucaia","Juazeiro do Norte"]}
IMOVEIS_TITLES = ["Apartamento 3 quartos","Casa 2 quartos com garagem","Terreno 500m2","Sala Comercial 80m2",
    "Galpao Industrial 1200m2","Sitio 5 hectares","Cobertura Duplex","Flat Mobiliado","Loja Comercial",
    "Casa de Praia","Apartamento Studio","Sobrado 4 quartos"]
VEICULOS_TITLES = ["VW Gol 2019","Fiat Strada 2020","Toyota Corolla 2021","Honda Civic 2018",
    "Chevrolet Onix 2022","Hyundai HB20 2020","Ford Ranger 2019","Mercedes Sprinter 2018",
    "Yamaha Factor 150 2021","Honda CG 160 2020","Scania R450 2017","Volvo FH 540 2019"]


def generate_demo_data(n=200):
    data = []
    for i in range(n):
        cat = random.choice(CATEGORIES)
        state = random.choice(STATES[:15])
        city_list = CITIES.get(state, ["Capital"])
        titles = IMOVEIS_TITLES if cat == "Imoveis" else VEICULOS_TITLES if cat == "Veiculos" else [f"Lote {cat} #{i}"]
        base_price = random.uniform(10000, 2000000) if cat == "Imoveis" else random.uniform(5000, 300000)
        discount = random.randint(10, 60)
        data.append({
            "title": random.choice(titles),
            "category": cat,
            "current_bid": round(base_price * (1 - discount/100), 2),
            "minimum_bid": round(base_price * (1 - discount/100) * 0.8, 2),
            "market_value": round(base_price, 2),
            "discount_percentage": discount,
            "auction_date": (datetime.now() + timedelta(days=random.randint(-5, 30))).strftime("%Y-%m-%d"),
            "city": random.choice(city_list),
            "state": state,
            "auction_type": random.choice(TYPES),
            "source": random.choice(SOURCES),
            "source_url": f"https://example.com/lote/{i+1}",
            "scraped_at": datetime.now().isoformat(),
        })
    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
def load_data():
    data_path = config.PROCESSED_DIR / config.COMBINED_OUTPUT_FILE
    if data_path.exists():
        try:
            df = pd.read_json(data_path)
            if len(df) > 0:
                return df
        except Exception:
            pass
    return generate_demo_data(250)


def main():
    st.title("🇧🇷 Leiloes Brazil Dashboard")
    st.markdown("**Painel de leiloes do Brasil** - Dados agregados de 6+ plataformas de leilao")
    df = load_data()
    if "auction_date" in df.columns:
        df["auction_date"] = pd.to_datetime(df["auction_date"], errors="coerce")

    # Sidebar Filters
    st.sidebar.header("🔍 Filtros")
    categories = st.sidebar.multiselect("Categoria", options=sorted(df["category"].dropna().unique()), default=sorted(df["category"].dropna().unique()))
    states = st.sidebar.multiselect("Estado", options=sorted(df["state"].dropna().unique()), default=sorted(df["state"].dropna().unique()))
    auction_types = st.sidebar.multiselect("Tipo de Leilao", options=sorted(df["auction_type"].dropna().unique()), default=sorted(df["auction_type"].dropna().unique()))
    if "current_bid" in df.columns:
        min_p, max_p = float(df["current_bid"].min() or 0), float(df["current_bid"].max() or 1000000)
        price_range = st.sidebar.slider("Faixa de Preco (R$)", min_p, max_p, (min_p, max_p), format="R$ %.0f")
    else:
        price_range = (0, 9999999)
    sources = st.sidebar.multiselect("Fonte", options=sorted(df["source"].dropna().unique()), default=sorted(df["source"].dropna().unique()))

    # Apply filters
    mask = (df["category"].isin(categories)) & (df["state"].isin(states)) & (df["auction_type"].isin(auction_types)) & (df["source"].isin(sources))
    if "current_bid" in df.columns:
        mask = mask & (df["current_bid"] >= price_range[0]) & (df["current_bid"] <= price_range[1])
    filtered = df[mask]

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Leiloes", f"{len(filtered):,}")
    avg_discount = filtered["discount_percentage"].mean() if ("discount_percentage" in filtered.columns and len(filtered) > 0) else 0
    col2.metric("💰 Desconto Medio", f"{avg_discount:.0f}%" if pd.notna(avg_discount) else "0%")
    if "auction_date" in filtered.columns:
        now = pd.Timestamp(datetime.now())
        week_mask = (filtered["auction_date"] >= now) & (filtered["auction_date"] <= now + timedelta(days=7))
        col3.metric("📅 Esta Semana", f"{week_mask.sum():,}")
    else:
        col3.metric("📅 Esta Semana", "-")
    col4.metric("🌐 Fontes Ativas", f"{filtered['source'].nunique()}")
    st.divider()

    if len(filtered) == 0:
        st.warning("Nenhum leilao encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
    else:
        # Charts Row
        chart1, chart2 = st.columns(2)
        with chart1:
            st.subheader("Leiloes por Categoria")
            cat_counts = filtered["category"].value_counts().reset_index()
            cat_counts.columns = ["Categoria", "Quantidade"]
            fig1 = px.bar(cat_counts, x="Categoria", y="Quantidade", color="Categoria", color_discrete_sequence=px.colors.qualitative.Set2)
            fig1.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig1, use_container_width=True)
        with chart2:
            st.subheader("Leiloes por Estado (Top 10)")
            state_counts = filtered["state"].value_counts().head(10).reset_index()
            state_counts.columns = ["Estado", "Quantidade"]
            fig2 = px.bar(state_counts, x="Estado", y="Quantidade", color="Quantidade", color_continuous_scale="Viridis")
            fig2.update_layout(height=350)
            st.plotly_chart(fig2, use_container_width=True)

        chart3, chart4 = st.columns(2)
        with chart3:
            st.subheader("Tipos de Leilao")
            type_counts = filtered["auction_type"].value_counts().reset_index()
            type_counts.columns = ["Tipo", "Quantidade"]
            fig3 = px.pie(type_counts, values="Quantidade", names="Tipo", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig3.update_layout(height=350)
            st.plotly_chart(fig3, use_container_width=True)
        with chart4:
            st.subheader("Leiloes por Fonte")
            src_counts = filtered["source"].value_counts().reset_index()
            src_counts.columns = ["Fonte", "Quantidade"]
            fig4 = px.bar(src_counts, x="Fonte", y="Quantidade", color="Fonte", color_discrete_sequence=px.colors.qualitative.Bold)
            fig4.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig4, use_container_width=True)

        # Data Table
        st.divider()
        st.subheader("📋 Lista de Leiloes")
        display_cols = [c for c in ["title","category","current_bid","state","city","auction_type","auction_date","source","source_url"] if c in filtered.columns]
        st.dataframe(filtered[display_cols].sort_values("auction_date", ascending=True, na_position="last"), use_container_width=True, height=400)

        # Export
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Exportar CSV", csv, "leiloes_brazil_filtered.csv", "text/csv")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Leiloes Brazil** v1.0")
    st.sidebar.markdown(f"Ultima atualizacao: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


if __name__ == "__main__":
    main()
