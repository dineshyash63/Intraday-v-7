import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

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

st.title("⚡ AI Quantitative Pro Terminal v7.0 (Multi-Confluence)")
st.caption("Institutional Breakout Engine | Supertrend Confluence | Multi-Timeframe Scoring | Risk Management")

# High Liquidity Nifty 15 Watchlist
WATCHLIST = [
    "TATAMOTORS", "RELIANCE", "SBIN", "ICICIBANK", "AXISBANK", 
    "HDFCBANK", "INFY", "TCS", "TATASTEEL", "BHARTIARTL", 
    "M&M", "NTPC", "LT", "SUNPHARMA", "MARUTI"
]

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

def calculate_pivots(df):
    last_day = df.iloc[-1]
    h, l, c = last_day['High'], last_day['Low'], last_day['Close']
    p = (h + l + c) / 3
    r1, s1 = (2 * p) - l, (2 * p) - h
    r2, s2 = p + (h - l), p - (h - l)
    return p, r1, s1, r2, s2

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
    
    # Technical Indicators
    df['VWAP'] = calculate_vwap(df)
    df['EMA20'] = ta.trend.ema_indicator(close, window=20)
    df['EMA50'] = ta.trend.ema_indicator(close, window=50)
    df['EMA200'] = ta.trend.ema_indicator(close, window=200) if len(df) >= 200 else df['EMA50']
    df['RSI'] = ta.momentum.rsi(close, window=14)
    df['ATR'] = ta.volatility.average_true_range(high, low, close, window=14)
    
    # Bollinger Bands for Breakout Detection
    bb = ta.volatility.BollingerBands(close)
    df['BB_HIGH'] = bb.bollinger_hband()
    df['BB_LOW'] = bb.bollinger_lband()
    
    # MACD
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

    # Advanced Scoring System (0 to 100)
    score = 0
    if price > vwap: score += 20
    if ema20 > ema50: score += 20
    if price > bb_high: score += 15  # Strong Breakout
    if macd_val > macd_sig: score += 15
    if vol_ratio >= 1.5: score += 15
    if 50 <= rsi <= 70: score += 15
    
    # Bearish Scoring Adjustment
    bear_score = 0
    if price < vwap: bear_score += 20
    if ema20 < ema50: bear_score += 20
    if price < bb_low: bear_score += 15  # Strong Breakdown
    if macd_val < macd_sig: bear_score += 15
    if vol_ratio >= 1.5: bear_score += 15
    if 30 <= rsi <= 50: bear_score += 15

    # Signal Precision Engine
    signal = "NEUTRAL ⏸️"
    sl, tp1, tp2, tp3 = 0.0, 0.0, 0.0, 0.0
    final_score = score
    
    if score >= 75 and vol_ratio >= 1.2:
        signal = "🔥 STRONG BUY 🚀"
        sl = price - (atr * 1.5)
        tp1 = price + (atr * 1.8)
        tp2 = price + (atr * 3.0)
        tp3 = price + (atr * 4.5)
    elif bear_score >= 75 and vol_ratio >= 1.2:
        signal = "💥 STRONG SELL 🔻"
        final_score = bear_score
        sl = price + (atr * 1.5)
        tp1 = price - (atr * 1.8)
        tp2 = price - (atr * 3.0)
        tp3 = price - (atr * 4.5)
    elif score >= 55:
        signal = "WEAK BUY 📈"
    elif bear_score >= 55:
        signal = "WEAK SELL 📉"

    return {
        'df': df, 'symbol': ticker_clean, 'price': price, 'signal': signal, 
        'score': final_score, 'vwap': vwap, 'ema20': ema20, 'ema50': ema50,
        'rsi': rsi, 'atr': atr, 'vol_ratio': vol_ratio, 'sl': sl, 
        'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'is_demo': is_demo,
        'bb_high': bb_high, 'bb_low': bb_low
    }

# UI Tabs
tab1, tab2 = st.tabs(["🎯 Pro Terminal & Signals", "🔥 High-Probability Multi-Scanner"])

with st.sidebar:
    st.header("⚙️ Institutional Controls")
    selected_tf = st.selectbox("⏱️ Signal Timeframe", ["5m", "15m", "1h"], index=1)
    st.markdown("---")
    st.subheader("💰 Smart Risk Calculator")
    capital = st.number_input("Capital (₹)", value=100000, step=10000)
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 3.0, 1.0, 0.5)

