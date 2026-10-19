import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# CONFIGURAZIONE INTERFACCIA E TEMA SCURO
# ==========================================
st.set_page_config(
    page_title="Macro Risk Terminal | Global Market Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Iniezione CSS ad Alto Contrasto: Testi Bianchi e Card Nitide
st.markdown("""
<style>
/* Sfondo Generale */
.stApp {
    background-color: #07090e !important;
    color: #ffffff !important;
}

/* METRICHE IN ALTO: BIANCO PURO E ALTO CONTRASTO */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #161f30, #0c121e) !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
}

div[data-testid="stMetricLabel"] > div > p {
    color: #f8fafc !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

div[data-testid="stMetricValue"] > div {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 30px !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.5) !important;
}

div[data-testid="stMetricDelta"] > div {
    font-weight: 600 !important;
}

/* Stile Scheda Report Esecutivo (Niente codice o font monospazio) */
.report-container {
    background: linear-gradient(145deg, #111a2e, #090e17);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 24px;
    margin: 20px 0;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
}

.report-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
    padding-bottom: 12px;
    margin-bottom: 20px;
}

.pillar-card {
    background-color: #152238;
    border-radius: 8px;
    padding: 18px;
    border-top: 3px solid #38bdf8;
    margin-bottom: 15px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
.custom-table th {
    background-color: #1e293b;
    color: #f8fafc;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}
.custom-table td {
    padding: 12px;
    border-bottom: 1px solid #1e293b;
    font-size: 13.5px;
    color: #e2e8f0;
}

/* Guide didattiche sotto i grafici */
.chart-guide {
    background-color: #0d1527;
    border-left: 4px solid #38bdf8;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-top: -8px;
    margin-bottom: 30px;
    font-size: 13.5px;
    color: #e2e8f0;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

st.title("🌐 Macro Risk & Liquidity Intelligence Terminal")
st.markdown("Piattaforma quantitativa per l'analisi dei cicli economici, della solidità del credito e del rischio sistemico sui mercati globali.")

# ==========================================
# GESTIONE DATI IN CACHE (FRED & YAHOO OHLC)
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
            # Normalizzazione colonne se multi-index
            df = df.xs(ticker, level=1, axis=1) if ticker in df.columns.levels[1] else df.droplevel(1, axis=1)
        return df.dropna()
    except Exception:
        return pd.DataFrame()

with st.spinner("Aggiornamento dati in tempo reale dai mercati internazionali..."):
    # FRED Macro & Credito
    hy_spread = load_fred_data("BAMLH0A0HYM2")
    ccc_spread = load_fred_data("BAMLH0A3HYC")
    unrate = load_fred_data("UNRATE")
    sahm = load_fred_data("SAHMREALTIME")
    t10y2y = load_fred_data("T10Y2Y")
    
    # Yahoo Finance (Dati OHLC Completi per Candele)
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

# Calcolo Ratios
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

# Valori Attuali per il Calcolo
curr_sahm = float(sahm.iloc[-1].values[0]) if not sahm.empty else 0.0
curr_curve = float(t10y2y.iloc[-1].values[0]) if not t10y2y.empty else 0.0
curr_ratio_cred = float(ratio_ccc_hy.iloc[-1].values[0]) if not ratio_ccc_hy.empty else 3.0
curr_vix = float(vix["Close"].iloc[-1]) if not vix.empty else 15.0

# Calcolo Algoritmico Rischio Sistemico (0-100)
risk_score = 0
if curr_sahm >= 0.50: risk_score += 35
elif curr_sahm >= 0.35: risk_score += 20

if curr_curve > 0 and not t10y2y.empty and (t10y2y.tail(180).min().values[0] < -0.2):
    risk_score += 25  # Disinversione della curva post inversione
elif curr_curve < 0:
    risk_score += 15

if curr_ratio_cred > 3.8: risk_score += 25
elif curr_ratio_cred > 3.2: risk_score += 15

if curr_vix > 25: risk_score += 15
elif curr_vix > 20: risk_score += 8
risk_score = min(risk_score, 100)

# Diagnosi di Ciclo
if curr_sahm >= 0.50:
    fase_ciclo = "Fase 4: Rischio Recessione Confermato (Regola di Sahm Attiva)"
    badge_col = "#ef4444"
elif curr_curve > 0 and risk_score >= 50:
    fase_ciclo = "Fase 3: Fine Ciclo (Disinversione Curva & Primi Segnali di Rallentamento)"
    badge_col = "#f59e0b"
elif not ratio_sox_ndx.empty and ratio_sox_ndx.iloc[-1].values[0] > ratio_sox_ndx.tail(252).quantile(0.85).values[0]:
    fase_ciclo = "Fase 2: Espansione Guidata dal Settore Tecnologico / AI Capex"
    badge_col = "#38bdf8"
else:
    fase_ciclo = "Fase 1: Espansione / Accumulazione Sincrona"
    badge_col = "#10b981"

# ==========================================
# METRICHE PRINCIPALI CON COLORI AD ALTO CONTRASTO
# ==========================================
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Indice Rischio Sistemico",
    value=f"{risk_score} / 100",
    delta="Critico" if risk_score > 65 else ("Attenzione" if risk_score > 40 else "Stabile"),
    delta_color="inverse",
    help="COSA SIGNIFICA: Punteggio complessivo da 0 a 100 che sintetizza lo stress sul debito, la curva dei tassi, la volatilità e l'occupazione.\n\nCOME LEGGERLO:\n• Sotto 40: Mercato solido.\n• 40 - 65: Allerta, aumentano le divergenze.\n• Sopra 65: Rischio sistemico elevato di correzione."
)

col2.metric(
    label="Regola di Sahm (Recessione)",
    value=f"{curr_sahm:.2f}",
    delta="Soglia Trigger: 0.50",
    delta_color="inverse" if curr_sahm >= 0.5 else "off",
    help="COSA SIGNIFICA: Indicatore della Fed che misura la velocità di aumento della disoccupazione USA.\n\nCOME LEGGERLO:\n• Sotto 0.35: Mercato del lavoro solido.\n• Tra 0.35 e 0.49: Rallentamento in corso.\n• Sopra 0.50: Segnala l'inizio di una recessione storicamente senza falsi allarmi."
)

col3.metric(
    label="Curva Rendimenti (10Y - 2Y)",
    value=f"{curr_curve:.2f}%",
    delta="Disinvertita" if curr_curve > 0 else "Invertita",
    help="COSA SIGNIFICA: Differenza tra rendimento dei titoli di stato USA a 10 anni e a 2 anni.\n\nCOME LEGGERLO:\n• Valore Negativo (Inversione): I mercati prevedono problemi economici.\n• Ritorno a Valori Positivi (Disinversione): Momento critico, indica tagli dei tassi d'urgenza."
)

col4.metric(
    label="Rapporto Debito CCC / High Yield",
    value=f"{curr_ratio_cred:.2f}x",
    delta="Stress Credito" if curr_ratio_cred > 3.5 else "Stabile",
    delta_color="inverse",
    help="COSA SIGNIFICA: Confronta i rendimenti dei titoli spazzatura CCC con quelli High Yield ordinari.\n\nCOME LEGGERLO:\n• Sotto 3.2x: Liquidità fluida.\n• Sopra 3.5x - 4.0x: Le aziende fragili non riescono a rifinanziarsi. È qui che inizia il contagio."
)

st.markdown(f"""
<div style="background-color:#111b2b; border-left: 5px solid {badge_col}; padding: 12px 18px; border-radius: 8px; margin: 18px 0 25px 0;">
    <span style="font-size:12px; text-transform:uppercase; color:#94a3b8; font-weight:bold;">Inquadramento di Mercato:</span><br>
    <span style="font-size:16px; font-weight:700; color:#ffffff;">{fase_ciclo}</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. GRAFICO A CIPOLLA AD ANELLI CONCENTRICI
# ==========================================
st.markdown("### 🧅 Modello di Trasmissione del Rischio ad Anelli Concentrici")
st.caption("Mappa visiva della vulnerabilità: il rischio di default si manifesta prima nell'anello esterno (Rosso) del credito spazzatura, propagandosi verso il nucleo delle Big Tech (Verde) che possiede riserve di cassa.")

fig_onion = go.Figure()

onion_rings = [
    {
        "r": 4.0,
        "fill": "rgba(239, 68, 68, 0.18)",
        "line": "#ef4444",
        "title": "LIVELLO 4 (PERIFERIA): DEBITO SPAZZATURA & AZIENDE ZOMBIE",
        "desc": "Spread Titoli CCC • Ratio CCC/HY • Startup prive di flussi di cassa • Token speculativi",
        "status": "🔴 AREA DI PRIMO COLLASSO / ALTA VULNERABILITÀ",
        "y": 3.42
    },
    {
        "r": 3.0,
        "fill": "rgba(249, 115, 22, 0.25)",
        "line": "#f97316",
        "title": "LIVELLO 3: PRIVATE CREDIT & FINANZIAMENTO INFRASTRUTTURE",
        "desc": "Blue Owl (OWL) • BIZD (BDC) • Debito CoreWeave (USU2069EAB6) • Obbligazioni a 30-40 anni Big Tech",
        "status": "🟠 SOSTENIBILITÀ DEL DEBITO SOTTO PRESSIONE",
        "y": 2.42
    },
    {
        "r": 2.0,
        "fill": "rgba(163, 230, 53, 0.30)",
        "line": "#84cc16",
        "title": "LIVELLO 2: HARDWARE, SEMICONDUTTORI & FORNITORI CRITICI",
        "desc": "SK Hynix (Memorie HBM) • Indice Semiconduttori (^SOX) • Produttori di Chip Fisici",
        "status": "🟡 CICLICO / DIPENDENTE DAL BUDGET DELLE BIG TECH",
        "y": 1.45
    },
    {
        "r": 1.0,
        "fill": "rgba(16, 185, 129, 0.85)",
        "line": "#10b981",
        "title": "LIVELLO 1 (CENTRO): BIG TECH & MONOPOLI DI MERCATO",
        "desc": "Nvidia (NVDA) • Mega-Cap Tecnologiche (MAGS: Microsoft, Google, Meta, Apple)",
        "status": "🟢 BILANCI FORTIFICATI / CASSA RECORD / RESISTENTI",
        "y": 0.0
    }
]

for ring in onion_rings:
    r = ring["r"]
    fig_onion.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-r, y0=-r, x1=r, y1=r,
        fillcolor=ring["fill"],
        line=dict(color=ring["line"], width=2.5, dash="solid" if r == 1.0 else "dot")
    )
    fig_onion.add_annotation(
        x=0, y=ring["y"],
        text=f"<b>{ring['title']}</b><br><span style='font-size:11px; color:#f1f5f9;'>{ring['desc']}</span><br><b>[{ring['status']}]</b>",
        showarrow=False,
        font=dict(color="#ffffff", size=11.5),
        align="center",
        bgcolor="rgba(10, 15, 29, 0.88)",
        bordercolor=ring["line"],
        borderwidth=1,
        borderpad=6
    )

fig_onion.update_xaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_yaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_layout(
    height=670,
    margin=dict(l=5, r=5, t=10, b=10),
    paper_bgcolor="#07090e",
    plot_bgcolor="#07090e"
)
st.plotly_chart(fig_onion, use_container_width=True)

# ==========================================
# 2. RAPPORTO ESECUTIVO (SENZA STILE CODICE)
# ==========================================
st.markdown("### 📑 Bollettino Esecutivo di Analisi Macroeconomica")

# Costruzione del report privo di rientri (previene il bug del rendering a codice)
report_html = (
'<div class="report-container">'
'<div class="report-header">'
'<div>'
'<h3 style="margin:0; color:#38bdf8; font-size:19px; font-weight:700;">Rapporto di Intelligence sui Mercati Finanziari</h3>'
'<p style="margin:4px 0 0 0; font-size:13px; color:#94a3b8;">Elaborazione quantitativa dei parametri di rischio, credito e liquidità globale.</p>'
'</div>'
f'<span style="background-color:#1e293b; color:#ffffff; padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600;">Data: {datetime.now().strftime("%d %B %Y")}</span>'
'</div>'
'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">'
'<div class="pillar-card" style="border-top-color: #ef4444;">'
'<h4 style="color:#f87171; margin-top:0; font-size:15px; font-weight:700;">1. Canale del Debito & Private Credit</h4>'
f'<p style="font-size:13.5px; line-height:1.6; color:#e2e8f0;">Il ratio <b>CCC / High Yield si attesta a {curr_ratio_cred:.2f}x</b>. '
'I problemi finanziari non nascono dai colossi con grandi riserve di liquidità, ma dal debito privato e dalle aziende ad alto indebitamento. '
'Se i gestori di prestiti alternativi come Blue Owl e i fondi BDC (BIZD) registrano pressioni sui rimborsi legati all\'infrastruttura dei data center, '
'il rifinanziamento diventerà oneroso per l\'intera filiera tecnologica.</p>'
'</div>'
'<div class="pillar-card" style="border-top-color: #eab308;">'
'<h4 style="color:#facc15; margin-top:0; font-size:15px; font-weight:700;">2. Ampiezza di Mercato & Settore Tech</h4>'
'<p style="font-size:13.5px; line-height:1.6; color:#e2e8f0;">Il confronto tra l\'indice S&P 500 equiponderato (RSP) e le Mega-Cap (MAGS) '
'evidenzia la concentrazione della performance azionaria. '
'Quando pochi titoli sostengono i massimi mentre il resto delle aziende resta fermo, la struttura di mercato diventa fragile. '
'I produttori di semiconduttori (SOX/NDX) continuano a beneficiare degli investimenti, ma la sostenibilità dipenderà dal ritorno economico effettivo.</p>'
'</div>'
'<div class="pillar-card" style="border-top-color: #10b981;">'
'<h4 style="color:#34d399; margin-top:0; font-size:15px; font-weight:700;">3. Oro, Bitcoin & Liquidità</h4>'
'<p style="font-size:13.5px; line-height:1.6; color:#e2e8f0;">La solidità dell\'Oro riflette la domanda di protezione contro la svalutazione monetaria. '
'Sul fronte digitale, Bitcoin si trova all\'interno del proprio canale quantitativo storico di medio-lungo periodo: '
'la tenuta delle fasce settimanali chiave identifica la linea di confine tra un mercato in espansione e una fase di debolezza ciclica.</p>'
'</div>'
'</div>'
'<div style="margin-top:20px;">'
'<h4 style="color:#ffffff; font-size:14px; margin-bottom:10px; font-weight:700;">Quadro Operativo di Allocazione Strategica</h4>'
'<table class="custom-table">'
'<thead>'
'<tr>'
'<th>Classe di Attivo</th>'
'<th>Stato di Mercato</th>'
'<th>Orientamento Strategico</th>'
'<th>Fattore Chiave da Monitorare</th>'
'</tr>'
'</thead>'
'<tbody>'
'<tr>'
'<td><b>Titoli Tecnologici Mega-Cap</b></td>'
'<td><span style="color:#34d399; font-weight:700;">Stabili / Rifugio</span></td>'
'<td>Mantenimento selettivo con gestione del rischio; evitare l\'eccesso di leva finanziaria.</td>'
'<td>Crescita degli investimenti in conto capitale (Capex) rispetto ai ricavi.</td>'
'</tr>'
'<tr>'
'<td><b>Small-Cap & Titoli Indebitati</b></td>'
'<td><span style="color:#f87171; font-weight:700;">Rischio Elevato</span></td>'
'<td>Prudenza verso società con rating basso e flussi di cassa operativi negativi.</td>'
'<td>Allargamento degli spread creditizi e scadenze di rinnovo del debito.</td>'
'</tr>'
'<tr>'
'<td><b>Metalli Preziosi (Oro / Hard Assets)</b></td>'
'<td><span style="color:#38bdf8; font-weight:700;">Accumulazione Difensiva</span></td>'
'<td>Esposizione strategica a copertura da shock di liquidità o svalutazione debitoria.</td>'
'<td>Rendimenti reali dei titoli governativi e andamento del dollaro.</td>'
'</tr>'
'<tr>'
'<td><b>Bitcoin & Criptovalute</b></td>'
'<td><span style="color:#facc15; font-weight:700;">Sensibilità alla Liquidità</span></td>'
'<td>Accumulo progressivo in prossimità della fascia inferiore della regressione.</td>'
'<td>Liquidità delle banche centrali e volumi sui mercati istituzionali.</td>'
'</tr>'
'</tbody>'
'</table>'
'</div>'
'</div>'
)
st.markdown(report_html, unsafe_allow_html=True)

# ==========================================
# 3. PANNELLO GRAFICI CON SELETTORE CANDELSTICK & TIMEFRAME
# ==========================================
st.markdown("### 📊 Analisi Dettagliata dei Grafici")

# Selettore Globale Modalità Grafico
col_ctrl1, col_ctrl2 = st.columns([1, 3])
with col_ctrl1:
    chart_mode = st.radio(
        "Modalità Visualizzazione:",
        ["Candele Giapponesi (Candlestick)", "Linea Continua"],
        horizontal=True
    )

# Funzione Universale per Generare Grafici Interattivi (Linee o Candele + Selettori Temporali)
def render_interactive_chart(df, title, is_candlestick=False, default_color="#38bdf8", is_ratio=False):
    fig = go.Figure()
    
    has_ohlc = not is_ratio and {'Open', 'High', 'Low', 'Close'}.issubset(df.columns)
    
    if is_candlestick and has_ohlc:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Prezzo",
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ))
    else:
        y_data = df['Close'] if 'Close' in df.columns else df.iloc[:, 0]
        fig.add_trace(go.Scatter(
            x=df.index,
            y=y_data,
            mode='lines',
            name="Valore",
            line=dict(color=default_color, width=2)
        ))
    
    # Barra di Selezione Timeframe Dinamica (Ore, Giorni, Mesi, Anni)
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7G", step="day", stepmode="backward"),
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1A", step="year", stepmode="backward"),
                dict(count=3, label="3A", step="year", stepmode="backward"),
                dict(step="all", label="TUTTO")
            ]),
            bgcolor="#131d31",
            activecolor="#2563eb",
            font=dict(color="#ffffff", size=11)
        ),
        rangeslider=dict(visible=False),
        type="date"
    )
    
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=390,
        paper_bgcolor="#07090e",
        plot_bgcolor="#07090e",
        font=dict(color="#ffffff"),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

