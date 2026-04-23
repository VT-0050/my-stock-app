import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
# 針對新版 fear-and-greed 套件的引入方式
try:
    from fear_and_greed import CNNFearAndGreedIndex
except ImportError:
    CNNFearAndGreedIndex = None

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
        # 自動抓取最近一年的資料
        df = yf.download(sym, period="1y")
        data[name] = df
    return data

@st.cache_data(ttl=3600)
def get_fear_greed():
    if CNNFearAndGreedIndex is None:
        return "套件未正確安裝"
    try:
        cnn_fg = CNNFearAndGreedIndex()
        # 取得當前指數文字描述與數值
        return str(cnn_fg.get_index().split('\n')[0]) 
    except:
        return "CNN 官網讀取中..."

data_dict = get_market_data()
fg_text = get_fear_greed()

# --- 2. 顯示即時關鍵數據 (Top Row) ---
col1, col2, col3 = st.columns(3)

with col1:
    # 匯率處理：確保抓到最新一筆非空值
    rate_df = data_dict["台幣/美金匯率"]
    if not rate_df.empty:
        current_rate = rate_df['Close'].iloc[-1]
        # 處理 yfinance 可能回傳的多維數據
        final_rate = float(current_rate.iloc[0]) if hasattr(current_rate, 'iloc') else float(current_rate)
        st.metric("💵 台幣對美金匯率", f"{final_rate:.2f}")
    else:
        st.metric("💵 台幣對美金匯率", "維護中")

with col2:
    vix_df = data_dict["VIX (恐慌指數)"]
    if not vix_df.empty:
        vix_val = vix_df['Close'].iloc[-1]
        final_vix = float(vix_val.iloc[0]) if hasattr(vix_val, 'iloc') else float(vix_val)
        st.metric("😱 VIX 恐慌指數", f"{final_vix:.2f}")

with col3:
    st.metric("📊 CNN 恐懼貪婪指數", fg_text)
    st.caption("數值越高越貪婪，越低越恐懼")

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
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("暫時無法取得該股票圖表數據")

# 顯示數據表格
with st.expander("查看最近五日數據明細"):
    st.write(plot_df.tail(5))