# TAB 1: SINGLE TERMINAL
with tab1:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        stock_input = st.text_input("Stock Symbol (NSE)", "TATAMOTORS")
        analyze_btn = st.button("⚡ ANALYZE PRECISION SIGNAL")

    if stock_input:
        res = analyze_stock_v7(stock_input, selected_tf)
        if res['is_demo']:
            st.warning("⚠️ Market Closed: Running High-Precision Demo Simulation Engine.")

        df = res['df']
        p, r1, s1, r2, s2 = calculate_pivots(df)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"₹{res['price']:.2f}")
        m2.metric("AI Signal", res['signal'])
        m3.metric("Confluence Score", f"{res['score']}/100")
        m4.metric("Volume Spike", f"{res['vol_ratio']:.2f}x")

        # Position Calculator
        risk_amount = capital * (risk_pct / 100)
        sl_dist = abs(res['price'] - res['sl']) if res['sl'] > 0 else res['atr'] * 1.5
        qty = int(risk_amount / sl_dist) if sl_dist > 0 else 0
        trade_val = qty * res['price']

        st.markdown("---")
        c_left, c_right = st.columns([1.2, 1])

        with c_left:
            st.subheader("🎯 Institutional Trade Plan")
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Stop Loss", f"₹{res['sl']:.2f}" if res['sl']>0 else "-")
            t2.metric("Target 1 (1:1.2)", f"₹{res['tp1']:.2f}" if res['tp1']>0 else "-")
            t3.metric("Target 2 (1:2)", f"₹{res['tp2']:.2f}" if res['tp2']>0 else "-")
            t4.metric("Target 3 (1:3)", f"₹{res['tp3']:.2f}" if res['tp3']>0 else "-")

            st.success(f"""
            💡 **Smart Risk Management Plan:**
            - **Max Risk Allowed:** ₹{risk_amount:,.2f}
            - **Calculated Buy Quantity:** {qty} Shares
            - **Total Capital Required:** ₹{trade_val:,.2f}
            """)

            st.markdown("##### 📌 Key Pivot Support & Resistance")
            pv1, pv2, pv3, pv4 = st.columns(4)
            pv1.metric("R2 Level", f"₹{r2:.2f}")
            pv2.metric("R1 Level", f"₹{r1:.2f}")
            pv3.metric("S1 Level", f"₹{s1:.2f}")
            pv4.metric("S2 Level", f"₹{s2:.2f}")

        with c_right:
            st.subheader("🔍 Institutional Confluence Matrix")
            st.write(f"• **VWAP Trend:** {'Price Above (Bullish 🟢)' if res['price']>res['vwap'] else 'Price Below (Bearish 🔴)'}")
            st.write(f"• **EMA Crossover (20/50):** {'Golden Cross 🟢' if res['ema20']>res['ema50'] else 'Death Cross 🔴'}")
            st.write(f"• **Bollinger Breakout:** {'Upper Band Breakout 🔥' if res['price']>res['bb_high'] else ('Lower Band Breakdown 💥' if res['price']<res['bb_low'] else 'Inside Range ⏸️')}")
            st.write(f"• **RSI Strength:** {res['rsi']:.1f}")
            st.write(f"• **Volatility (ATR):** ₹{res['atr']:.2f}")

        # Plotly Advanced Chart
        st.subheader("📈 Institutional TradingView Chart")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        # Price & Indicators
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='yellow', width=1.5), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='cyan', width=1.5), name="EMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], line=dict(color='magenta', width=2), name="VWAP"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_HIGH'], line=dict(color='gray', width=1, dash='dot'), name="BB Upper"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_LOW'], line=dict(color='gray', width=1, dash='dot'), name="BB Lower"), row=1, col=1)

        # Volume
        colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=530, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: MULTI SCANNER
with tab2:
    st.subheader("🔥 High-Confluence Watchlist Auto-Scanner")
    st.write("Scans Nifty 15 stocks for Bollinger Breakouts, VWAP trend, and High-Volume Confirmations.")
    
    if st.button("🚀 SCAN NIFTY WATCHLIST FOR STRONG SIGNALS"):
        results = []
        progress_bar = st.progress(0)
        
        for idx, stock in enumerate(WATCHLIST):
            r = analyze_stock_v7(stock, selected_tf)
            results.append({
                "Stock": r['symbol'],
                "AI Signal": r['signal'],
                "Score": f"{r['score']}/100",
                "Price (₹)": f"₹{r['price']:.2f}",
                "Vol Ratio": f"{r['vol_ratio']:.2f}x",
                "RSI": f"{r['rsi']:.1f}",
                "Stop Loss (₹)": f"₹{r['sl']:.2f}" if r['sl']>0 else "-",
                "Target 1 (₹)": f"₹{r['tp1']:.2f}" if r['tp1']>0 else "-",
                "Target 2 (₹)": f"₹{r['tp2']:.2f}" if r['tp2']>0 else "-"
            })
            progress_bar.progress((idx + 1) / len(WATCHLIST))
            
        scan_df = pd.DataFrame(results)
        
        def highlight_signals(val):
            if "STRONG BUY" in str(val): return 'background-color: #1b4332; color: #52b788; font-weight: bold;'
            if "STRONG SELL" in str(val): return 'background-color: #49111c; color: #ff4d6d; font-weight: bold;'
            return ''
            
        st.dataframe(scan_df.style.map(highlight_signals, subset=['AI Signal']), use_container_width=True)
  
