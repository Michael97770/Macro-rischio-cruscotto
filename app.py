import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
/* Sfondo Generale */
.stApp {
    background-color: #07090e !important;
    color: #ffffff !important;
}

/* FORZATURA TESTI BIANCHI PER RADIO BUTTON E CONTROLLI */
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] p,
div[data-testid="stRadio"] span {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}

/* METRICHE NATIVE CON TOOLTIP: BIANCO PURO E ICONA CIANO */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #131c2e, #0a101b) !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
}

div[data-testid="stMetricLabel"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

div[data-testid="stMetricValue"] div {
    color: #38bdf8 !important;
    font-weight: 800 !important;
    font-size: 32px !important;
}

div[data-testid="stMetricDelta"] div {
    font-weight: 700 !important;
}

/* Icona ? del Tooltip bianca/azzurra visibile */
div[data-testid="stMetric"] svg {
    color: #38bdf8 !important;
    fill: #38bdf8 !important;
}

/* NEWS TICKER BOX */
.news-container {
    background-color: #0d1527;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 20px;
}
.news-item {
    padding: 6px 0;
    border-bottom: 1px solid #1a263e;
    font-size: 13px;
    color: #ffffff;
}
.news-item:last-child {
    border-bottom: none;
}
.news-time {
    color: #38bdf8;
    font-weight: 700;
    margin-right: 8px;
}
.news-link {
    color: #ffffff !important;
    text-decoration: none;
    font-weight: 500;
}
.news-link:hover {
    color: #38bdf8 !important;
    text-decoration: underline;
}

/* SCHEDE COMPARATIVE DELLE BOLLE STORICHE */
.bubble-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

/* GUIDA E APPROFONDIMENTO MACRO */
.macro-depth {
    background-color: #0b1324;
    border-left: 4px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-top: 10px;
    font-size: 13.5px;
    line-height: 1.6;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.title("🌐 Macro Risk & Liquidity Intelligence Terminal")
st.markdown("<span style='color:#ffffff; font-size:15px; font-weight:500;'>Analisi integrata del ciclo macroeconomico, della fragilità del debito e dei canali di liquidità.</span>", unsafe_allow_html=True)

# ==========================================
# FEED NOTIZIARIO FINANZIARIO & CRYPTO LIVE
# ==========================================
@st.cache_data(ttl=900)
def fetch_market_news():
    news_items = []
    feed_urls = [
        ("Macro & Mercati", "https://finance.yahoo.com/news/rssindex"),
        ("Crypto & Bitcoin", "https://cointelegraph.com/rss")
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
                # Formattazione orario
                time_str = pub_date[:16] if len(pub_date) >= 16 else "Recente"
                news_items.append({"category": category, "time": time_str, "title": title, "link": link})
                count += 1
                if count >= 3:
                    break
        except Exception:
            continue
    return news_items

news_feed = fetch_market_news()

if news_feed:
    news_html = '<div class="news-container"><div style="font-size:12px; font-weight:800; color:#38bdf8; text-transform:uppercase; margin-bottom:6px;">📡 Ultime Notizie di Mercato & Crypto (Feed Live):</div>'
    for n in news_feed:
        news_html += f'<div class="news-item"><span class="news-time">[{n["category"]}] {n["time"]}</span> — <a class="news-link" href="{n["link"]}" target="_blank">{n["title"]}</a></div>'
    news_html += '</div>'
    st.markdown(news_html, unsafe_allow_html=True)

# ==========================================
# CARICAMENTO DATI (FRED & YAHOO OHLC)
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

with st.spinner("Acquisizione indicatori macro e quotazioni ad alta risoluzione..."):
    hy_spread = load_fred_data("BAMLH0A0HYM2")
    ccc_spread = load_fred_data("BAMLH0A3HYC")
    unrate = load_fred_data("UNRATE")
    sahm = load_fred_data("SAHMREALTIME")
    t10y2y = load_fred_data("T10Y2Y")
    
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

# Calcolo Rischio Sistemico (0-100)
risk_score = 0
allerta_list = []

if curr_sahm >= 0.50: 
    risk_score += 35
    allerta_list.append("Regola di Sahm Attiva (Trigger Recessione USA superato)")
elif curr_sahm >= 0.35: 
    risk_score += 20
    allerta_list.append("Accelerazione Disoccupazione USA (Sahm > 0.35)")

if curr_curve > 0 and not t10y2y.empty and (t10y2y.tail(180).min().values[0] < -0.2):
    risk_score += 25
    allerta_list.append("Disinversione Curva dei Rendimenti (Fase Pre-Recessiva)")
elif curr_curve < 0:
    risk_score += 15

if curr_ratio_cred > 3.8: 
    risk_score += 25
    allerta_list.append("Stress Acuto Debito CCC: Contrazione Liquidità Emittenti Fragili")
elif curr_ratio_cred > 3.4: 
    risk_score += 15
    allerta_list.append("Spread Credito Spazzatura in Allargamento")

if curr_vix > 25: 
    risk_score += 15
    allerta_list.append("Volatilità Azionaria Elevata (VIX > 25)")
elif curr_vix > 20: 
    risk_score += 8

risk_score = min(risk_score, 100)

# ==========================================
# METRICHE PRINCIPALI CON TOOLTIP CIRCOLARE (?)
# ==========================================
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Indice Rischio Sistemico",
    value=f"{risk_score} / 100",
    delta="Critico" if risk_score > 60 else ("Attenzione" if risk_score > 35 else "Stabile"),
    delta_color="inverse",
    help="COSA SERVE: Misura lo stress combinato dei mercati finanziari aggregando 4 parametri critici (Debito Spazzatura, Curva dei Tassi, Sahm Rule e Volatilità VIX).\n\nCOME INTERPRETARLO:\n• Sotto 35: Mercato in equilibrio, bassa probabilità di shock.\n• 35 - 60: Prime crepe nel debito e divergenze azionarie.\n• Sopra 60: Condizioni storiche che precedono violente correzioni o recessioni."
)

col2.metric(
    label="Regola di Sahm (Lavoro USA)",
    value=f"{curr_sahm:.2f}",
    delta="Soglia Trigger: 0.50",
    delta_color="inverse" if curr_sahm >= 0.5 else "off",
    help="COSA SERVE: È l'indicatore principe della Federal Reserve per rilevare l'inizio di una recessione basandosi sull'aumento della disoccupazione rispetto ai minimi dell'ultimo anno.\n\nCOME INTERPRETARLO:\n• Sotto 0.35: Occupazione sana e consumi stabili.\n• Tra 0.35 e 0.49: Il mercato del lavoro si sta deteriorando.\n• Sopra 0.50: Segnale oggettivo di recessione, storicamente privo di falsi positivi."
)

col3.metric(
    label="Curva Rendimenti (10Y - 2Y)",
    value=f"{curr_curve:.2f}%",
    delta="Disinvertita (Critica)" if curr_curve > 0 else "Invertita (Precoce)",
    help="COSA SERVE: Confronta i rendimenti dei titoli di stato USA a 10 anni con quelli a 2 anni.\n\nCOME INTERPRETARLO:\n• Valore Negativo (Curva Invertita): Il mercato obbligazionario anticipa un rallentamento futuro.\n• Ritorno Sopra lo Zero (Disinversione): È il vero allarme storico. Accade quando la banca centrale è costretta a tagliare i tassi in fretta a causa di un'economia che rallenta."
)

col4.metric(
    label="Rapporto Debito CCC / High Yield",
    value=f"{curr_ratio_cred:.2f}x",
    delta="Stress Elevato" if curr_ratio_cred > 3.5 else "Nella Norma",
    delta_color="inverse",
    help="COSA SERVE: Misura il premio al rischio richiesto per prestare denaro alle aziende con rating CCC (massimo rischio default) rispetto alle normali obbligazioni High Yield.\n\nCOME INTERPRETARLO:\n• Sotto 3.2x: Liquidità abbondante per tutti gli emittenti.\n• Sopra 3.5x - 4.0x: Gli investitori chiudono i rubinetti del credito alle aziende deboli. È il primo segnale di default prima che le azioni crollino."
)

# BANNER ALLARMI
alerts_str = " &nbsp; | &nbsp; ".join([f"⚠️ <b>{a}</b>" for a in allerta_list]) if allerta_list else "✅ <b>Nessun campanello d'allarme critico rilevato sui dati odierni.</b>"
st.markdown(f"""
<div style="background:#0f172a; border-left:5px solid #ef4444; border-radius:8px; padding:12px 18px; margin:15px 0 22px 0;">
    <div style="font-size:12px; color:#ffffff; font-weight:800; text-transform:uppercase; margin-bottom:4px;">Stato degli Allarmi Attivi:</div>
    <div style="font-size:14px; color:#ffffff;">{alerts_str}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. GRAFICO A CIPOLLA DINAMICO
# ==========================================
st.markdown("### 🧅 Modello a Cipolla del Rischio: Radar Dinamico")

l4_color = "#ef4444" if curr_ratio_cred > 3.4 else "#f59e0b"
l4_status = "🔴 AREA DI PRIMO COLLASSO / ALLARME ATTIVO" if curr_ratio_cred > 3.4 else "🟡 CREDITO SOTTO CONTROLLO"

bizd_ma50 = bizd["Close"].rolling(50).mean().iloc[-1] if not bizd.empty else 0
l3_color = "#f97316" if (not bizd.empty and bizd["Close"].iloc[-1] < bizd_ma50) else "#84cc16"
l3_status = "🟠 SOSTENIBILITÀ DEBITO PRIVATE SOTTO PRESSIONE" if l3_color == "#f97316" else "🟢 PRIVATE CREDIT RESILIENTE"

l2_color = "#84cc16"
l2_status = "🟡 CICLICO / DOMANDA ELEVATA MA VULNERABILE AL CAPEX"

nvda_ma200 = nvda["Close"].rolling(200).mean().iloc[-1] if not nvda.empty else 0
l1_color = "#10b981" if (not nvda.empty and nvda["Close"].iloc[-1] >= nvda_ma200) else "#f59e0b"
l1_status = "🟢 BILANCI SOLIDI / LIQUIDITÀ RECORD (Trend Rialzista)" if l1_color == "#10b981" else "🟡 DIVERGENZA SUL NUCLEO TECH"

fig_onion = go.Figure()

onion_rings = [
    {"r": 4.0, "fill": "rgba(239, 68, 68, 0.16)", "line": l4_color, "title": "LIVELLO 4 (PERIFERIA): DEBITO SPAZZATURA & AZIENDE ZOMBIE", "desc": f"Spread CCC • Ratio CCC/HY ({curr_ratio_cred:.2f}x) • Startup senza utili • Token speculativi", "status": l4_status, "y": 3.42},
    {"r": 3.0, "fill": "rgba(249, 115, 22, 0.22)", "line": l3_color, "title": "LIVELLO 3: PRIVATE CREDIT & FINANZIAMENTO INFRASTRUTTURE", "desc": "Blue Owl (OWL) • BIZD (BDC) • Debito CoreWeave (USU2069EAB6) • Obbligazioni lunghi Tech", "status": l3_status, "y": 2.42},
    {"r": 2.0, "fill": "rgba(132, 204, 22, 0.26)", "line": l2_color, "title": "LIVELLO 2: HARDWARE, SEMICONDUTTORI & FILIERA CRITICA", "desc": "SK Hynix (Memorie HBM) • Indice Semiconduttori (^SOX) • Fornitori Chiave", "status": l2_status, "y": 1.45},
    {"r": 1.0, "fill": "rgba(16, 185, 129, 0.88)", "line": l1_color, "title": "LIVELLO 1 (CENTRO): BIG TECH & MONOPOLI DI MERCATO", "desc": "Nvidia (NVDA) • Mega-Cap Tecnologiche (MAGS)", "status": l1_status, "y": 0.0}
]

for ring in onion_rings:
    r = ring["r"]
    fig_onion.add_shape(
        type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r,
        fillcolor=ring["fill"], line=dict(color=ring["line"], width=2.8, dash="solid" if r == 1.0 else "dot")
    )
    fig_onion.add_annotation(
        x=0, y=ring["y"],
        text=f"<b>{ring['title']}</b><br><span style='font-size:11px; color:#ffffff;'>{ring['desc']}</span><br><b>[{ring['status']}]</b>",
        showarrow=False, font=dict(color="#ffffff", size=11.5), align="center",
        bgcolor="rgba(10, 15, 29, 0.90)", bordercolor=ring["line"], borderwidth=1.2, borderpad=6
    )

fig_onion.update_xaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_yaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_layout(height=670, margin=dict(l=5, r=5, t=10, b=10), paper_bgcolor="#07090e", plot_bgcolor="#07090e")
st.plotly_chart(fig_onion, use_container_width=True)

# ==========================================
# 2. NUOVO MODULO: BAROMETRO COMPARATIVO DELLE GRANDI BOLLE
# ==========================================
st.markdown("### 🏛️ Barometro Comparativo delle Grandi Bolle (2000, 2008, 2020 vs Ciclo Attuale)")

st.markdown("""
<div style="background-color:#10192a; border:1px solid #1e293b; border-radius:10px; padding:20px; margin-bottom:25px;">
    <h4 style="color:#38bdf8; margin-top:0; font-size:16px;">Mappatura sulle 5 Fasi della Bolla (Teoria di Hyman Minsky)</h4>
    <p style="color:#ffffff; font-size:13.5px; line-height:1.6;">
        Ogni bolla finanziaria della storia segue una scansione temporale precisa in 5 atti:
        <br><b>1. Spostamento:</b> Arriva una nuova tecnologia o paradigma monetario (es. Internet nel 1995, Mutui facili nel 2003, Stimoli Covid nel 2020, Modelli AI generativi nel 2022).
        <br><b>2. Boom:</b> Entrano i capitali istituzionali, investimenti giganteschi in infrastruttura (Capex data center, chip GPU).
        <br><b>3. Euforia:</b> Rally trainato da pochi titoli colossali, multipli di valutazione storicamente insostenibili (Nvidia, Mag 7).
        <br><b>4. Prime Crepe nel Debito & Prese di Beneficio <span style="color:#f59e0b; font-weight:800;">[FASE DI TRANSIZIONE ATTUALE]</span>:</b> 
        I tassi alti prosciugano il debito più debole (CCC, prestiti privati non garantiti). I titoli ordinari smettono di salire, mentre solo i colossi con riserve di cassa reggono i massimi.
        <br><b>5. Panico / Revirement Sistemico:</b> L'insolvenza del debito periferico congela gli investimenti Capex e si trasmette al centro della cipolla.
    </p>

    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top:15px;">
        <div class="bubble-card">
            <b style="color:#f87171; font-size:14px;">Bolla Dot-Com (2000)</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Fibre ottiche, portali web.<br>
                • <b>Concentrazione:</b> Top 10 titoli = 27% dell'S&P.<br>
                • <b>Innesco Crisi:</b> Mancanza di utili reali nelle startup; debito telecom insostenibile.
            </div>
        </div>
        <div class="bubble-card">
            <b style="color:#f87171; font-size:14px;">Crisi Subprime (2008)</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Derivati immobiliari (MBS, CDO).<br>
                • <b>Concentrazione:</b> Settore finanziario a leva.<br>
                • <b>Innesco Crisi:</b> Insolvenza mutui periferici a tasso variabile con contagio bancario.
            </div>
        </div>
        <div class="bubble-card">
            <b style="color:#f87171; font-size:14px;">Shock Covid / QE (2020)</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Espansione M2 record e lockdown.<br>
                • <b>Concentrazione:</b> Titoli stay-at-home tech.<br>
                • <b>Innesco Crisi:</b> Interruzione supply-chain seguita dalla più rapida stretta tassi in 40 anni.
            </div>
        </div>
        <div class="bubble-card" style="border:1.5px solid #38bdf8;">
            <b style="color:#38bdf8; font-size:14px;">Ciclo Attuale: AI & Private Debt</b>
            <div style="font-size:12.5px; color:#ffffff; margin-top:6px; line-height:1.5;">
                • <b>Driver:</b> Capex cluster GPU e data center.<br>
                • <b>Concentrazione:</b> Top 10 titoli = ~35% dell'S&P (Record).<br>
                • <b>Vulnerabilità:</b> Se il ROI dell'AI ritarda, il debito cartolarizzato delle infrastrutture (OWL, BIZD) implode.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 3. PANNELLO GRAFICI AD ALTA RISOLUZIONE & MODAL INTERATTIVO
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

# Funzione Universale Grafici: Candele Nitide con Zoom Automatico agli ultimi 180 Giorni
def render_detailed_chart(df, title, is_candlestick=False, default_color="#38bdf8", is_ratio=False):
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
    
    # Range iniziale impostato agli ultimi 6 mesi per candele ampie e dettagliate
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
            y=1.14, x=0.99, xanchor="right"
        ),
        rangeslider=dict(visible=False), type="date"
    )
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
        template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e",
        font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
    )
    return fig

