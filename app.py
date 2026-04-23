import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# 網頁基本設定
st.set_page_config(page_title="核心資產配置監控", layout="wide")

# --- 1. 數據抓取工具 ---

def get_data_safely(ticker_symbol):
    """ 強力處理 yfinance 抓取與多層索引問題 """
    try:
        # 抓取最近 5 天資料確保能取到最新收盤價
        df = yf.download(ticker_symbol, period="5d", progress=False)
        if df.empty:
            return None
        
        # 處理 Yahoo 最近改版的多層索引 (Multi-Index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except:
        return None

def get_fng_index():
    """ 抓取市場恐懼貪婪指數 (替代 CNN 穩定方案) """
    try:
        # Alternative.me 提供的公開 API，不容易被封鎖
        response = requests.get("https://alternative.me", timeout=5)
        if response.status_code == 200:
            data = response.json()['data'][0]
            return data['value'], data['value_classification']
    except:
        pass
    return None, "讀取中"

# --- 2. 標題與側邊欄 ---
st.title("📈 核心資產配置監控")
st.sidebar.header("💰 投資配置設定")
total_budget = st.sidebar.number_input("請輸入總投入金額 (台幣)", value=1000000, step=10000)

# --- 3. 顯示頂部數據看板 ---
col1, col2, col3 = st.columns(3)

with col1:
    rate_df = get_data_safely("TWD=X")
    if rate_df is not None:
        val = float(rate_df['Close'].iloc[-1])
        st.metric("💵 台幣對美金匯率", f"{val:.2f}")
    else:
        st.metric("💵 台幣對美金匯率", "Yahoo 讀取中")

with col2:
    vix_df = get_data_safely("^VIX")
    if vix_df is not None:
        val = float(vix_df['Close'].iloc[-1])
        st.metric("😱 VIX 恐慌指數", f"{val:.2f}", 
                  delta="市場不安" if val > 20 else "市場平穩", delta_color="inverse")
    else:
        st.metric("😱 VIX 恐慌指數", "讀取中")

with col3:
    fng_val, fng_desc = get_fng_index()
    if fng_val:
        st.metric("📊 市場恐懼貪婪指數", f"{fng_val} - {fng_desc}")
    else:
        # 若 API 也失敗，提供手動查看連結
        st.markdown("[🔗 **點此手動查看 CNN 指數**](https://cnn.com)")
        st.metric("📊 市場恐懼貪婪指數", fng_desc)

# --- 4. 配置建議計算 ---
st.divider()
st.subheader("📊 投資配置試算 (0050 vs VT)")
c1, c2 = st.columns(2)

def show_allocation(ratio_name, r1, r2):
    with st.container():
        st.info(f"建議比例 {ratio_name}")
        col_a, col_b = st.columns(2)
        col_a.write(f"📍 0050 應投入:")
        col_a.subheader(f"{total_budget * r1:,.0f} 元")
        col_b.write(f"📍 VT 應投入:")
        col_b.subheader(f"{total_budget * r2:,.0f} 元")

with c1: show_allocation("3 : 7 (穩健型)", 0.3, 0.7)
with c2: show_allocation("4 : 6 (標準型)", 0.4, 0.6)

# --- 5. 繪製歷史圖表 ---
st.divider()
target_map = {"0050": "0050.TW", "VT (全世界股市)": "VT", "VIX (恐慌指數)": "^VIX"}
target_name = st.selectbox("切換查看歷史 K 線圖", list(target_map.keys()))

# 抓取一年資料繪圖
plot_df = yf.download(target_map[target_name], period="1y", progress=False)
if isinstance(plot_df.columns, pd.MultiIndex):
    plot_df.columns = plot_df.columns.get_level_values(0)

if not plot_df.empty:
    fig = go.Figure(data=[go.Candlestick(
                    x=plot_df.index,
                    open=plot_df['Open'], high=plot_df['High'],
                    low=plot_df['Low'], close=plot_df['Close'],
                    name='K線')])
    fig.update_layout(
        title=f"{target_name} 歷史走勢", 
        xaxis_rangeslider_visible=False, 
        template="plotly_dark", 
        height=500
    )
    st.plotly_chart(fig, width='stretch')
else:
    st.warning("Yahoo 數據請求過於頻繁，請等待 1 分鐘後重新整理頁面。")

with st.expander("查看最近五日數據明細"):
    st.write(plot_df.tail(5))
