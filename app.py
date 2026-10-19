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

# Stile CSS Obsidian Black & Card Istituzionali
st.markdown("""
<style>
    /* Sfondo generale e container scuro profondo */
    .stApp {
        background-color: #07090e;
        color: #e2e8f0;
    }
    
    /* Box Report AI Esecutivo */
    .executive-card {
        background: linear-gradient(145deg, #0f172a, #0b1120);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
    }
    
    .pillar-box {
        background-color: #131d31;
        border-radius: 8px;
        padding: 18px;
        border-top: 3px solid #38bdf8;
        height: 100%;
    }
    
    .strategy-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .strategy-table th {
        background-color: #1e293b;
        color: #94a3b8;
        padding: 10px;
        text-align: left;
        font-size: 13px;
    }
    .strategy-table td {
        padding: 12px 10px;
        border-bottom: 1px solid #1e293b;
        font-size: 13.5px;
    }
    
    /* Guide didattiche sotto i grafici */
    .guide-card {
        background-color: #0d1527;
        border-left: 4px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-top: -10px;
        margin-bottom: 25px;
        font-size: 13px;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Macro Risk & Liquidity Intelligence Terminal")
st.markdown("Piattaforma quantitativa per l'analisi dei cicli economici, della solidità del credito e del rischio sistemico sui mercati globali.")

# ==========================================
# GESTIONE DATI IN CACHE (FRED & YAHOO)
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

with st.spinner("Aggiornamento dati in tempo reale dai mercati internazionali..."):
    # Dati Federal Reserve (FRED)
    hy_spread = load_fred_data("BAMLH0A0HYM2")       # High Yield Spread
    ccc_spread = load_fred_data("BAMLH0A3HYC")       # CCC Spread
    unrate = load_fred_data("UNRATE")               # Disoccupazione
    sahm = load_fred_data("SAHMREALTIME")           # Sahm Rule
    t10y2y = load_fred_data("T10Y2Y")               # Curva 10Y-2Y
    
    # Dati Finanziari (Yahoo Finance)
    owl = load_yahoo_data("OWL")                    # Blue Owl (Private Credit)
    bizd = load_yahoo_data("BIZD")                  # BDC ETF
    nvda = load_yahoo_data("NVDA")                  # Nvidia
    mags = load_yahoo_data("MAGS")                  # Mega-Cap Tech ETF
    rsp = load_yahoo_data("RSP")                    # S&P Equal Weight
    sox = load_yahoo_data("^SOX")                   # Semiconduttori
    ndx = load_yahoo_data("^NDX")                   # Nasdaq 100
    skhynix = load_yahoo_data("000660.KS")          # SK Hynix
    gold = load_yahoo_data("GC=F")                  # Oro
    vix = load_yahoo_data("^VIX")                   # Indice Volatilità VIX
    btc = load_yahoo_data("BTC-USD", period="5y")   # Bitcoin

# Calcolo Ratios
ratio_ccc_hy = pd.DataFrame()
if not ccc_spread.empty and not hy_spread.empty:
    m_cred = pd.concat([ccc_spread, hy_spread], axis=1).dropna()
    ratio_ccc_hy = (m_cred["BAMLH0A3HYC"] / m_cred["BAMLH0A0HYM2"]).to_frame("Ratio_CCC_HY")

ratio_sox_ndx = pd.DataFrame()
if not sox.empty and not ndx.empty:
    m_tech = pd.concat([sox, ndx], axis=1).dropna()
    ratio_sox_ndx = (m_tech["^SOX"] / m_tech["^NDX"]).to_frame("Ratio_SOX_NDX")

ratio_gold_ndx = pd.DataFrame()
if not gold.empty and not ndx.empty:
    m_gold = pd.concat([gold, ndx], axis=1).dropna()
    ratio_gold_ndx = (m_gold["GC=F"] / m_gold["^NDX"]).to_frame("Ratio_Gold_NDX")

# Valori Attuali per il Calcolo
curr_sahm = float(sahm.iloc[-1].values[0]) if not sahm.empty else 0.0
curr_curve = float(t10y2y.iloc[-1].values[0]) if not t10y2y.empty else 0.0
curr_ratio_cred = float(ratio_ccc_hy.iloc[-1].values[0]) if not ratio_ccc_hy.empty else 3.0
curr_vix = float(vix.iloc[-1].values[0]) if not vix.empty else 15.0

# Calcolo Algoritmico Rischio Sistemico (0-100)
risk_score = 0
if curr_sahm >= 0.50: risk_score += 35
elif curr_sahm >= 0.35: risk_score += 20

if curr_curve > 0 and not t10y2y.empty and (t10y2y.tail(180).min().values[0] < -0.2):
    risk_score += 25  # Disinversione della curva
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
# METRICHE PRINCIPALI CON TOOLTIP EDUCATIVI
# ==========================================
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Indice di Rischio Sistemico",
    value=f"{risk_score} / 100",
    delta="Critico" if risk_score > 65 else ("Attenzione" if risk_score > 40 else "Stabile"),
    delta_color="inverse",
    help="COSA SIGNIFICA: Punteggio complessivo da 0 a 100 che aggrega 4 elementi chiave: tasso di disoccupazione, curva dei rendimenti, spread sui titoli spazzatura e volatilità VIX.\n\nCOME LEGGERLO:\n• Sotto 40: Mercato solido, bassa probabilità di crolli imminenti.\n• 40 - 65: Allerta, aumentano le divergenze tra debito e azioni.\n• Sopra 65: Rischio sistemico elevato, storicamente associato a forti correzioni o recessioni."
)

col2.metric(
    label="Regola di Sahm (Recessione USA)",
    value=f"{curr_sahm:.2f}",
    delta="Soglia Recessione: 0.50",
    delta_color="inverse" if curr_sahm >= 0.5 else "off",
    help="COSA SIGNIFICA: Indicatore storico della Federal Reserve che misura quanto velocemente sta salendo la disoccupazione rispetto ai minimi dell'ultimo anno.\n\nCOME LEGGERLO:\n• Sotto 0.35: Mercato del lavoro in piena salute.\n• Tra 0.35 e 0.49: Il mercato del lavoro sta rallentando.\n• Sopra 0.50: Ha anticipato senza mai fallire ogni singola recessione negli Stati Uniti dal 1950 a oggi."
)

col3.metric(
    label="Curva Rendimenti USA (10Y - 2Y)",
    value=f"{curr_curve:.2f}%",
    delta="Disinvertita" if curr_curve > 0 else "Invertita",
    help="COSA SIGNIFICA: Differenza tra il rendimento dei titoli di stato USA a 10 anni e quelli a 2 anni.\n\nCOME LEGGERLO:\n• Valore Negativo (Inversione): I mercati prevedono problemi economici a medio termine.\n• Ritorno a Valori Positivi (Disinversione): È il vero momento di allerta. Segnala che la banca centrale sta per tagliare i tassi in fretta perché l'economia sta rallentando."
)

col4.metric(
    label="Rapporto Debito CCC / High Yield",
    value=f"{curr_ratio_cred:.2f}x",
    delta="Stress Credito" if curr_ratio_cred > 3.5 else "Normale",
    delta_color="inverse",
    help="COSA SIGNIFICA: Confronta i rendimenti delle aziende con rating peggiore (titoli spazzatura CCC) con quelle High Yield ordinarie. È il vero campanello d'allarme del debito aziendale.\n\nCOME LEGGERLO:\n• Sotto 3.2x: Le aziende fragili riescono a rifinanziarsi facilmente.\n• Sopra 3.5x - 4.0x: Gli investitori rifiutano di prestare soldi alle imprese deboli. È qui che inizia la catena di default prima che si rifletta sui mercati azionari."
)

st.markdown(f"""
<div style="background-color:#0f172a; border-left: 5px solid {badge_col}; padding: 10px 16px; border-radius: 6px; margin: 15px 0 25px 0;">
    <span style="font-size:12px; text-transform:uppercase; color:#94a3b8; font-weight:bold;">Inquadramento di Mercato:</span><br>
    <span style="font-size:15px; font-weight:600; color:#f8fafc;">{fase_ciclo}</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. GRAFICO A CIPOLLA AD ANELLI CONCENTRICI
# ==========================================
st.markdown("### 🧅 Modello di Trasmissione del Rischio ad Anelli Concentrici")
st.markdown("""
Questo diagramma mappa la vulnerabilità del mercato come una serie di strati protettivi. 
La bolla e le perdite partono sempre dall'**anello esterno (rosso)**, dove risiede il debito più debole, 
mentre il **nucleo centrale (verde)** è composto da aziende ricche di liquidità che cedono solo per ultime.
""")

fig_onion = go.Figure()

onion_rings = [
    {
        "r": 4.0,
        "fill": "rgba(239, 68, 68, 0.20)",
        "line": "#ef4444",
        "title": "LIVELLO 4 (PERIFERIA): DEBITO SPAZZATURA & AZIENDE ZOMBIE",
        "desc": "Spread Titoli CCC • Rapporto Debito CCC/HY • Startup non profittevoli • Token speculativi",
        "status": "🔴 AREA DI PRIMO COLLASSO / ALTO TASSO DI VULNERABILITÀ",
        "y": 3.42
    },
    {
        "r": 3.0,
        "fill": "rgba(249, 115, 22, 0.28)",
        "line": "#f97316",
        "title": "LIVELLO 3: PRIVATE CREDIT & FINANZIAMENTO INFRASTRUTTURE",
        "desc": "Blue Owl (OWL) • BIZD (BDC) • Debito CoreWeave (USU2069EAB6) • Obbligazioni a 30-40 anni Big Tech",
        "status": "🟠 SOSTENIBILITÀ DEL DEBITO SOTTO PRESSIONE",
        "y": 2.42
    },
    {
        "r": 2.0,
        "fill": "rgba(163, 230, 53, 0.35)",
        "line": "#84cc16",
        "title": "LIVELLO 2: HARDWARE, SEMICONDUTTORI & FORNITORI CRITICI",
        "desc": "SK Hynix (Memorie HBM) • Indice Semiconduttori (^SOX) • Produttori di Chip Fisici",
        "status": "🟡 OTTIMI UTILI MA FORTEMENTE DIPENDENTI DAL CAPEX",
        "y": 1.45
    },
    {
        "r": 1.0,
        "fill": "rgba(16, 185, 129, 0.88)",
        "line": "#10b981",
        "title": "LIVELLO 1 (CENTRO): BIG TECH & MONOPOLI DI MERCATO",
        "desc": "Nvidia (NVDA) • Mega-Cap Tecnologiche (MAGS: Microsoft, Google, Meta, Apple)",
        "status": "🟢 BILANCI FORTIFICATI / CASSA RECORD / IMBATTUTI",
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
        text=f"<b>{ring['title']}</b><br><span style='font-size:11px; color:#cbd5e1;'>{ring['desc']}</span><br><b>[{ring['status']}]</b>",
        showarrow=False,
        font=dict(color="#f8fafc", size=11.5),
        align="center",
        bgcolor="rgba(10, 15, 29, 0.85)",
        bordercolor=ring["line"],
        borderwidth=1,
        borderpad=6
    )

fig_onion.update_xaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_yaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_layout(
    height=670,
    margin=dict(l=5, r=5, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_onion, use_container_width=True)

# ==========================================
# 2. RAPPORTO ESECUTIVO DI ANALISI (FORMATO PROFESSIONALE)
# ==========================================
st.markdown("### 📑 Bollettino Esecutivo di Analisi Macroeconomica")

st.markdown(f"""
<div class="executive-card">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:14px; margin-bottom:20px;">
        <div>
            <h3 style="margin:0; color:#38bdf8; font-size:18px;">Rapporto Sintetico di Posizionamento sui Mercati</h3>
            <p style="margin:4px 0 0 0; font-size:13px; color:#94a3b8;">Sintesi dei dati calcolata automaticamente dai modelli di bilancio e credito.</p>
        </div>
        <span style="background-color:#1e293b; color:#cbd5e1; padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600;">
            Data di Riferimento: {datetime.now().strftime('%d %B %Y')}
        </span>
    </div>

    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
        <div class="pillar-box" style="border-top-color: #ef4444;">
            <h4 style="color:#f87171; margin-top:0; font-size:15px;">1. Canale del Debito & Private Credit</h4>
            <p style="font-size:13px; line-height:1.6; color:#cbd5e1;">
                Il ratio <b>CCC / High Yield si attesta a {curr_ratio_cred:.2f}x</b>. I fallimenti aziendali non iniziano mai dalle grandi aziende con miliardi in banca, 
                ma dal mercato dei prestiti privati e dalle aziende con bassi rating. 
                Se le aziende BDC (BIZD) e i gestori come Blue Owl incontrano difficoltà nei prestiti erogati per i data center e per contratti GPU, 
                il costo di rifinanziamento salirà repentinamente per l'intera catena industriale.
            </p>
        </div>

        <div class="pillar-box" style="border-top-color: #eab308;">
            <h4 style="color:#facc15; margin-top:0; font-size:15px;">2. Ampiezza di Mercato & Settore Tech</h4>
            <p style="font-size:13px; line-height:1.6; color:#cbd5e1;">
                Confrontando l'indice S&P 500 equiponderato (RSP) con le Mega-Cap, si osserva la concentrazione delle performance. 
                Quando i massimi dell'indice generale sono sostenuti da una manciata di titoli tech mentre la maggior parte delle aziende resta ferma, 
                la struttura di mercato diventa fragile. L'hardware (SOX/NDX) guida ancora il ciclo, ma il rendimento effettivo sugli investimenti resta il fattore determinante.
            </p>
        </div>

        <div class="pillar-box" style="border-top-color: #10b981;">
            <h4 style="color:#34d399; margin-top:0; font-size:15px;">3. Oro, Bitcoin & Liquidità</h4>
            <p style="font-size:13px; line-height:1.6; color:#cbd5e1;">
                La forza dell'Oro rispetto agli indici tecnologici riflette la domanda istituzionale di protezione contro la svalutazione monetaria. 
                Nel comparto criptovalute, Bitcoin si trova all'interno del proprio canale quantitativo storico di medio termine: 
                la tenuta della media settimanale a medio periodo rappresenta il discrimine tra mercato rialzista strutturale e fase di debolezza macro.
            </p>
        </div>
    </div>

    <div style="margin-top:24px;">
        <h4 style="color:#f8fafc; font-size:14px; margin-bottom:8px;">Quadro Operativo di Allocazione Strategica</h4>
        <table class="strategy-table">
            <thead>
                <tr>
                    <th>Classe di Attivo</th>
                    <th>Stato del Ciclo</th>
                    <th>Comportamento Consigliato</th>
                    <th>Fattore Chiave da Monitorare</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Titoli Tecnologici Mega-Cap</b></td>
                    <td><span style="color:#34d399; font-weight:600;">Stabili / Rifugio</span></td>
                    <td>Mantenere con posizioni selezionate, proteggere i guadagni senza esporsi eccessivamente alla leva.</td>
                    <td>Crescita degli investimenti in conto capitale (Capex) rispetto ai ricavi generati.</td>
                </tr>
                <tr>
                    <td><b>Small-Cap & Titoli Altamente Indebitati</b></td>
                    <td><span style="color:#f87171; font-weight:600;">Alto Rischio</span></td>
                    <td>Evitare o ridurre l'esposizione verso aziende prive di flussi di cassa operativi positivi.</td>
                    <td>Allargamento degli spread creditizi e difficoltà di rinnovo delle scadenze di debito.</td>
                </tr>
                <tr>
                    <td><b>Metalli Preziosi (Oro / Beni Rifugio)</b></td>
                    <td><span style="color:#38bdf8; font-weight:600;">Accumulazione Difensiva</span></td>
                    <td>Mantenere una quota strategica a portafoglio per assorbire eventuali shock da liquidità o geopolitici.</td>
                    <td>Rendimento reale dei titoli governativi e andamento del dollaro.</td>
                </tr>
                <tr>
                    <td><b>Bitcoin & Criptovalute</b></td>
                    <td><span style="color:#facc15; font-weight:600;">Sensibilità alla Liquidità</span></td>
                    <td>Accumulazione graduale nei pressi della fascia bassa della regressione; prudenza sulle altcoin a bassa liquidità.</td>
                    <td>Dinamica di bilancio della banca centrale e flussi istituzionali su ETF.</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 3. GRAFICI ORGANIZZATI CON GUIDE DIDATTICHE SINGOLE
# ==========================================
st.markdown("### 📊 Analisi Dettagliata dei Grafici")

tab1, tab2, tab3, tab4 = st.tabs([
    "💳 Mercato Obbligazionario & Credito",
    "💻 Settore Tecnologico & AI Capex",
    "🌍 Indicatori Macro USA & Beni Rifugio",
    "₿ Bitcoin & Modello di Canale Storico"
])

# ------------- TAB 1: CREDITO -------------
with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        if not ccc_spread.empty and not hy_spread.empty:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=hy_spread.index, y=hy_spread["BAMLH0A0HYM2"], name="Spread High Yield", line=dict(color="#38bdf8")))
            fig1.add_trace(go.Scatter(x=ccc_spread.index, y=ccc_spread["BAMLH0A3HYC"], name="Spread Titoli CCC (Rischio Alto)", line=dict(color="#ef4444")))
            fig1.update_layout(title="Spread Obbligazioni USA: High Yield vs Spazzatura CCC", template="plotly_dark", height=380)
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> Il tasso di interesse extra che le aziende a rischio devono pagare rispetto ai titoli di stato USA sicuri.<br>
                <b>🔍 Come interpretarlo:</b> Quando le due linee salgono rapidamente, il mercato rifiuta di prestare denaro alle aziende deboli. Storicamente anticipa i crolli azionari di diversi mesi.
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        if not ratio_ccc_hy.empty:
            fig2 = px.line(ratio_ccc_hy, title="Rapporto di Stress tra Debito CCC e Debito High Yield", template="plotly_dark", height=380)
            fig2.update_traces(line_color="#dc2626")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> La pressione specifica scaricata sull'anello più fragile del debito aziendale.<br>
                <b>🔍 Come interpretarlo:</b> Se questo rapporto supera 3.5x - 4.0x, significa che le aziende più vulnerabili stanno entrando in crisi prima ancora che l'azionario se ne accorga.
            </div>
            """, unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        if not bizd.empty:
            fig3 = px.line(bizd, title="ETF BIZD: Barometro del Private Credit e Prestiti Aziendali", template="plotly_dark", height=380)
            fig3.update_traces(line_color="#f59e0b")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> Il valore delle società di sviluppo aziendale (BDC) che concedono prestiti diretti alle medie imprese non quotate.<br>
                <b>🔍 Come interpretarlo:</b> Un trend discendente prolungato indica difficoltà nei rimborsi dei prestiti privati e contrazione del credito non bancario.
            </div>
            """, unsafe_allow_html=True)

    with col_d:
        if not owl.empty:
            fig4 = px.line(owl, title="Blue Owl Capital (OWL): Finanziatore di Data Center & Infrastruttura", template="plotly_dark", height=380)
            fig4.update_traces(line_color="#a855f7")
            st.plotly_chart(fig4, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> L'andamento di uno dei massimi gestori alternativi di credito privato, ampiamente esposto sui contratti di leasing per data center e cluster di server.<br>
                <b>🔍 Come interpretarlo:</b> La sua solidità dimostra se i flussi di capitale continuano ad affluire verso le infrastrutture tecnologiche.
            </div>
            """, unsafe_allow_html=True)

# ------------- TAB 2: TECH & AI -------------
with tab2:
    col_e, col_f = st.columns(2)
    with col_e:
        if not nvda.empty:
            fig5 = px.line(nvda, title="Nvidia (NVDA): Il Nucleo Portante del Ciclo Tecnologico", template="plotly_dark", height=380)
            fig5.update_traces(line_color="#10b981")
            st.plotly_chart(fig5, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> L'azienda cardine su cui si concentrano gli investimenti mondiali per i chip di calcolo accelerato.<br>
                <b>🔍 Come interpretarlo:</b> Finché Nvidia mantiene minimi crescenti, l'intero comparto tecnologico beneficia dell'effetto traino.
            </div>
            """, unsafe_allow_html=True)

    with col_f:
        if not skhynix.empty:
            fig6 = px.line(skhynix, title="SK Hynix (000660.KS): Fornitore Monopolista di Memorie HBM", template="plotly_dark", height=380)
            fig6.update_traces(line_color="#84cc16")
            st.plotly_chart(fig6, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> Il produttore primario dei moduli di memoria ad alta velocità necessari per il funzionamento delle GPU avanzate.<br>
                <b>🔍 Come interpretarlo:</b> Misura la domanda fisica reale della filiera produttiva. Un rallentamento qui anticipa una flessione negli ordini dei chipmaker.
            </div>
            """, unsafe_allow_html=True)

    col_g, col_h = st.columns(2)
    with col_g:
        if not ratio_sox_ndx.empty:
            fig7 = px.line(ratio_sox_ndx, title="Rapporto Semiconduttori / Nasdaq 100 (^SOX / ^NDX)", template="plotly_dark", height=380)
            fig7.update_traces(line_color="#38bdf8")
            st.plotly_chart(fig7, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> La forza relativa dei produttori di chip rispetto a tutte le altre aziende tecnologiche e del software.<br>
                <b>🔍 Come interpretarlo:</b> Quando sale, l'hardware sovraperforma il resto del mercato. Picchi estremi segnalano fasi di euforia speculativa sui produttori fisici.
            </div>
            """, unsafe_allow_html=True)

    with col_h:
        if not rsp.empty and not mags.empty:
            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=rsp.index, y=rsp["RSP"] / rsp["RSP"].iloc[0] * 100, name="S&P 500 Equal Weight (RSP)", line=dict(color="#94a3b8")))
            fig8.add_trace(go.Scatter(x=mags.index, y=mags["MAGS"] / mags["MAGS"].iloc[0] * 100, name="Mega-Cap Mag 7 (MAGS)", line=dict(color="#f43f5e")))
            fig8.update_layout(title="Ampiezza di Mercato: Titoli Ordinari (RSP) vs Giganti Tech (MAGS)", template="plotly_dark", height=380)
            st.plotly_chart(fig8, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> Confronta l'andamento delle 500 aziende americane equiponderate contro i 7 colossi tecnologici a maggior capitalizzazione.<br>
                <b>🔍 Come interpretarlo:</b> Se la linea rossa sale molto più della linea grigia, significa che il mercato è tenuto su da pochissime azioni. È una divergenza tipica dei massimi di fine ciclo.
            </div>
            """, unsafe_allow_html=True)

# ------------- TAB 3: MACRO & BENI RIFUGIO -------------
with tab3:
    col_i, col_l = st.columns(2)
    with col_i:
        if not unrate.empty and not sahm.empty:
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Tasso Disoccupazione (%)", line=dict(color="#94a3b8")))
            fig9.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Regola di Sahm", line=dict(color="#ef4444", width=2)))
            fig9.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Soglia Allarme (0.50)")
            fig9.update_layout(title="Dinamica della Disoccupazione USA & Trigger Recessionario", template="plotly_dark", height=380)
            st.plotly_chart(fig9, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> La salute del mercato del lavoro statunitense e la rapidità dei licenziamenti aggregati.<br>
                <b>🔍 Come interpretarlo:</b> Quando la linea rossa supera quota 0.50, scatta il segnale oggettivo di recessione economica con conseguente impatto sugli utili aziendali.
            </div>
            """, unsafe_allow_html=True)

    with col_l:
        if not t10y2y.empty:
            fig10 = px.line(t10y2y, title="Differenziale dei Tassi USA a 10 Anni vs 2 Anni", template="plotly_dark", height=380)
            fig10.add_hline(y=0.0, line_dash="dash", line_color="white")
            fig10.update_traces(line_color="#06b6d4")
            st.plotly_chart(fig10, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> La pendenza della curva governativa dei tassi USA.<br>
                <b>🔍 Come interpretarlo:</b> L'inversione sottozero preavvisa il rallentamento; la disinversione che riporta il valore sopra lo zero coincide storicamente con l'inizio della fase di correzione sui listini azionari.
            </div>
            """, unsafe_allow_html=True)

    col_m, col_n = st.columns(2)
    with col_m:
        if not vix.empty:
            fig11 = px.line(vix, title="Indice della Paura VIX: Volatilità delle Opzioni S&P 500", template="plotly_dark", height=380)
            fig11.add_hline(y=20, line_dash="dot", line_color="orange")
            fig11.add_hline(y=30, line_dash="dash", line_color="red")
            fig11.update_traces(line_color="#f43f5e")
            st.plotly_chart(fig11, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> Il costo per assicurarsi contro improvvisi crolli sul mercato azionario americano a 30 giorni.<br>
                <b>🔍 Come interpretarlo:</b> Sotto 15 regna la calma e la compiacenza; tra 20 e 30 aumentano le vendite; sopra 30 si è nel mezzo di uno scarico da panico.
            </div>
            """, unsafe_allow_html=True)

    with col_n:
        if not ratio_gold_ndx.empty:
            fig12 = px.line(ratio_gold_ndx, title="Rapporto Oro / Nasdaq 100: Riserva di Valore vs Crescita Tech", template="plotly_dark", height=380)
            fig12.update_traces(line_color="#eab308")
            st.plotly_chart(fig12, use_container_width=True)
            st.markdown("""
            <div class="guide-card">
                <b>📌 Cosa misura:</b> La preferenza degli investitori globali tra beni fisici non svalutabili (Oro) e azioni speculative di crescita (Tech).<br>
                <b>🔍 Come interpretarlo:</b> Quando questo rapporto si alza, i grandi capitali stanno fuggendo verso la sicurezza per proteggersi da incertezza o svalutazione monetaria.
            </div>
            """, unsafe_allow_html=True)

# ------------- TAB 4: BITCOIN -------------
with tab4:
    if not btc.empty:
        df_btc = btc.copy()
        
        # Medie Mobili Chiave a Medio Termine (20 e 21 Settimane)
        df_btc["SMA_20W"] = df_btc["BTC-USD"].rolling(window=140).mean()
        df_btc["EMA_21W"] = df_btc["BTC-USD"].ewm(span=147, adjust=False).mean()
        
        # Regressione Logaritmica
        x_d = np.arange(1, len(df_btc) + 1)
        log_x = np.log(x_d)
        log_y = np.log(df_btc["BTC-USD"].values)
        poly = np.polyfit(log_x, log_y, 1)
        fit_l = poly[0] * log_x + poly[1]
        
        df_btc["Canale_Centrale"] = np.exp(fit_l)
        std_d = np.std(log_y - fit_l)
        df_btc["Canale_Superiore"] = np.exp(fit_l + 1.25 * std_d)
        df_btc["Canale_Inferiore"] = np.exp(fit_l - 1.25 * std_d)

        fig13 = go.Figure()
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["BTC-USD"], name="Prezzo Bitcoin ($)", line=dict(color="#f8fafc", width=1.5)))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["SMA_20W"], name="Media Mobile 20 Settimane", line=dict(color="#10b981", width=1.3)))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["EMA_21W"], name="Media Esponenziale 21 Settimane", line=dict(color="#06b6d4", width=1.3)))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Canale_Superiore"], name="Banda Alta (Fase Euforica)", line=dict(color="#ef4444", dash="dash")))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Canale_Centrale"], name="Valore Equo Storico", line=dict(color="#eab308", dash="dot")))
        fig13.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Canale_Inferiore"], name="Banda Bassa (Accumulazione)", line=dict(color="#22c55e", dash="dash")))

        fig13.update_yaxes(type="log", title="Prezzo BTC (Scala Logaritmica)")
        fig13.update_layout(
            title="Bitcoin: Canale Quantitativo di Regressione Logaritmica & Fasce di Supporto Settimanale",
            template="plotly_dark",
            height=580
        )
        st.plotly_chart(fig13, use_container_width=True)
        st.markdown("""
        <div class="guide-card">
            <b>📌 Cosa misura:</b> L'andamento di Bitcoin all'interno del suo canale storico di lungo periodo, depurato dall'iper-volatilità iniziale.<br>
            <b>🔍 Come interpretarlo:</b><br>
            • <b>Fascia tra le due medie verdi/azzurre (20W SMA & 21W EMA):</b> Se il prezzo è sopra, il trend rialzista è intatto. Se il prezzo rompe al ribasso queste medie, inizia una fase di debolezza ciclica prolungata.<br>
            • <b>Banda Verde Inferiore:</b> Area storica di massimo sconto e accumulo di lungo termine.<br>
            • <b>Banda Rossa Superiore:</b> Area di euforia speculativa e massimi ciclici, dove è opportuno prendere profitto.
        </div>
        """, unsafe_allow_html=True)
