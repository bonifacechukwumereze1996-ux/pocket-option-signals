import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
import time

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Pocket Option Multi-Pair Signals",
    layout="wide"
)

st.title("📊 Pocket Option Multi-Pair Dashboard")
st.caption("⚠️ Educational & Demo Use Only — No Guarantees")

# -------------------------
# AUTO REFRESH
# -------------------------
refresh_sec = st.slider("Auto-refresh interval (seconds)", 15, 120, 30)
time.sleep(refresh_sec)
st.experimental_rerun()

# -------------------------
# PAIR LISTS
# -------------------------
REAL_PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
}

OTC_PAIRS = [
    "EURUSD OTC",
    "GBPUSD OTC",
    "USDJPY OTC",
    "AUDUSD OTC",
    "USDCAD OTC",
    "NZDUSD OTC",
]

ALL_PAIRS = list(REAL_PAIRS.keys()) + OTC_PAIRS

# -------------------------
# USER INPUTS
# -------------------------
pairs = st.multiselect(
    "Select Pairs (Real + OTC)",
    ALL_PAIRS,
    default=["EURUSD", "GBPUSD", "EURUSD OTC"]
)

timeframe_label = st.selectbox(
    "Select Time Frame",
    ["5 Minutes", "15 Minutes"]
)

interval_map = {
    "5 Minutes": "5m",
    "15 Minutes": "15m"
}
interval = interval_map[timeframe_label]

# -------------------------
# FUNCTIONS
# -------------------------
def load_data(pair_key):
    symbol = REAL_PAIRS.get(pair_key.replace(" OTC", ""), None)
    if symbol is None:
        return None

    df = yf.download(symbol, period="5d", interval=interval, progress=False)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df

def compute_indicators(df):
    if len(df) < 60:
        return None

    close = df["Close"]

    df["ema20"] = ta.trend.EMAIndicator(close, 20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(close, 50).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(close, 14).rsi()

    df.dropna(inplace=True)
    return df

def generate_signal(row):
    if row["ema20"] > row["ema50"] and row["rsi"] > 55:
        return "🟢 BUY", "green"
    elif row["ema20"] < row["ema50"] and row["rsi"] < 45:
        return "🔴 SELL", "red"
    else:
        return "⏸ HOLD", "gray"

# -------------------------
# MAIN LOOP
# -------------------------
for pair in pairs:
    is_otc = "OTC" in pair

    st.markdown(f"## 📌 {pair} {'🟠 OTC (Simulated)' if is_otc else ''}")

    data = load_data(pair)

    if data is None:
        st.warning("No data available")
        continue

    data = compute_indicators(data)

    if data is None or data.empty:
        st.info("Not enough data yet")
        continue

    last = data.iloc[-1]
    signal, color = generate_signal(last)

    st.markdown(
        f"<h2 style='color:{color}; text-align:center'>{signal}</h2>",
        unsafe_allow_html=True
    )

    # -------------------------
    # CHART
    # -------------------------
    fig = go.Figure()

    fig.add_candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Price"
    )

    fig.add_scatter(
        x=data.index,
        y=data["ema20"],
        mode="lines",
        name="EMA 20"
    )

    fig.add_scatter(
        x=data.index,
        y=data["ema50"],
        mode="lines",
        name="EMA 50"
    )

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📊 Indicator Values"):
        st.write(last[["ema20", "ema50", "rsi"]])

# -------------------------
# FOOTER
# -------------------------
st.info("""
📘 Notes  
• Real pairs use Yahoo Finance data  
• OTC pairs are simulated using real market behavior  
• Phone & PC compatible  
• Educational & demo use only  
""")