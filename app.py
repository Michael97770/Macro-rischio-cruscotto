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
    page_title="Macro Risk Terminal | Market Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Iniezione CSS ad Altissimo Contrasto (Testi Bianco Puro #FFFFFF)
st.markdown("""
<style>
/* Reset sfondo generale */
.stApp {
    background-color: #07090e !important;
    color: #ffffff !important;
}

/* CARD METRICHE SUPERIORI AD ALTO CONTRASTO */
.metric-box {
    background: linear-gradient(145deg, #131c2e, #0a101b);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    height: 100%;
}
.metric-title {
    color: #ffffff !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    margin-bottom: 6px;
}
.metric-val {
    color: #38bdf8 !important;
    font-size: 32px !important;
    font-weight: 800 !important;
    line-height: 1.1;
    margin-bottom: 6px;
}
.metric-sub {
    font-size: 13px !important;
    font-weight: 700 !important;
}

/* BANNER ALLARMI DI MERCATO */
.alert-banner {
    background: #0f172a;
    border-left: 5px solid #ef4444;
    border-radius: 8px;
    padding: 14px 20px;
    margin: 15px 0 25px 0;
}

/* SCHEDA REPORT ESECUTIVO */
.report-container {
    background: linear-gradient(145deg, #10192a, #090e17);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 24px;
    margin: 20px 0;
}
.pillar-card {
    background-color: #141f33;
    border-radius: 8px;
    padding: 18px;
    border-top: 3px solid #38bdf8;
    height: 100%;
}
.custom-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
.custom-table th {
    background-color: #1e293b;
    color: #ffffff;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 700;
}
.custom-table td {
    padding: 12px;
    border-bottom: 1px solid #1e293b;
    font-size: 13.5px;
    color: #ffffff;
}

/* GUIDE DIDATTICHE SOTTO I GRAFICI */
.chart-guide {
    background-color: #0c1424;
    border-left: 4px solid #38bdf8;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-top: -6px;
    margin-bottom: 30px;
    font-size: 13.5px;
    color: #ffffff;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

st.title("🌐 Macro Risk & Liquidity Intelligence Terminal")
st.markdown("<span style='color:#ffffff; font-size:15px;'>Piattaforma quantitativa per il monitoraggio della liquidità, del debito aziendale e delle asimmetrie di mercato.</span>", unsafe_allow_html=True)

# ==========================================
# ACQUISIZIONE DATI LIVE (FRED & YAHOO OHLC)
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

with st.spinner("Aggiornamento feed quantitativi in tempo reale..."):
    # FRED Macro & Credito
    hy_spread = load_fred_data("BAMLH0A0HYM2")
    ccc_spread = load_fred_data("BAMLH0A3HYC")
    unrate = load_fred_data("UNRATE")
    sahm = load_fred_data("SAHMREALTIME")
    t10y2y = load_fred_data("T10Y2Y")
    
    # Yahoo Finance (Dati OHLC Completi)
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

# Valori Istantanei
curr_sahm = float(sahm.iloc[-1].values[0]) if not sahm.empty else 0.0
curr_curve = float(t10y2y.iloc[-1].values[0]) if not t10y2y.empty else 0.0
curr_ratio_cred = float(ratio_ccc_hy.iloc[-1].values[0]) if not ratio_ccc_hy.empty else 3.0
curr_vix = float(vix["Close"].iloc[-1]) if not vix.empty else 15.0

# Calcolo Punteggio Rischio Sistemico (0-100)
risk_score = 0
allerta_list = []

if curr_sahm >= 0.50: 
    risk_score += 35
    allerta_list.append("Regola di Sahm Attiva: Rischio Recessione Imminente")
elif curr_sahm >= 0.35: 
    risk_score += 20
    allerta_list.append("Disoccupazione USA in rapido aumento (Sahm > 0.35)")

if curr_curve > 0 and not t10y2y.empty and (t10y2y.tail(180).min().values[0] < -0.2):
    risk_score += 25
    allerta_list.append("Disinversione Curva dei Rendimenti (Fase Storica Pre-Recessiva)")
elif curr_curve < 0:
    risk_score += 15

if curr_ratio_cred > 3.8: 
    risk_score += 25
    allerta_list.append("Stress Acuto Debito CCC: Difficoltà di Rifinanziamento")
elif curr_ratio_cred > 3.4: 
    risk_score += 15
    allerta_list.append("Spread Credito Fragile in Allargamento")

if curr_vix > 25: 
    risk_score += 15
    allerta_list.append("Picco di Volatilità Azionaria (VIX > 25)")
elif curr_vix > 20: 
    risk_score += 8

risk_score = min(risk_score, 100)

# Diagnosi di Ciclo e Runway Temporale
if curr_sahm >= 0.50:
    fase_ciclo = "Fase 4: Rischio Recessione Confermato"
    runway_desc = "Finestra di tolleranza chiusa. Massimo rischio di ribasso sui titoli ciclici."
    badge_col = "#ef4444"
elif curr_curve > 0 and risk_score >= 45:
    fase_ciclo = "Fase 3: Fine Ciclo (Disinversione Curva)"
    runway_desc = "Finestra stimata: 3 - 8 Mesi prima del massimo stress di mercato. Fase tipica di rotazione difensiva."
    badge_col = "#f59e0b"
elif not ratio_sox_ndx.empty and ratio_sox_ndx.iloc[-1].values[0] > ratio_sox_ndx.tail(252).quantile(0.85).values[0]:
    fase_ciclo = "Fase 2: Espansione Concentrata AI Capex"
    runway_desc = "Finestra stimata: 6 - 12 Mesi di liquidità residua, ma con divergenze crescenti sulle small-cap."
    badge_col = "#38bdf8"
else:
    fase_ciclo = "Fase 1: Espansione Sincrona"
    runway_desc = "Finestra favorevole: 12+ Mesi. Contesto favorevole all'accumulo azionario."
    badge_col = "#10b981"

# ==========================================
# METRICHE SUPERIORI AD ALTO CONTRASTO
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    col_status = "#ef4444" if risk_score > 60 else ("#f59e0b" if risk_score > 35 else "#10b981")
    delta_text = "RISCHIO ELEVATO" if risk_score > 60 else ("ATTENZIONE" if risk_score > 35 else "CONDIZIONI NORMALI")
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Indice Rischio Sistemico</div>
        <div class="metric-val">{risk_score} <span style="font-size:18px; color:#ffffff;">/ 100</span></div>
        <div class="metric-sub" style="color:{col_status};">● {delta_text}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    sahm_col = "#ef4444" if curr_sahm >= 0.5 else ("#f59e0b" if curr_sahm >= 0.35 else "#10b981")
    sahm_status = "RECESSIONE" if curr_sahm >= 0.5 else ("PREALLARME" if curr_sahm >= 0.35 else "MERCATO SOLIDO")
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Regola di Sahm (Lavoro USA)</div>
        <div class="metric-val">{curr_sahm:.2f}</div>
        <div class="metric-sub" style="color:{sahm_col};">● {sahm_status} (Trigger: 0.50)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    curve_col = "#38bdf8" if curr_curve > 0 else "#f59e0b"
    curve_status = "DISINVERTITA (Rischio Tagli)" if curr_curve > 0 else "INVERTITA (Fase Precoce)"
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Curva Rendimenti (10Y - 2Y)</div>
        <div class="metric-val">{curr_curve:.2f}%</div>
        <div class="metric-sub" style="color:{curve_col};">● {curve_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    cred_col = "#ef4444" if curr_ratio_cred > 3.5 else "#10b981"
    cred_status = "STRESS SU EMITTENTI CCC" if curr_ratio_cred > 3.5 else "SPREAD NELLA NORMA"
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-title">Rapporto Debito CCC / High Yield</div>
        <div class="metric-val">{curr_ratio_cred:.2f}x</div>
        <div class="metric-sub" style="color:{cred_col};">● {cred_status}</div>
    </div>
    """, unsafe_allow_html=True)

