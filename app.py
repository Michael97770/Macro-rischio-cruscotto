import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET

# ==========================================
# CONFIGURAZIONE INTERFACCIA E TEMA SCURO
# ==========================================
st.set_page_config(
    page_title="Macro Risk Terminal | Market Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Iniezione CSS ad Altissimo Contrasto: Bianco Puro, Niente Toni Grigi
st.markdown("""
<style>
/* Reset sfondo generale */
.stApp {
    background-color: #07090e !important;
    color: #ffffff !important;
}

/* FORZATURA TESTI BIANCHI PER CONTROLLI E RADIO BUTTON */
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] p,
div[data-testid="stRadio"] span {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 15px !important;
}

/* CARD METRICHE SUPERIORI (HTML PURO) */
.metric-card-custom {
    background: linear-gradient(145deg, #131c2e, #0a101b);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    height: 100%;
    position: relative;
}
.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.metric-title-custom {
    color: #ffffff !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
.metric-val-custom {
    color: #38bdf8 !important;
    font-size: 32px !important;
    font-weight: 900 !important;
    line-height: 1.1;
    margin-bottom: 6px;
}
.metric-sub-custom {
    font-size: 13px !important;
    font-weight: 800 !important;
}

/* TOOLTIP PERSONALIZZATO AD ALTO CONTRASTO */
.tooltip-wrap {
    position: relative;
    display: inline-block;
    cursor: pointer;
}
.help-icon {
    background: #1e293b;
    color: #38bdf8;
    border: 1px solid #38bdf8;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
}
.tooltip-box {
    display: none;
    position: absolute;
    right: 0;
    top: 25px;
    z-index: 9999;
    background: #0f172a;
    border: 1.5px solid #38bdf8;
    color: #ffffff;
    padding: 14px;
    border-radius: 8px;
    width: 290px;
    font-size: 12.5px;
    line-height: 1.5;
    box-shadow: 0 10px 30px rgba(0,0,0,0.9);
}
.tooltip-wrap:hover .tooltip-box {
    display: block;
}

/* NOTIZIARIO LATERALE CON SCROLL */
.news-box-side {
    background: linear-gradient(145deg, #10192a, #0b111e);
    border: 1.5px solid #38bdf8;
    border-radius: 10px;
    padding: 14px 16px;
    height: 260px;
    overflow-y: auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}
.news-box-side::-webkit-scrollbar {
    width: 6px;
}
.news-box-side::-webkit-scrollbar-thumb {
    background-color: #38bdf8;
    border-radius: 4px;
}
.news-row {
    padding: 8px 0;
    border-bottom: 1px solid #1e293b;
    font-size: 12.5px;
    line-height: 1.4;
}
.news-row:last-child {
    border-bottom: none;
}
.news-tag {
    color: #38bdf8;
    font-weight: 800;
    font-size: 11px;
}
.news-anchor {
    color: #ffffff !important;
    text-decoration: none;
    font-weight: 600;
}
.news-anchor:hover {
    color: #38bdf8 !important;
    text-decoration: underline;
}

/* BANNER ALLARMI */
.alert-strip {
    background: #0f172a;
    border-left: 5px solid #ef4444;
    border-radius: 8px;
    padding: 12px 18px;
    margin: 15px 0 25px 0;
}

/* RAPPORTO DI ANALISI ESECUTIVO */
.report-panel {
    background: linear-gradient(145deg, #10192a, #080d16);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 24px;
    margin: 20px 0;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
}
.pillar-card-ui {
    background-color: #141f33;
    border-radius: 8px;
    padding: 18px;
    border-top: 3px solid #38bdf8;
    height: 100%;
}
.custom-matrix-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
.custom-matrix-table th {
    background-color: #1e293b;
    color: #ffffff;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 800;
}
.custom-matrix-table td {
    padding: 12px;
    border-bottom: 1px solid #1e293b;
    font-size: 13.5px;
    color: #ffffff;
}

/* GUIDA E APPROFONDIMENTO MACRO */
.chart-header-title {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 800 !important;
    margin-bottom: 4px;
}
.macro-depth-box {
    background-color: #0b1324;
    border-left: 4px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-top: 8px;
    font-size: 13.5px;
    line-height: 1.6;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.title("🌐 Macro Risk & Liquidity Intelligence Terminal")
st.markdown("<span style='color:#ffffff; font-size:15px; font-weight:600;'>Terminale di posizionamento ciclico, Fed Net Liquidity, debito infrastrutturale e asimmetrie di mercato.</span>", unsafe_allow_html=True)

# ==========================================
# FEED NOTIZIARIO FINANZIARIO & CRYPTO LIVE
# ==========================================
@st.cache_data(ttl=900)
def fetch_live_news():
    news_items = []
    feed_urls = [
        ("Macro USA", "https://finance.yahoo.com/news/rssindex"),
        ("Crypto Live", "https://cointelegraph.com/rss")
    ]
    for category, url in feed_urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=4)
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            count = 0
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else "#"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                time_str = pub_date[17:22] if len(pub_date) >= 22 else "Live"
                news_items.append({"category": category, "time": time_str, "title": title, "link": link})
                count += 1
                if count >= 4:
                    break
        except Exception:
            continue
    return news_items

news_feed = fetch_live_news()

# ==========================================
# ACQUISIZIONE DATI (FRED & YAHOO OHLC)
# ==========================================
@st.cache_data(ttl=3600)
def load_fred_data(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        df = pd.read_csv(url, index_col=0, parse_dates=True)
        df.columns = [series_id]
        df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
        return df.dropna()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_yahoo_ohlc(ticker, period="5y"):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, level=1, axis=1) if ticker in df.columns.levels[1] else df.droplevel(1, axis=1)
        return df.dropna()
    except Exception:
        return pd.DataFrame()

with st.spinner("Acquisizione feed macroeconomici, liquidità della Fed e mercati..."):
    # FRED Macro & Credito
    hy_spread = load_fred_data("BAMLH0A0HYM2")
    ccc_spread = load_fred_data("BAMLH0A3HYC")
    unrate = load_fred_data("UNRATE")
    sahm = load_fred_data("SAHMREALTIME")
    t10y2y = load_fred_data("T10Y2Y")
    
    # FED NET LIQUIDITY COMPONENTS
    walcl = load_fred_data("WALCL")          # Fed Total Assets (Milioni $)
    wtregen = load_fred_data("WTREGEN")      # Treasury General Account (Milioni $)
    rrp = load_fred_data("RRPONTSYD")        # Reverse Repo (Miliardi $)
    
    # YAHOO FINANCE
    owl = load_yahoo_ohlc("OWL")
    bizd = load_yahoo_ohlc("BIZD")
    nvda = load_yahoo_ohlc("NVDA")
    mags = load_yahoo_ohlc("MAGS")
    rsp = load_yahoo_ohlc("RSP")
    sox = load_yahoo_ohlc("^SOX")
    ndx = load_yahoo_ohlc("^NDX")
    skhynix = load_yahoo_ohlc("000660.KS")
    gold = load_yahoo_ohlc("GC=F")
    vix = load_yahoo_ohlc("^VIX")
    btc = load_yahoo_ohlc("BTC-USD")

# Calcolo Fed Net Liquidity (in Trilioni di Dollari)
net_liquidity = pd.DataFrame()
if not walcl.empty and not wtregen.empty and not rrp.empty:
    m_liq = pd.concat([walcl, wtregen, rrp], axis=1).ffill().dropna()
    # Formula: (WALCL - WTREGEN - RRP*1000) / 1,000,000
    net_liquidity = ((m_liq["WALCL"] - m_liq["WTREGEN"] - m_liq["RRPONTSYD"] * 1000) / 1_000_000).to_frame("Net_Liquidity_Trillion")

# Ratios
ratio_ccc_hy = pd.DataFrame()
if not ccc_spread.empty and not hy_spread.empty:
    m_cred = pd.concat([ccc_spread, hy_spread], axis=1).dropna()
    ratio_ccc_hy = (m_cred["BAMLH0A3HYC"] / m_cred["BAMLH0A0HYM2"]).to_frame("Ratio_CCC_HY")

ratio_sox_ndx = pd.DataFrame()
if not sox.empty and not ndx.empty:
    m_tech = pd.concat([sox["Close"], ndx["Close"]], axis=1).dropna()
    ratio_sox_ndx = (m_tech.iloc[:, 0] / m_tech.iloc[:, 1]).to_frame("Ratio_SOX_NDX")

ratio_gold_ndx = pd.DataFrame()
if not gold.empty and not ndx.empty:
    m_gold = pd.concat([gold["Close"], ndx["Close"]], axis=1).dropna()
    ratio_gold_ndx = (m_gold.iloc[:, 0] / m_gold.iloc[:, 1]).to_frame("Ratio_Gold_NDX")

# Valori Attuali
curr_sahm = float(sahm.iloc[-1].values[0]) if not sahm.empty else 0.0
curr_curve = float(t10y2y.iloc[-1].values[0]) if not t10y2y.empty else 0.0
curr_ratio_cred = float(ratio_ccc_hy.iloc[-1].values[0]) if not ratio_ccc_hy.empty else 3.0
curr_vix = float(vix["Close"].iloc[-1]) if not vix.empty else 15.0
curr_net_liq = float(net_liquidity.iloc[-1].values[0]) if not net_liquidity.empty else 5.80

# Calcolo Rischio Sistemico (0-100)
risk_score = 0
allerta_list = []

if curr_sahm >= 0.50: 
    risk_score += 35
    allerta_list.append("Regola di Sahm Attiva (Trigger Recessionario USA)")
elif curr_sahm >= 0.35: 
    risk_score += 20
    allerta_list.append("Deterioramento Occupazione USA (Sahm > 0.35)")

if curr_curve > 0 and not t10y2y.empty and (t10y2y.tail(180).min().values[0] < -0.2):
    risk_score += 25
    allerta_list.append("Disinversione Curva dei Rendimenti (Fase Storica Pre-Recessiva)")
elif curr_curve < 0:
    risk_score += 15

if curr_ratio_cred > 3.8: 
    risk_score += 25
    allerta_list.append("Stress Acuto Debito CCC: Contrazione Liquidità Emittenti Deboli")
elif curr_ratio_cred > 3.4: 
    risk_score += 15
    allerta_list.append("Spread Credito Spazzatura in Allargamento")

if curr_vix > 25: 
    risk_score += 15
    allerta_list.append("Volatilità Azionaria Elevata (VIX > 25)")
elif curr_vix > 20: 
    risk_score += 8

risk_score = min(risk_score, 100)

# Diagnosi di Ciclo e Runway Temporale
if curr_sahm >= 0.50:
    fase_ciclo = "Fase 4: Rischio Recessione Confermato"
    runway_desc = "Finestra di tolleranza esaurita. Elevato rischio di ribasso sui titoli ciclici."
elif curr_curve > 0 and risk_score >= 45:
    fase_ciclo = "Fase 3: Fine Ciclo (Disinversione della Curva)"
    runway_desc = "Finestra stimata: 3 - 8 Mesi prima del massimo stress sistemico. Fase classica di rotazione difensiva."
elif not ratio_sox_ndx.empty and ratio_sox_ndx.iloc[-1].values[0] > ratio_sox_ndx.tail(252).quantile(0.85).values[0]:
    fase_ciclo = "Fase 2: Espansione Concentrata AI Capex"
    runway_desc = "Finestra stimata: 6 - 12 Mesi di liquidità residua, ma con ampiezza ristretta alle mega-cap."
else:
    fase_ciclo = "Fase 1: Espansione Sincrona"
    runway_desc = "Finestra favorevole: 12+ Mesi. Contesto favorevole all'accumulazione azionaria."

# ==========================================
# SEZIONE SUPERIORE: 4 METRICHE (A SINISTRA) + NOTIZIARIO LIVE (A DESTRA)
# ==========================================
col_metrics_grid, col_news_side = st.columns([3, 1.1])

with col_metrics_grid:
    m_c1, m_c2 = st.columns(2)
    m_c3, m_c4 = st.columns(2)
    
    col_status = "#ef4444" if risk_score > 60 else ("#f59e0b" if risk_score > 35 else "#10b981")
    delta_text = "RISCHIO ELEVATO" if risk_score > 60 else ("ATTENZIONE" if risk_score > 35 else "CONDIZIONI NORMALI")
    with m_c1:
        st.markdown(f"""
        <div class="metric-card-custom">
            <div class="metric-header">
                <span class="metric-title-custom">Indice Rischio Sistemico</span>
                <div class="tooltip-wrap">
                    <span class="help-icon">?</span>
                    <div class="tooltip-box">
                        <b>COSA SIGNIFICA:</b> Sintesi quantitativa da 0 a 100 che aggrega Debito Spazzatura, Curva dei Tassi, Sahm Rule e Volatilità VIX.<br><br>
                        <b>COME LEGGERLO:</b><br>
                        • Sotto 35: Mercato stabile.<br>
                        • 35 - 60: Prime divergenze e crepe nel debito.<br>
                        • Sopra 60: Condizioni storiche che precedono correzioni o recessioni.
                    </div>
                </div>
            </div>
            <div class="metric-val-custom">{risk_score} <span style="font-size:18px; color:#ffffff;">/ 100</span></div>
            <div class="metric-sub-custom" style="color:{col_status};">● {delta_text}</div>
        </div>
        """, unsafe_allow_html=True)

    sahm_col = "#ef4444" if curr_sahm >= 0.5 else ("#f59e0b" if curr_sahm >= 0.35 else "#10b981")
    sahm_status = "RECESSIONE" if curr_sahm >= 0.5 else ("PREALLARME" if curr_sahm >= 0.35 else "MERCATO SOLIDO")
    with m_c2:
        st.markdown(f"""
        <div class="metric-card-custom">
            <div class="metric-header">
                <span class="metric-title-custom">Regola di Sahm (Lavoro USA)</span>
                <div class="tooltip-wrap">
                    <span class="help-icon">?</span>
                    <div class="tooltip-box">
                        <b>COSA SIGNIFICA:</b> Misura la velocità di aumento della disoccupazione USA rispetto ai minimi dell'ultimo anno.<br><br>
                        <b>COME LEGGERLO:</b><br>
                        • Sotto 0.35: Occupazione sana.<br>
                        • Tra 0.35 e 0.49: Il lavoro sta rallentando.<br>
                        • Sopra 0.50: Segnale oggettivo di recessione economica storicamente infallibile.
                    </div>
                </div>
            </div>
            <div class="metric-val-custom">{curr_sahm:.2f}</div>
            <div class="metric-sub-custom" style="color:{sahm_col};">● {sahm_status} (Soglia: 0.50)</div>
        </div>
        """, unsafe_allow_html=True)

    curve_col = "#38bdf8" if curr_curve > 0 else "#f59e0b"
    curve_status = "DISINVERTITA (Rischio Tagli)" if curr_curve > 0 else "INVERTITA (Fase Precoce)"
    with m_c3:
        st.markdown(f"""
        <div class="metric-card-custom" style="margin-top:12px;">
            <div class="metric-header">
                <span class="metric-title-custom">Curva Rendimenti (10Y - 2Y)</span>
                <div class="tooltip-wrap">
                    <span class="help-icon">?</span>
                    <div class="tooltip-box">
                        <b>COSA SIGNIFICA:</b> Differenza tra rendimento dei titoli di stato USA a 10 anni e a 2 anni.<br><br>
                        <b>COME LEGGERLO:</b><br>
                        • Negativa (Inversione): Previsione di rallentamento.<br>
                        • Ritorno Sopra lo Zero (Disinversione): È il vero momento di pericolo storico; anticipa i tagli d'emergenza della Fed.
                    </div>
                </div>
            </div>
            <div class="metric-val-custom">{curr_curve:.2f}%</div>
            <div class="metric-sub-custom" style="color:{curve_col};">● {curve_status}</div>
        </div>
        """, unsafe_allow_html=True)

    cred_col = "#ef4444" if curr_ratio_cred > 3.5 else "#10b981"
    cred_status = "STRESS SU EMITTENTI CCC" if curr_ratio_cred > 3.5 else "SPREAD NELLA NORMA"
    with m_c4:
        st.markdown(f"""
        <div class="metric-card-custom" style="margin-top:12px;">
            <div class="metric-header">
                <span class="metric-title-custom">Ratio Debito CCC / High Yield</span>
                <div class="tooltip-wrap">
                    <span class="help-icon">?</span>
                    <div class="tooltip-box">
                        <b>COSA SIGNIFICA:</b> Rapporto tra i rendimenti dei titoli spazzatura CCC e le obbligazioni High Yield ordinarie.<br><br>
                        <b>COME LEGGERLO:</b><br>
                        • Sotto 3.2x: Liquidità distesa.<br>
                        • Sopra 3.5x - 4.0x: Le aziende fragili non riescono a rifinanziarsi. È qui che inizia la catena di insolvenze.
                    </div>
                </div>
            </div>
            <div class="metric-val-custom">{curr_ratio_cred:.2f}x</div>
            <div class="metric-sub-custom" style="color:{cred_col};">● {cred_status}</div>
        </div>
        """, unsafe_allow_html=True)

with col_news_side:
    news_inner_html = '<div class="news-box-side"><div style="font-size:12px; font-weight:900; color:#38bdf8; text-transform:uppercase; margin-bottom:8px; border-bottom:1px solid #334155; padding-bottom:4px;">📡 Notiziario Live (Macro & Crypto)</div>'
    if news_feed:
        for n in news_feed:
            news_inner_html += f'<div class="news-row"><span class="news-tag">[{n["category"]} - {n["time"]}]</span><br><a class="news-anchor" href="{n["link"]}" target="_blank">{n["title"]}</a></div>'
    else:
        news_inner_html += '<div style="font-size:12px; color:#ffffff;">Connessione feed in corso...</div>'
    news_inner_html += '</div>'
    st.markdown(news_inner_html, unsafe_allow_html=True)

alerts_str = " &nbsp; | &nbsp; ".join([f"⚠️ <b>{a}</b>" for a in allerta_list]) if allerta_list else "✅ <b>Nessun campanello d'allarme critico rilevato sui dati odierni.</b>"
st.markdown(f"""
<div class="alert-strip">
    <div style="font-size:12px; color:#ffffff; font-weight:800; text-transform:uppercase; margin-bottom:4px;">Quadro Allarmi Attivi:</div>
    <div style="font-size:14px; color:#ffffff;">{alerts_str}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. GRAFICO A CIPOLLA SEMAFORO A LINEE CONTINUE
# ==========================================
st.markdown("### 🧅 Semaforo del Rischio: Radar Concentrico Reattivo")
st.markdown("<span style='color:#ffffff; font-size:14px; font-weight:600;'>Mappa a linee continue: il rischio parte dall'anello esterno (debito spazzatura) e si trasmette a cascata verso il nucleo delle Big Tech.</span>", unsafe_allow_html=True)

l4_color = "#ef4444" if curr_ratio_cred > 3.4 else "#f59e0b"
l4_status = "🔴 AREA DI PRIMO COLLASSO / ALLARME ATTIVO" if curr_ratio_cred > 3.4 else "🟡 CREDITO SOTTO CONTROLLO"

bizd_ma50 = bizd["Close"].rolling(50).mean().iloc[-1] if not bizd.empty else 0
bizd_under = (not bizd.empty and bizd["Close"].iloc[-1] < bizd_ma50)

if l4_color == "#ef4444" and bizd_under:
    l3_color = "#ef4444"
    l3_status = "🔴 CONTAGIO AL PRIVATE CREDIT ATTIVO"
elif bizd_under:
    l3_color = "#f97316"
    l3_status = "🟠 SOSTENIBILITÀ PRIVATE DEBT SOTTO PRESSIONE"
else:
    l3_color = "#84cc16"
    l3_status = "🟢 PRIVATE CREDIT RESILIENTE"

l2_color = "#84cc16"
l2_status = "🟡 CICLICO / DOMANDA ELEVATA MA VULNERABILE AL CAPEX"

nvda_ma200 = nvda["Close"].rolling(200).mean().iloc[-1] if not nvda.empty else 0
if not nvda.empty and nvda["Close"].iloc[-1] < nvda_ma200:
    l1_color = "#ef4444"
    l1_status = "🔴 ROTTURA SUPPORTO STRUTTURALE NUCLEO TECH"
else:
    l1_color = "#10b981"
    l1_status = "🟢 BILANCI SOLIDI / LIQUIDITÀ RECORD (Trend Rialzista)"

fig_onion = go.Figure()

onion_rings = [
    {"r": 4.0, "fill": "rgba(239, 68, 68, 0.16)", "line": l4_color, "title": "LIVELLO 4 (PERIFERIA): DEBITO SPAZZATURA & AZIENDE ZOMBIE", "desc": f"Spread CCC • Ratio CCC/HY ({curr_ratio_cred:.2f}x) • Startup senza utili • Token speculativi", "status": l4_status, "y": 3.42},
    {"r": 3.0, "fill": "rgba(249, 115, 22, 0.22)", "line": l3_color, "title": "LIVELLO 3: PRIVATE CREDIT & CAPEX DATA CENTER (ALLARME FINK)", "desc": "Blue Owl (OWL) • BIZD (BDC) • Debito CoreWeave • Moratorie permessi & Rete Elettrica", "status": l3_status, "y": 2.42},
    {"r": 2.0, "fill": "rgba(132, 204, 22, 0.26)", "line": l2_color, "title": "LIVELLO 2: HARDWARE, SEMICONDUTTORI & FILIERA CRITICA", "desc": "SK Hynix (Memorie HBM) • Indice Semiconduttori (^SOX) • Fornitori Chiave", "status": l2_status, "y": 1.45},
    {"r": 1.0, "fill": "rgba(16, 185, 129, 0.88)", "line": l1_color, "title": "LIVELLO 1 (CENTRO): BIG TECH & MONOPOLI DI MERCATO", "desc": "Nvidia (NVDA) • Mega-Cap Tecnologiche (MAGS)", "status": l1_status, "y": 0.0}
]

for ring in onion_rings:
    r = ring["r"]
    fig_onion.add_shape(
        type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r,
        fillcolor=ring["fill"], line=dict(color=ring["line"], width=3, dash="solid")
    )
    fig_onion.add_annotation(
        x=0, y=ring["y"],
        text=f"<b>{ring['title']}</b><br><span style='font-size:11px; color:#ffffff;'>{ring['desc']}</span><br><b>[{ring['status']}]</b>",
        showarrow=False, font=dict(color="#ffffff", size=11.5), align="center",
        bgcolor="rgba(10, 15, 29, 0.92)", bordercolor=ring["line"], borderwidth=1.5, borderpad=6
    )

fig_onion.update_xaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_yaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_layout(height=670, margin=dict(l=5, r=5, t=10, b=10), paper_bgcolor="#07090e", plot_bgcolor="#07090e")
st.plotly_chart(fig_onion, use_container_width=True)

# MODULO INTERATTIVO: RADIOGRAFIA A STRATI DELLA CIPOLLA
with st.expander("🔬 Radiografia Interattiva dei 4 Livelli di Rischio (Clicca per Esplorare)"):
    r_tab1, r_tab2, r_tab3, r_tab4 = st.tabs(["Livello 4: Debito Spazzatura", "Livello 3: Data Center & Private Credit", "Livello 2: Hardware & Chip", "Livello 1: Big Tech Fortress"])
    with r_tab1:
        st.markdown(f"**Stato Livello 4:** `{l4_status}` — Rapporto CCC/HY attuale: **{curr_ratio_cred:.2f}x**.<br>Se supera 3.5x, le aziende zombie e le small-cap non riescono a rifinanziarsi e scatta il contagio sistemico.", unsafe_allow_html=True)
    with r_tab2:
        st.markdown(f"**Stato Livello 3:** `{l3_status}`.<br><b>Focus Rischio Moratoria Data Center (Larry Fink):</b> Se gli Stati bloccano le autorizzazioni per motivi ambientali o di rete elettrica, si fermano i contratti di debito privato (Blue Owl, CoreWeave, BIZD), congelando la principale locomotiva di PIL degli Stati Uniti.", unsafe_allow_html=True)
    with r_tab3:
        st.markdown(f"**Stato Livello 2:** `{l2_status}`.<br>SK Hynix e SOX dipendono interamente dalla prosecuzione del Capex dei colossi del Livello 1. Se il debito infrastrutturale subisce un freno, gli ordinativi di GPU e memorie HBM crollano per primi.", unsafe_allow_html=True)
    with r_tab4:
        st.markdown(f"**Stato Livello 1:** `{l1_status}`.<br>Nvidia e le Mega-Cap (MAGS) posseggono centinaia di miliardi di liquidità netta. Reggono i massimi fino all'ultimo atto del ciclo distributivo.", unsafe_allow_html=True)

# ==========================================
# 2. SINTESI MACROECONOMICA INTEGRATA
# ==========================================
st.markdown("### 📑 Bussola Macroeconomica & Sintesi Operativa")

report_clean_html = (
'<div class="report-panel">'
'<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:20px;">'
'<div>'
'<h3 style="margin:0; color:#38bdf8; font-size:19px; font-weight:800;">Inquadramento Strategico di Mercato</h3>'
f'<p style="margin:4px 0 0 0; font-size:13.5px; color:#ffffff;"><b>Diagnosi di Ciclo:</b> {fase_ciclo} &nbsp;|&nbsp; <b>Orizzonte Runway:</b> <span style="color:#facc15; font-weight:700;">{runway_desc}</span> &nbsp;|&nbsp; <b>Fed Net Liquidity:</b> <span style="color:#38bdf8; font-weight:800;">${curr_net_liq:.2f}T</span></p>'
'</div>'
f'<span style="background-color:#1e293b; color:#ffffff; padding:6px 14px; border-radius:6px; font-size:12px; font-weight:800;">Data: {datetime.now().strftime("%d %B %Y")}</span>'
'</div>'
'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">'
'<div class="pillar-card-ui" style="border-top-color: #ef4444;">'
'<h4 style="color:#ffffff; margin-top:0; font-size:15px; font-weight:800;">1. Debito, Data Center & Rischio Moratorie</h4>'
f'<p style="font-size:13.5px; line-height:1.6; color:#ffffff;">Il ratio <b>CCC / High Yield si attesta a {curr_ratio_cred:.2f}x</b>. '
'Come ammonito recentemente da Larry Fink (BlackRock), la vera minaccia recessiva non è tecnologica ma infrastrutturale: '
'se gli Stati approvano moratorie sui data center per saturazione della rete elettrica, la catena di spesa miliardaria sostenuta dal Private Credit (Blue Owl, BIZD) '
'si interrompe, innescando una recessione immediata.</p>'
'</div>'
'<div class="pillar-card-ui" style="border-top-color: #eab308;">'
'<h4 style="color:#ffffff; margin-top:0; font-size:15px; font-weight:800;">2. Ampiezza e Concentrazione Azionaria</h4>'
'<p style="font-size:13.5px; line-height:1.6; color:#ffffff;">Il divario tra l\'indice equiponderato (RSP) e le Mega-Cap (MAGS) '
'mostra che il rialzo continua a essere sorretto da un gruppo ristretto di titoli monopolisti. '
'Quando le small cap divergono mentre i chip (SOX/NDX) viaggiano a valutazioni record, '
'il mercato sta prezzando uno scenario privo di margine di errore sul ritorno economico effettivo dell\'AI.</p>'
'</div>'
'<div class="pillar-card-ui" style="border-top-color: #10b981;">'
'<h4 style="color:#ffffff; margin-top:0; font-size:15px; font-weight:800;">3. Fed Net Liquidity, Oro & Bitcoin</h4>'
f'<p style="font-size:13.5px; line-height:1.6; color:#ffffff;">La <b>Liquidità Netta della Fed a quota ${curr_net_liq:.2f} Trilioni</b> '
'è la vera marea che sostiene Bitcoin e il Nasdaq. '
'Finché la liquidità netta tiene e la Bull Market Support Band settimanale su Bitcoin viene difesa, il trend primario resta intatto, '
'mentre l\'Oro sui massimi storici conferma la massiccia copertura istituzionale dalla svalutazione debitoria.</p>'
'</div>'
'</div>'
'<div style="margin-top:22px;">'
'<h4 style="color:#ffffff; font-size:15px; margin-bottom:10px; font-weight:800;">Matrice Decisionale: Dove Allocare Capitale Oggi</h4>'
'<table class="custom-matrix-table">'
'<thead>'
'<tr>'
'<th>Classe di Attivo</th>'
'<th>Rischio Ingresso Attuale</th>'
'<th>Orizzonte Consigliato</th>'
'<th>Azione Operativa Concreta</th>'
'</tr>'
'</thead>'
'<tbody>'
'<tr>'
'<td><b>Big Tech (Nvidia, Mag 7)</b></td>'
'<td><span style="color:#facc15; font-weight:800;">Medio / Monitorare</span></td>'
'<td>Medio Periodo (3-6 Mesi)</td>'
'<td>Mantenere con stop profit rigidi; non entrare con leva sui massimi.</td>'
'</tr>'
'<tr>'
'<td><b>Small-Cap & Zombie Debt</b></td>'
'<td><span style="color:#ef4444; font-weight:800;">Critico (Sotto Pressione)</span></td>'
'<td>Prudenza Assoluta</td>'
'<td>Evitare società che necessitano di rinnovare debito ad alto tasso d\'interesse.</td>'
'</tr>'
'<tr>'
'<td><b>Oro & Beni Rifugio</b></td>'
'<td><span style="color:#10b981; font-weight:800;">Basso (Trend Solido)</span></td>'
'<td>Lungo Periodo (12-24 Mesi)</td>'
'<td>Accumulazione strategica a copertura da shock sistemici o svalutazione monetaria.</td>'
'</tr>'
'<tr>'
'<td><b>Bitcoin & Crypto</b></td>'
'<td><span style="color:#38bdf8; font-weight:800;">Medio / Trend Following</span></td>'
'<td>Ciclico (6-18 Mesi)</td>'
'<td>Accumulo sopra le medie settimanali o nei pressi della fascia bassa del Mayer Multiple.</td>'
'</tr>'
'</tbody>'
'</table>'
'</div>'
'</div>'
)
st.markdown(report_clean_html, unsafe_allow_html=True)

# ==========================================
# 3. PANNELLO GRAFICI CON NBER RECESSION SHADING & FED LIQUIDITY
# ==========================================
st.markdown("### 📊 Analisi Grafica Interattiva con Zoom & Intreccio Dati")

col_ctrl1, col_ctrl2 = st.columns([1, 2])
with col_ctrl1:
    chart_mode = st.radio(
        "Seleziona Modalità Visualizzazione:",
        ["Candele Giapponesi (Candlestick)", "Linea Continua"],
        horizontal=True
    )

use_candles = (chart_mode == "Candele Giapponesi (Candlestick)")

# Funzione per Aggiungere le Bande di Recessione NBER Ufficiali
def add_nber_recessions(fig):
    recessions = [
        ("2001-03-01", "2001-11-01"),  # Dot-com
        ("2007-12-01", "2009-06-01"),  # Subprime
        ("2020-02-01", "2020-04-01")   # Covid
    ]
    for start, end in recessions:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="rgba(255, 255, 255, 0.08)",
            layer="below", line_width=0,
            annotation_text="RECESSIONE", annotation_position="top left",
            annotation_font=dict(color="#94a3b8", size=9)
        )

def render_isolated_chart(df, is_candlestick=False, default_color="#38bdf8", is_ratio=False, has_recession_shading=False):
    fig = go.Figure()
    has_ohlc = not is_ratio and {'Open', 'High', 'Low', 'Close'}.issubset(df.columns)
    
    if is_candlestick and has_ohlc:
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Prezzo",
            increasing_line_color='#00e676', increasing_fillcolor='#00e676',
            decreasing_line_color='#ff1744', decreasing_fillcolor='#ff1744',
            line=dict(width=1.4)
        ))
    else:
        y_data = df['Close'] if 'Close' in df.columns else df.iloc[:, 0]
        fig.add_trace(go.Scatter(
            x=df.index, y=y_data, mode='lines', name="Valore",
            line=dict(color=default_color, width=2)
        ))
    
    if has_recession_shading:
        add_nber_recessions(fig)
        
    start_date = df.index[-180] if len(df) > 180 else df.index[0]
    
    fig.update_xaxes(
        range=[start_date, df.index[-1]],
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7G", step="day", stepmode="backward"),
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1A", step="year", stepmode="backward"),
                dict(count=3, label="3A", step="year", stepmode="backward"),
                dict(step="all", label="TUTTO")
            ]),
            bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff", size=11),
            y=1.16, x=0.99, xanchor="right"
        ),
        rangeslider=dict(visible=False), type="date"
    )
    
    fig.update_layout(
        title=None,
        template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e",
        font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15)
    )
    return fig

