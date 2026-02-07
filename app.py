import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# -----------------------------
# STREAMLIT CONFIG
st.set_page_config(page_title="Pocket Option AI Heat-Map", layout="wide")
st.title("🤖 Pocket Option AI Heat-Map Signals")
st.caption("⚠️ Demo & Educational Use Only")

st_autorefresh(interval=30 * 1000, key="refresh")  # 30s refresh

# -----------------------------
# SESSION STATE
if "signal_start" not in st.session_state:
    st.session_state.signal_start = {}

# -----------------------------
# PAIRS
pairs = st.multiselect(
    "Select Pairs",
    [
        "EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X","NZDUSD=X",
        "EURJPY=X","GBPJPY=X","AUDJPY=X",
        "EURUSD OTC","GBPUSD OTC","USDJPY OTC","AUDUSD OTC"
    ],
    default=["EURUSD=X","GBPUSD=X"]
)

# -----------------------------
# TIMEFRAME
tf_label = st.selectbox("Select Time Frame", ["1m","5m","15m","1h"])
interval_map = {"1m":"1m","5m":"5m","15m":"15m","1h":"60m"}
period_map = {"1m":"1d","5m":"1d","15m":"2d","1h":"7d"}
signal_minutes = {"1m":1,"5m":5,"15m":15,"1h":60}

interval = interval_map[tf_label]

# Adjust EMA periods for small timeframes
if tf_label in ["1m","5m"]:
    ema_short, ema_long = 10, 25
else:
    ema_short, ema_long = 20, 50

# -----------------------------
# DATA FUNCTION
def get_data(pair):
    symbol = pair.replace(" OTC","=X")
    df = yf.download(symbol, interval=interval, period=period_map[tf_label], progress=False)
    
    # Retry if OTC data missing
    if df.empty and "OTC" in pair:
        symbol = pair.replace(" OTC","=X")
        df = yf.download(symbol, interval=interval, period=period_map[tf_label], progress=False)

    if df.empty or len(df)<50:
        return None

    df.columns = df.columns.get_level_values(0)
    close = df["Close"]

    df["ema_short"] = ta.trend.EMAIndicator(close, ema_short).ema_indicator()
    df["ema_long"] = ta.trend.EMAIndicator(close, ema_long).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(close, 14).rsi()
    macd = ta.trend.MACD(close)
    df["macd"] = macd.macd()
    df["macds"] = macd.macd_signal()
    df["adx"] = ta.trend.ADXIndicator(df["High"], df["Low"], close).adx()

    df.dropna(inplace=True)
    return df

# -----------------------------
# SIGNAL FUNCTION
def get_signal(row):
    buy, sell = 0, 0

    if row.ema_short > row.ema_long: buy += 1
    else: sell += 1

    if row.rsi > 55: buy += 1
    elif row.rsi < 45: sell += 1

    if row.macd > row.macds: buy += 1
    else: sell += 1

    # Adjust points threshold to 2 for faster responsiveness
    if buy >= 2: return "BUY"
    elif sell >= 2: return "SELL"
    else: return "WAIT"

# -----------------------------
# MAIN TABLE
rows = []
now = datetime.now()

for pair in pairs:
    df = get_data(pair)
    if df is None:
        rows.append([pair,"WAIT","No Data","-","-"])
        continue

    last = df.iloc[-1]
    signal = get_signal(last)
    price = round(last.Close,5)

    # Strength based on ADX
    if last.adx > 30:
        strength = "Strong"
    elif last.adx > 20:
        strength = "Moderate"
    else:
        strength = "Weak"

    # Time Remaining
    if signal in ["BUY","SELL"]:
        if pair not in st.session_state.signal_start:
            st.session_state.signal_start[pair] = now

        elapsed = (now - st.session_state.signal_start[pair]).total_seconds()
        remaining = max(signal_minutes[tf_label]*60 - elapsed, 0)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        time_left = f"{mins}m {secs}s"
    else:
        st.session_state.signal_start.pop(pair, None)
        time_left = "-"

    rows.append([pair, signal, strength, price, time_left])

# -----------------------------
# DISPLAY TABLE
df_table = pd.DataFrame(rows, columns=["Pair","Signal","Strength","Price","Time Remaining"])

def color_signal(val):
    if val=="BUY": return "background-color:green;color:white"
    elif val=="SELL": return "background-color:red;color:white"
    elif val=="WAIT": return "background-color:gray;color:white"
    return ""

st.subheader("📊 Multi-Pair Signal Heat-Map")
st.dataframe(df_table.style.applymap(color_signal, subset=["Signal"]))

# -----------------------------
# CHARTS
st.subheader("📈 Detailed Charts")
for pair in pairs:
    df = get_data(pair)
    if df is None: continue
    with st.expander(pair):
        fig = go.Figure()
        fig.add_candlestick(
            x=df.index, open=df.Open, high=df.High,
            low=df.Low, close=df.Close
        )
        fig.add_scatter(x=df.index, y=df.ema_short, name=f"EMA{ema_short}")
        fig.add_scatter(x=df.index, y=df.ema_long, name=f"EMA{ema_long}")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

st.info("Auto-refresh every 30s | Signals + countdown fixed | Demo & learning only")