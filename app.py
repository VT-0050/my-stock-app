import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 引入 CNN 指數套件
try:
    from fear_and_greed import CNNFearAndGreedIndex
except:
    CNNFearAndGreedIndex = None

st.set_page_config(page_title="核心資產配置監控", layout="wide")

def fix_yf_dataframe(df):
    """ 強力處理 yfinance 的多層索引問題 """
    if df.empty:
        return df
    # 如果標題是多層的 (MultiIndex)，只保留第一層 (例如把 ('Close', 'VT') 變成 'Close')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_single_price(ticker_symbol):
    """ 抓取單一數值專用 """
    try:
        df = yf.download(ticker_symbol, period="5d", progress=False)
        df = fix_yf_dataframe(df)
        if not df.empty and 'Close' in df.columns:
            return float(df['Close'].iloc[-1])
    except:
        pass
    return None

# --- 標題與側邊欄 ---
st.title("📈 核心資產配置監控")
st.sidebar.header("💰 投資配置設定")
total_budget = st.sidebar.number_input("請輸入總金額 (台幣)", value=1000000)

# --- 1. 數據看板 ---
col1, col2, col3 = st.columns(3)

with col1:
    rate = get_single_price("TWD=X")
    if rate:
        st.metric("💵 台幣對美金匯率", f"{rate:.2f}")
    else:
        st.metric("💵 台幣對美金匯率", "維修中", help="Yahoo API 暫時阻擋，請稍後")

with col2:
    vix = get_single_price("^VIX")
    if vix:
        st.metric("😱 VIX 恐慌指數", f"{vix:.2f}", 
                  delta="市場不安" if vix > 20 else "市場平穩", delta_color="inverse")
    else:
        st.metric("😱 VIX 恐慌指數", "讀取中")

with col3:
    try:
        cnn_fg = CNNFearAndGreedIndex()
        indicator = cnn_fg.index_summary
        st.metric("📊 CNN 恐懼貪婪指數", f"{int(indicator.value)} - {indicator.description}")
    except:
        st.metric("📊 CNN 恐懼貪婪指數", "網站維修中")

# --- 2. 配置建議 ---
st.divider()
st.subheader("📊 投資配置試算 (0050 vs VT)")
c1, c2 = st.columns(2)
with c1:
    st.info("建議比例 3 : 7")
    st.write(f"📍 0050: **{total_budget*0.3:,.0f}** | VT: **{total_budget*0.7:,.0f}**")
with c2:
    st.info("建議比例 4 : 6")
    st.write(f"📍 0050: **{total_budget*0.4:,.0f}** | VT: **{total_budget*0.6:,.0f}**")

# --- 3. K 線圖 ---
st.divider()
target_map = {"0050": "0050.TW", "VT (全世界股市)": "VT", "VIX (恐慌指數)": "^VIX"}
target_name = st.selectbox("切換查看圖表", list(target_map.keys()))

plot_df = yf.download(target_map[target_name], period="1y", progress=False)
plot_df = fix_yf_dataframe(plot_df)

if not plot_df.empty and 'Close' in plot_df.columns:
    fig = go.Figure(data=[go.Candlestick(
                    x=plot_df.index,
                    open=plot_df['Open'], high=plot_df['High'],
                    low=plot_df['Low'], close=plot_df['Close'])])
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=450)
    st.plotly_chart(fig, width='stretch')
else:
    st.warning("Yahoo 數據暫時無法讀取，請一分鐘後重新整理頁面。")

