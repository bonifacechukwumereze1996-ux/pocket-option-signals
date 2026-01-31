import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
import time

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Pocket Option Multi-Pair Signals",
    layout="wide"
)

st.title("📊 Pocket Option Multi-Pair Dashboard")
st.caption("⚠️ Demo & Educational Use Only — No Guarantees")

# -------------------------------
# AUTO REFRESH
# -------------------------------
refresh_interval = st.sidebar.number_input(
    "Auto-refresh interval (seconds)", min_value=5, value=10, step=1
)

# -------------------------------
# USER INPUTS
# -------------------------------
pairs = st.multiselect(
    "Select Pairs",
    [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X",
        "GBPUSD OTC", "EURUSD OTC", "USDJPY OTC"  # Add more OTC pairs here
    ],
    default=["EURUSD=X", "GBPUSD=X"]
)

timeframe_label = st.selectbox(
    "Select Time Frame",
    ["1 Minute", "5 Minutes", "15 Minutes"]
)

timeframe_map = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "15 Minutes": "15m"
}
interval = timeframe_map[timeframe_label]

st.info("📘 Note: OTC pairs may not have complete Yahoo Finance data.")

# -------------------------------
# FUNCTIONS
# -------------------------------
def get_data(pair, interval):
    # For OTC pairs, use the regular Yahoo Finance symbol
    yf_pair = pair.replace(" OTC", "=X")
    data = yf.download(yf_pair, period="1d", interval=interval)
    if data.empty:
        return None
    data["ema20"] = ta.trend.EMAIndicator(close=data["Close"], window=20).ema_indicator()
    data["ema50"] = ta.trend.EMAIndicator(close=data["Close"], window=50).ema_indicator()
    data["rsi"] = ta.momentum.RSIIndicator(close=data["Close"], window=14).rsi()
    data.dropna(inplace=True)
    return data

def get_signal(last):
    if last["ema20"] > last["ema50"] and last["rsi"] > 55:
        return "🟢 BUY", "green"
    elif last["ema20"] < last["ema50"] and last["rsi"] < 45:
        return "🔴 SELL", "red"
    else:
        return "⏸ NO TRADE", "gray"

def plot_candlestick(data, pair):
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=pair
    )])
    fig.add_trace(go.Scatter(x=data.index, y=data['ema20'], mode='lines', name='EMA20'))
    fig.add_trace(go.Scatter(x=data.index, y=data['ema50'], mode='lines', name='EMA50'))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=20))
    return fig

# -------------------------------
# AUTO REFRESH MECHANISM
# -------------------------------
st_autorefresh = st.empty()  # placeholder for auto refresh

while True:
    st_autorefresh.empty()  # refresh page content

    # -------------------------------
    # DISPLAY SIGNALS
    # -------------------------------
    for pair in pairs:
        st.subheader(f"📌 {pair}")
        data = get_data(pair, interval)
        if data is None:
            st.warning("No data available for this pair.")
            continue

        last = data.iloc[-1]
        signal, color = get_signal(last)

        st.markdown(
            f"<h2 style='color:{color}; text-align:center;'>{signal}</h2>",
            unsafe_allow_html=True
        )

        # Show table
        with st.expander("📈 Recent Indicator Data"):
            st.dataframe(data[["Close", "ema20", "ema50", "rsi"]].tail(20))

        # Show candlestick chart
        with st.expander("🕯 Candlestick Chart"):
            fig = plot_candlestick(data, pair)
            st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # EDUCATION NOTE
    # -------------------------------
    st.info(
        "📘 Tips:\n"
        "- Use for DEMO practice only\n"
        "- Combine with support & resistance\n"
        "- Avoid over-trading\n"
        "- No signal is 100% accurate"
    )

    time.sleep(refresh_interval)  # wait before next refresh