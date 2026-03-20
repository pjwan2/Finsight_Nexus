# -*- coding: utf-8 -*-
"""
src/data_fetcher.py - Production Stable Edition
- Removed all custom threading/sessions. Relies on yfinance's native mechanisms.
- Disables multi-threading (threads=False) to prevent Streamlit Deadlocks.
- Uses /tmp strictly for GCP read-only filesystem compatibility.
"""
import os
# 必须在导入 yfinance 之前设置，解决 GCP 只读系统报错
os.environ["YFINANCE_CACHE_DIR"] = "/tmp/yfinance_cache"

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

# 让 yfinance 自己在 /tmp 管理时区缓存
try:
    yf.set_tz_cache_location("/tmp/yfinance_tz")
except Exception:
    pass

FALLBACK_SECTOR_MAP = {
    "XLK": {"name": "Technology", "top": ["MSFT", "AAPL", "NVDA", "AVGO", "ADBE", "CRM", "AMD", "CSCO", "INTC", "ORCL"]},
    "XLF": {"name": "Financials", "top": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "C", "BLK"]},
    "XLV": {"name": "Healthcare", "top": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "TMO", "AMGN", "DHR", "PFE", "ISRG"]},
    "XLY": {"name": "Consumer Discretionary", "top": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "BKNG", "TJX", "CMG"]},
    "XLC": {"name": "Communication", "top": ["META", "GOOGL", "GOOG", "NFLX", "DIS", "CMCSA", "VZ", "T", "CHTR", "EA"]},
    "XLI": {"name": "Industrials", "top": ["GE", "CAT", "UBER", "BA", "UNP", "HON", "RTX", "UPS", "LMT", "DE"]},
    "XLP": {"name": "Consumer Staples", "top": ["PG", "COST", "KO", "PEP", "WMT", "PM", "MDLZ", "MO", "CL", "EL"]},
    "XLE": {"name": "Energy", "top": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY", "WMB"]},
    "XLU": {"name": "Utilities", "top": ["NEE", "SO", "DUK", "SRE", "AEP", "D", "EXC", "PCG", "XEL", "ED"]},
    "XLRE": {"name": "Real Estate", "top": ["PLD", "AMT", "EQIX", "WELL", "SPG", "PSA", "O", "CCI", "DLR", "CSGP"]},
    "XLB": {"name": "Materials", "top": ["LIN", "SHW", "FCX", "ECL", "NEM", "APD", "DOW", "DD", "CTVA", "VMC"]}
}

