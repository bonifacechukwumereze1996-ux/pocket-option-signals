import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import requests, time

# -----------------------
BOT_TOKEN = "PUT_BOT_TOKEN"
CHAT_ID = "PUT_CHAT_ID"

def send_telegram(msg):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url,data={"chat_id":CHAT_ID,"text":msg})

# -----------------------
st.set_page_config(page_title="Pocket Option AI Signals", layout="wide")
st.title("🤖 Pocket Option AI Signals")
st_autorefresh(interval=30000,key="refresh")

pairs = st.multiselect("Pairs",["EURUSD=X","GBPUSD=X","USDJPY=X"],default=["EURUSD=X"])
tf = st.selectbox("Timeframe",["1m","5m","15m"])

if "trades" not in st.session_state:
    st.session_state.trades=[]
if "last_signal" not in st.session_state:
    st.session_state.last_signal={}
if "last_price" not in st.session_state:
    st.session_state.last_price={}

# -----------------------
def get_data(pair):
    df=yf.download(pair,period="1d",interval=tf)
    df.columns=df.columns.get_level_values(0)
    close=df["Close"]
    df["ema20"]=ta.trend.EMAIndicator(close,20).ema_indicator()
    df["ema50"]=ta.trend.EMAIndicator(close,50).ema_indicator()
    df["rsi"]=ta.momentum.RSIIndicator(close,14).rsi()
    macd=ta.trend.MACD(close)
    df["macd"]=macd.macd()
    df["macds"]=macd.macd_signal()
    adx=ta.trend.ADXIndicator(df["High"],df["Low"],close)
    df["adx"]=adx.adx()
    df.dropna(inplace=True)
    return df

# -----------------------
def signal(row):
    if row.ema20>row.ema50 and row.rsi>55 and row.macd>row.macds and row.adx>20:
        return "BUY"
    if row.ema20<row.ema50 and row.rsi<45 and row.macd<row.macds and row.adx>20:
        return "SELL"
    return "WAIT"

# -----------------------
wins=0
losses=0

for pair in pairs:
    st.subheader(pair)
    df=get_data(pair)

    if df is None or len(df)<50:
        st.warning("Waiting data...")
        continue

    last=df.iloc[-1]
    sig=signal(last)
    price=last.Close

    # TREND STRENGTH
    strength="Weak"
    if last.adx>30: strength="Strong"
    elif last.adx>20: strength="Moderate"

    st.info(f"Trend Strength: {strength}")

    color="gray"
    if sig=="BUY": color="green"
    if sig=="SELL": color="red"

    st.markdown(f"<h2 style='color:{color};text-align:center'>{sig}</h2>",unsafe_allow_html=True)

    prev=st.session_state.last_signal.get(pair)
    prev_price=st.session_state.last_price.get(pair)

    if sig in ["BUY","SELL"] and sig!=prev:
        if prev in ["BUY","SELL"]:
            if (prev=="BUY" and price>prev_price) or (prev=="SELL" and price<prev_price):
                result="WIN"
            else:
                result="LOSS"

            st.session_state.trades.append({"Pair":pair,"Signal":prev,"Result":result})

        st.session_state.last_signal[pair]=sig
        st.session_state.last_price[pair]=price

        send_telegram(f"{pair} {sig} on {tf}")

    fig=go.Figure()
    fig.add_candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close)
    fig.add_scatter(x=df.index,y=df.ema20,name="EMA20")
    fig.add_scatter(x=df.index,y=df.ema50,name="EMA50")
    st.plotly_chart(fig,use_container_width=True)

# -----------------------
if len(st.session_state.trades)>0:
    hist=pd.DataFrame(st.session_state.trades)
    st.subheader("Trade History")
    st.dataframe(hist)

    wins=len(hist[hist.Result=="WIN"])
    losses=len(hist[hist.Result=="LOSS"])
    acc=round((wins/(wins+losses))*100,2)

    st.success(f"Wins: {wins} | Losses: {losses} | Accuracy: {acc}%")

st.info("Best timeframe: 5m & 15m | Demo & Learning Only")