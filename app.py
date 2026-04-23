import requests # 確保程式碼最上方有 import requests

with col3:
    try:
        # 改用 Alternative.me 提供的 Crypto/Market Fear & Greed API (這是公開且穩定的)
        response = requests.get("https://alternative.me", timeout=5)
        if response.status_code == 200:
            fng_data = response.json()['data'][0]
            fg_val = fng_data['value']
            fg_desc = fng_data['value_classification']
            st.metric("📊 市場恐懼貪婪指數", f"{fg_val} - {fg_desc}")
        else:
            st.metric("📊 市場恐懼貪婪指數", "API 請求過多")
    except:
        # 如果 API 也失敗，提供一個手動查看連結
        st.markdown("[🔗 **點此手動查看 CNN 指數**](https://cnn.com)")
        st.metric("📊 市場恐懼貪婪指數", "讀取失敗")

