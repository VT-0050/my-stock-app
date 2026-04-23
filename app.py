import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 引入 CNN 指數套件
try:
    from fear_and_greed import CNNFearAndGreedIndex
except ImportError:
    CNNFearAndGreedIndex = None

st.set_page_config(page_title="核心資產配置監控", layout="wide")

# --- 數據抓取工具 ---
def get_single_price(ticker_symbol):
    """ 強制抓取單一股票最新價格 """
    try:
        df = yf.download(ticker_symbol, period="5d", progress=False)
        if not df.empty:
            # 解決多層索引問題，只取 Close 欄位最後一個值
            val = df['Close'].iloc[-1]
            return float(val)
    except:
        pass
    return 0.0

def get_stock_df(ticker_symbol):
    """ 抓取 K 線圖用的資料表 """
    try:
        df = yf.download(ticker_symbol, period="1y", progress=False)
        # 強制攤平索引，避免繪圖錯誤
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 標題與側邊欄 ---
st.title("📈 核心資產配置監控")
st.sidebar.header("💰 投資配置設定")
total_budget = st.sidebar.number_input("請輸入預計投入總金額 (台幣)", value=1000000, step=10000)

# --- 1. 顯示上方數據看板 ---
col1, col2, col3 = st.columns(3)

with col1:
    rate = get_single_price("TWD=X")
    st.metric("💵 台幣對美金匯率", f"{rate:.2f}" if rate > 0 else "讀取中")

with col2:
    vix = get_single_price("^VIX")
    st.metric("😱 VIX 恐慌指數", f"{vix:.2f}" if vix > 0 else "讀取中", 
              delta="市場不安" if vix > 20 else "市場平穩", delta_color="inverse")

with col3:
    try:
        cnn_fg = CNNFearAndGreedIndex()
        fg_val = int(cnn_fg.index_summary.value)
        fg_desc = cnn_fg.index_summary.description
        st.metric("📊 CNN 恐懼貪婪指數", f"{fg_val} - {fg_desc}")
    except:
        st.metric("📊 CNN 恐懼貪婪指數", "網站維護中")

# --- 2. 配置建議計算 ---
st.divider()
st.subheader("📊 投資配置試算 (0050 vs VT)")
c1, c2 = st.columns(2)

def show_allocation(ratio_name, r1, r2):
    st.info(f"建議比例 {ratio_name}")
    st.write(f"📍 0050 應投入: **{total_budget * r1:,.0f}** 元")
    st.write(f"📍 VT 應投入: **{total_budget * r2:,.0f}** 元")

with c1: show_allocation("3 : 7 (穩健型)", 0.3, 0.7)
with c2: show_allocation("4 : 6 (標準型)", 0.4, 0.6)

# --- 3. 繪製圖表 ---
st.divider()
target_map = {"0050": "0050.TW", "VT (全世界股市)": "VT", "VIX (恐慌指數)": "^VIX"}
target_name = st.selectbox("切換查看歷史 K 線圖", list(target_map.keys()))

plot_df = get_stock_df(target_map[target_name])

if not plot_df.empty:
    fig = go.Figure(data=[go.Candlestick(
                    x=plot_df.index,
                    open=plot_df['Open'], high=plot_df['High'],
                    low=plot_df['Low'], close=plot_df['Close'],
                    name='K線')])
    fig.update_layout(title=f"{target_name} 歷史走勢", xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
    st.plotly_chart(fig, width='stretch')
else:
    st.warning("數據抓取頻率過高，請稍等一分鐘後重新整理網頁")

