import streamlit as st
import yfinance as yf
import ta
import pandas as pd
import plotly.graph_objects as go

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Pocket Option Live Multi-Pair Signals",
    layout="wide"
)

st.title("📊 Pocket Option Demo Dashboard")
st.caption("⚠️ Demo & Educational Use Only — No Guarantees")

# -------------------------
# USER INPUTS
# -------------------------
pairs = st.multiselect(
    "Select Assets (Learning Pairs)",
    ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"],
    default=["EURUSD=X", "GBPUSD=X"]
)

timeframe_label = st.selectbox(
    "Select Time Frame",
    ["1 Minute", "5 Minutes", "15 Minutes"]
)

interval_map = {"1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m"}
interval = interval_map[timeframe_label]

# -------------------------
# LOOP THROUGH PAIRS
# -------------------------
for pair in pairs:
    st.markdown(f"## 💹 {pair} Signals & Chart")

    # LOAD DATA
    data = yf.download(pair, period="1d", interval=interval)

    # Flatten multi-index columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty:
        st.warning(f"No data for {pair}. Skipping.")
        continue

    # INDICATORS
    close = data["Close"].squeeze()
    data["ema20"] = ta.trend.EMAIndicator(close=close, window=20).ema_indicator()
    data["ema50"] = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()
    data["rsi"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    data.dropna(inplace=True)

    # SIGNAL LOGIC
    last = data.iloc[-1]
    ema20 = float(last["ema20"])
    ema50 = float(last["ema50"])
    rsi = float(last["rsi"])

    signal = "⏸ NO TRADE"
    color = "gray"

    if ema20 > ema50 and rsi > 55:
        signal = "🟢 BUY"
        color = "green"
    elif ema20 < ema50 and rsi < 45:
        signal = "🔴 SELL"
        color = "red"

    st.subheader("📍 Current Signal")
    st.markdown(
        f"<h2 style='color:{color}; text-align:center;'>{signal}</h2>",
        unsafe_allow_html=True
    )

    # PLOTLY CANDLESTICKS + EMA
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Price",
        increasing_line_color="green",
        decreasing_line_color="red"
    ))
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["ema20"],
        mode="lines",
        line=dict(color="blue", width=2),
        name="EMA 20"
    ))
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["ema50"],
        mode="lines",
        line=dict(color="orange", width=2),
        name="EMA 50"
    ))
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # DATA TABLE
    with st.expander(f"📊 {pair} Market Data (Last 20 rows)"):
        st.dataframe(data.tail(20))

# EDUCATION NOTE
st.info("""
📘 Tips:
- Demo & learning only
- Signals combine EMA crossover + RSI
- Refresh the browser every 60 seconds to see live updates
- No signal is 100% accurate
""")