tab_liq, tab1, tab2, tab3, tab4 = st.tabs([
    "🌊 Fed Net Liquidity & Crypto/Tech",
    "💳 Mercato del Credito & Spazzatura",
    "💻 Settore Tech & AI Capex",
    "🌍 Macro USA, Curva & Beni Rifugio",
    "₿ Bitcoin & Oscillatori Quantitativi"
])

# ------------- TAB 0: FED NET LIQUIDITY (NUOVO MODULO) -------------
with tab_liq:
    st.markdown('<div class="chart-header-title">Fed Net Liquidity (WALCL - TGA - RRP) vs Bitcoin & Nasdaq 100</div>', unsafe_allow_html=True)
    if not net_liquidity.empty and not btc.empty and not ndx.empty:
        fig_liq = go.Figure()
        
        # Net Liquidity line
        fig_liq.add_trace(go.Scatter(
            x=net_liquidity.index, y=net_liquidity["Net_Liquidity_Trillion"],
            name="Fed Net Liquidity ($ Trilioni)", line=dict(color="#38bdf8", width=2.5)
        ))
        
        # Normalizzazione BTC e NDX su asse secondario (Base 100)
        norm_btc = (btc["Close"] / btc["Close"].iloc[0]) * 100
        norm_ndx = (ndx["Close"] / ndx["Close"].iloc[0]) * 100
        
        fig_liq.add_trace(go.Scatter(
            x=btc.index, y=norm_btc, name="Bitcoin (Base 100)", yaxis="y2",
            line=dict(color="#facc15", width=1.5)
        ))
        fig_liq.add_trace(go.Scatter(
            x=ndx.index, y=norm_ndx, name="Nasdaq 100 (Base 100)", yaxis="y2",
            line=dict(color="#10b981", width=1.5)
        ))
        
        fig_liq.update_layout(
            yaxis=dict(title="Net Liquidity ($T)", titlefont=dict(color="#38bdf8"), tickfont=dict(color="#38bdf8")),
            yaxis2=dict(title="Performance Relativa (Base 100)", titlefont=dict(color="#ffffff"), tickfont=dict(color="#ffffff"), overlaying="y", side="right"),
            template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e",
            font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15)
        )
        st.plotly_chart(fig_liq, use_container_width=True)
        with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
            st.markdown("""
            <div class="macro-depth-box">
                <b>Perché la Fed Net Liquidity è il Sacro Graal della Macro:</b><br>
                La formula calcola il denaro contante reale a disposizione del sistema bancario e dei dealer primari di Wall Street:
                <br>• $\\text{Net Liquidity} = \\text{Bilancio Fed} - \\text{Conto del Tesoro (TGA)} - \\text{Reverse Repo (RRP)}$.
                <br>• <b>La correlazione empirica:</b> Negli ultimi 5 anni, l'85% dei movimenti del Nasdaq e di Bitcoin ha seguito con precisione matematica la pendenza della Net Liquidity. Se la Fed continua il Quantitative Tightening (QT) e il Tesoro ricostituisce il conto TGA emettendo debito, la liquidità netta drena via dal sistema, portando correzioni improvvise sui mercati azionari e crypto.
            </div>
            """, unsafe_allow_html=True)

