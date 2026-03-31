"""
🇧🇷 Leilões Brazil Dashboard – Interactive Streamlit dashboard for
exploring Brazilian auction data.
"""

import json
import os
import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import config

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="🇧🇷 Leilões Brazil Dashboard",
    page_icon="🇧🇷",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Demo / sample data generator
# ---------------------------------------------------------------------------

_SAMPLE_TITLES = {
    "Imóveis": [
        "Apartamento 3 quartos – Copacabana",
        "Casa 4 suítes com piscina – Alphaville",
        "Terreno 500m² – Florianópolis",
        "Sala comercial 80m² – Paulista",
        "Sobrado 2 andares – Curitiba",
        "Cobertura duplex – Barra da Tijuca",
        "Chácara 2.000m² – Campinas",
        "Loft moderno – Vila Madalena",
    ],
    "Veículos": [
        "Toyota Corolla 2022 – Prata",
        "Honda Civic 2021 – Branco",
        "VW Gol 2020 – Preto",
        "Chevrolet Onix 2023 – Vermelho",
        "Fiat Strada 2022 – Prata",
        "Hyundai HB20 2021 – Azul",
        "Ford Ranger 2020 – Branco",
        "Jeep Compass 2023 – Preto",
    ],
    "Máquinas & Equipamentos": [
        "Retroescavadeira CAT 416F2",
        "Trator John Deere 6130J",
        "Empilhadeira Toyota 2.5t",
        "Gerador Cummins 500kVA",
        "Compressor Atlas Copco",
        "Escavadeira Volvo EC210",
    ],
    "Bens de Consumo": [
        "Lote de eletrônicos – 50 itens",
        "Mobiliário de escritório completo",
        "Eletrodomésticos variados",
        "Equipamentos de informática",
        "Lote de smartphones",
    ],
    "Rural & Animais": [
        "Lote de 30 bovinos Nelore",
        "Lote de 15 cavalos Quarto de Milha",
        "Fazenda 200ha – Goiás",
        "Lote de ovinos – 50 cabeças",
    ],
    "Diversos": [
        "Lote judicial – bens diversos",
        "Acervo artístico – 20 peças",
        "Materiais de construção",
        "Equipamentos hospitalares",
        "Lote de sucata ferrosa",
    ],
}

_SAMPLE_CITIES = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
    ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
    ("Brasília", "DF"), ("Fortaleza", "CE"), ("Recife", "PE"),
    ("Manaus", "AM"), ("Florianópolis", "SC"), ("Goiânia", "GO"),
    ("Campinas", "SP"), ("Ribeirão Preto", "SP"), ("Joinville", "SC"),
    ("Londrina", "PR"), ("Niterói", "RJ"), ("Belém", "PA"),
    ("Vitória", "ES"), ("Natal", "RN"),
]

_SOURCES = [
    "superbid", "mega_leiloes", "zuk",
    "leiloes_brasil", "sodre_santoro", "leilao_vip",
]


