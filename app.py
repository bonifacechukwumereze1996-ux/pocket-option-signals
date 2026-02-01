import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

# -----------------------------------
st.set_page_config(page_title="Pocket Option Signals", layout="wide")

st.title("📊 Pocket Option Multi-Pair Dashboard")
st.caption("⚠️ Demo & Educational Use Only — No Guarantees")

# -----------------------------------
pairs = st.multiselect(
    "Select Pairs",
    [
        "EURUSD=X",
        "GBPUSD=X",
        "USDJPY=X",
        "AUDUSD=X",
        "EURUSD OTC",
        "GBPUSD OTC",
        "USDJPY OTC"
    ],
    default=["EURUSD=X", "GBPUSD=X"]
)

timeframe_label = st.selectbox(
    "Select Time Frame",
    ["1 Minute", "5 Minutes", "15 Minutes"]
)

interval = {"1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m"}[timeframe_label]

# -----------------------------------
def get_data(pair, interval):
    symbol = pair.replace(" OTC", "=X")
    df = yf.download(symbol, period="1d", interval=interval)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].astype(float)

    df["ema20"] = ta.trend.EMAIndicator(close, 20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(close, 50).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(close, 14).rsi()

    df.dropna(inplace=True)
    return df

# -----------------------------------
def signal(row):
    if row["ema20"] > row["ema50"] and row["rsi"] > 55:
        return "🟢 BUY", "green"
    elif row["ema20"] < row["ema50"] and row["rsi"] < 45:
        return "🔴 SELL", "red"
    else:
        return "⏸ NO TRADE", "gray"

# -----------------------------------
def candle(df):
    fig = go.Figure()
    fig.add_candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )
    fig.add_scatter(x=df.index, y=df["ema20"], name="EMA20")
    fig.add_scatter(x=df.index, y=df["ema50"], name="EMA50")
    fig.update_layout(height=350)
    return fig

# -----------------------------------
for pair in pairs:

    st.subheader(f"📌 {pair}")

    data = get_data(pair, interval)

    if data is None or data.empty:
        st.warning("Waiting for data...")
        continue

    sig, color = signal(data.iloc[-1])

    st.markdown(
        f"<h2 style='color:{color};text-align:center'>{sig}</h2>",
        unsafe_allow_html=True
    )

    with st.expander("📈 Indicator Data"):
        st.dataframe(data[["Close", "ema20", "ema50", "rsi"]].tail(20))

    with st.expander("🕯 Candlestick Chart"):
        st.plotly_chart(candle(data), use_container_width=True)

# -----------------------------------
st.info(
    "- Demo & learning only\n"
    "- EMA20 + EMA50 + RSI strategy\n"
    "- Best on 5m and 15m\n"
    "- No signal is 100% accurate"
)