# -*- coding: utf-8 -*-
"""
src/dashboard.py - Golden Master
- Elastic Firehose Logic: Min 30 items padding, OR absolute 48-hour flood.
"""
import streamlit as st

st.set_page_config(page_title="FINSIGHT AI TERMINAL", page_icon="📟", layout="wide", initial_sidebar_state="collapsed")

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
import json

try:
    from data_fetcher import *
    from agent_node import fetch_ai_analysis, fetch_exact_option_playbook, translate_news_headlines
    DATA_READY = True
except Exception as e:
    st.error(f"FATAL BOOT ERROR: {e}")
    DATA_READY = False

WLST_CONFIG_FILE = "user_watchlist.json"

if 'ticker' not in st.session_state: st.session_state.ticker = "SPY"
if 'lang' not in st.session_state: st.session_state.lang = "CN"
if 'cmd_error' not in st.session_state: st.session_state.cmd_error = ""

if 'custom_wlst' not in st.session_state: 
    default_wlst = ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "AMD"]
    if os.path.exists(WLST_CONFIG_FILE):
        try:
            with open(WLST_CONFIG_FILE, "r") as f:
                st.session_state.custom_wlst = json.load(f)
        except:
            st.session_state.custom_wlst = default_wlst
    else:
        st.session_state.custom_wlst = default_wlst

T = {
    "EN": {
        "des": "FUNDAMENTALS", "nws": "FEED", "nws_macro": "MARKET FEED",
        "adv": "ADVANCED TECHNICALS", "wlst": "CUSTOM WATCHLIST",
        "msg": "MACRO STRATEGIST", "omon": "EXECUTION DESK", "scan": "MACRO & AGENT LOGS",
        "btn": "\u26a1 GENERATE OPTION STRIKES", "edit": "\u2699\ufe0f EDIT WATCHLIST"
    },
    "CN": {
        "des": "\u6838\u5fc3\u57fa\u672c\u9762",
        "nws": "\u5b9e\u65f6\u8d44\u8baf",
        "nws_macro": "\u5168\u5e02\u573a\u5b8f\u89c2\u8d44\u8baf",
        "adv": "\u673a\u6784\u7ea7\u6280\u672f\u56fe\u8868",
        "wlst": "\u81ea\u5b9a\u4e49\u8d44\u91d1\u6d41\u5411\u6392\u540d",
        "msg": "AI \u5b8f\u89c2\u7b56\u7565\u5e08",
        "omon": "\u671f\u6743\u4ea4\u6613\u6218\u672f\u53f0",
        "scan": "\u5e95\u5c42\u96f7\u8fbe\u65e5\u5fd7",
        "btn": "\u26a1 \u70b9\u51fb\u751f\u6210\u671f\u6743\u65b9\u6848",
        "edit": "\u2699\ufe0f \u7f16\u8f91\u81ea\u9009\u80a1\u4ee3\u7801"
    }
}

def handle_cmd():
    cmd = st.session_state.cmd_in.upper().strip()
    if cmd: st.session_state.ticker = cmd

