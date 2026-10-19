import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# CONFIGURAZIONE PAGINA
# ==========================================
st.set_page_config(
    page_title="Macro Risk Terminal | Macro, Credit & AI Bubble Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS per lo stile "Terminale Finanziario"
st.markdown("""
<style>
    .report-box {
        background-color: #0e1726;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .metric-card {
        background-color: #111827;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Macro & Systemic Risk Intelligence Terminal")
st.caption("Framework di Analisi Ciclica: Liquidità Netta, Canale del Credito, AI Capex & Modelli Quantitativi")

# ==========================================
# FUNZIONI DOWNLOAD DATI (FRED & YAHOO)
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

with st.spinner("Acquisizione feed macroeconomici, obbligazionari e azionari in corso..."):
    # FRED Macro & Credit
    hy_spread = load_fred_data("BAMLH0A0HYM2")       # 1. High Yield Spread
    ccc_spread = load_fred_data("BAMLH0A3HYC")       # 2. CCC Spread
    unrate = load_fred_data("UNRATE")               # Disoccupazione USA
    sahm = load_fred_data("SAHMREALTIME")           # Sahm Rule
    t10y2y = load_fred_data("T10Y2Y")               # Curva 10Y-2Y
    
    # Yahoo Finance: Equity, Hardware AI, Private Credit
    owl = load_yahoo_data("OWL")                    # Blue Owl (Private Credit / AI data center)
    bizd = load_yahoo_data("BIZD")                  # BDC ETF (Private debt canary)
    nvda = load_yahoo_data("NVDA")                  # Nvidia
    mags = load_yahoo_data("MAGS")                  # Mag 7 ETF
    rsp = load_yahoo_data("RSP")                    # S&P Equal Weight
    sox = load_yahoo_data("^SOX")                   # Philly Semiconductor
    ndx = load_yahoo_data("^NDX")                   # Nasdaq 100
    skhynix = load_yahoo_data("000660.KS")          # SK Hynix (HBM Memory Bottleneck)
    gold = load_yahoo_data("GC=F")                  # Oro Futures
    vix = load_yahoo_data("^VIX")                   # VIX
    btc = load_yahoo_data("BTC-USD", period="5y")   # Bitcoin per modello Cowen

# Calcoli Spread e Ratios
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

# ==========================================
# CALCOLATORE RISCHIO SISTEMICO & CICLO MACRO
# ==========================================
curr_sahm = float(sahm.iloc[-1].values[0]) if not sahm.empty else 0.0
curr_curve = float(t10y2y.iloc[-1].values[0]) if not t10y2y.empty else 0.0
curr_ccc = float(ccc_spread.iloc[-1].values[0]) if not ccc_spread.empty else 0.0
curr_ratio_cred = float(ratio_ccc_hy.iloc[-1].values[0]) if not ratio_ccc_hy.empty else 3.0
curr_vix = float(vix.iloc[-1].values[0]) if not vix.empty else 15.0

# Algoritmo di punteggio di Rischio Sistemico (0 - 100)
risk_score = 0
if curr_sahm >= 0.50: risk_score += 35
elif curr_sahm >= 0.35: risk_score += 20

if curr_curve > 0 and not t10y2y.empty and (t10y2y.tail(180).min().values[0] < -0.2):
    risk_score += 25  # Disinversione post-inversione profonda (pericolosissima)
elif curr_curve < 0:
    risk_score += 15  # Curva ancora invertita

if curr_ratio_cred > 3.8: risk_score += 25
elif curr_ratio_cred > 3.2: risk_score += 15

if curr_vix > 25: risk_score += 15
elif curr_vix > 20: risk_score += 8

risk_score = min(risk_score, 100)

# Diagnosi Fase di Ciclo Macro
if curr_sahm >= 0.50:
    fase_ciclo = "FASE 4: RECESSIONE SISTEMICA / SHOCK LAVORO (Risk-Off Totale)"
    fase_badge = "🔴 CONTRAZIONE REALE"
elif curr_curve > 0 and risk_score >= 50:
    fase_ciclo = "FASE 3: LATE CYCLE AVANZATO - Disinversione della Curva & Stress da Debito"
    fase_badge = "⚠️ LATE CYCLE / ROTAZIONE DIFENSIVA"
elif not ratio_sox_ndx.empty and ratio_sox_ndx.iloc[-1].values[0] > ratio_sox_ndx.tail(252).quantile(0.85).values[0]:
    fase_ciclo = "FASE 2: ESPANSIONE SPECULATIVA GUIDATA DALL'AI (Capex Overdrive)"
    fase_badge = "🟡 ESPANSIONE CONCENTRATA"
else:
    fase_ciclo = "FASE 1: RIPRESA / ACCUMULAZIONE EQUILIBRATA"
    fase_badge = "🟢 ACCUMULAZIONE"

# Visualizzazione Header Metriche
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Indice Rischio Sistemico", f"{risk_score} / 100", delta="Allerta Alta" if risk_score > 60 else "Normale", delta_color="inverse")
col_m2.metric("Regola di Sahm (Recessione)", f"{curr_sahm:.2f}", delta="Trigger a 0.50", delta_color="inverse" if curr_sahm >= 0.5 else "off")
col_m3.metric("Curva 10Y - 2Y", f"{curr_curve:.2f}%", delta="Disinvertita" if curr_curve > 0 else "Invertita")
col_m4.metric("Ratio CCC / HY", f"{curr_ratio_cred:.2f}x", delta="Stress Creditizio" if curr_ratio_cred > 3.5 else "Stabile", delta_color="inverse")

st.info(f"**Diagnosi Macro Quantitativa Corrente:** {fase_badge} — *{fase_ciclo}*")

# ==========================================
# 1. IL GRAFICO A CIPOLLA AD ANELLI CONCENTRICI (STILE VITO LOPS)
# ==========================================
st.subheader("🧅 Il Modello a Cipolla del Rischio AI: Struttura ad Anelli Concentrici")
st.caption("Rappresentazione ad anelli non a fette (stile Vito Lops): dal nucleo solido con cassa (Verde) verso l'esterno dove il debito spazzatura e i rifinanziamenti collassano per primi (Rosso).")

fig_onion = go.Figure()

# Definizione raggi anelli concentrici
# Anello 4 (Esterno): R=4 | Anello 3: R=3 | Anello 2: R=2 | Nucleo: R=1
rings = [
    {
        "r": 4.0,
        "fill": "rgba(239, 68, 68, 0.22)",
        "line": "#ef4444",
        "title": "LIVELLO 4 (PERIFERIA): CREDITO SPAZZATURA & STARTUP ZOMBIE",
        "desc": "Spread CCC (BAMLH0A3HYC) • Ratio CCC/HY • Startup AI prive di flussi di cassa • Altcoin speculative",
        "status": "🔴 BOLLA IN CONTRAZIONE / STRESS ELEVATO",
        "y_pos": 3.4
    },
    {
        "r": 3.0,
        "fill": "rgba(249, 115, 22, 0.30)",
        "line": "#f97316",
        "title": "LIVELLO 3: PRIVATE CREDIT & DEBITO INFRASTRUTTURALE DATA CENTER",
        "desc": "Blue Owl (OWL) • BIZD (BDC) • Debito CoreWeave (USU2069EAB6) • Bond lunghi Oracle (2065) & Tech",
        "status": "🟠 FRAGILITÀ FINANZIARIA / SOSTENIBILITÀ CAPEX",
        "y_pos": 2.4
    },
    {
        "r": 2.0,
        "fill": "rgba(163, 230, 53, 0.38)",
        "line": "#84cc16",
        "title": "LIVELLO 2: HARDWARE, SEMICONDUTTORI & CATENA DI FORNITURA",
        "desc": "SK Hynix (000660.KS - Memorie HBM) • Indice Semiconduttori (^SOX) • TSMC • ASML",
        "status": "🟡 CICLICO / MARGINI ELEVATI MA VULNERABILI A RALLENTAMENTI",
        "y_pos": 1.45
    },
    {
        "r": 1.0,
        "fill": "rgba(16, 185, 129, 0.88)",
        "line": "#10b981",
        "title": "LIVELLO 1 (NUCLEO): BIG TECH & MEGA-CAPS (LA FORTEZZA)",
        "desc": "Nvidia (NVDA) • Microsoft • Meta • Alphabet • Apple • Mag 7 (MAGS)",
        "status": "🟢 BILANCI FORTIFICATI / CASSA ENORME / MONOPOLI INTATTI",
        "y_pos": 0.0
    }
]

# Disegno anelli concentrici
for ring in rings:
    r = ring["r"]
    fig_onion.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-r, y0=-r, x1=r, y1=r,
        fillcolor=ring["fill"],
        line=dict(color=ring["line"], width=3, dash="solid" if r == 1.0 else "dot")
    )
    # Annotazione testuale descrittiva posizionata nell'anello
    fig_onion.add_annotation(
        x=0, y=ring["y_pos"],
        text=f"<b>{ring['title']}</b><br><span style='font-size:11px;'>{ring['desc']}</span><br><b>[{ring['status']}]</b>",
        showarrow=False,
        font=dict(color="#f8fafc", size=12),
        align="center",
        bgcolor="rgba(15, 23, 42, 0.7)",
        bordercolor=ring["line"],
        borderwidth=1,
        borderpad=5
    )

fig_onion.update_xaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_yaxes(range=[-4.3, 4.3], showgrid=False, zeroline=False, showticklabels=False)
fig_onion.update_layout(
    height=680,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_onion, use_container_width=True)

# ==========================================
# 2. LOCANDINA ASSISTENTE AI: SINTESI ANALITICA INTELLIGENTE
# ==========================================
st.markdown("### 📋 Bollettino di Intelligence Macroeconomica & Sintesi Operativa")

report_html = f"""
<div class="report-box">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:16px;">
        <h4 style="margin:0; color:#38bdf8;">🧠 Macro AI Copilot Report — Metodologia Lops, Bottaioli, Cowen, Pizzino</h4>
        <span style="background-color:#1e293b; color:#94a3b8; padding:4px 10px; border-radius:6px; font-size:12px;">Data Feed: {datetime.now().strftime('%d/%m/%Y')}</span>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
            <h5 style="color:#ef4444;">1. Il Canale del Debito & Private Credit (La Canarina nella Miniera)</h5>
            <p style="font-size:13.5px; line-height:1.6; color:#cbd5e1;">
                Il ratio <b>CCC / HY ({curr_ratio_cred:.2f}x)</b> indica se il mercato obbligazionario sta prezzando default selettivi. 
                Come insegna Vito Lops, la bolla non scoppia dalle Big Tech (che posseggono miliardi di liquidità), ma dal <b>rifinanziamento dell'infrastruttura a debito</b>: 
                Blue Owl (OWL) e BIZD rappresentano il termometro del <i>private credit</i> che sostiene i contratti GPU di CoreWeave e i data center ipotecati. 
                Se BIZD continua a comprimere i margini e i rendimenti dei bond ultra-trentennali (Oracle 2065, Alphabet 2060) chiedono un premio maggiore, 
                il costo di rifinanziamento per il capex AI diventerà insostenibile.
            </p>
            
            <h5 style="color:#eab308;">2. Ampiezza di Mercato: S&P Equal Weight (RSP) vs Mega-Caps</h5>
            <p style="font-size:13.5px; line-height:1.6; color:#cbd5e1;">
                Nello stile di Jason Pizzino e Stefano Bottaioli, la divergenza primaria è visibile confrontando <b>RSP (Equal Weight)</b> con le Mag 7. 
                Quando solo Nvidia e 4-5 colossi registrano nuovi massimi mentre l'indice equiponderato lateralizza, siamo in una <b>distribuzione di Wyckoff tardiva</b>.
                La bolla dell'hardware (SOX/NDX) evidenzia che la domanda di chip sta correndo molto più velocemente dei ritorni economici del software applicativo.
            </p>
        </div>
        
        <div>
            <h5 style="color:#10b981;">3. Ciclo di Liquidità & Prospettiva Crypto (Benjamin Cowen)</h5>
            <p style="font-size:13.5px; line-height:1.6; color:#cbd5e1;">
                Bitcoin e il Nasdaq sono entrambi ostaggio della <b>politica di bilancio della Fed e della liquidità netta</b>. 
                Il canale di regressione logaritmica evidenzia come Bitcoin stia maturando rendimenti decrescenti tipici di asset istituzionali. 
                La tenuta della <i>Bull Market Support Band</i> (20W SMA & 21W EMA) funge da discriminante oggettiva tra espansione e capitolazione ciclica, 
                mentre il rapporto <b>Oro / Nasdaq</b> evidenzia l'inizio di una rotazione verso hard asset come protezione dalla svalutazione debitoria.
            </p>
            
            <h5 style="color:#38bdf8;">4. Conclusione & Asimmetria Operativa (Dove Allocare)</h5>
            <ul style="font-size:13.5px; line-height:1.6; color:#cbd5e1; margin-left:-15px;">
                <li><b>Rischio Asimmetrico Negativo:</b> Evitare le small-cap a leva con rating CCC, tech non profittevole e altcoin speculative prive di trazione on-chain reale.</li>
                <li><b>Resilienza:</b> Le Big Tech con cassa fungono da rifugio temporaneo, ma non sono immuni se il debito periferico congela il capex.</li>
                <li><b>Hedge Strategico:</b> Oro e liquidità a breve termine (T-Bills) garantiscono optionalità liquida per entrare al picco della disinversione recessionaria.</li>
            </ul>
        </div>
    </div>
</div>
"""
st.markdown(report_html, unsafe_allow_html=True)

# ==========================================
# 3. TUTTI I GRAFICI DETTAGLIATI (CATEGORIZZATI)
# ==========================================
st.markdown("---")
st.subheader("📊 Moduli di Analisi Grafica Interattiva")

tab_cred, tab_ai, tab_macro, tab_btc = st.tabs([
    "💳 1. Mercato del Credito & Junk Debt",
    "💻 2. Hardware AI, Mag 7 & Ampiezza",
    "🌍 3. Macro USA, Curva & Oro",
    "₿ 4. Bitcoin & Canale Cowen"
])

# ----------------- TAB 1: CREDITO -----------------
with tab_cred:
    c1, c2 = st.columns(2)
    with c1:
        if not ccc_spread.empty and not hy_spread.empty:
            fig_cr = go.Figure()
            fig_cr.add_trace(go.Scatter(x=hy_spread.index, y=hy_spread["BAMLH0A0HYM2"], name="HY USA Spread (OAS)"))
            fig_cr.add_trace(go.Scatter(x=ccc_spread.index, y=ccc_spread["BAMLH0A3HYC"], name="CCC & Lower Spread", line=dict(color="#ef4444")))
            fig_cr.update_layout(title="FRED: Spread Credito High Yield vs CCC & Lower", template="plotly_dark")
            st.plotly_chart(fig_cr, use_container_width=True)
            
    with c2:
        if not ratio_ccc_hy.empty:
            fig_r = px.line(ratio_ccc_hy, title="Ratio di Stress Acuto: Spread CCC / High Yield (FRED)", template="plotly_dark")
            fig_r.update_traces(line_color="#dc2626")
            st.plotly_chart(fig_r, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        if not bizd.empty:
            fig_b = px.line(bizd, title="AMEX: BIZD (VanEck BDC - Proxy Private Credit & Leveraged Loans)", template="plotly_dark")
            st.plotly_chart(fig_b, use_container_width=True)
    with c4:
        if not owl.empty:
            fig_o = px.line(owl, title="NYSE: OWL (Blue Owl Capital - Asset Manager Private Debt AI)", template="plotly_dark")
            fig_o.update_traces(line_color="#f97316")
            st.plotly_chart(fig_o, use_container_width=True)

    st.markdown("""
    > **Note Monitoraggio Obbligazionario Big Tech & AI Debt (FINRA / OTC):**
    > - **Oracle Corp Bonds:** FINRA `orcl6185589` (Scadenza 2035) e `orcl6186140` (Scadenza 2065 - Debito a lunghissimo termine per capex cloud).
    > - **CoreWeave Debt:** FWB `USU2069EAB6` (Senior Secured Notes per finanziamento cluster GPU).
    > - **Big Tech Duration 2035 & 2060/65:** Alphabet `US02079KAE83` (2060), Amazon `AMZN5087114` (2061), Meta `META5388048` (2063).
    """)

# ----------------- TAB 2: HARDWARE & AI -----------------
with tab_ai:
    c1, c2 = st.columns(2)
    with c1:
        if not nvda.empty:
            fig_n = px.line(nvda, title="NASDAQ: NVDA (Nvidia - Il Cuore Intatto della Cipolla)", template="plotly_dark")
            fig_n.update_traces(line_color="#10b981")
            st.plotly_chart(fig_n, use_container_width=True)
    with c2:
        if not skhynix.empty:
            fig_sk = px.line(skhynix, title="KRX: 000660.KS (SK Hynix - Monopolio Memorie HBM per GPU)", template="plotly_dark")
            fig_sk.update_traces(line_color="#84cc16")
            st.plotly_chart(fig_sk, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        if not ratio_sox_ndx.empty:
            fig_sx = px.line(ratio_sox_ndx, title="Ratio: Semiconduttori vs Nasdaq 100 (^SOX / ^NDX)", template="plotly_dark")
            fig_sx.update_traces(line_color="#f59e0b")
            st.plotly_chart(fig_sx, use_container_width=True)
    with c4:
        if not rsp.empty and not mags.empty:
            fig_amp = go.Figure()
            fig_amp.add_trace(go.Scatter(x=rsp.index, y=rsp["RSP"] / rsp["RSP"].iloc[0] * 100, name="RSP (Equal Weight)"))
            fig_amp.add_trace(go.Scatter(x=mags.index, y=mags["MAGS"] / mags["MAGS"].iloc[0] * 100, name="MAGS (Mag 7 ETF)", line=dict(color="#38bdf8")))
            fig_amp.update_layout(title="Ampiezza di Mercato: RSP (Equal Weight) vs MAGS (Mag 7 ETF) Normalizzati", template="plotly_dark")
            st.plotly_chart(fig_amp, use_container_width=True)

# ----------------- TAB 3: MACRO & ORO -----------------
with tab_macro:
    c1, c2 = st.columns(2)
    with c1:
        if not unrate.empty and not sahm.empty:
            fig_m = go.Figure()
            fig_m.add_trace(go.Scatter(x=unrate.index, y=unrate["UNRATE"], name="Tasso Disoccupazione (%)", line=dict(color="#94a3b8")))
            fig_m.add_trace(go.Scatter(x=sahm.index, y=sahm["SAHMREALTIME"], name="Sahm Rule Recession Indicator", line=dict(color="#ef4444", width=2)))
            fig_m.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Soglia Recessione Sahm (0.50)")
            fig_m.update_layout(title="Disoccupazione USA & Trigger Recessionario Sahm Rule (FRED)", template="plotly_dark")
            st.plotly_chart(fig_m, use_container_width=True)
    with c2:
        if not t10y2y.empty:
            fig_c = px.line(t10y2y, title="Curva dei Rendimenti USA: 10 Anni - 2 Anni (T10Y2Y)", template="plotly_dark")
            fig_c.add_hline(y=0.0, line_dash="dash", line_color="white")
            fig_c.update_traces(line_color="#38bdf8")
            st.plotly_chart(fig_c, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        if not vix.empty:
            fig_vx = px.line(vix, title="CBOE: VIX Volatility Index (^VIX)", template="plotly_dark")
            fig_vx.add_hline(y=20, line_dash="dot", line_color="orange")
            fig_vx.add_hline(y=30, line_dash="dash", line_color="red")
            fig_vx.update_traces(line_color="#f43f5e")
            st.plotly_chart(fig_vx, use_container_width=True)
    with c4:
        if not ratio_gold_ndx.empty:
            fig_g = px.line(ratio_gold_ndx, title="Ratio: Oro / Nasdaq 100 (Hard Asset vs Tech)", template="plotly_dark")
            fig_g.update_traces(line_color="#eab308")
            st.plotly_chart(fig_g, use_container_width=True)

# ----------------- TAB 4: BITCOIN COWEN CHANNEL -----------------
with tab_btc:
    if not btc.empty:
        df_btc = btc.copy()
        
        # Bull Market Support Band (Cowen: 20-week SMA & 21-week EMA)
        # 20 settimane = 140 giorni, 21 settimane = 147 giorni
        df_btc["SMA_20W"] = df_btc["BTC-USD"].rolling(window=140).mean()
        df_btc["EMA_21W"] = df_btc["BTC-USD"].ewm(span=147, adjust=False).mean()
        
        # Canale di Regressione Logaritmica
        x_days = np.arange(1, len(df_btc) + 1)
        log_x = np.log(x_days)
        log_y = np.log(df_btc["BTC-USD"].values)
        poly = np.polyfit(log_x, log_y, 1)
        fit_log = poly[0] * log_x + poly[1]
        
        df_btc["Fit_Regression"] = np.exp(fit_log)
        std_dev = np.std(log_y - fit_log)
        df_btc["Upper_Band"] = np.exp(fit_log + 1.25 * std_dev)
        df_btc["Lower_Band"] = np.exp(fit_log - 1.25 * std_dev)

        fig_btc = go.Figure()
        
        # Prezzo BTC
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["BTC-USD"], name="BTC Prezzo USD", line=dict(color="#f8fafc", width=1.5)))
        
        # Bull Market Support Band
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["SMA_20W"], name="20-Week SMA", line=dict(color="#10b981", width=1.5)))
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["EMA_21W"], name="21-Week EMA", line=dict(color="#06b6d4", width=1.5)))
        
        # Regression Bands (Cowen)
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Upper_Band"], name="Canale Superiore (Overheated)", line=dict(color="#ef4444", dash="dash")))
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Fit_Regression"], name="Regressione Log Media", line=dict(color="#eab308", dash="dot")))
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Lower_Band"], name="Canale Inferiore (Accumulo)", line=dict(color="#22c55e", dash="dash")))

        fig_btc.update_yaxes(type="log", title="Prezzo BTC (Scala Logaritmica)")
        fig_btc.update_layout(
            title="Bitcoin: Canale di Regressione Logaritmica & Bull Market Support Band (Metodologia Benjamin Cowen)",
            template="plotly_dark",
            height=600
        )
        st.plotly_chart(fig_btc, use_container_width=True)
        st.caption("La Bull Market Support Band (20W SMA / 21W EMA) identifica se il mercato è in espansione sopra le medie o in bear market strutturale sotto di esse.")
