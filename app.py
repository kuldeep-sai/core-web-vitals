import streamlit as st
import requests
import pandas as pd
import concurrent.futures
from datetime import datetime

st.set_page_config(page_title="CWV Monitor", layout="wide")

st.title("🚀 Core Web Vitals Monitor")
st.write("Upload CSV to check CWV for Mobile + Desktop")

# ---------------- SAFE SECRET LOADER ---------------- #

API_KEY = None

try:
    API_KEY = st.secrets["PAGESPEED_API_KEY"]
except:
    st.error("❌ PageSpeed API Key NOT FOUND")

    st.info("""
Follow these steps:

1. Click **Manage App** (bottom right)
2. Go to **Settings → Secrets**
3. Delete everything inside the box
4. Paste EXACTLY this:

PAGESPEED_API_KEY="AIzaSyYOURKEYHERE"

5. Click SAVE
6. Click REBOOT APP
7. Wait 20–30 seconds
""")
    st.stop()

# ---------------------------------------------------- #

uploaded_file = st.file_uploader("Upload CSV (Column name must be: url)", type=["csv"])

strategies = ["mobile", "desktop"]

def check_cwv(url, strategy):

    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    params = {
        "url": url,
        "strategy": strategy,
        "key": API_KEY,
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
            "CLS": round(cls, 2),
            "INP (ms)": round(inp, 0),
            "FCP (s)": round(fcp, 2),
            "TTFB (ms)": round(ttfb, 0),
            "LCP Status": "Pass" if lcp <= 2.5 else "Fail",
            "CLS Status": "Pass" if cls <= 0.1 else "Fail",
            "INP Status": "Pass" if inp <= 200 else "Fail",
            "Date": datetime.now().date()
        }

    except:
        return {
            "URL": url,
            "Device": strategy,
            "Error": "Failed"
        }

if uploaded_file:

    urls = pd.read_csv(uploaded_file)["url"].dropna().tolist()

    st.info(f"Checking {len(urls)} URLs (Mobile + Desktop)...")

    results = []

    progress = st.progress(0)

    total_tasks = len(urls) * 2
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []

        for u in urls:
            for s in strategies:
                futures.append(executor.submit(check_cwv, u, s))

        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            completed += 1
            progress.progress(completed / total_tasks)

    df = pd.DataFrame(results)

    st.success("CWV Check Completed!")

    st.dataframe(df)

    st.subheader("📊 Average Performance Score")
    st.bar_chart(df.groupby("Device")["Performance Score"].mean())

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV Report",
        csv,
        f"cwv_report_{datetime.now().date()}.csv",
        "text/csv"
    )
