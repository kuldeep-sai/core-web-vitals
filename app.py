import streamlit as st
import requests
import pandas as pd
import concurrent.futures
import time
from datetime import datetime

st.set_page_config(page_title="CWV Monitor - Free", layout="wide")

st.title("🚀 Core Web Vitals Monitor (FREE)")
st.write("Upload CSV with column name: url")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

strategies = ["mobile", "desktop"]

# -------- CWV CHECK FUNCTION -------- #

def check_cwv(url, strategy):

    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    params = {
        "url": url,
        "strategy": strategy,
        "category": "performance"
    }

    try:
        r = requests.get(endpoint, params=params).json()

        audits = r["lighthouseResult"]["audits"]
        score = r["lighthouseResult"]["categories"]["performance"]["score"] * 100

        lcp = audits["largest-contentful-paint"]["numericValue"] / 1000
        cls = audits["cumulative-layout-shift"]["numericValue"]
        inp = audits.get("interaction-to-next-paint", {}).get("numericValue", 0)
        fcp = audits["first-contentful-paint"]["numericValue"] / 1000
        ttfb = audits["server-response-time"]["numericValue"]

        return {
            "URL": url,
            "Device": strategy,
            "Performance Score": round(score, 0),
            "LCP (s)": round(lcp, 2),
            "CLS": round(cls, 3),
            "INP (ms)": round(inp, 0),
            "FCP (s)": round(fcp, 2),
            "TTFB (ms)": round(ttfb, 0),
            "LCP Status": "Pass" if lcp <= 2.5 else "Fail",
            "CLS Status": "Pass" if cls <= 0.1 else "Fail",
            "INP Status": "Pass" if inp <= 200 else "Fail",
            "Checked On": datetime.now().date()
        }

    except:
        return {
            "URL": url,
            "Device": strategy,
            "Error": "Failed"
        }

# -------- BULK RUN -------- #

if uploaded_file:

    df_urls = pd.read_csv(uploaded_file)

    if "url" not in df_urls.columns:
        st.error("CSV must have column name: url")
        st.stop()

    urls = df_urls["url"].dropna().tolist()

    st.info(f"Checking {len(urls)} URLs (Mobile + Desktop)...")

    results = []
    progress = st.progress(0)

    total_tasks = len(urls) * 2
    completed = 0

    for url in urls:
        for strategy in strategies:
            result = check_cwv(url, strategy)
            results.append(result)

            completed += 1
            progress.progress(completed / total_tasks)

            time.sleep(2)   # FREE MODE RATE LIMIT PROTECTION

    df = pd.DataFrame(results)

    st.success("CWV Check Completed!")

    st.dataframe(df)

    st.subheader("📊 Avg Performance Score")
    st.bar_chart(df.groupby("Device")["Performance Score"].mean())

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV Report",
        csv,
        f"cwv_report_{datetime.now().date()}.csv",
        "text/csv"
    )