def update_wlst():
    raw_input = st.session_state.wlst_input
    cleaned = []
    for x in raw_input.split(","):
        t = x.strip().upper()
        if t and t not in cleaned:
            cleaned.append(t)
            
    st.session_state.custom_wlst = cleaned[:12]
    try:
        with open(WLST_CONFIG_FILE, "w") as f:
            json.dump(st.session_state.custom_wlst, f)
    except Exception as e:
        print(f"[SYS Warning] Failed to save config: {e}")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
    .stApp { background-color: #000000 !important; }
    html, body, p, .stMarkdown, table { font-family: 'Fira Code', monospace !important; color: #FFB000; font-size: 11px; line-height: 1.2; }
    .block-container { padding: 0.5rem !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    .stTextInput > div > div > input { background-color: #000044 !important; color: #00FF00 !important; border: 1px solid #FFB000 !important; border-radius: 0px !important; font-weight: bold !important; padding-left: 10px !important; }
    div[role="radiogroup"] { margin-top: -5px; gap: 0px; }
    table.bbg { width: 100%; border-collapse: collapse; margin-top: 2px;}
    table.bbg th, table.bbg td { border: 1px solid #222; padding: 1px 3px; text-align: right; font-size: 10px; color: #FFB000;}
    table.bbg th { background-color: #111; border-bottom: 2px solid #FFB000;}
    .cyan { color: #00FFFF !important; }
    .hdr { color: #FFB000; font-weight: bold; border-bottom: 1px solid #FFB000; display: block; margin-top: 3px; font-size: 12px;}
    .scroll { height: 52vh; overflow-y: auto; border: 1px solid #222; padding: 2px; }
    a { color: inherit !important; text-decoration: none !important; }
    a:hover { text-decoration: underline !important; color: #FFFFFF !important; }
    div[data-testid="stExpander"] details summary { border: 1px dashed #FF00FF !important; background-color: #110011 !important; }
    div[data-testid="stExpander"] details summary p { color: #FF00FF !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

def fmt_html(v, is_pct=False, is_px=False):
    p, s = ("$", "") if is_px else ("", "%" if is_pct else "")
    if isinstance(v, (int, float)):
        cls = "up" if v > 0 else ("down" if v < 0 else "cyan")
        return f"<span style='color:{'#00FF00' if v>0 else '#FF0000' if v<0 else '#00FFFF'}'>{' + ' if v>0 else ''}{p}{abs(v):,.2f}{s}</span>"
    return f"<span>{v}</span>"

def main():
    if not DATA_READY: return
    TICKER = st.session_state.ticker

    top_col1, top_col2 = st.columns([9, 1])
    with top_col1:
        st.text_input("CMD", key="cmd_in", on_change=handle_cmd, label_visibility="collapsed", placeholder=f"CMD> ENTER TICKER (NOW: {TICKER})")
    with top_col2:
        st.session_state.lang = st.radio("LANG", ["EN", "CN"], horizontal=True, label_visibility="collapsed", key="lang_radio")
        
    L = st.session_state.lang
    UI = T[L]
        
    macro = fetch_real_macro()
    vix = next((m[1] for m in macro if m[0]=="VIX"), 20.0)
    
    wlst_data = fetch_watchlist(st.session_state.custom_wlst)
    des = fetch_fundamentals(TICKER)
    chart = fetch_chart_data(TICKER)

    raw_news = fetch_macro_news() + fetch_live_news(TICKER)
    
    unique_news = []
    seen_links = set()
    for n in raw_news:
        if n['link'] not in seen_links:
            seen_links.add(n['link'])
            unique_news.append(n)
            
    sorted_news = sorted(unique_news, key=lambda x: x['timestamp'], reverse=True)
    
    # 🌟 CORE LOGIC: Elastic Throttling (Min 30 padding vs True 48h Firehose)
    current_ts = datetime.now().timestamp()
    cutoff_ts = current_ts - (48 * 3600)
    
    recent_48h_news = [n for n in sorted_news if n['timestamp'] >= cutoff_ts]
    
    if len(recent_48h_news) < 30:
        final_news_list = sorted_news[:30] # Pad with older news to guarantee 30 items
    else:
        final_news_list = recent_48h_news # Unleash the full 48-hour firehose
        
    combined_news = translate_news_headlines(final_news_list, L)

    m_html = "<div style='display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #333; font-size: 10px; margin-top:-5px; margin-bottom: 5px;'>"
    for name, val, chg, pct in macro: 
        m_html += f"<div>{name} <span style='color:#00FFFF'>{val:.2f}</span> {fmt_html(chg)} ({fmt_html(pct, True)})</div>"
    st.markdown(m_html + "</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2, 2.5, 1.3])
    
    with c1:
        st.markdown(f"<span class='hdr'>DES &lt;GO&gt; - {TICKER} {UI['des']}</span>", unsafe_allow_html=True)
        st.markdown(pd.DataFrame(list(des.items())).to_html(header=False, index=False, classes='bbg'), unsafe_allow_html=True)
        
        feed_title = f"{TICKER} {UI['nws']}" if TICKER != "SPY" else UI['nws_macro']
        st.markdown(f"<span class='hdr'>NWS &lt;GO&gt; - {feed_title}</span>", unsafe_allow_html=True)
        
        n_html = "<div class='scroll'>"
        # 🌟 UI renders the elastic list exactly as determined above
        for n in combined_news: 
            link_color = "#FF3333" if n.get('is_macro') and "GEO" in n.get('publisher', '') else ("#FFB000" if n.get('is_macro') else "#00FFFF")
            n_html += f"<div style='margin-bottom:4px; border-bottom:1px solid #222;'><span class='cyan'>[{n['time_str']}]</span> <a href='{n['link']}' target='_blank' style='color:{link_color};'>[{n['publisher']}] {n['headline']}</a></div>"
        st.markdown(n_html + "</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(f"<span class='hdr'>G &lt;GO&gt; - {TICKER} {UI['adv']}</span>", unsafe_allow_html=True)
        if not chart.empty:
            fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.45, 0.15, 0.20, 0.20])
            
            fig.add_trace(go.Candlestick(x=chart['Date'], open=chart['Open'], high=chart['High'], low=chart['Low'], close=chart['Close'], increasing_line_color='#00FF00', decreasing_line_color='#FF0000', showlegend=False), 1, 1)
            fig.add_trace(go.Scatter(x=chart['Date'], y=chart['SMA_20'], mode='lines', line=dict(color='#00FFFF', width=1), showlegend=False), 1, 1)
            
            fig.add_trace(go.Bar(x=chart['Date'], y=chart['Volume'], marker_color=['#00FF00' if r['Close']>=r['Open'] else '#FF0000' for _,r in chart.iterrows()], showlegend=False), 2, 1)
            
            if 'MACD_Hist' in chart.columns:
                fig.add_trace(go.Bar(x=chart['Date'], y=chart['MACD_Hist'], marker_color=['#00FF00' if val >= 0 else '#FF0000' for val in chart['MACD_Hist']], showlegend=False), 3, 1)
                fig.add_trace(go.Scatter(x=chart['Date'], y=chart['MACD'], mode='lines', line=dict(color='#00FFFF', width=1.2), showlegend=False), 3, 1)
                fig.add_trace(go.Scatter(x=chart['Date'], y=chart['MACD_Signal'], mode='lines', line=dict(color='#FFB000', width=1.2), showlegend=False), 3, 1)
            
            if 'RSI_14' in chart.columns:
                fig.add_trace(go.Scatter(x=chart['Date'], y=chart['RSI_14'], mode='lines', line=dict(color='#FFB000', width=1.5), showlegend=False), 4, 1)
                fig.add_hline(y=70, line_dash="dash", line_color="#FF0000", line_width=1, row=4, col=1) 
                fig.add_hline(y=30, line_dash="dash", line_color="#00FF00", line_width=1, row=4, col=1) 
            
            fig.update_layout(
                margin=dict(l=0,r=30,t=10,b=0), height=680, paper_bgcolor='#000', plot_bgcolor='#000', font=dict(color='#FFB000', size=9), 
                xaxis_rangeslider_visible=False, yaxis=dict(side='right', gridcolor='#1a1a1a'),
                yaxis2=dict(side='right', gridcolor='#1a1a1a'), yaxis3=dict(side='right', gridcolor='#1a1a1a'),
                yaxis4=dict(side='right', gridcolor='#1a1a1a', range=[0, 100], tickvals=[30, 70])
            )
            
            fig.update_xaxes(rangeselector=dict(buttons=list([dict(count=1, label="1M", step="month", stepmode="backward"), dict(count=3, label="3M", step="month", stepmode="backward"), dict(count=6, label="6M", step="month", stepmode="backward"), dict(step="all", label="1Y")]), bgcolor="#111", activecolor="#333", font=dict(color="#FFB000", size=10)), row=1, col=1)
            fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
        else:
            st.warning("NO CHART DATA.")

    with c3:
        st.markdown(f"<span class='hdr'>WLST &lt;GO&gt; - {UI['wlst']}</span>", unsafe_allow_html=True)
        
        w_html = "<table class='bbg'><tr><th>TKR</th><th>LAST</th><th>CHG%</th></tr>"
        for w in wlst_data: w_html += f"<tr><td>{w['TICKER']}</td><td>{fmt_html(w['LAST'],is_px=True)}</td><td>{fmt_html(w['CHG%'],True)}</td></tr>"
        st.markdown(w_html + "</table>", unsafe_allow_html=True)
        
        with st.expander(UI['edit']):
            st.text_input("TICKERS:", key="wlst_input", value=", ".join(st.session_state.custom_wlst), on_change=update_wlst, label_visibility="collapsed", placeholder="e.g., AAPL, SOFI, TSLA")

        st.markdown(f"<span class='hdr'>MSG &lt;GO&gt; - {TICKER} {UI['msg']}</span>", unsafe_allow_html=True)
        latest = chart['Close'].iloc[-1] if not chart.empty else 0.0
        analysis = fetch_ai_analysis(TICKER, latest, 0, 0, 0, des.get("EARNINGS", "N/A"), vix, combined_news, L)
        if "PLAYBOOK:" in analysis: analysis = analysis.replace("PLAYBOOK:", "<br><br><span style='color:#FF00FF; text-decoration: underline;'>MACRO PLAYBOOK:</span>")
        st.markdown(f"<div style='color:#00FFFF; border:1px solid #00FFFF; padding:8px; font-size:10px;'>{analysis}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<span class='hdr'>OMON &lt;GO&gt; - {UI['omon']}</span>", unsafe_allow_html=True)
        with st.expander(UI['btn']):
            chain = fetch_target_options_chain(TICKER, latest)
            if chain:
                plan = fetch_exact_option_playbook(TICKER, latest, chain, analysis, L)
                clean = plan.replace("\n", "<br>").replace("STRATEGY:", "<span style='color:#FF00FF;'>[STRATEGY]</span>").replace("EXECUTION:", "<br><br><span style='color:#00FF00;'>[EXECUTION]</span>").replace("RATIONALE:", "<br><br><span style='color:#00FFFF;'>[RATIONALE]</span>")
                st.markdown(f"<div style='border:1px dashed #FF00FF; padding:10px; font-size:11px; background-color:#1a001a;'>{clean}</div>", unsafe_allow_html=True)

    st.markdown(f"<span class='hdr'>SCAN &lt;GO&gt; - {UI['scan']}</span>", unsafe_allow_html=True)
    l_html = "<div class='log-box'>"
    for i, n in enumerate(combined_news[:3]):
        l_html += f"<div style='color:#FF3333;'>[{datetime.now().strftime('%H:%M:%S')}] [RADAR] Macro intercept: {n['headline'][:60]}...</div>"
    st.markdown(l_html + "</div>", unsafe_allow_html=True)

if __name__ == "__main__": main()