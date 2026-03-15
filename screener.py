import requests
import pandas as pd
import streamlit as st
import anthropic
import json

FMP_API_KEY = "dt8bltqqKLrikCzikk12UtcJtZQ96iQC"
GNEWS_API_KEY = "4c66b654872af7e4152dceb707628974"
ANTHROPIC_API_KEY = "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"

companies = ["AAPL", "RIVN", "SHOP", "TSLA", "F", "BA", "INTC", "NKLA", "BYND", "GME"]

company_names = {
    "AAPL": "Apple", "RIVN": "Rivian", "SHOP": "Shopify",
    "TSLA": "Tesla", "F": "Ford", "BA": "Boeing",
    "INTC": "Intel", "NKLA": "Nikola", "BYND": "Beyond Meat", "GME": "GameStop"
}

st.title("🔍 Distressed Asset Screener")
st.write("Combines live financial data with AI-powered news sentiment analysis.")

def get_financial_score(company):
    try:
        url = f"https://financialmodelingprep.com/stable/ratios?symbol={company}&apikey={FMP_API_KEY}"
        data = requests.get(url).json()
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
            return score, round(debt_equity,2), round(current_ratio,2), round(profit_margin,2), round(debt_assets,2)
    except:
        pass
    return 0, 0, 0, 0, 0

def get_news_headlines(company_name):
    try:
        url = f"https://gnews.io/api/v4/search?q={company_name}+stock&lang=en&max=5&apikey={GNEWS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        articles = data.get("articles", [])
        headlines = [a["title"] for a in articles if "title" in a]
        return headlines
    except:
        return []

def get_sentiment_score(company_name, headlines):
    if not headlines:
        return 0, "No recent news found."
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        headlines_text = "\n".join([f"- {h}" for h in headlines])
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""Analyse these recent news headlines for {company_name}.
Return ONLY a raw JSON object with no extra text, no markdown, no backticks.
Use this exact format: {{"score": 0, "summary": "one sentence"}}
Score range: -20 (very bad news) to +20 (very good news), 0 is neutral.

Headlines:
{headlines_text}"""
            }]
        )
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return result.get("score", 0), result.get("summary", "")
    except Exception as e:
        return 0, f"Sentiment unavailable."

@st.cache_data
def fetch_all_data():
    results = []
    for company in companies:
        name = company_names.get(company, company)
        fin_score, de, cr, pm, da = get_financial_score(company)
        if fin_score == 0 and de == 0:
            continue
        headlines = get_news_headlines(name)
        sentiment_score, sentiment_summary = get_sentiment_score(name, headlines)
        final_score = max(0, fin_score - sentiment_score)
        results.append({
            "Ticker": company,
            "Company": name,
            "Financial Score": fin_score,
            "Sentiment Score": sentiment_score,
            "Distress Score": final_score,
            "Debt/Equity": de,
            "Current Ratio": cr,
            "Profit Margin": pm,
            "News Summary": sentiment_summary
        })
    return pd.DataFrame(results).sort_values("Distress Score", ascending=False)

with st.spinner("Fetching financial data and analysing news sentiment with AI..."):
    df = fetch_all_data()

def color_score(val):
    if val >= 60: return "background-color: #ff4444; color: white"
    elif val >= 30: return "background-color: #ffaa00; color: white"
    else: return "background-color: #00cc44; color: white"

st.subheader("📊 Company Rankings")
display_cols = ["Ticker", "Company", "Financial Score", "Sentiment Score", "Distress Score"]
styled = df[display_cols].style.map(color_score, subset=["Distress Score"])
st.dataframe(styled, use_container_width=True)

st.subheader("📈 Distress Score Chart")
st.bar_chart(df.set_index("Company")["Distress Score"])

st.subheader("🔎 Company Detail")
selected = st.selectbox("Select a company", df["Company"].tolist())
row = df[df["Company"] == selected].iloc[0]
col1, col2, col3 = st.columns(3)
col1.metric("Distress Score", row["Distress Score"])
col2.metric("Financial Score", row["Financial Score"])
col3.metric("Sentiment Score", row["Sentiment Score"])
st.info(f"📰 News Summary: {row['News Summary']}")