# BANNER DIAGNOSTICO DEI CAMPANELLI D'ALLARME
alerts_str = " &nbsp; | &nbsp; ".join([f"⚠️ <b>{a}</b>" for a in allerta_list]) if allerta_list else "✅ <b>Nessun campanello d'allarme critico rilevato sui dati odierni.</b>"
st.markdown(f"""
<div class="alert-banner">
    <div style="font-size:12px; color:#ffffff; font-weight:800; text-transform:uppercase; margin-bottom:4px;">Stato degli Allarmi Real-Time:</div>
    <div style="font-size:14px; color:#ffffff;">{alerts_str}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. GRAFICO A CIPOLLA DINAMICO (REATTIVO AI DATI)
# ==========================================
st.markdown("### 🧅 Modello a Cipolla del Rischio: Radar Concentrico Dinamico")
st.markdown("<span style='color:#ffffff; font-size:14px;'>Gli anelli aggiornano dinamicamente colore e stato in base alle letture live del mercato (dal debito fragile esterno al nucleo tech interno).</span>", unsafe_allow_html=True)

# Calcolo dinamico dello stato degli anelli
# Anello 4 (Junk): Rosso se ratio CCC/HY > 3.4 o spread CCC > 11%
l4_color = "#ef4444" if curr_ratio_cred > 3.4 else "#f59e0b"
l4_status = "🔴 AREA DI PRIMO COLLASSO / ALLARME ATTIVO" if curr_ratio_cred > 3.4 else "🟡 CREDITO SOTTO CONTROLLO"

# Anello 3 (Private Credit): Arancio se BIZD scende sotto la media a 50 giorni
bizd_ma50 = bizd["Close"].rolling(50).mean().iloc[-1] if not bizd.empty else 0
l3_color = "#f97316" if (not bizd.empty and bizd["Close"].iloc[-1] < bizd_ma50) else "#84cc16"
l3_status = "🟠 SOSTENIBILITÀ DEBITO PRIVATE SOTTO PRESSIONE" if l3_color == "#f97316" else "🟢 PRIVATE CREDIT RESILIENTE"

# Anello 2 (Hardware/SOX): Dipende dalla forza relativa SOX/NDX
l2_color = "#84cc16"
l2_status = "🟡 CICLICO / DOMANDA ELEVATA MA VULNERABILE AL CAPEX"

# Anello 1 (Nucleo Big Tech NVDA): Verde se sopra 200 SMA, altrimenti Giallo
nvda_ma200 = nvda["Close"].rolling(200).mean().iloc[-1] if not nvda.empty else 0
l1_color = "#10b981" if (not nvda.empty and nvda["Close"].iloc[-1] >= nvda_ma200) else "#f59e0b"
l1_status = "🟢 BILANCI SOLIDI / LIQUIDITÀ RECORD (Trend Rialzista)" if l1_color == "#10b981" else "🟡 DIVERGENZA SUL NUCLEO TECH"

fig_onion = go.Figure()

onion_rings = [
    {
        "r": 4.0, "fill": "rgba(239, 68, 68, 0.16)", "line": l4_color,
        "title": "LIVELLO 4 (PERIFERIA): DEBITO SPAZZATURA & AZIENDE ZOMBIE",
        "desc": f"Spread CCC • Ratio CCC/HY ({curr_ratio_cred:.2f}x) • Startup senza utili • Token speculativi",
        "status": l4_status, "y": 3.42
    },
    {
        "r": 3.0, "fill": "rgba(249, 115, 22, 0.22)", "line": l3_color,
        "title": "LIVELLO 3: PRIVATE CREDIT & FINANZIAMENTO INFRASTRUTTURE",
        "desc": "Blue Owl (OWL) • BIZD (BDC) • Debito CoreWeave (USU2069EAB6) • Obbligazioni lunghi Tech",
        "status": l3_status, "y": 2.42
    },
    {
        "r": 2.0, "fill": "rgba(132, 204, 22, 0.26)", "line": l2_color,
        "title": "LIVELLO 2: HARDWARE, SEMICONDUTTORI & FILIERA CRITICA",
        "desc": "SK Hynix (Memorie HBM) • Indice Semiconduttori (^SOX) • Fornitori Chiave",
        "status": l2_status, "y": 1.45
    },
    {
        "r": 1.0, "fill": "rgba(16, 185, 129, 0.88)", "line": l1_color,
        "title": "LIVELLO 1 (CENTRO): BIG TECH & MONOPOLI DI MERCATO",
        "desc": "Nvidia (NVDA) • Mega-Cap Tecnologiche (MAGS)",
        "status": l1_status, "y": 0.0
    }
]

for ring in onion_rings:
    r = ring["r"]
    fig_onion.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-r, y0=-r, x1=r, y1=r,
        fillcolor=ring["fill"],
        line=dict(color=ring["line"], width=2.8, dash="solid" if r == 1.0 else "dot")
    )
    fig_onion.add_annotation(
        x=0, y=ring["y"],
        text=f"<b>{ring['title']}</b><br><span style='font-size:11px; color:#ffffff;'>{ring['desc']}</span><br><b>[{ring['status']}]</b>",
        showarrow=False,
        font=dict(color="#ffffff", size=11.5),
        align="center",
        bgcolor="rgba(10, 15, 29, 0.90)",
        bordercolor=ring["line"],
        borderwidth=1.2,
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
# 2. RAPPORTO DI INTELLIGENCE CON BUSSOLA DI ORIENTAMENTO
# ==========================================
st.markdown("### 📑 Bussola Macroeconomica & Orizzonte Temporale Operativo")

report_html = (
'<div class="report-container">'
'<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:20px;">'
'<div>'
'<h3 style="margin:0; color:#38bdf8; font-size:19px; font-weight:700;">Inquadramento Strategico di Mercato</h3>'
f'<p style="margin:4px 0 0 0; font-size:13.5px; color:#ffffff;"><b>Diagnosi:</b> {fase_ciclo} &nbsp;|&nbsp; <b>Orizzonte Runway:</b> <span style="color:#facc15;">{runway_desc}</span></p>'
'</div>'
f'<span style="background-color:#1e293b; color:#ffffff; padding:6px 14px; border-radius:6px; font-size:12px; font-weight:700;">Aggiornato: {datetime.now().strftime("%d %B %Y")}</span>'
'</div>'
'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">'
'<div class="pillar-card" style="border-top-color: #ef4444;">'
'<h4 style="color:#ffffff; margin-top:0; font-size:15px; font-weight:700;">1. Canale del Debito & Rifinanziamento</h4>'
f'<p style="font-size:13.5px; line-height:1.6; color:#ffffff;">Il moltiplicatore <b>CCC / High Yield si attesta a {curr_ratio_cred:.2f}x</b>. '
'Nelle fasi di cambio ciclo, il mercato azionario continua a salire per inerzia mentre il credito più rischioso comincia a mostrare insolvenze. '
'I fondi di Private Credit (Blue Owl, BIZD) indicano se il capitale continua a finanziare il debito infrastrutturale delle GPU. '
'Se i rendimenti dei bond ultra-lunghi delle Big Tech rimangono tesi, il costo di espansione dei data center aumenterà in modo marcato.</p>'
'</div>'
'<div class="pillar-card" style="border-top-color: #eab308;">'
'<h4 style="color:#ffffff; margin-top:0; font-size:15px; font-weight:700;">2. Ampiezza e Concentrazione Azionaria</h4>'
'<p style="font-size:13.5px; line-height:1.6; color:#ffffff;">Il rapporto tra l\'indice equiponderato (RSP) e i colossi tecnologici (MAGS) '
'mostra se la partecipazione al rialzo è corale o circoscritta a pochi titoli monopolisti. '
'Una concentrazione persistente indica un mercato guidato dalla scarsità di alternative profittevoli. '
'I titoli hardware (SOX/NDX) evidenziano che la fase di acquisto delle componenti fisiche è ancora forte, ma anticipa la necessità di vedere utili reali nelle applicazioni software.</p>'
'</div>'
'<div class="pillar-card" style="border-top-color: #10b981;">'
'<h4 style="color:#ffffff; margin-top:0; font-size:15px; font-weight:700;">3. Liquidità Sistemica, Oro & Bitcoin</h4>'
'<p style="font-size:13.5px; line-height:1.6; color:#ffffff;">La forza dell\'Oro sui massimi certifica la volontà degli operatori di coprirsi dalla svalutazione monetaria. '
'Su Bitcoin, la tenuta della fascia 20W SMA / 21W EMA rappresenta il discrimine tra mercato toro e fase distributiva. '
'L\'oscillatore Mayer Multiple permette di evitare ingressi su massimi di euforia speculativa, individuando invece le aree ottimali di accumulo.</p>'
'</div>'
'</div>'
'<div style="margin-top:22px;">'
'<h4 style="color:#ffffff; font-size:15px; margin-bottom:10px; font-weight:700;">Matrice Decisionale: Dove Allocare Capitale Oggi</h4>'
'<table class="custom-table">'
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
'<td><span style="color:#facc15; font-weight:700;">Medio / Monitorare</span></td>'
'<td>Medio Periodo (3-6 Mesi)</td>'
'<td>Mantenere con stop profit rigidi; evitare acquisti aggressivi a leva sui massimi.</td>'
'</tr>'
'<tr>'
'<td><b>Small-Cap & Zombie Debt</b></td>'
'<td><span style="color:#ef4444; font-weight:700;">Critico (Sotto Pressione)</span></td>'
'<td>Prudenza Assoluta</td>'
'<td>Evitare società che necessitano di rifinanziare debito ad alto rendimento.</td>'
'</tr>'
'<tr>'
'<td><b>Oro & Beni Rifugio</b></td>'
'<td><span style="color:#10b981; font-weight:700;">Basso (Trend Solido)</span></td>'
'<td>Lungo Periodo (12-24 Mesi)</td>'
'<td>Accumulazione strategica come assicurazione patrimoniale e contro shock sistemici.</td>'
'</tr>'
'<tr>'
'<td><b>Bitcoin & Crypto</b></td>'
'<td><span style="color:#38bdf8; font-weight:700;">Medio / Guidato da Medie</span></td>'
'<td>Ciclico (6-18 Mesi)</td>'
'<td>Accumulo se sopra le medie settimanali o in prossimità della fascia bassa del Mayer Multiple.</td>'
'</tr>'
'</tbody>'
'</table>'
'</div>'
'</div>'
)
st.markdown(report_html, unsafe_allow_html=True)

# ==========================================
# 3. PANNELLO GRAFICI OTTIMIZZATO (TITOLI SEPARATI DAI BOTTONI)
# ==========================================
st.markdown("### 📊 Analisi Grafica Interattiva")

col_ctrl1, col_ctrl2 = st.columns([1, 3])
with col_ctrl1:
    chart_mode = st.radio(
        "Stile Grafico:",
        ["Candele Giapponesi (Candlestick)", "Linea Continua"],
        horizontal=True
    )

# Funzione Universale per Grafici: Risolve la collisione tra titolo e time selector
def render_interactive_chart(df, title, is_candlestick=False, default_color="#38bdf8", is_ratio=False):
    fig = go.Figure()
    has_ohlc = not is_ratio and {'Open', 'High', 'Low', 'Close'}.issubset(df.columns)
    
    if is_candlestick and has_ohlc:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Prezzo", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
        ))
    else:
        y_data = df['Close'] if 'Close' in df.columns else df.iloc[:, 0]
        fig.add_trace(go.Scatter(
            x=df.index, y=y_data, mode='lines', name="Valore",
            line=dict(color=default_color, width=2)
        ))
    
    # Barra di Selezione Temporale
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
            font=dict(color="#ffffff", size=11),
            y=1.14,
            x=0.99,
            xanchor="right"
        ),
        rangeslider=dict(visible=False),
        type="date"
    )
    
    # Aumentato il margine superiore (t=80) e posizionato il titolo in alto a sinistra per azzerare le collisioni
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            y=0.96,
            x=0.01,
            xanchor='left',
            yanchor='top',
            font=dict(color="#ffffff", size=14)
        ),
        template="plotly_dark",
        height=410,
        paper_bgcolor="#07090e",
        plot_bgcolor="#07090e",
        font=dict(color="#ffffff"),
        margin=dict(l=15, r=15, t=80, b=15)
    )
    return fig

use_candles = (chart_mode == "Candele Giapponesi (Candlestick)")

tab1, tab2, tab3, tab4 = st.tabs([
    "💳 Mercato del Credito & Spazzatura",
    "💻 Settore Tech & AI Capex",
    "🌍 Macro USA & Beni Rifugio",
    "₿ Bitcoin & Indicatori Quantitativi"
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
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig1.update_layout(
                title=dict(text="<b>Spread Obbligazioni USA: High Yield vs Spazzatura CCC</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=410, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il tasso di interesse extra preteso dal mercato per prestare denaro a società fragili rispetto ai Treasury USA.<br><b>🔍 Come interpretarlo:</b> Un\'impennata anticipa le correzioni azionarie perché le aziende ad alto debito non riescono più a rifinanziarsi.</div>', unsafe_allow_html=True)

    with col_b:
        if not ratio_ccc_hy.empty:
            fig2 = render_interactive_chart(ratio_ccc_hy, "Rapporto di Stress: Spread CCC / High Yield", is_candlestick=False, default_color="#dc2626", is_ratio=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La pressione relativa scaricata sull\'anello più debole del debito.<br><b>🔍 Come interpretarlo:</b> Valori superiori a 3.5x evidenziano che il rischio di default si sta concentrando prima ancora che l\'indice generale lo rifletta.</div>', unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        if not bizd.empty:
            fig3 = render_interactive_chart(bizd, "ETF BIZD: Barometro del Private Credit & Prestiti Diretti", is_candlestick=use_candles, default_color="#f59e0b")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il valore delle società che erogano debito privato a media scadenza.<br><b>🔍 Come interpretarlo:</b> La rottura dei minimi indica sofferenza nei bilanci non quotati e stretta del credito alternativo.</div>', unsafe_allow_html=True)

    with col_d:
        if not owl.empty:
            fig4 = render_interactive_chart(owl, "Blue Owl Capital (OWL): Finanziatore Infrastrutture AI", is_candlestick=use_candles, default_color="#a855f7")
            st.plotly_chart(fig4, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La solidità di uno dei massimi finanziatori di data center per l\'Intelligenza Artificiale.<br><b>🔍 Come interpretarlo:</b> La tenuta delle quotazioni conferma che i capitali continuano a fluire verso l\'infrastruttura server.</div>', unsafe_allow_html=True)

# ------------- TAB 2: TECH & AI -------------
with tab2:
    col_e, col_f = st.columns(2)
    with col_e:
        if not nvda.empty:
            fig5 = render_interactive_chart(nvda, "Nvidia (NVDA): Cuore del Ciclo Computazionale AI", is_candlestick=use_candles, default_color="#10b981")
            st.plotly_chart(fig5, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il leader indiscusso della fornitura di schede acceleratrici per l\'elaborazione dati.<br><b>🔍 Come interpretarlo:</b> Finché Nvidia mantiene una struttura di massimi e minimi crescenti, la tesi rialzista del settore tecnologico rimane solida.</div>', unsafe_allow_html=True)

    with col_f:
        if not skhynix.empty:
            fig6 = render_interactive_chart(skhynix, "SK Hynix (000660.KS): Memorie ad Alta Velocità (HBM)", is_candlestick=use_candles, default_color="#84cc16")
            st.plotly_chart(fig6, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il fornitore critico dei moduli di memoria indispensabili per i chip grafici.<br><b>🔍 Come interpretarlo:</b> Monitora la catena di approvvigionamento reale; una flessione negli ordinativi anticipa rallentamenti per i produttori di GPU.</div>', unsafe_allow_html=True)

    col_g, col_h = st.columns(2)
    with col_g:
        if not ratio_sox_ndx.empty:
            fig7 = render_interactive_chart(ratio_sox_ndx, "Rapporto Semiconduttori / Nasdaq 100 (^SOX / ^NDX)", is_candlestick=False, default_color="#38bdf8", is_ratio=True)
            st.plotly_chart(fig7, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La sovraperformance dei produttori di chip rispetto a tutto il paniere tecnologico.<br><b>🔍 Come interpretarlo:</b> Valori record segnalano che l\'hardware sta anticipando ritorni economici che dovranno poi essere confermati dai software.</div>', unsafe_allow_html=True)

    with col_h:
        if not rsp.empty and not mags.empty:
            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=rsp.index, y=rsp["Close"] / rsp["Close"].iloc[0] * 100, name="S&P 500 Equal Weight (RSP)", line=dict(color="#94a3b8", width=1.5)))
            fig8.add_trace(go.Scatter(x=mags.index, y=mags["Close"] / mags["Close"].iloc[0] * 100, name="Mega-Cap Mag 7 (MAGS)", line=dict(color="#f43f5e", width=2)))
            fig8.update_xaxes(
                rangeselector=dict(
                    buttons=[dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="1A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig8.update_layout(
                title=dict(text="<b>Ampiezza di Mercato: Titoli Medi (RSP) vs Giganti Tech (MAGS)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=410, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig8, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il divario di rendimento tra le 500 aziende USA equiponderate e i 7 colossi monopolisti.<br><b>🔍 Come interpretarlo:</b> Se MAGS sale mentre RSP scende, l\'indice è trainato da pochi titoli, sintomo classico di fine ciclo distributivo.</div>', unsafe_allow_html=True)

# ------------- TAB 3: MACRO & BENI RIFUGIO -------------
with tab3:
    col_i, col_l = st.columns(2)
    with col_i:
        if not unrate.empty and not sahm.empty:
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Disoccupazione (%)", line=dict(color="#94a3b8", width=1.5)))
            fig9.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Regola di Sahm", line=dict(color="#ef4444", width=2.2)))
            fig9.add_hline(y=0.5, line_dash="dash", line_color="#ef4444", annotation_text="Trigger Recessione (0.50)", annotation_font_color="#ffffff")
            fig9.update_layout(
                title=dict(text="<b>Disoccupazione USA & Trigger Recessionario Sahm</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=410, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig9, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> L\'aumento percentuale della disoccupazione rispetto ai minimi dell\'ultimo anno.<br><b>🔍 Come interpretarlo:</b> Sopra quota 0.50 non ha mai fallito nell\'identificare l\'ingresso in una recessione con calo degli utili aziendali.</div>', unsafe_allow_html=True)

    with col_l:
        if not t10y2y.empty:
            fig10 = go.Figure()
            fig10.add_trace(go.Scatter(x=t10y2y.index, y=t10y2y["T10Y2Y"], name="Curva 10Y-2Y", line=dict(color="#06b6d4", width=1.8)))
            fig10.add_hline(y=0.0, line_dash="dash", line_color="#ffffff")
            fig10.update_layout(
                title=dict(text="<b>Differenziale Tassi USA (10 Anni - 2 Anni)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=410, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig10, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La pendenza della curva governativa americana.<br><b>🔍 Come interpretarlo:</b> L\'inversione è il segnale d\'allerta; la disinversione verso l\'alto è il momento in cui storicamente si verificano le correzioni di mercato.</div>', unsafe_allow_html=True)

    col_m, col_n = st.columns(2)
    with col_m:
        if not vix.empty:
            fig11 = render_interactive_chart(vix, "Indice della Paura VIX: Volatilità Opzioni S&P 500", is_candlestick=use_candles, default_color="#f43f5e")
            st.plotly_chart(fig11, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il prezzo delle opzioni di protezione contro ribassi sull\'indice S&P 500.<br><b>🔍 Come interpretarlo:</b> Valori inferiori a 15 riflettono euforia; impennate repentine sopra 25-30 segnalano scarichi violenti.</div>', unsafe_allow_html=True)

    with col_n:
        if not ratio_gold_ndx.empty:
            fig12 = render_interactive_chart(ratio_gold_ndx, "Rapporto Oro / Nasdaq 100: Riserva di Valore vs Tech", is_candlestick=False, default_color="#eab308", is_ratio=True)
            st.plotly_chart(fig12, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> La forza relativa del bene rifugio fisico primario rispetto alla tecnologia americana.<br><b>🔍 Come interpretarlo:</b> Una salita costante evidenzia il rifugio degli investitori istituzionali verso beni non stampabili.</div>', unsafe_allow_html=True)

# ------------- TAB 4: BITCOIN MACRO -------------
with tab4:
    if not btc.empty:
        df_btc = btc.copy()
        
        # Medie Chiave (20 e 21 Settimane)
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
                    name="BTC Candele", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
                ))
            else:
                fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Close"], name="BTC Prezzo ($)", line=dict(color="#ffffff", width=1.8)))
                
            fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["SMA_20W"], name="20W SMA", line=dict(color="#10b981", width=1.5)))
            fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["EMA_21W"], name="21W EMA", line=dict(color="#06b6d4", width=1.5)))

            fig13.update_xaxes(
                rangeselector=dict(
                    buttons=[dict(count=6, label="6M", step="month", stepmode="backward"), dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig13.update_yaxes(type="log", title="Prezzo BTC (Scala Logaritmica)")
            fig13.update_layout(
                title=dict(text="<b>Bitcoin: Prezzo & Bull Market Support Band (20W SMA / 21W EMA)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=410, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig13, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Il posizionamento del prezzo rispetto alla fascia di supporto dinamica settimanale.<br><b>🔍 Come interpretarlo:</b> Prezzo sopra le due medie = mercato toro strutturale; prezzo sotto = fase correttiva prolungata.</div>', unsafe_allow_html=True)

        with c_btc2:
            fig14 = go.Figure()
            fig14.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Mayer_Multiple"], name="Mayer Multiple", line=dict(color="#facc15", width=1.6)))
            fig14.add_hline(y=2.4, line_dash="dash", line_color="#ef4444", annotation_text="Area Bolla / Top Storico (2.4x)", annotation_font_color="#ffffff")
            fig14.add_hline(y=1.0, line_dash="dot", line_color="#94a3b8")
            fig14.add_hline(y=0.8, line_dash="dash", line_color="#10b981", annotation_text="Area Minimo / Massimo Sconto (0.8x)", annotation_font_color="#ffffff")
            
            fig14.update_xaxes(
                rangeselector=dict(
                    buttons=[dict(count=1, label="1A", step="year", stepmode="backward"), dict(count=3, label="3A", step="year", stepmode="backward"), dict(step="all", label="TUTTO")],
                    bgcolor="#131d31", activecolor="#2563eb", font=dict(color="#ffffff"), y=1.14, x=0.99, xanchor="right"
                )
            )
            fig14.update_layout(
                title=dict(text="<b>Bitcoin: Oscillatore Mayer Multiple (Prezzo / 200 SMA)</b>", y=0.96, x=0.01, xanchor='left', font=dict(color="#ffffff", size=14)),
                template="plotly_dark", height=410, paper_bgcolor="#07090e", plot_bgcolor="#07090e", font=dict(color="#ffffff"), margin=dict(l=15, r=15, t=80, b=15)
            )
            st.plotly_chart(fig14, use_container_width=True)
            st.markdown('<div class="chart-guide"><b>📌 Cosa misura:</b> Multiplo tra il prezzo attuale di BTC e la sua media a 200 giorni.<br><b>🔍 Come interpretarlo:</b> Sotto 0.8x = aree di accumulo eccezionale; sopra 2.4x = picco di surriscaldamento speculativo in cui prendere profitto.</div>', unsafe_allow_html=True)
