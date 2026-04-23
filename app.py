import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from fear_greed_index.CNNFearAndGreedIndex import CNNFearAndGreedIndex

st.set_page_config(page_title="家人專屬看盤室", layout="wide")

# --- 標題與側邊欄設定 ---
st.title("📈 核心資產配置監控")
st.sidebar.header("💰 投資配置設定")

# 設定投入總金額
total_budget = st.sidebar.number_input("請輸入預計投入總金額 (台幣)", value=1000000, step=10000)

# --- 1. 抓取數據 (包含匯率與 CNN 指數) ---
@st.cache_data(ttl=3600) # 快取一小時
def get_market_data():
    tickers = {
        "0050": "0050.TW",
        "VT (全世界股市)": "VT",
        "VIX (恐慌指數)": "^VIX",
        "台幣/美金匯率": "TWD=X"
    }
    data = {}
    for name, sym in tickers.items():
        data[name] = yf.download(sym, period="1y")
    return data

@st.cache_data(ttl=3600)
def get_fear_greed():
    try:
        cnn_fg = CNNFearAndGreedIndex()
        return cnn_fg.get_index() # 回傳包含 value 和 description 的字串
    except:
        return "無法取得數據"

data_dict = get_market_data()
fg_text = get_fear_greed()

# --- 2. 顯示即時關鍵數據 (Top Row) ---
col1, col2, col3 = st.columns(3)
with col1:
    rate = data_dict["台幣/美金匯率"]['Close'].iloc[-1]
    # 如果 yfinance 抓取的是多維度 Dataframe，確保取到單一數值
    rate_val = float(rate.iloc[0]) if isinstance(rate, pd.Series) else float(rate)
    st.metric("💵 台幣對美金匯率", f"{rate_val:.2f}")

with col2:
    vix = data_dict["VIX (恐慌指數)"]['Close'].iloc[-1]
    vix_val = float(vix.iloc[0]) if isinstance(vix, pd.Series) else float(vix)
    st.metric("😱 VIX 恐慌指數", f"{vix_val:.2f}")

with col3:
    st.metric("📊 CNN 恐懼貪婪指數", fg_text)
    st.caption("數值越高越貪婪，越低越恐懼")

# --- 3. 配置建議計算 ---
st.subheader("📊 投資配置試算 (0050 vs VT)")
c1, c2 = st.columns(2)

def show_allocation(ratio_name, r1, r2):
    st.info(f"建議比例 {ratio_name}")
    amt_0050 = total_budget * r1
    amt_vt = total_budget * r2
    st.write(f"📍 0050 應投入: **{amt_0050:,.0f}** 元")
    st.write(f"📍 VT 應投入: **{amt_vt:,.0f}** 元")

with c1:
    show_allocation("3 : 7", 0.3, 0.7)
with c2:
    show_allocation("4 : 6", 0.4, 0.6)

# --- 4. 繪製圖表 ---
st.divider()
target_stock = st.selectbox("切換查看 K 線圖", ["0050", "VT (全世界股市)", "VIX (恐慌指數)"])
plot_df = data_dict[target_stock]

fig = go.Figure(data=[go.Candlestick(x=plot_df.index,
                open=plot_df['Open'], high=plot_df['High'],
                low=plot_df['Low'], close=plot_df['Close'], name='K線')])

fig.update_layout(title=f"{target_stock} 歷史走勢", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# 顯示數據表格
st.subheader("最近數據細節")
st.write(plot_df.tail(5))
