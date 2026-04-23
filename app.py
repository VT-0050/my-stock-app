import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 針對新版 fear-and-greed 套件的引入方式 ---
try:
    from fear_and_greed import CNNFearAndGreedIndex
except ImportError:
    CNNFearAndGreedIndex = None

st.set_page_config(page_title="核心資產配置監控", layout="wide")

# --- 1. 數據抓取函式 ---
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {
        "0050": "0050.TW",
        "VT (全世界股市)": "VT",
        "VIX (恐慌指數)": "^VIX",
        "台幣/美金匯率": "TWD=X"
    }
    data = {}
    for name, sym in tickers.items():
        df = yf.download(sym, period="1y")
        data[name] = df
    return data

@st.cache_data(ttl=3600)
def get_fear_greed_data():
    if CNNFearAndGreedIndex is None:
        return None
    try:
        cnn_fg = CNNFearAndGreedIndex()
        return cnn_fg.index_summary # 包含 value 和 description 的物件
    except:
        return None

# 執行抓取
data_dict = get_market_data()
fg_data = get_fear_greed_data()

# --- 標題與側邊欄 ---
st.title("📈 核心資產配置監控")
st.sidebar.header("💰 投資配置設定")
total_budget = st.sidebar.number_input("請輸入預計投入總金額 (台幣)", value=1000000, step=10000)

# --- 2. 顯示上方數據看板 (Top Metrics) ---
col1, col2, col3 = st.columns(3)

with col1:
    rate_df = data_dict["台幣/美金匯率"]
    if not rate_df.empty:
        val = float(rate_df['Close'].iloc[-1])
        st.metric("💵 台幣對美金匯率", f"{val:.2f}")

with col2:
    vix_df = data_dict["VIX (恐慌指數)"]
    if not vix_df.empty:
        val = float(vix_df['Close'].iloc[-1])
        # VIX 超過 20 通常代表市場較不安
        st.metric("😱 VIX 恐慌指數", f"{val:.2f}", delta="市場不安" if val > 20 else "市場平穩", delta_color="inverse")

with col3:
    if fg_data:
        val = int(fg_data.value)
        desc = fg_data.description
        st.metric("📊 CNN 恐懼貪婪指數", f"{val} - {desc}")
    else:
        st.metric("📊 CNN 恐懼貪婪指數", "讀取中/暫不支援")

# --- 3. 配置建議計算 ---
st.divider()
st.subheader("📊 投資配置試算 (0050 vs VT)")
c1, c2 = st.columns(2)

def show_allocation(ratio_name, r1, r2):
    st.info(f"建議比例 {ratio_name}")
    amt_0050 = total_budget * r1
    amt_vt = total_budget * r2
    st.write(f"📍 0050 應投入: **{amt_0050:,.0f}** 元")
    st.write(f"📍 VT 應投入: **{amt_vt:,.0f}** 元")

with c1:
    show_allocation("3 : 7 (穩健型)", 0.3, 0.7)
with c2:
    show_allocation("4 : 6 (標準型)", 0.4, 0.6)

# --- 4. 繪製圖表 ---
st.divider()
target_stock = st.selectbox("切換查看歷史 K 線圖", ["0050", "VT (全世界股市)", "VIX (恐慌指數)"])
plot_df = data_dict[target_stock]

if not plot_df.empty:
    fig = go.Figure(data=[go.Candlestick(x=plot_df.index,
                    open=plot_df['Open'], high=plot_df['High'],
                    low=plot_df['Low'], close=plot_df['Close'], name='K線')])

    fig.update_layout(
        title=f"{target_stock} 歷史走勢",
        xaxis_rangeslider_visible=False,
        template="plotly_dark", # 改為深色主題看起來更專業
        height=500
    )
    # 使用最新語法 width='stretch' 替代 use_container_width
    st.plotly_chart(fig, width='stretch')
else:
    st.warning("暫時無法取得該股票圖表數據")

# 明細數據表格
with st.expander("查看最近五日數據明細"):
    st.write(plot_df.tail(5))