def _generate_sample_data(n: int = 200) -> pd.DataFrame:
    """Create realistic-looking sample auction data."""
    rng = random.Random(42)
    rows = []
    categories = list(_SAMPLE_TITLES.keys())
    auction_types = config.AUCTION_TYPES

    base_date = datetime.now()

    for i in range(n):
        cat = rng.choice(categories)
        title = rng.choice(_SAMPLE_TITLES[cat])
        city, state = rng.choice(_SAMPLE_CITIES)
        source = rng.choice(_SOURCES)
        a_type = rng.choice(auction_types)
        days_offset = rng.randint(-10, 60)
        auction_date = (base_date + timedelta(days=days_offset)).isoformat()

        # Price ranges differ by category
        if cat == "Imóveis":
            min_bid = rng.uniform(80_000, 2_000_000)
        elif cat == "Veículos":
            min_bid = rng.uniform(15_000, 250_000)
        elif cat == "Máquinas & Equipamentos":
            min_bid = rng.uniform(20_000, 800_000)
        elif cat == "Rural & Animais":
            min_bid = rng.uniform(5_000, 500_000)
        else:
            min_bid = rng.uniform(500, 50_000)

        current_bid = min_bid * rng.uniform(1.0, 1.4)
        discount = rng.uniform(5, 55) if cat == "Imóveis" else None

        rows.append({
            "title": title,
            "description": f"Lote {i + 1:04d} – {title}",
            "category": cat,
            "current_bid": round(current_bid, 2),
            "minimum_bid": round(min_bid, 2),
            "discount_percentage": round(discount, 1) if discount else None,
            "auction_date": auction_date,
            "city": city,
            "state": state,
            "auction_type": a_type,
            "source": source,
            "source_url": f"https://example.com/auction/{i + 1}",
            "image_url": "",
            "scraped_at": datetime.now().isoformat(),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Load processed data or fall back to sample data."""
    json_path = os.path.join(config.PROCESSED_DIR, "all_auctions.json")
    if os.path.exists(json_path):
        try:
            df = pd.read_json(json_path)
            if not df.empty:
                st.sidebar.success(f"✅ Loaded {len(df)} real auctions")
                return df
        except Exception:
            pass

    st.sidebar.info("ℹ️ Using demo data – run scrapers for live results")
    return _generate_sample_data()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("🇧🇷 Leilões Brazil Dashboard")

    df = load_data()

    if df.empty:
        st.warning("No auction data available.")
        return

    # Ensure auction_date is datetime
    if "auction_date" in df.columns:
        df["auction_date"] = pd.to_datetime(df["auction_date"], errors="coerce")

    # ── Sidebar filters ──────────────────────────────────────────────────
    st.sidebar.header("🔍 Filters")

    categories = sorted(df["category"].dropna().unique())
    sel_categories = st.sidebar.multiselect("Category", categories, default=categories)

    states = sorted(df["state"].dropna().unique())
    sel_states = st.sidebar.multiselect("State (UF)", states, default=states)

    auction_types = sorted(df["auction_type"].dropna().unique())
    sel_types = st.sidebar.multiselect("Auction Type", auction_types, default=auction_types)

    price_col = "minimum_bid" if "minimum_bid" in df.columns else "current_bid"
    price_vals = df[price_col].dropna()
    if not price_vals.empty:
        p_min, p_max = float(price_vals.min()), float(price_vals.max())
        sel_price = st.sidebar.slider(
            "Price range (R$)",
            min_value=p_min,
            max_value=p_max,
            value=(p_min, p_max),
            format="R$ %,.0f",
        )
    else:
        sel_price = (0.0, 0.0)

    if "auction_date" in df.columns:
        valid_dates = df["auction_date"].dropna()
        if not valid_dates.empty:
            d_min = valid_dates.min().date()
            d_max = valid_dates.max().date()
            sel_dates = st.sidebar.date_input(
                "Date range",
                value=(d_min, d_max),
                min_value=d_min,
                max_value=d_max,
            )
        else:
            sel_dates = None
    else:
        sel_dates = None

    # ── Apply filters ─────────────────────────────────────────────────────
    mask = (
        df["category"].isin(sel_categories)
        & df["state"].isin(sel_states)
        & df["auction_type"].isin(sel_types)
    )
    if price_col in df.columns:
        mask = mask & (
            df[price_col].fillna(0).between(sel_price[0], sel_price[1])
        )
    if sel_dates and len(sel_dates) == 2 and "auction_date" in df.columns:
        start_dt = pd.Timestamp(sel_dates[0])
        end_dt = pd.Timestamp(sel_dates[1])
        mask = mask & (
            df["auction_date"].between(start_dt, end_dt) | df["auction_date"].isna()
        )

    filtered = df[mask].copy()

    # ── KPI cards ─────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Total Auctions", f"{len(filtered):,}")

    with col2:
        if "discount_percentage" in filtered.columns:
            avg_disc = filtered["discount_percentage"].dropna().mean()
            st.metric("💰 Avg Discount", f"{avg_disc:.1f}%" if pd.notna(avg_disc) else "N/A")
        else:
            st.metric("💰 Avg Discount", "N/A")

    with col3:
        if "auction_date" in filtered.columns:
            now = pd.Timestamp.now()
            week_ahead = now + pd.Timedelta(days=7)
            this_week = filtered[
                filtered["auction_date"].between(now, week_ahead)
            ]
            st.metric("📅 This Week", f"{len(this_week):,}")
        else:
            st.metric("📅 This Week", "N/A")

    with col4:
        n_sources = filtered["source"].nunique() if "source" in filtered.columns else 0
        st.metric("🌐 Sources", n_sources)

    st.divider()

    # ── Data table ────────────────────────────────────────────────────────
    st.subheader("📋 Auction Listings")

    display_cols = [
        c for c in [
            "title", "category", "minimum_bid", "current_bid",
            "auction_date", "city", "state", "auction_type", "source",
            "source_url",
        ] if c in filtered.columns
    ]
    st.dataframe(
        filtered[display_cols].sort_values("auction_date", ascending=True, na_position="last"),
        use_container_width=True,
        height=400,
    )

    # CSV export
    csv_data = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name="leiloes_brazil_filtered.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Auctions by Category")
        cat_counts = filtered["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig_cat = px.bar(
            cat_counts, x="Category", y="Count", color="Category",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_cat.update_layout(showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)

    with chart_col2:
        st.subheader("🗺️ Auctions by State")
        state_counts = filtered["state"].value_counts().head(15).reset_index()
        state_counts.columns = ["State", "Count"]
        fig_state = px.bar(
            state_counts, x="State", y="Count", color="State",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_state.update_layout(showlegend=False)
        st.plotly_chart(fig_state, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.subheader("🏷️ Auction Types")
        type_counts = filtered["auction_type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        fig_type = px.pie(
            type_counts, names="Type", values="Count",
            color_discrete_sequence=px.colors.qualitative.Pastel2,
        )
        st.plotly_chart(fig_type, use_container_width=True)

    with chart_col4:
        st.subheader("📅 Upcoming Auctions (next 30 days)")
        if "auction_date" in filtered.columns:
            future = filtered[
                filtered["auction_date"] >= pd.Timestamp.now()
            ].copy()
            if not future.empty:
                future["date_only"] = future["auction_date"].dt.date
                daily = future.groupby("date_only").size().reset_index(name="Count")
                daily.columns = ["Date", "Count"]
                fig_time = px.line(
                    daily, x="Date", y="Count", markers=True,
                )
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("No upcoming auctions in the filtered data.")
        else:
            st.info("No date information available.")

    # ── Map visualisation ─────────────────────────────────────────────────
    if "lat" in filtered.columns and "lon" in filtered.columns:
        map_data = filtered.dropna(subset=["lat", "lon"])
        if not map_data.empty:
            st.subheader("🗺️ Auction Locations")
            st.map(map_data[["lat", "lon"]])


if __name__ == "__main__":
    main()
