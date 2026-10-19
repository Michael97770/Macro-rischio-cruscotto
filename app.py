import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(
    page_title="Macro Risk Radar | Private Credit, Tech & Systemic Risk",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo & Descrizione
st.title("🌐 Macro Risk & Liquidity Radar")
st.markdown("""
*Dashboard integrata per l'analisi del rischio sistemico, drenaggio di liquidità, debito corporate e ciclo tecnologico.*
""")

# ==========================================
# 1. FUNZIONI DI SCARICAMENTO DATI (FRED & YAHOO)
# ==========================================
@st.cache_data(ttl=3600)  # Cache 1 ora
def load_fred_data(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        df = pd.read_csv(url, index_col=0, parse_dates=True)
        df.columns = [series_id]
        df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
        df = df.dropna()
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_yahoo_data(ticker, period="3y"):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df = df['Close']
        else:
            df = df[['Close']]
        df.columns = [ticker]
        return df.dropna()
    except Exception:
        return pd.DataFrame()

with st.spinner("Aggiornamento dati macroeconomici e mercati in tempo reale..."):
    # Dati FRED
    hy_spread = load_fred_data("BAMLH0A0HYM2")       # 1. HY Spread
    ccc_spread = load_fred_data("BAMLH0A3HYC")       # 2. CCC Spread
    unrate = load_fred_data("UNRATE")               # Disoccupazione USA
    sahm = load_fred_data("SAHMREALTIME")           # Sahm Rule
    t10y2y = load_fred_data("T10Y2Y")               # Curva 10Y-2Y
    
    # Dati Yahoo Finance
    owl = load_yahoo_data("OWL")                    # Blue Owl (Private Credit)
    bizd = load_yahoo_data("BIZD")                  # BDC ETF
    nvda = load_yahoo_data("NVDA")                  # Nvidia
    mags = load_yahoo_data("MAGS")                  # Mag 7 ETF
    rsp = load_yahoo_data("RSP")                    # S&P Equal Weight
    sox = load_yahoo_data("^SOX")                   # Philly Semiconductor
    ndx = load_yahoo_data("^NDX")                   # Nasdaq 100
    gold = load_yahoo_data("GC=F")                  # Oro
    vix = load_yahoo_data("^VIX")                   # VIX
    btc = load_yahoo_data("BTC-USD")                # Bitcoin

# Calcolo Ratio
ratio_ccc_hy = pd.DataFrame()
if not ccc_spread.empty and not hy_spread.empty:
    merged_credit = pd.concat([ccc_spread, hy_spread], axis=1).dropna()
    ratio_ccc_hy = (merged_credit["BAMLH0A3HYC"] / merged_credit["BAMLH0A0HYM2"]).to_frame("CCC_HY_Ratio")

ratio_sox_ndx = pd.DataFrame()
if not sox.empty and not ndx.empty:
    merged_tech = pd.concat([sox, ndx], axis=1).dropna()
    ratio_sox_ndx = (merged_tech["^SOX"] / merged_tech["^NDX"]).to_frame("SOX_NDX_Ratio")

ratio_gold_ndx = pd.DataFrame()
if not gold.empty and not ndx.empty:
    merged_gold = pd.concat([gold, ndx], axis=1).dropna()
    ratio_gold_ndx = (merged_gold["GC=F"] / merged_gold["^NDX"]).to_frame("Gold_NDX_Ratio")

# ==========================================
# 2. IL GRAFICO A CIPOLLA DEL RISCHIO (SUNBURST)
# ==========================================
st.subheader("🧅 Il Radar a Cipolla: Dalle Big Tech (Centro) al Junk Debt (Esterno)")
st.caption("Il modello mostra la fragilità concentrica: il centro (Big Tech) resiste ed è solido (Verde); l'anello esterno (Junk / Private Credit) subisce le prime crepe della bolla (Rosso).")

# Struttura Gerarchica per il Grafico a Cipolla
onion_data = {
    "ids": [
        "Core", "Mid_Layer", "Outer_Junk",
        # Livello 0: Centro (Fortezza / Big Tech)
        "Nvidia", "MagSeven",
        # Livello 1: Mercato & Capex AI
        "EqualWeight_RSP", "Semis_Ratio_SOX_NDX", "Gold_NDX_Ratio",
        # Livello 2: Private Credit & Fragilità Corporate
        "BlueOwl_Credit", "BIZD_BDC", "Tech_Bonds_Stress",
        # Livello 3: Esterno (Junk / Già in Allarme / Bolla Spazzatura)
        "CCC_Spread", "CCC_HY_Ratio", "HY_Spread", "Sahm_Recession_Risk", "VIX_Stress"
    ],
    "labels": [
        "NUCLEO: Big Tech<br>(Intatte / Cassa)", 
        "ANELLO 1: Ciclo AI<br>& Ampiezza Mercato", 
        "ANELLO 2: Junk Debt<br>& Private Credit",
        "Nvidia (NVDA)", "Mag 7 (MAGS)",
        "RSP (S&P Equal Weight)", "SOX / NDX (Semis vs Tech)", "Oro / NDX (Hedge)",
        "Blue Owl (OWL)", "BIZD (BDC / Private Credit)", "Long Tech Bonds (ORCL/GOOGL)",
        "Spread CCC (BAMLH0A3HYC)", "Ratio CCC / HY", "Spread High Yield (HY)", "Sahm Rule (Disoccupazione)", "VIX Volatility"
    ],
    "parents": [
        "", "", "",
        "Core", "Core",
        "Mid_Layer", "Mid_Layer", "Mid_Layer",
        "Outer_Junk", "Outer_Junk", "Outer_Junk",
        "Outer_Junk", "Outer_Junk", "Outer_Junk", "Outer_Junk", "Outer_Junk"
    ],
    "status_color": [
        "#10b981", "#f59e0b", "#ef4444",  # Verde (Centro), Giallo (Mid), Rosso (Esterno)
        "#10b981", "#10b981",              # Big Tech: Verde
        "#f59e0b", "#f59e0b", "#10b981",  # Mid layer
        "#f97316", "#ef4444", "#f97316",  # Private credit: Arancio/Rosso
        "#ef4444", "#dc2626", "#f97316", "#ef4444", "#f59e0b" # Junk: Rosso intenso
    ],
    "risk_level": [
        "Nucleo: Basso Rischio Immediato", "Rischio Intermedio: Divergenze", "Rischio Alto: Stress da Debito",
        "Leader Indiscusso AI", "Concentrazione Massima Indici",
        "Ampiezza S&P debole se diverge da SPY", "Valutazione estrema semiconduttori", "Copertura monetaria attiva",
        "Esposizione Debito AI Data Center", "Prestiti Diretti / Zombie Risk", "Pressione sui rendimenti lunghi",
        "Primi a fallire / Rifinanziamento impossibile", "Canarina nella miniera del credito", "Indice generale stress HY",
        "Trigger recessione macro", "Stress emotivo opzioni"
    ]
}

fig_sunburst = go.Figure(go.Sunburst(
    ids=onion_data["ids"],
    labels=onion_data["labels"],
    parents=onion_data["parents"],
    hovertext=onion_data["risk_level"],
    marker=dict(colors=onion_data["status_color"]),
    branchvalues="total",
    insidetextorientation='horizontal'
))

fig_sunburst.update_layout(
    margin=dict(t=10, l=10, r=10, b=10),
    height=600,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white", size=13)
)
st.plotly_chart(fig_sunburst, use_container_width=True)

# ==========================================
# 3. PANNELLO DETTAGLIO GRAFICI (SERIE TEMPORALI)
# ==========================================
st.markdown("---")
st.subheader("📈 Analisi Dettagliata delle Serie Macro e di Mercato")

tab1, tab2, tab3 = st.tabs(["🔥 Canale Credito & Junk Debt", "💻 AI, Big Tech & Mercato", "📊 Macro USA & Recession Indicators"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        if not ccc_spread.empty and not hy_spread.empty:
            fig_credit = go.Figure()
            fig_credit.add_trace(go.Scatter(x=hy_spread.index, y=hy_spread["BAMLH0A0HYM2"], name="Spread HY USA (OAS)"))
            fig_credit.add_trace(go.Scatter(x=ccc_spread.index, y=ccc_spread["BAMLH0A3HYC"], name="Spread CCC & Lower"))
            fig_credit.update_layout(title="FRED: Spread Credito High Yield vs CCC", template="plotly_dark")
            st.plotly_chart(fig_credit, use_container_width=True)
            
    with col2:
        if not ratio_ccc_hy.empty:
            fig_ratio = px.line(ratio_ccc_hy, title="Ratio Stress: Spread CCC / HY (FRED)", template="plotly_dark")
            fig_ratio.update_traces(line_color="#ef4444")
            st.plotly_chart(fig_ratio, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        if not bizd.empty:
            fig_bizd = px.line(bizd, title="AMEX: BIZD (VanEck BDC / Private Credit Proxy)", template="plotly_dark")
            st.plotly_chart(fig_bizd, use_container_width=True)
    with col4:
        if not owl.empty:
            fig_owl = px.line(owl, title="NYSE: OWL (Blue Owl Capital - AI Private Debt)", template="plotly_dark")
            fig_owl.update_traces(line_color="#f97316")
            st.plotly_chart(fig_owl, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        if not nvda.empty:
            fig_nvda = px.line(nvda, title="NASDAQ: NVDA (Il Nucleo Sano della Cipolla)", template="plotly_dark")
            fig_nvda.update_traces(line_color="#10b981")
            st.plotly_chart(fig_nvda, use_container_width=True)
    with col2:
        if not ratio_sox_ndx.empty:
            fig_sox = px.line(ratio_sox_ndx, title="Ratio: Semiconduttori vs Nasdaq 100 (^SOX / ^NDX)", template="plotly_dark")
            st.plotly_chart(fig_sox, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        if not rsp.empty:
            fig_rsp = px.line(rsp, title="AMEX: RSP (S&P 500 Equal Weight - Ampiezza Reale)", template="plotly_dark")
            st.plotly_chart(fig_rsp, use_container_width=True)
    with col4:
        if not ratio_gold_ndx.empty:
            fig_gold = px.line(ratio_gold_ndx, title="Ratio: Oro / Nasdaq 100 (Hard Asset vs Tech Capex)", template="plotly_dark")
            fig_gold.update_traces(line_color="#eab308")
            st.plotly_chart(fig_gold, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        if not unrate.empty and not sahm.empty:
            fig_macro = go.Figure()
            fig_macro.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Tasso Disoccupazione USA (%)"))
            fig_macro.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Indicatore Recessione Sahm"))
            fig_macro.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Trigger Recessione (0.5)")
            fig_macro.update_layout(title="Disoccupazione & Sahm Rule (FRED)", template="plotly_dark")
            st.plotly_chart(fig_macro, use_container_width=True)
    with col2:
        if not t10y2y.empty:
            fig_curve = px.line(t10y2y, title="Curva dei Rendimenti USA 10Y - 2Y (T10Y2Y)", template="plotly_dark")
            fig_curve.add_hline(y=0.0, line_dash="dash", line_color="white")
            fig_curve.update_traces(line_color="#38bdf8")
            st.plotly_chart(fig_curve, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        if not vix.empty:
            fig_vix = px.line(vix, title="CBOE: VIX Volatility Index", template="plotly_dark")
            fig_vix.update_traces(line_color="#f43f5e")
            st.plotly_chart(fig_vix, use_container_width=True)
    with col4:
        if not btc.empty:
            fig_btc = px.line(btc, title="BTC-USD & Ciclo Macro Crypto", template="plotly_dark")
            fig_btc.update_traces(line_color="#f59e0b")
            st.plotly_chart(fig_btc, use_container_width=True)

st.sidebar.title("Parametri Radar")
st.sidebar.info("""
**Logica Operativa:**
- Se l'anello esterno (Junk / CCC / Sahm) entra in allerta rossa ma NVDA resta verde: **Fase di Divergenza Tardiva**.
- Se BIZD e OWL scendono mentre l'Oro/NDX sale: **Fuga verso la sicurezza**.
- Il link di questa pagina può essere condiviso direttamente con i propri soci e colleghi investitori.
""")