use_candles = (chart_mode == "Candele Giapponesi (Candlestick)")

tab1, tab2, tab3, tab4 = st.tabs([
    "💳 Mercato Obbligazionario & Credito",
    "💻 Settore Tecnologico & AI Capex",
    "🌍 Indicatori Macro USA & Beni Rifugio",
    "₿ Bitcoin & Modello Quantitativo"
])

# ------------- TAB 1: CREDITO -------------
with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        if not ccc_spread.empty and not hy_spread.empty:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=hy_spread.index, y=hy_spread["BAMLH0A0HYM2"], name="Spread High Yield", line=dict(color="#38bdf8", width=1.8)))
            fig1.add_trace(go.Scatter(x=ccc_spread.index, y=ccc_spread["BAMLH0A3HYC"], name="Spread Titoli CCC", line=dict(color="#ef4444", width=2)))
            fig1.update_xaxes(
                rangeselector=dict(
                    buttons=[dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff")
                )
            )
            fig1.update_layout(title="Spread Obbligazioni USA: High Yield vs Spazzatura CCC", template="plotly_dark", height=390, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"))
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il tasso di interesse aggiuntivo richiesto dal mercato per prestare denaro ad aziende con rating fragile rispetto ai titoli di stato USA.<br><b>🔍 Come interpretarlo:</b> Un aumento rapido segnala una stretta sul credito e anticipa storicamente le correzioni dei listini azionari.</div>', unsafe_allow_html=True)

    with col_b:
        if not ratio_ccc_hy.empty:
            fig2 = render_interactive_chart(ratio_ccc_hy, "Rapporto di Stress: Spread CCC / High Yield", is_candlestick=False, default_color="#dc2626", is_ratio=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La pressione relativa che grava sull\'anello più fragile della catena debitoria.<br><b>🔍 Come interpretarlo:</b> Se il rapporto supera 3.5x - 4.0x, le aziende più vulnerabili sono in difficoltà di rifinanziamento prima ancora che il mercato azionario reagisca.</div>', unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        if not bizd.empty:
            fig3 = render_interactive_chart(bizd, "ETF BIZD: Barometro del Private Credit & Prestiti Diretti", is_candlestick=use_candles, default_color="#f59e0b")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il valore delle società di sviluppo aziendale (BDC) che finanziano a debito le medie imprese.<br><b>🔍 Come interpretarlo:</b> Un trend discendente indica difficoltà nei rimborsi dei prestiti e minore disponibilità di capitale non bancario.</div>', unsafe_allow_html=True)

    with col_d:
        if not owl.empty:
            fig4 = render_interactive_chart(owl, "Blue Owl Capital (OWL): Finanziatore Infrastrutture AI", is_candlestick=use_candles, default_color="#a855f7")
            st.plotly_chart(fig4, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> L\'andamento di un primario gestore alternativo con ingente esposizione verso data center e leasing per server.<br><b>🔍 Come interpretarlo:</b> Un andamento solido indica la continuità degli afflussi di capitale verso l\'infrastruttura tecnologica.</div>', unsafe_allow_html=True)

# ------------- TAB 2: TECH & AI -------------
with tab2:
    col_e, col_f = st.columns(2)
    with col_e:
        if not nvda.empty:
            fig5 = render_interactive_chart(nvda, "Nvidia (NVDA): Cuore del Ciclo Computazionale AI", is_candlestick=use_candles, default_color="#10b981")
            st.plotly_chart(fig5, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il titolo di riferimento su cui converge la spesa globale per acceleratori grafici e calcolo intensivo.<br><b>🔍 Come interpretarlo:</b> Finché Nvidia mantiene minimi crescenti, l\'intero ecosistema dell\'hardware tecnologico gode di fiducia e flussi.</div>', unsafe_allow_html=True)

    with col_f:
        if not skhynix.empty:
            fig6 = render_interactive_chart(skhynix, "SK Hynix (000660.KS): Memorie ad Alta Velocità (HBM)", is_candlestick=use_candles, default_color="#84cc16")
            st.plotly_chart(fig6, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il produttore leader di memorie indispensabili per il funzionamento delle GPU avanzate.<br><b>🔍 Come interpretarlo:</b> Monitora la produzione fisica reale della catena di fornitura. Un rallentamento anticipa flessioni nei ricavi dei semiconduttori.</div>', unsafe_allow_html=True)

    col_g, col_h = st.columns(2)
    with col_g:
        if not ratio_sox_ndx.empty:
            fig7 = render_interactive_chart(ratio_sox_ndx, "Rapporto Semiconduttori / Nasdaq 100 (^SOX / ^NDX)", is_candlestick=False, default_color="#38bdf8", is_ratio=True)
            st.plotly_chart(fig7, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La forza relativa dei produttori di microchip rispetto al settore tecnologico allargato.<br><b>🔍 Come interpretarlo:</b> Picchi storici indicano che l\'hardware sta correndo molto più velocemente rispetto ai ritorni economici del software.</div>', unsafe_allow_html=True)

    with col_h:
        if not rsp.empty and not mags.empty:
            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=rsp.index, y=rsp["Close"] / rsp["Close"].iloc[0] * 100, name="S&P 500 Equal Weight (RSP)", line=dict(color="#94a3b8", width=1.5)))
            fig8.add_trace(go.Scatter(x=mags.index, y=mags["Close"] / mags["Close"].iloc[0] * 100, name="Mega-Cap Mag 7 (MAGS)", line=dict(color="#f43f5e", width=2)))
            fig8.update_xaxes(
                rangeselector=dict(
                    buttons=[dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="1A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff")
                )
            )
            fig8.update_layout(title="Ampiezza di Mercato: Titoli Medi (RSP) vs Giganti Tech (MAGS)", template="plotly_dark", height=390, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"))
            st.plotly_chart(fig8, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Confronta l\'andamento medio delle 500 aziende USA contro i primi 7 colossi tech.<br><b>🔍 Come interpretarlo:</b> Una divergenza in cui solo MAGS sale mentre RSP lateralizza segnala una fase distributiva guidata da pochi titoli.</div>', unsafe_allow_html=True)

# ------------- TAB 3: MACRO & BENI RIFUGIO -------------
with tab3:
    col_i, col_l = st.columns(2)
    with col_i:
        if not unrate.empty and not sahm.empty:
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Disoccupazione (%)", line=dict(color="#94a3b8", width=1.5)))
            fig9.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Regola di Sahm", line=dict(color="#ef4444", width=2.2)))
            fig9.add_hline(y=0.5, line_dash="dash", line_color="#ef4444", annotation_text="Trigger Recessione (0.50)", annotation_font_color="#ffffff")
            fig9.update_layout(title="Disoccupazione USA & Trigger Recessionario Sahm", template="plotly_dark", height=390, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"))
            st.plotly_chart(fig9, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> L\'accelerazione del tasso di disoccupazione rispetto ai minimi dell\'ultimo anno solare.<br><b>🔍 Come interpretarlo:</b> Il superamento della soglia 0.50 ha sempre coinciso con l\'inizio formale di una recessione negli Stati Uniti.</div>', unsafe_allow_html=True)

    with col_l:
        if not t10y2y.empty:
            fig10 = go.Figure()
            fig10.add_trace(go.Scatter(x=t10y2y.index, y=t10y2y["T10Y2Y"], name="Curva 10Y-2Y", line=dict(color="#06b6d4", width=1.8)))
            fig10.add_hline(y=0.0, line_dash="dash", line_color="#ffffff")
            fig10.update_layout(title="Differenziale dei Tassi Governativi USA (10 Anni - 2 Anni)", template="plotly_dark", height=390, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"))
            st.plotly_chart(fig10, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La pendenza della curva dei rendimenti governativi americani.<br><b>🔍 Come interpretarlo:</b> L\'inversione (sotto zero) anticipa i problemi; il ritorno sopra zero (disinversione) coincide con l\'avvicinarsi della correzione economica.</div>', unsafe_allow_html=True)

    col_m, col_n = st.columns(2)
    with col_m:
        if not vix.empty:
            fig11 = render_interactive_chart(vix, "Indice della Paura VIX: Volatilità Implicita Opzioni S&P 500", is_candlestick=use_candles, default_color="#f43f5e")
            st.plotly_chart(fig11, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La volatilità attesa a 30 giorni sul mercato azionario statunitense.<br><b>🔍 Come interpretarlo:</b> Sotto 15 regna la compiacenza; sopra 20 iniziano le coperture; sopra 30 si manifestano fasi di scarico emotivo.</div>', unsafe_allow_html=True)

    with col_n:
        if not ratio_gold_ndx.empty:
            fig12 = render_interactive_chart(ratio_gold_ndx, "Rapporto Oro / Nasdaq 100: Riserva di Valore vs Crescita Tech", is_candlestick=False, default_color="#eab308", is_ratio=True)
            st.plotly_chart(fig12, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La preferenza degli investitori globali tra bene rifugio fisico (Oro) e asset di crescita a lungo termine (Nasdaq).<br><b>🔍 Come interpretarlo:</b> Un aumento evidenzia la ricerca di protezione del capitale contro svalutazione o shock sistemici.</div>', unsafe_allow_html=True)

# ------------- TAB 4: BITCOIN -------------
with tab4:
    if not btc.empty:
        df_btc = btc.copy()
        
        # Medie Mobili Chiave
        df_btc["SMA_20W"] = df_btc["Close"].rolling(window=140).mean()
        df_btc["EMA_21W"] = df_btc["Close"].ewm(span=147, adjust=False).mean()
        
        # Regressione Logaritmica Storica
        x_d = np.arange(1, len(df_btc) + 1)
        log_x = np.log(x_d)
        log_y = np.log(df_btc["Close"].values)
        poly = np.polyfit(log_x, log_y, 1)
        fit_l = poly[0] * log_x + poly[1]
        
        df_btc["Canale_Centrale"] = np.exp(fit_l)
        std_d = np.std(log_y - fit_l)
        df_btc["Canale_Superiore"] = np.exp(fit_l + 1.25 * std_d)
        df_btc["Canale_Inferiore"] = np.exp(fit_l - 1.25 * std_d)

        fig13 = go.Figure()
        
        if use_candles:
            fig13.add_trace(go.Candlestick(
                x=df_btc.index, open=df_btc['Open'], high=df_btc['High'], low=df_btc['Low'], close=df_btc['Close'],
                name="BTC Candele", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
            ))
        else:
            fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Close"], name="BTC Prezzo ($)", line=dict(color="#ffffff", width=1.8)))
            
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["SMA_20W"], name="Media 20 Settimane (SMA)", line=dict(color="#10b981", width=1.4)))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["EMA_21W"], name="Media 21 Settimane (EMA)", line=dict(color="#06b6d4", width=1.4)))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Canale_Superiore"], name="Banda Alta (Euforia)", line=dict(color="#ef4444", dash="dash")))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Canale_Centrale"], name="Valore Equo Storico", line=dict(color="#eab308", dash="dot")))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Canale_Inferiore"], name="Banda Bassa (Accumulo)", line=dict(color="#22c55e", dash="dash")))

        fig13.update_xaxes(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(count=3, label="3A", step="year", stepmode="backward"),
                    dict(step="all", label="TUTTO")
                ],
                bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff")
            )
        )
        fig13.update_yaxes(type="log", title="Prezzo BTC (Scala Logaritmica)")
        fig13.update_layout(
            title="Bitcoin: Canale Quantitativo di Regressione Logaritmica & Support Band Settimanale",
            template="plotly_dark",
            height=600,
            paper_bgcolor="#07090e",
            plot_bgcolor="#07090e",
            font=dict(color="#ffffff")
        )
        st.plotly_chart(fig13, use_container_width=True)
        st.markdown("""
        <div class="chart-guide">
            <b>📌 Cosa misura:</b> Il posizionamento di Bitcoin rispetto al suo canale logaritmico storico e alle medie settimanali a medio termine.<br>
            <b>🔍 Come interpretarlo:</b><br>
            • <b>Fascia tra le due medie mobili (20W SMA & 21W EMA):</b> Se il prezzo scambia sopra, la fase rialzista è confermata; la perdita di queste medie segnala una transizione correttiva prolungata.<br>
            • <b>Banda Verde Inferiore:</b> Area storica di massimo sconto e accumulazione strategica.<br>
            • <b>Banda Rossa Superiore:</b> Area di surriscaldamento del ciclo in cui storicamente maturano prese di profitto.
        </div>
        """, unsafe_allow_html=True)
