import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import ta

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

WATCHLIST = [
    "TATAMOTORS", "RELIANCE", "SBIN", "ICICIBANK", "AXISBANK", 
    "HDFCBANK", "INFY", "TCS", "TATASTEEL", "BHARTIARTL", 
    "M&M", "NTPC", "LT", "SUNPHARMA", "MARUTI"
]

def send_telegram(msg):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        except Exception:
            pass

def run_auto_scan():
    for stock in WATCHLIST:
        try:
            df = yf.Ticker(f"{stock}.NS").history(period="1mo", interval="15m")
            if df.empty or len(df) < 20: 
                continue

            close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
            
            # Indicators
            tp = (high + low + close) / 3
            vwap = (tp * volume).cumsum() / volume.cumsum()
            ema20 = ta.trend.ema_indicator(close, window=20)
            ema50 = ta.trend.ema_indicator(close, window=50)
            rsi = ta.momentum.rsi(close, window=14)
            atr = ta.volatility.average_true_range(high, low, close, window=14)
            bb = ta.volatility.BollingerBands(close)
            
            latest = df.iloc[-1]
            price = float(latest['Close'])
            vol_sma = ta.trend.sma_indicator(volume, window=20).iloc[-1]
            vol_ratio = float(latest['Volume']) / float(vol_sma) if vol_sma > 0 else 1.0
            
            # Scoring logic
            score = 0
            if price > vwap.iloc[-1]: score += 20
            if ema20.iloc[-1] > ema50.iloc[-1]: score += 20
            if price > bb.bollinger_hband().iloc[-1]: score += 15
            if vol_ratio >= 1.5: score += 15
            if 50 <= rsi.iloc[-1] <= 70: score += 15

            bear_score = 0
            if price < vwap.iloc[-1]: bear_score += 20
            if ema20.iloc[-1] < ema50.iloc[-1]: bear_score += 20
            if price < bb.bollinger_lband().iloc[-1]: bear_score += 15
            if vol_ratio >= 1.5: bear_score += 15
            if 30 <= rsi.iloc[-1] <= 50: bear_score += 15

            curr_atr = float(atr.iloc[-1]) if not np.isnan(atr.iloc[-1]) else price * 0.01

            if score >= 75 and vol_ratio >= 1.2:
                sl, tp1 = price - (curr_atr * 1.5), price + (curr_atr * 1.8)
                msg = f"🔥 *AUTO ALERT: STRONG BUY* 🚀\n\n📌 *Stock:* {stock}\n💰 *Price:* ₹{price:.2f}\n🛑 *SL:* ₹{sl:.2f}\n🎯 *Target 1:* ₹{tp1:.2f}\n📊 *Score:* {score}/100"
                send_telegram(msg)
            elif bear_score >= 75 and vol_ratio >= 1.2:
                sl, tp1 = price + (curr_atr * 1.5), price - (curr_atr * 1.8)
                msg = f"💥 *AUTO ALERT: STRONG SELL* 🔻\n\n📌 *Stock:* {stock}\n💰 *Price:* ₹{price:.2f}\n🛑 *SL:* ₹{sl:.2f}\n🎯 *Target 1:* ₹{tp1:.2f}\n📊 *Score:* {bear_score}/100"
                send_telegram(msg)
        except Exception:
            continue

if __name__ == "__main__":
    run_auto_scan()
          