# ------------- TAB 1: CREDITO -------------
with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="chart-header-title">Spread Obbligazioni USA: High Yield vs Spazzatura CCC (con Aree Recessione)</div>', unsafe_allow_html=True)
        if not ccc_spread.empty and not hy_spread.empty:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=hy_spread.index, y=hy_spread["BAMLH0A0HYM2"], name="Spread High Yield", line=dict(color="#38bdf8", width=1.8)))
            fig1.add_trace(go.Scatter(x=ccc_spread.index, y=ccc_spread["BAMLH0A3HYC"], name="Spread Titoli CCC", line=dict(color="#ef4444", width=2)))
            add_nber_recessions(fig1)
            start_d = hy_spread.index[-365*3] if len(hy_spread) > 365*3 else hy_spread.index[0]
            fig1.update_xaxes(
                range=[start_d, hy_spread.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.16, x=0.99, xanchor="right"
                )
            )
            fig1.update_layout(title=None, template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15))
            st.plotly_chart(fig1, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Le bande grigie evidenziano le recessioni ufficiali USA. Guarda come lo spread CCC si impenna sempre violentemente PRIMA dell'ingresso nella banda grigia.
                    <br>• Se lo spread CCC sale mentre l'S&P 500 è sui massimi, la contrazione del credito costringe i fondi a vendere anche i titoli azionari più solidi per coprire le perdite obbligazionarie.
                </div>
                """, unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-header-title">Rapporto di Stress: Spread CCC / High Yield</div>', unsafe_allow_html=True)
        if not ratio_ccc_hy.empty:
            fig2 = render_isolated_chart(ratio_ccc_hy, is_candlestick=False, default_color="#dc2626", is_ratio=True, has_recession_shading=True)
            st.plotly_chart(fig2, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Questo rapporto isola lo stress sistemico ripulendolo dai tassi governativi.
                    <br>• Se il ratio supera 3.5x - 4.0x, significa che il mercato rifiuta categoricamente di finanziare la parte bassa della piramide creditizia.
                </div>
                """, unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="chart-header-title">ETF BIZD: Barometro del Private Credit & Prestiti Diretti</div>', unsafe_allow_html=True)
        if not bizd.empty:
            fig3 = render_isolated_chart(bizd, is_candlestick=use_candles, default_color="#f59e0b")
            st.plotly_chart(fig3, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    BIZD racchiude le BDC (Business Development Companies), ovvero il cuore del debito privato americano non regolamentato.
                    <br>• Se BIZD cala, i tassi di insolvenza nei prestiti diretti stanno aumentando, segnalando che la liquidità alternativa si sta prosciugando.
                </div>
                """, unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="chart-header-title">Blue Owl Capital (OWL): Finanziatore Infrastrutture AI</div>', unsafe_allow_html=True)
        if not owl.empty:
            fig4 = render_isolated_chart(owl, is_candlestick=use_candles, default_color="#a855f7")
            st.plotly_chart(fig4, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Blue Owl è il principale asset manager che finanzia a debito cluster di GPU e centri di calcolo.
                    <br>• È il barometro borsistico della sostenibilità del debito dei data center.
                </div>
                """, unsafe_allow_html=True)

# ------------- TAB 2: TECH & AI -------------
with tab2:
    col_e, col_f = st.columns(2)
    with col_e:
        st.markdown('<div class="chart-header-title">Nvidia (NVDA): Cuore del Ciclo Computazionale AI</div>', unsafe_allow_html=True)
        if not nvda.empty:
            fig5 = render_isolated_chart(nvda, is_candlestick=use_candles, default_color="#10b981")
            st.plotly_chart(fig5, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Finché le Big Tech aumentano il budget Capex per i data center, Nvidia sale. Se il debito infrastrutturale subisce un freno, le Big Tech taglieranno gli ordini di chip e Nvidia guiderà la correzione.
                </div>
                """, unsafe_allow_html=True)

    with col_f:
        st.markdown('<div class="chart-header-title">SK Hynix (000660.KS): Memorie ad Alta Velocità (HBM)</div>', unsafe_allow_html=True)
        if not skhynix.empty:
            fig6 = render_isolated_chart(skhynix, is_candlestick=use_candles, default_color="#84cc16")
            st.plotly_chart(fig6, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    SK Hynix è l'unico collo di bottiglia fisico reale dei processori Nvidia (fornisce oltre l'80% delle memorie HBM3/HBM3e).
                </div>
                """, unsafe_allow_html=True)

    col_g, col_h = st.columns(2)
    with col_g:
        st.markdown('<div class="chart-header-title">Rapporto Semiconduttori / Nasdaq 100 (^SOX / ^NDX)</div>', unsafe_allow_html=True)
        if not ratio_sox_ndx.empty:
            fig7 = render_isolated_chart(ratio_sox_ndx, is_candlestick=False, default_color="#38bdf8", is_ratio=True)
            st.plotly_chart(fig7, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Misura se l'hardware sta correndo molto più velocemente del software. Storicamente i picchi parabolici di questo ratio coincidono con i top ciclici del Nasdaq.
                </div>
                """, unsafe_allow_html=True)

    with col_h:
        st.markdown('<div class="chart-header-title">Ampiezza di Mercato: Titoli Medi (RSP) vs Giganti Tech (MAGS)</div>', unsafe_allow_html=True)
        if not rsp.empty and not mags.empty:
            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=rsp.index, y=rsp["Close"] / rsp["Close"].iloc[0] * 100, name="S&P 500 Equal Weight (RSP)", line=dict(color="#94a3b8", width=1.5)))
            fig8.add_trace(go.Scatter(x=mags.index, y=mags["Close"] / mags["Close"].iloc[0] * 100, name="Mega-Cap Mag 7 (MAGS)", line=dict(color="#f43f5e", width=2)))
            start_d = rsp.index[-180] if len(rsp) > 180 else rsp.index[0]
            fig8.update_xaxes(
                range=[start_d, rsp.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="1A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.16, x=0.99, xanchor="right"
                )
            )
            fig8.update_layout(title=None, template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15))
            st.plotly_chart(fig8, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Se RSP è debole mentre le prime 7 società salgono, siamo in piena divergenza da concentrazione.
                </div>
                """, unsafe_allow_html=True)

# ------------- TAB 3: MACRO & BENI RIFUGIO -------------
with tab3:
    col_i, col_l = st.columns(2)
    with col_i:
        st.markdown('<div class="chart-header-title">Disoccupazione USA & Trigger Recessionario Sahm (con Aree NBER)</div>', unsafe_allow_html=True)
        if not unrate.empty and not sahm.empty:
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Disoccupazione (%)", line=dict(color="#94a3b8", width=1.5)))
            fig9.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Regola di Sahm", line=dict(color="#ef4444", width=2.2)))
            fig9.add_hline(y=0.5, line_dash="dash", line_color="#ef4444", annotation_text="Trigger Recessione (0.50)", annotation_font_color="#ffffff")
            add_nber_recessions(fig9)
            start_d = sahm.index[-365*3] if len(sahm) > 365*3 else sahm.index[0]
            fig9.update_xaxes(range=[start_d, sahm.index[-1]])
            fig9.update_layout(title=None, template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15))
            st.plotly_chart(fig9, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Guarda come il superamento di quota 0.50 coincide con precisione chirurgica con l'inizio delle bande grigie di recessione.
                </div>
                """, unsafe_allow_html=True)

    with col_l:
        st.markdown('<div class="chart-header-title">Differenziale Tassi USA (10 Anni - 2 Anni) con Aree Recessione</div>', unsafe_allow_html=True)
        if not t10y2y.empty:
            fig10 = go.Figure()
            fig10.add_trace(go.Scatter(x=t10y2y.index, y=t10y2y["T10Y2Y"], name="Curva 10Y-2Y", line=dict(color="#06b6d4", width=1.8)))
            fig10.add_hline(y=0.0, line_dash="dash", line_color="#ffffff")
            add_nber_recessions(fig10)
            start_d = t10y2y.index[-365*3] if len(t10y2y) > 365*3 else t10y2y.index[0]
            fig10.update_xaxes(range=[start_d, t10y2y.index[-1]])
            fig10.update_layout(title=None, template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15))
            st.plotly_chart(fig10, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Nota come la recessione (banda grigia) non parte MAI durante l'inversione sotto zero, ma sempre DURANTE la disinversione verso l'alto.
                </div>
                """, unsafe_allow_html=True)

    col_m, col_n = st.columns(2)
    with col_m:
        st.markdown('<div class="chart-header-title">Indice della Paura VIX: Volatilità Opzioni S&P 500</div>', unsafe_allow_html=True)
        if not vix.empty:
            fig11 = render_isolated_chart(vix, is_candlestick=use_candles, default_color="#f43f5e")
            st.plotly_chart(fig11, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    I rialzi improvvisi oltre quota 25-30 segnalano scarichi forzati da parte dei fondi quantitativi sistematici.
                </div>
                """, unsafe_allow_html=True)

    with col_n:
        st.markdown('<div class="chart-header-title">Rapporto Oro / Nasdaq 100: Riserva di Valore vs Tech</div>', unsafe_allow_html=True)
        if not ratio_gold_ndx.empty:
            fig12 = render_isolated_chart(ratio_gold_ndx, is_candlestick=False, default_color="#eab308", is_ratio=True)
            st.plotly_chart(fig12, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Quando il ratio sale stabilmente, i grandi patrimoni globali stanno disinvestendo dalla crescita tecnologica per proteggere il capitale nei beni reali.
                </div>
                """, unsafe_allow_html=True)

