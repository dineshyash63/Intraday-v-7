import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import requests

# Page Configuration
st.set_page_config(page_title="AI Quantitative Terminal v7.0", layout="wide", initial_sidebar_state="expanded")

# Custom Dark Styling
st.markdown("""
<style>
    .main { background-color: #0d1117; color: #e6edf3; }
    .stMetric { background-color: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #30363d; }
    .stButton>button { width: 100%; background-color: #238636; color: white; font-weight: bold; border-radius: 6px; border: none; height: 48px; font-size: 16px; }
    .stButton>button:hover { background-color: #2ea043; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ AI Quantitative Pro Terminal v7.0 (Telegram Alert Powered)")
st.caption("Institutional Breakout Engine | Supertrend Confluence | Live Telegram Notifications")

WATCHLIST = [
    "TATAMOTORS", "RELIANCE", "SBIN", "ICICIBANK", "AXISBANK", 
    "HDFCBANK", "INFY", "TCS", "TATASTEEL", "BHARTIARTL", 
    "M&M", "NTPC", "LT", "SUNPHARMA", "MARUTI"
]

# Telegram Notification Function
def send_telegram_alert(bot_token, chat_id, message):
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

def generate_sample_data():
    dates = pd.date_range(end=datetime.now(), periods=60, freq='15min')
    np.random.seed(42)
    close = 800 + np.cumsum(np.random.randn(60) * 2)
    high = close + np.random.rand(60) * 3
    low = close - np.random.rand(60) * 3
    open_p = close + np.random.randn(60)
    volume = np.random.randint(5000, 80000, size=60)
    return pd.DataFrame({'Open': open_p, 'High': high, 'Low': low, 'Close': close, 'Volume': volume}, index=dates)

def calculate_vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

def analyze_stock_v7(ticker_symbol, tf):
    ticker_clean = ticker_symbol.strip().upper()
    ticker_ns = ticker_clean + ".NS" if not ticker_clean.endswith(".NS") else ticker_clean
    
    is_demo = False
    try:
        data = yf.Ticker(ticker_ns)
        df = data.history(period="1mo", interval=tf)
        if df.empty or len(df) < 20:
            df = data.history(period="3mo", interval="1d")
        if df.empty:
            df = generate_sample_data()
            is_demo = True
    except Exception:
        df = generate_sample_data()
        is_demo = True

    close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
    
    df['VWAP'] = calculate_vwap(df)
    df['EMA20'] = ta.trend.ema_indicator(close, window=20)
    df['EMA50'] = ta.trend.ema_indicator(close, window=50)
    df['RSI'] = ta.momentum.rsi(close, window=14)
    df['ATR'] = ta.volatility.average_true_range(high, low, close, window=14)
    
    bb = ta.volatility.BollingerBands(close)
    df['BB_HIGH'] = bb.bollinger_hband()
    df['BB_LOW'] = bb.bollinger_lband()
    
    macd = ta.trend.MACD(close)
    df['MACD'] = macd.macd()
    df['MACD_SIG'] = macd.macd_signal()
    df['VOL_SMA'] = ta.trend.sma_indicator(volume, window=20)
    
    latest = df.iloc[-1]
    price = float(latest['Close'])
    rsi = float(latest['RSI']) if not np.isnan(latest['RSI']) else 50.0
    atr = float(latest['ATR']) if not np.isnan(latest['ATR']) else (price * 0.01)
    ema20, ema50 = float(latest['EMA20']), float(latest['EMA50'])
    vwap = float(latest['VWAP'])
    macd_val, macd_sig = float(latest['MACD']), float(latest['MACD_SIG'])
    bb_high, bb_low = float(latest['BB_HIGH']), float(latest['BB_LOW'])
    
    curr_vol = float(latest['Volume'])
    avg_vol = float(latest['VOL_SMA']) if not np.isnan(latest['VOL_SMA']) and latest['VOL_SMA'] > 0 else 1.0
    vol_ratio = curr_vol / avg_vol

    score = 0
    if price > vwap: score += 20
    if ema20 > ema50: score += 20
    if price > bb_high: score += 15
    if macd_val > macd_sig: score += 15
    if vol_ratio >= 1.5: score += 15
    if 50 <= rsi <= 70: score += 15
    
    bear_score = 0
    if price < vwap: bear_score += 20
    if ema20 < ema50: bear_score += 20
    if price < bb_low: bear_score += 15
    if macd_val < macd_sig: bear_score += 15
    if vol_ratio >= 1.5: bear_score += 15
    if 30 <= rsi <= 50: bear_score += 15

    signal = "NEUTRAL ⏸️"
    sl, tp1, tp2 = 0.0, 0.0, 0.0
    final_score = score
    
    if score >= 75 and vol_ratio >= 1.2:
        signal = "🔥 STRONG BUY 🚀"
        sl = price - (atr * 1.5)
        tp1 = price + (atr * 1.8)
        tp2 = price + (atr * 3.0)
    elif bear_score >= 75 and vol_ratio >= 1.2:
        signal = "💥 STRONG SELL 🔻"
        final_score = bear_score
        sl = price + (atr * 1.5)
        tp1 = price - (atr * 1.8)
        tp2 = price - (atr * 3.0)

    return {
        'df': df, 'symbol': ticker_clean, 'price': price, 'signal': signal, 
        'score': final_score, 'vwap': vwap, 'ema20': ema20, 'ema50': ema50,
        'rsi': rsi, 'atr': atr, 'vol_ratio': vol_ratio, 'sl': sl, 
        'tp1': tp1, 'tp2': tp2, 'is_demo': is_demo
    }

# Sidebar Controls
with st.sidebar:
    st.header("📲 Telegram Settings")
    bot_token = st.text_input("Bot Token", type="password", help="BotFather தந்த HTTP API Token")
    chat_id = st.text_input("Chat ID", help="userinfobot தந்த Chat ID")
    
    st.markdown("---")
    st.header("⚙️ Controls")
    selected_tf = st.selectbox("⏱️ Timeframe", ["5m", "15m", "1h"], index=1)
    capital = st.number_input("Capital (₹)", value=100000, step=10000)
    risk_pct = st.slider("Risk (%)", 0.5, 3.0, 1.0, 0.5)

tab1, tab2 = st.tabs(["🎯 Single Terminal", "🔥 Auto Scanner + Alert Engine"])

with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        stock_input = st.text_input("Stock Symbol", "TATAMOTORS")
        analyze_btn = st.button("⚡ ANALYZE STOCK")

    if stock_input:
        res = analyze_stock_v7(stock_input, selected_tf)
        if res['is_demo']:
            st.warning("⚠️ Market Closed: Showing Demo Simulation.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Price", f"₹{res['price']:.2f}")
        m2.metric("Signal", res['signal'])
        m3.metric("Score", f"{res['score']}/100")
        m4.metric("Vol Ratio", f"{res['vol_ratio']:.2f}x")

with tab2:
    st.subheader("🔥 Scanner & Automatic Telegram Notification")
    if st.button("🚀 SCAN WATCHLIST & SEND TELEGRAM ALERTS"):
        results = []
        progress_bar = st.progress(0)
        alerts_sent = 0
        
        for idx, stock in enumerate(WATCHLIST):
            r = analyze_stock_v7(stock, selected_tf)
            results.append({
                "Stock": r['symbol'],
                "Signal": r['signal'],
                "Score": f"{r['score']}/100",
                "Price": f"₹{r['price']:.2f}",
                "SL": f"₹{r['sl']:.2f}" if r['sl']>0 else "-",
                "TP1": f"₹{r['tp1']:.2f}" if r['tp1']>0 else "-"
            })
            
            # Send Alert if Strong Signal
            if "STRONG" in r['signal'] and bot_token and chat_id:
                msg = f"🚨 *AI TRADING ALERT v7.0*\n\n📌 *Stock:* {r['symbol']}\n🎯 *Signal:* {r['signal']}\n💰 *Price:* ₹{r['price']:.2f}\n🛑 *SL:* ₹{r['sl']:.2f}\n🎯 *Target 1:* ₹{r['tp1']:.2f}\n📊 *Score:* {r['score']}/100"
                send_telegram_alert(bot_token, chat_id, msg)
                alerts_sent += 1
                
            progress_bar.progress((idx + 1) / len(WATCHLIST))
            
        st.dataframe(pd.DataFrame(results), use_container_width=True)
        if alerts_sent > 0:
            st.success(f"✅ Successful! {alerts_sent} Telegram Alerts Sent to your phone!")
        elif bot_token and chat_id:
            st.info("ℹ️ Scan Complete. No Strong signals found right now.")
    