tab1, tab2, tab3, tab4 = st.tabs([
    "💳 Mercato del Credito & Spazzatura",
    "💻 Settore Tech & AI Capex",
    "🌍 Macro USA & Beni Rifugio",
    "₿ Bitcoin & Oscillatori Quantitativi"
])

# ------------- TAB 1: CREDITO -------------
with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        if not ccc_spread.empty and not hy_spread.empty:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=hy_spread.index, y=hy_spread["BAMLH0A0HYM2"], name="Spread High Yield", line=dict(color="#38bdf8", width=1.8)))
            fig1.add_trace(go.Scatter(x=ccc_spread.index, y=ccc_spread["BAMLH0A3HYC"], name="Spread Titoli CCC", line=dict(color="#ef4444", width=2)))
            start_d = hy_spread.index[-365] if len(hy_spread) > 365 else hy_spread.index[0]
            fig1.update_xaxes(
                range=[start_d, hy_spread.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig1.update_layout(
                title=dict(text="<b>Spread Obbligazioni USA: High Yield vs Spazzatura CCC</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig1, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Lo spread del credito è il vero indicatore anticipatore della borsa. Le azioni riflettono l'ottimismo, ma il mercato obbligazionario muove trilioni di dollari ed è governato da investitori istituzionali.
                    <br>• <b>La catena di trasmissione:</b> Quando i tassi della Fed restano elevati a lungo, le aziende deboli non riescono a ripagare il debito emesso a tasso zero negli anni passati.
                    <br>• <b>Perché guardare CCC vs HY:</b> Le aziende con rating CCC sono le prime a fare default. Se lo spread CCC sale mentre l'S&P 500 è sui massimi, si crea una divergenza ribassista insanabile: entro 4-6 mesi la contrazione del credito costringe i fondi a vendere anche i titoli azionari più solidi per coprire le perdite obbligazionarie.
                </div>
                """, unsafe_allow_html=True)

    with col_b:
        if not ratio_ccc_hy.empty:
            fig2 = render_detailed_chart(ratio_ccc_hy, "Rapporto di Stress: Spread CCC / High Yield", is_candlestick=False, default_color="#dc2626", is_ratio=True)
            st.plotly_chart(fig2, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Questo rapporto isola lo stress sistemico ripulendolo dai tassi governativi.
                    <br>• Se il ratio supera 3.5x - 4.0x, significa che il mercato rifiuta categoricamente di finanziare la parte bassa della piramide creditizia. 
                    È esattamente la configurazione osservata tra il 2007 e l'inizio del 2008 prima del crack finanziario.
                </div>
                """, unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        if not bizd.empty:
            fig3 = render_detailed_chart(bizd, "ETF BIZD: Barometro del Private Credit & Prestiti Diretti", is_candlestick=use_candles, default_color="#f59e0b")
            st.plotly_chart(fig3, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    BIZD racchiude le BDC (Business Development Companies), ovvero il cuore del debito privato americano non regolamentato.
                    <br>• <b>Il legame con l'AI:</b> Gran parte del leasing per i server e data center delle startup viene garantito con debito privato a tassi variabili alti. Se BIZD cala, i tassi di insolvenza nei prestiti diretti stanno aumentando.
                </div>
                """, unsafe_allow_html=True)

    with col_d:
        if not owl.empty:
            fig4 = render_detailed_chart(owl, "Blue Owl Capital (OWL): Finanziatore Infrastrutture AI", is_candlestick=use_candles, default_color="#a855f7")
            st.plotly_chart(fig4, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Blue Owl è il principale asset manager che finanzia a debito cluster di GPU e centri di calcolo (inclusi accordi da miliardi con operatori come CoreWeave).
                    <br>• Monitorare OWL permette di capire se il mercato azionario crede nella solvibilità a lungo termine degli investimenti in data center.
                </div>
                """, unsafe_allow_html=True)

# ------------- TAB 2: TECH & AI -------------
with tab2:
    col_e, col_f = st.columns(2)
    with col_e:
        if not nvda.empty:
            fig5 = render_detailed_chart(nvda, "Nvidia (NVDA): Cuore del Ciclo Computazionale AI", is_candlestick=use_candles, default_color="#10b981")
            st.plotly_chart(fig5, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Nvidia è il barometro della liquidità azionaria globale. I suoi chip sono venduti a margini del 70-80% perché le Big Tech stanno spendendo decine di miliardi di cassa (Capex) per non rimanere indietro nella corsa all'AI.
                    <br>• <b>Punto di rottura:</b> Finché le Big Tech aumentano il budget di spesa, Nvidia sale. Se il debito infrastrutturale o il rendimento del software deludono, le Big Tech taglieranno gli ordini di chip e Nvidia guiderà la correzione del Nasdaq.
                </div>
                """, unsafe_allow_html=True)

    with col_f:
        if not skhynix.empty:
            fig6 = render_detailed_chart(skhynix, "SK Hynix (000660.KS): Memorie ad Alta Velocità (HBM)", is_candlestick=use_candles, default_color="#84cc16")
            st.plotly_chart(fig6, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    SK Hynix è l'unico collo di bottiglia fisico reale dei processori Nvidia (fornisce oltre l'80% delle memorie HBM3/HBM3e).
                    <br>• Le sue trimestrali rivelano se la produzione di server fisici è in accelerazione o se emergono accumuli di scorte nei magazzini asiatici.
                </div>
                """, unsafe_allow_html=True)

    col_g, col_h = st.columns(2)
    with col_g:
        if not ratio_sox_ndx.empty:
            fig7 = render_detailed_chart(ratio_sox_ndx, "Rapporto Semiconduttori / Nasdaq 100 (^SOX / ^NDX)", is_candlestick=False, default_color="#38bdf8", is_ratio=True)
            st.plotly_chart(fig7, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Misura se il mercato sta prezzando una crescita dell'hardware superiore al software.
                    <br>• Storicamente, i picchi parabolici di questo ratio coincidono con i top ciclici del Nasdaq (è accaduto nel 2000 e a fine 2021). Quando l'hardware ha finito di costruire l'infrastruttura, il ciclo entra nella fase di maturità o correzione.
                </div>
                """, unsafe_allow_html=True)

    with col_h:
        if not rsp.empty and not mags.empty:
            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=rsp.index, y=rsp["Close"] / rsp["Close"].iloc[0] * 100, name="S&P 500 Equal Weight (RSP)", line=dict(color="#94a3b8", width=1.5)))
            fig8.add_trace(go.Scatter(x=mags.index, y=mags["Close"] / mags["Close"].iloc[0] * 100, name="Mega-Cap Mag 7 (MAGS)", line=dict(color="#f43f5e", width=2)))
            start_d = rsp.index[-180] if len(rsp) > 180 else rsp.index[0]
            fig8.update_xaxes(
                range=[start_d, rsp.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="1A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig8.update_layout(
                title=dict(text="<b>Ampiezza di Mercato: Titoli Medi (RSP) vs Giganti Tech (MAGS)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig8, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Questa è l'anatomia della divergenza tecnica. 
                    <br>• Se l'indice equiponderato (RSP) è debole mentre le prime 7 società (MAGS) continuano a segnare massimi, gli investitori non stanno comprando l'economia reale, ma si stanno rifugiando negli unici 7 monopoli dotati di liquidità infinita. È la tipica fase distributiva di fine ciclo.
                </div>
                """, unsafe_allow_html=True)

# ------------- TAB 3: MACRO & BENI RIFUGIO -------------
with tab3:
    col_i, col_l = st.columns(2)
    with col_i:
        if not unrate.empty and not sahm.empty:
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Disoccupazione (%)", line=dict(color="#94a3b8", width=1.5)))
            fig9.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Regola di Sahm", line=dict(color="#ef4444", width=2.2)))
            fig9.add_hline(y=0.5, line_dash="dash", line_color="#ef4444", annotation_text="Trigger Recessione (0.50)", annotation_font_color="#ffffff")
            start_d = sahm.index[-365] if len(sahm) > 365 else sahm.index[0]
            fig9.update_xaxes(range=[start_d, sahm.index[-1]])
            fig9.update_layout(
                title=dict(text="<b>Disoccupazione USA & Trigger Recessionario Sahm</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig9, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    L'economia statunitense è basata per il 70% sui consumi interni.
                    <br>• Se i licenziamenti aumentano e l'indicatore Sahm raggiunge 0.50, i consumi contraggono a catena i margini operativi aziendali, innescando revisioni al ribasso degli utili (EPS) per tutto l'azionario.
                </div>
                """, unsafe_allow_html=True)

    with col_l:
        if not t10y2y.empty:
            fig10 = go.Figure()
            fig10.add_trace(go.Scatter(x=t10y2y.index, y=t10y2y["T10Y2Y"], name="Curva 10Y-2Y", line=dict(color="#06b6d4", width=1.8)))
            fig10.add_hline(y=0.0, line_dash="dash", line_color="#ffffff")
            start_d = t10y2y.index[-365] if len(t10y2y) > 365 else t10y2y.index[0]
            fig10.update_xaxes(range=[start_d, t10y2y.index[-1]])
            fig10.update_layout(
                title=dict(text="<b>Differenziale Tassi USA (10 Anni - 2 Anni)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig10, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico (L'esempio del 10 Anni e dell'Oro):</b><br>
                    I bond a 10 anni fissano il costo globale del denaro. 
                    <br>• <b>Relazione con l'Oro:</b> L'Oro non stacca cedole. Quando i rendimenti reali dei bond salgono molto, l'Oro fatica; ma quando la curva si disinverte perché l'inflazione resta vischiosa e la Fed taglia i tassi (abbassando i tassi reali a breve), l'Oro esplode verso l'alto come scudo primario contro la svalutazione monetaria.
                </div>
                """, unsafe_allow_html=True)

    col_m, col_n = st.columns(2)
    with col_m:
        if not vix.empty:
            fig11 = render_detailed_chart(vix, "Indice della Paura VIX: Volatilità Opzioni S&P 500", is_candlestick=use_candles, default_color="#f43f5e")
            st.plotly_chart(fig11, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Il VIX misura il prezzo pagato dai market maker per assicurarsi contro correzioni repentine.
                    <br>• Un VIX persistentemente sotto 14 riflette compiacenza cieca. I rialzi improvvisi oltre quota 25 provocano liquidazioni forzate da parte dei fondi quantitativi sistematici (CTA).
                </div>
                """, unsafe_allow_html=True)

    with col_n:
        if not ratio_gold_ndx.empty:
            fig12 = render_detailed_chart(ratio_gold_ndx, "Rapporto Oro / Nasdaq 100: Riserva di Valore vs Tech", is_candlestick=False, default_color="#eab308", is_ratio=True)
            st.plotly_chart(fig12, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Questo rapporto mette a confronto la "moneta incorruttibile" (Oro) contro l'asset speculativo cartolare per eccellenza (Nasdaq).
                    <br>• Quando il ratio inverte la rotta e sale stabilmente, i grandi patrimoni globali stanno disinvestendo dalla crescita tecnologica per proteggere il potere d'acquisto nei beni reali.
                </div>
                """, unsafe_allow_html=True)

# ------------- TAB 4: BITCOIN & OSCILLATORI -------------
with tab4:
    if not btc.empty:
        df_btc = btc.copy()
        
        # Medie Mobili Chiave
        df_btc["SMA_20W"] = df_btc["Close"].rolling(window=140).mean()
        df_btc["EMA_21W"] = df_btc["Close"].ewm(span=147, adjust=False).mean()
        
        # Mayer Multiple (Prezzo / 200 SMA giornaliera)
        df_btc["SMA_200D"] = df_btc["Close"].rolling(window=200).mean()
        df_btc["Mayer_Multiple"] = df_btc["Close"] / df_btc["SMA_200D"]

        c_btc1, c_btc2 = st.columns(2)
        
        with c_btc1:
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
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig13.update_yaxes(type="log", title="Prezzo BTC (Scala Logaritmica)")
            fig13.update_layout(
                title=dict(text="<b>Bitcoin: Prezzo & Bull Market Support Band (20W SMA / 21W EMA)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig13, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Bitcoin è un termometro purissimo della liquidità fiat globale.
                    <br>• La combinazione tra la media mobile semplice a 20 settimane e l'esponenziale a 21 settimane forma la "Bull Market Support Band".
                    <br>• Finché il prezzo scambia stabilmente sopra questa fascia verde/azzurra, ogni ritracciamento è considerabile correzione all'interno di un trend rialzista. La perdita confermata di queste medie segnala il passaggio a una fase di contrazione o bear market prolungato.
                </div>
                """, unsafe_allow_html=True)

        with c_btc2:
            fig14 = go.Figure()
            fig14.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Mayer_Multiple"], name="Mayer Multiple", line=dict(color="#facc15", width=1.8)))
            fig14.add_hline(y=2.4, line_dash="dash", line_color="#ef4444", annotation_text="Area Bolla / Top Storico (2.4x)", annotation_font_color="#ffffff")
            fig14.add_hline(y=1.0, line_dash="dot", line_color="#94a3b8")
            fig14.add_hline(y=0.8, line_dash="dash", line_color="#10b981", annotation_text="Area Minimo / Massimo Sconto (0.8x)", annotation_font_color="#ffffff")
            
            start_mayer = df_btc.index[-365] if len(df_btc) > 365 else df_btc.index[0]
            fig14.update_xaxes(
                range=[start_mayer, df_btc.index[-1]],
                rangeselector=dict(
                    buttons=[dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig14.update_layout(
                title=dict(text="<b>Bitcoin: Oscillatore Mayer Multiple (Prezzo / 200 SMA)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=420, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig14, use_container_width=True)
            with st.expander("🔍 Ingrandisci & Analisi Intreccio Dati Macro"):
                st.markdown("""
                <div class="macro-depth">
                    <b>Come funziona l'intreccio macroeconomico:</b><br>
                    Il Mayer Multiple calcola il rapporto tra il prezzo corrente di Bitcoin e la sua media mobile a 200 giorni.
                    <br>• Storicamente, Bitcoin non ha mai fatto un picco di ciclo senza aver prima superato il valore di 2.4x.
                    <br>• Al contrario, letture inferiori a 0.8x hanno sempre coinciso con i minimi generazionali di accumulo (es. fine 2018, marzo 2020, fine 2022).
                </div>
                """, unsafe_allow_html=True)