# ------------- TAB 4: BITCOIN & OSCILLATORI -------------
with tab4:
    if not btc.empty:
        df_btc = btc.copy()
        
        df_btc["SMA_20W"] = df_btc["Close"].rolling(window=140).mean()
        df_btc["EMA_21W"] = df_btc["Close"].ewm(span=147, adjust=False).mean()
        
        df_btc["SMA_200D"] = df_btc["Close"].rolling(window=200).mean()
        df_btc["Mayer_Multiple"] = df_btc["Close"] / df_btc["SMA_200D"]

        c_btc1, c_btc2 = st.columns(2)
        
        with c_btc1:
            st.markdown('<div class="chart-header-title">Bitcoin: Prezzo & Bull Market Support Band (20W SMA / 21W EMA)</div>', unsafe_allow_html=True)
            fig13 = go.Figure()
            if use_candles:
                fig13.add_trace(go.Candlestick(
                    x=df_btc.index, open=df_btc['Open'], high=df_btc['High'], low=df_btc['Low'], close=df_btc['Close'],
                    name="BTC Candele",
                    increasing_line_color='#00e676', increasing_fillcolor='#00e676',
                    decreasing_line_color='#ff1744', decreasing_fillcolor='#ff1744',
                    line=dict(width=1.4)
                ))
            else:
                fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Close"], name="BTC Prezzo ($)", line=dict(color="#ffffff", width=2)))
                
            fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["SMA_20W"], name="20W SMA", line=dict(color="#10b981", width=1.8)))
            fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["EMA_21W"], name="21W EMA", line=dict(color="#06b6d4", width=1.8)))

            start_btc = df_btc.index[-180] if len(df_btc) > 180 else df_btc.index[0]
            fig13.update_xaxes(
                range=[start_btc, df_btc.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.16, x=0.99, xanchor="right"
                )
            )
            fig13.update_yaxes(type="log", title="Prezzo BTC (Scala Logaritmica)")
            fig13.update_layout(title=None, template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15))
            st.plotly_chart(fig13, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Finché il prezzo scambia stabilmente sopra la fascia 20W SMA / 21W EMA, ogni ritracciamento è correzione fisiologica nel bull market.
                </div>
                """, unsafe_allow_html=True)

        with c_btc2:
            st.markdown('<div class="chart-header-title">Bitcoin: Oscillatore Mayer Multiple (Prezzo / 200 SMA)</div>', unsafe_allow_html=True)
            fig14 = go.Figure()
            fig14.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Mayer_Multiple"], name="Mayer Multiple", line=dict(color="#facc15", width=1.8)))
            fig14.add_hline(y=2.4, line_dash="dash", line_color="#ef4444", annotation_text="Bolla / Top Storico (2.4x)", annotation_font_color="#ffffff")
            fig14.add_hline(y=1.0, line_dash="dot", line_color="#94a3b8")
            fig14.add_hline(y=0.8, line_dash="dash", line_color="#10b981", annotation_text="Minimo / Massimo Sconto (0.8x)", annotation_font_color="#ffffff")
            
            start_mayer = df_btc.index[-365] if len(df_btc) > 365 else df_btc.index[0]
            fig14.update_xaxes(
                range=[start_mayer, df_btc.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.16, x=0.99, xanchor="right"
                )
            )
            fig14.update_layout(title=None, template="plotly_dark", height=380, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=35, b=15))
            st.plotly_chart(fig14, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth-box">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Valori sopra 2.4x indicano euforia speculativa e massimi di ciclo; valori inferiori a 0.8x hanno sempre coinciso con i minimi generazionali di accumulo.
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 4. MODULO SEPARATO: BAROMETRO COMPARATIVO DELLE GRANDI BOLLE
# ==========================================
st.markdown("---")
st.markdown("### 🏛️ Barometro Comparativo delle Grandi Bolle (2000, 2008, 2020 vs Ciclo Attuale)")

st.markdown("""
<div style="background-color:#10192a; border:1px solid #1e293b; border-radius:10px; padding:20px; margin-bottom:25px;">
    <h4 style="color:#38bdf8; margin-top:0; font-size:16px; font-weight:800;">Mappatura sulle 5 Fasi della Bolla (Teoria di Hyman Minsky)</h4>
    <p style="color:#ffffff; font-size:13.5px; line-height:1.6;">
        Ogni bolla finanziaria della storia segue una scansione in 5 atti:
        <br><b>1. Spostamento:</b> Nuovo paradigma tecnologico o monetario.
        <br><b>2. Boom:</b> Investimenti giganteschi in conto capitale (Capex data center, chip GPU).
        <br><b>3. Euforia:</b> Rally trainato da pochi titoli colossali, multipli storicamente insostenibili (Nvidia, Mag 7).
        <br><b>4. Prime Crepe nel Debito & Prese di Beneficio <span style="color:#f59e0b; font-weight:900;">[FASE DI TRANSIZIONE ATTUALE]</span>:</b> 
        I tassi alti prosciugano il debito più debole (CCC, prestiti privati BDC, rischio moratorie sui data center).
        <br><b>5. Panico / Revirement Sistemico:</b> L'insolvenza del debito periferico congela gli investimenti Capex e si trasmette al centro della cipolla.
    </p>

    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top:15px;">
        <div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:16px;">
            <b style="color:#f87171; font-size:14px;">Bolla Dot-Com (2000)</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Fibre ottiche, portali web.<br>
                • <b>Concentrazione:</b> Top 10 titoli = 27% dell'S&P.<br>
                • <b>Innesco Crisi:</b> Mancanza di utili reali nelle startup; debito telecom insostenibile.
            </div>
        </div>
        <div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:16px;">
            <b style="color:#f87171; font-size:14px;">Crisi Subprime (2008)</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Derivati immobiliari (MBS, CDO).<br>
                • <b>Concentrazione:</b> Settore finanziario a leva.<br>
                • <b>Innesco Crisi:</b> Insolvenza mutui periferici a tasso variabile con contagio bancario.
            </div>
        </div>
        <div style="background:#0f172a; border:1px solid #334155; border-radius:8px; padding:16px;">
            <b style="color:#f87171; font-size:14px;">Shock Covid / QE (2020)</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Espansione M2 record e lockdown.<br>
                • <b>Concentrazione:</b> Titoli stay-at-home tech.<br>
                • <b>Innesco Crisi:</b> Interruzione supply-chain seguita dalla più rapida stretta tassi in 40 anni.
            </div>
        </div>
        <div style="background:#0f172a; border:1.8px solid #38bdf8; border-radius:8px; padding:16px;">
            <b style="color:#38bdf8; font-size:14px;">Ciclo Attuale: AI & Private Debt</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Capex cluster GPU e data center.<br>
                • <b>Concentrazione:</b> Top 10 titoli = ~35% dell'S&P (Record).<br>
                • <b>Vulnerabilità (Fink Alert):</b> Se gli Stati bloccano i permessi energetici per i data center, il capex si congela e fa crollare l'intero castello.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
