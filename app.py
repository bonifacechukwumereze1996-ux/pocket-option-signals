import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import requests
from datetime import datetime, timedelta

# -----------------------------
# PUSH ALERT CONFIG (Pushover)
PUSHOVER_USER_KEY = ""  # Your Pushover User Key
PUSHOVER_APP_TOKEN = "" # Your Pushover App Token

def send_push(message):
    if PUSHOVER_USER_KEY=="" or PUSHOVER_APP_TOKEN=="":
        return
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_APP_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "priority": 1,
        "sound": "siren",
        "retry": 30,
        "expire": 300
    }
    requests.post(url, data=data)

def play_browser_sound():
    st.markdown("""
        <audio autoplay>
        <source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg">
        </audio>
    """, unsafe_allow_html=True)

# -----------------------------
# STREAMLIT CONFIG
st.set_page_config(page_title="Pocket Option Heat-Map", layout="wide")
st.title("🤖 Pocket Option AI Heat-Map Signals")
st.caption("⚠️ Demo & Educational Use Only")

st_autorefresh(interval=30*1000, key="refresh")  # auto-refresh every 30s

# -----------------------------
# SESSION STATE
if "last_signal" not in st.session_state: st.session_state.last_signal = {}
if "last_time" not in st.session_state: st.session_state.last_time = {}
if "trades" not in st.session_state: st.session_state.trades = []

# -----------------------------
# PAIRS AND TIMEFRAMES
pairs = st.multiselect(
    "Select Pairs",
    [
        "EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X","NZDUSD=X",
        "EURJPY=X","GBPJPY=X","AUDJPY=X","CADJPY=X","CHFJPY=X","EURGBP=X",
        "EURUSD OTC","GBPUSD OTC","USDJPY OTC","AUDUSD OTC",
        "EURJPY OTC","GBPJPY OTC","USDCHF OTC","USDCAD OTC"
    ],
    default=["EURUSD=X","GBPUSD=X"]
)

tf_label = st.selectbox("Select Time Frame", ["1m","5m","15m","1h"])
interval_map = {"1m":"1m","5m":"5m","15m":"15m","1h":"60m"}
tf = interval_map[tf_label]

signal_duration_map = {"1m":1, "5m":5, "15m":15, "60m":60}  # minutes per signal

# -----------------------------
# DATA FUNCTION
def get_data(pair):
    symbol = pair.replace(" OTC","=X")
    period_map = {"1m":"1d","5m":"1d","15m":"2d","60m":"7d"}
    df = yf.download(symbol, period=period_map[tf], interval=tf, progress=False, prepost=True)
    if df.empty or len(df)<50: return None
    df.columns = df.columns.get_level_values(0)
    close = df["Close"]
    df["ema20"] = ta.trend.EMAIndicator(close, 20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(close, 50).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(close, 14).rsi()
    macd = ta.trend.MACD(close)
    df["macd"] = macd.macd()
    df["macds"] = macd.macd_signal()
    adx = ta.trend.ADXIndicator(df["High"], df["Low"], close)
    df["adx"] = adx.adx()
    df.dropna(inplace=True)
    return df

# -----------------------------
# SIGNAL FUNCTION
def calc_signal(row):
    points_buy = 0
    points_sell = 0
    if row.ema20 > row.ema50: points_buy += 1
    elif row.ema20 < row.ema50: points_sell += 1
    if row.rsi > 55: points_buy += 1
    elif row.rsi < 45: points_sell += 1
    if row.macd > row.macds: points_buy += 1
    elif row.macd < row.macds: points_sell += 1
    if row.adx > 20: points_buy += 1; points_sell += 1
    if points_buy >= 3: return "BUY"
    elif points_sell >= 3: return "SELL"
    else: return "WAIT"

# -----------------------------
# CANDLE FUNCTION
def candle(df):
    fig = go.Figure()
    fig.add_candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close)
    fig.add_scatter(x=df.index, y=df.ema20, name="EMA20")
    fig.add_scatter(x=df.index, y=df.ema50, name="EMA50")
    fig.update_layout(height=350)
    return fig

# -----------------------------
# MAIN HEAT-MAP
table_rows = []

for pair in pairs:
    df = get_data(pair)
    if df is None or len(df)<50:
        table_rows.append([pair,"WAIT","No Data","-", "-"])
        continue

    last = df.iloc[-1]
    sig = calc_signal(last)
    price = last.Close

    # Trend strength
    strength = "Weak"
    if last.adx>30: strength="Strong"
    elif last.adx>20: strength="Moderate"

    # Signal time remaining
    now = datetime.now()
    prev_time = st.session_state.last_time.get(pair, now)
    if st.session_state.last_signal.get(pair) != sig:
        st.session_state.last_time[pair] = now
    elapsed = (now - st.session_state.last_time[pair]).total_seconds()
    remaining = max(signal_duration_map[tf_label]*60 - elapsed,0)
    mins = int(remaining//60)
    secs = int(remaining%60)
    time_remain = f"{mins}m {secs}s" if sig!="WAIT" else "-"

    # Push notification if signal changed
    prev_sig = st.session_state.last_signal.get(pair)
    if sig in ["BUY","SELL"] and sig != prev_sig:
        st.session_state.last_signal[pair] = sig
        send_push(f"{pair} {sig} on {tf_label} timeframe 🚨")
        play_browser_sound()
        st.toast(f"{pair} {sig} SIGNAL 🚨", icon="🔥")

    # Add row to table
    table_rows.append([pair, sig, strength, round(price,5), time_remain])

# Display Heat-Map Table
df_table = pd.DataFrame(table_rows, columns=["Pair","Signal","Strength","Last Price","Time Remaining"])
def color_signal(val):
    if val=="BUY": return "background-color:green;color:white"
    elif val=="SELL": return "background-color:red;color:white"
    elif val=="WAIT": return "background-color:gray;color:white"
    else: return ""
st.subheader("📊 Multi-Pair Signal Heat-Map")
st.dataframe(df_table.style.applymap(color_signal, subset=["Signal"]))

# -----------------------------
# Clickable pair detail charts
st.subheader("🕯 Detailed Pair Charts")
for pair in pairs:
    df = get_data(pair)
    if df is None or len(df)<50: continue
    with st.expander(pair):
        st.plotly_chart(candle(df), use_container_width=True)
        st.dataframe(df[["Close","ema20","ema50","rsi","macd","macds","adx"]].tail(20))

# -----------------------------
st.info("Demo & Learning Only | Auto-refresh every 30s | Signals show remaining time | Phone push + browser alerts active")