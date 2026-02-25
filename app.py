import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="CWV Monitor - Free", layout="wide")

st.title("🚀 Core Web Vitals Monitor (FREE)")
st.write("Upload CSV with column name: url")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

strategies = ["mobile", "desktop"]

def check_cwv(url, strategy):

    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    params = {
        "url": url,
        "strategy": strategy,
        "category": "performance"
    }

    try:
        r = requests.get(endpoint, params=params)

        if r.status_code != 200:
            return {"URL": url, "Device": strategy, "Error": "Blocked"}

        data = r.json()

        if "lighthouseResult" not in data:
            return {"URL": url, "Device": strategy, "Error": "No Data"}

        audits = data["lighthouseResult"]["audits"]
        score = data["lighthouseResult"]["categories"]["performance"]["score"] * 100

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
            "Status": "Success",
            "Checked On": datetime.now().date()
        }

    except:
        return {"URL": url, "Device": strategy, "Error": "Failed"}

# -------- RUN -------- #

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
            results.append(check_cwv(url, strategy))

            completed += 1
            progress.progress(completed / total_tasks)

            time.sleep(2)

    df = pd.DataFrame(results)

    st.success("CWV Check Completed!")

    st.dataframe(df)

    # -------- SAFE CHART -------- #

    if "Performance Score" in df.columns:

        success_df = df[df.get("Status") == "Success"]

        if not success_df.empty:

            st.subheader("📊 Avg Performance Score")
            st.bar_chart(success_df.groupby("Device")["Performance Score"].mean())

        else:
            st.warning("All URLs blocked by Google (rate limit). Try again later.")

    else:
        st.warning("Google blocked requests. Reduce URLs or retry later.")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV Report",
        csv,
        f"cwv_report_{datetime.now().date()}.csv",
        "text/csv"
    )
