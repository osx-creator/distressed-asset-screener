import requests
import pandas as pd
import streamlit as st

API_KEY = "dt8bltqqKLrikCzikk12UtcJtZQ96iQC"

companies = ["AAPL", "RIVN", "SHOP", "TSLA", "F", "BA", "INTC", "NKLA", "BYND", "GME"]

st.title("🔍 Distressed Asset Screener")
st.write("Automatically scans companies for signs of financial distress using live data.")

@st.cache_data
def fetch_data():
    results = []
    for company in companies:
        try:
            url = f"https://financialmodelingprep.com/stable/ratios?symbol={company}&apikey={API_KEY}"
            response = requests.get(url)
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                latest = data[0]

                debt_equity = latest.get("debtToEquityRatio") or 0
                current_ratio = latest.get("currentRatio") or 0
                profit_margin = latest.get("netProfitMargin") or 0
                debt_assets = latest.get("debtToAssetsRatio") or 0

                score = 0
                if debt_equity > 2: score += 30
                elif debt_equity > 1: score += 15
                if current_ratio < 1: score += 30
                elif current_ratio < 1.5: score += 15
                if profit_margin < 0: score += 25
                elif profit_margin < 0.05: score += 10
                if debt_assets > 0.6: score += 15
                elif debt_assets > 0.4: score += 8

                results.append({
                    "Company": company,
                    "Debt/Equity": round(debt_equity, 2),
                    "Current Ratio": round(current_ratio, 2),
                    "Profit Margin": round(profit_margin, 2),
                    "Debt/Assets": round(debt_assets, 2),
                    "Distress Score": score
                })
        except Exception:
            pass
    return pd.DataFrame(results).sort_values("Distress Score", ascending=False)

with st.spinner("Fetching live financial data..."):
    df = fetch_data()

def color_score(val):
    if val >= 60: return "background-color: #ff4444; color: white"
    elif val >= 30: return "background-color: #ffaa00; color: white"
    else: return "background-color: #00cc44; color: white"

st.subheader("📊 Company Rankings")
styled = df.style.applymap(color_score, subset=["Distress Score"])
st.dataframe(styled, use_container_width=True)

st.subheader("📈 Distress Score Chart")
st.bar_chart(df.set_index("Company")["Distress Score"])

st.subheader("🔎 Company Detail")
selected = st.selectbox("Select a company to inspect", df["Company"].tolist())
row = df[df["Company"] == selected].iloc[0]
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Distress Score", row["Distress Score"])
col2.metric("Debt/Equity", row["Debt/Equity"])
col3.metric("Current Ratio", row["Current Ratio"])
col4.metric("Profit Margin", row["Profit Margin"])
col5.metric("Debt/Assets", row["Debt/Assets"])