CROSS_ASSET_MAP = {
    "CRYPTO": {"name": "Cryptocurrencies", "top": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD"]},
    "COMMODITY": {"name": "Commodities & Metals", "top": ["GLD", "SLV", "USO", "UNG", "CPER", "DBA", "PPLT", "PDBC"]},
    "BONDS": {"name": "Treasury & Yields", "top": ["TLT", "IEF", "SHY", "BND", "AGG", "LQD", "HYG", "TIP"]}
}

@st.cache_data(ttl=86400, show_spinner=False) 
def get_dynamic_sector_map():
    # 业界成熟方案：仪表盘数据源尽量静态化，避免无意义的并发请求导致风控封锁
    return FALLBACK_SECTOR_MAP

@st.cache_data(ttl=300, show_spinner=False)
def fetch_real_macro():
    symbols = ["SPY", "QQQ", "^VIX", "^TNX"]
    results = []
    try:
        # 核心：threads=False 防止 Streamlit 在云端死锁
        data = yf.download(symbols, period="5d", interval="1d", progress=False, threads=False)['Close']
        for sym in symbols:
            if sym in data.columns and len(data[sym].dropna()) >= 2:
                series = data[sym].dropna()
                curr, prev = series.iloc[-1], series.iloc[-2]
                name = sym.replace("^", "")
                if name == "TNX": name = "US10Y"
                results.append((name, curr, curr - prev, ((curr - prev) / prev) * 100))
            else: results.append((sym, 0, 0, 0))
    except: results = [("SPX",0,0,0), ("NDX",0,0,0), ("US10Y",0,0,0), ("VIX",0,0,0)]
    return results

@st.cache_data(ttl=600, show_spinner=False)
def fetch_sector_performance():
    etfs = list(FALLBACK_SECTOR_MAP.keys())
    perf = []
    try:
        data = yf.download(etfs, period="2d", interval="1d", progress=False, threads=False)['Close']
        for etf in etfs:
            if etf in data.columns and len(data[etf].dropna()) >= 2:
                series = data[etf].dropna()
                pct = ((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]) * 100
                perf.append({"ETF": etf, "NAME": FALLBACK_SECTOR_MAP[etf]["name"], "CHG": pct})
    except: pass
    return sorted(perf, key=lambda x: abs(x["CHG"]), reverse=True)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamentals(ticker: str):
    if ticker.upper() == "SPY": return {"MKT CAP": "BROAD MARKET", "P/E": "N/A", "BETA": "1.00", "EARNINGS": "N/A", "DIV YLD": "N/A"}
    try:
        info = yf.Ticker(ticker).info
        def fmt(n):
            if not n: return "N/A"
            if n >= 1e12: return f"{n/1e12:.2f}T"
            if n >= 1e9: return f"{n/1e9:.2f}B"
            return f"{n/1e6:.2f}M"
            
        earn_ts = info.get('earningsTimestamp')
        earn_date = datetime.fromtimestamp(earn_ts).strftime('%Y-%m-%d') if earn_ts else "N/A"
        
        return {
            "MKT CAP": fmt(info.get('marketCap')), 
            "P/E": f"{info.get('trailingPE', 0):.2f}x", 
            "EARNINGS": earn_date, 
            "BETA": f"{info.get('beta', 0):.2f}", 
            "DIV YLD": f"{info.get('dividendYield', 0)*100:.2f}%"
        }
    except: return {"MKT CAP": "N/A", "P/E": "N/A", "EARNINGS": "N/A", "BETA": "N/A", "DIV YLD": "N/A"}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart_data(ticker: str):
    try:
        df = yf.Ticker(ticker).history(period="1y").reset_index()
        df.rename(columns={'Datetime': 'Date'}, inplace=True, errors='ignore')
        if df.empty: return pd.DataFrame()
        
        df['SMA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        
        delta = df['Close'].diff()
        gain, loss = delta.where(delta > 0, 0), -delta.where(delta < 0, 0)
        rs = gain.ewm(com=13, min_periods=14).mean() / loss.ewm(com=13, min_periods=14).mean()
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        return df.bfill().ffill()
    except: return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro_news():
    try:
        query = "Federal+Reserve+OR+Powell+OR+Interest+Rates+OR+Inflation+OR+Geopolitics+OR+War"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=5.0) as resp:
            root = ET.fromstring(resp.read())
        
        items = []
        for item in root.findall('./channel/item'):
            try:
                dt = parsedate_to_datetime(item.find('pubDate').text)
                ts = dt.timestamp()
                time_str = dt.astimezone().strftime("%m-%d %H:%M")
                items.append({'timestamp': ts, 'time_str': time_str, 'publisher': "MACRO", 'headline': item.find('title').text.upper(), 'link': item.find('link').text, 'is_macro': True})
            except: continue
        return items
    except: return []

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_news(ticker: str):
    try:
        query = f"{ticker}+stock" if ticker.upper() != "SPY" else "Stock+Market"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=5.0) as resp:
            root = ET.fromstring(resp.read())
            
        items = []
        for item in root.findall('./channel/item'):
            try:
                dt = parsedate_to_datetime(item.find('pubDate').text)
                ts = dt.timestamp()
                time_str = dt.astimezone().strftime("%m-%d %H:%M")
                items.append({'timestamp': ts, 'time_str': time_str, 'publisher': "NEWS", 'headline': item.find('title').text.upper(), 'link': item.find('link').text, 'is_macro': False})
            except: continue
        return items
    except: return []

@st.cache_data(ttl=60, show_spinner=False)
def fetch_watchlist(symbols):
    res = []
    try:
        data = yf.download(symbols, period="2d", interval="1d", progress=False, threads=False)['Close']
        for s in symbols:
            if s in data.columns:
                cp, pp = data[s].dropna().iloc[-1], data[s].dropna().iloc[-2]
                res.append({"TICKER": s, "LAST": cp, "CHG%": ((cp-pp)/pp)*100})
    except: pass
    return res

@st.cache_data(ttl=600, show_spinner=False)
def fetch_target_options_chain(ticker, current_price):
    try:
        t = yf.Ticker(ticker)
        exps = t.options
        if not exps: return {}
        now = datetime.now()
        theta_exp, leap_exp = exps[0], exps[-1]
        for exp in exps:
            if 30 <= (datetime.strptime(exp, '%Y-%m-%d') - now).days <= 60: theta_exp = exp; break
        for exp in reversed(exps):
            if 150 <= (datetime.strptime(exp, '%Y-%m-%d') - now).days <= 250: leap_exp = exp; break
        
        c_theta = t.option_chain(theta_exp)
        p_theta = c_theta.puts[(c_theta.puts['strike'] >= current_price * 0.8) & (c_theta.puts['strike'] <= current_price * 1.2)]
        
        c_leap = t.option_chain(leap_exp)
        cl_leap = c_leap.calls[(c_leap.calls['strike'] >= current_price * 0.8) & (c_leap.calls['strike'] <= current_price * 1.2)]
        
        return {
            "THETA_DTE": theta_exp,
            "THETA_DATA": f"PUTS: {', '.join([f'Strike {r.strike} Ask ${r.ask:.2f}' for _, r in p_theta.iterrows()])}",
            "LEAP_DTE": leap_exp,
            "LEAP_DATA": f"CALLS: {', '.join([f'Strike {r.strike} Ask ${r.ask:.2f}' for _, r in cl_leap.iterrows()])}"
        }
    except: return {}