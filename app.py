import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 網頁標題
st.set_page_config(page_title="我的簡易看盤工具", layout="wide")
st.title("📈 簡易投資看盤 APP")

# 側邊欄設定
st.sidebar.header("設定")
stock_id = st.sidebar.text_input("輸入股票代碼 (台股請加 .TW)", value="2330.TW")
period = st.sidebar.selectbox("選擇時間範圍", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

# 抓取資料
try:
    df = yf.download(stock_id, period=period)
    
    if df.empty:
        st.error("找不到該股票資料，請檢查代碼是否正確。")
    else:
        # 計算移動平均線
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        # 繪製 K 線圖 (使用 Plotly 讓圖表可以縮放)
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='K線')])
        
        # 加入均線
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20日均線', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='60日均線', line=dict(color='blue', width=1)))

        st.plotly_chart(fig, use_container_width=True)

        # 顯示最近幾天的數據表格
        st.subheader("最近五日數據")
        st.write(df.tail(5))

except Exception as e:
    st.error(f"發生錯誤: {e}")
