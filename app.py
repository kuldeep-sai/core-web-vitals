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

1. Click Manage App (bottom right)
2. Go to Settings → Secrets
3. Delete everything inside the box
4. Paste EXACTLY this:

PAGESPEED_API_KEY="AIzaSyYOURKEYHERE"

5. Click SAVE
6. Click REBOOT APP
7. Wait 20–30 seconds
""")
    st.stop()

# ---------------------------------------------------- #

strategies = ["mobile", "desktop"]

# METRIC STATUS ICON LOGIC

def metric_status(metric, value):

    if metric == "LCP":
        if value <= 2.5:
            return "🟢"
        elif value <= 4:
            return "🟡"
        else:
            return "🔴"

    if metric == "INP":
        if value <= 200:
            return "🟢"
        elif value <= 500:
            return "🟡"
        else:
            return "🔴"

    if metric == "CLS":
        if value <= 0.1:
            return "🟢"
        elif value <= 0.25:
            return "🟡"
        else:
            return "🔴"


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

        lcp_status = metric_status("LCP", lcp)
        cls_status = metric_status("CLS", cls)
        inp_status = metric_status("INP", inp)

        failed_metrics = []

        if lcp_status != "🟢":
            failed_metrics.append("LCP")

        if cls_status != "🟢":
            failed_metrics.append("CLS")

        if inp_status != "🟢":
            failed_metrics.append("INP")

        overall_cwv = "✅" if len(failed_metrics) == 0 else "❌"

        return {
            "URL": url,
            "Device": strategy,
            "Performance Score": round(score, 0),

            "LCP (s)": round(lcp, 2),
            "LCP Status": lcp_status,

            "INP (ms)": round(inp, 0),
            "INP Status": inp_status,

            "CLS": round(cls, 2),
            "CLS Status": cls_status,

            "CWV Overall": overall_cwv,
            "CWV Failed Due To": ", ".join(failed_metrics) if failed_metrics else "None",

            "FCP (s)": round(fcp, 2),
            "TTFB (ms)": round(ttfb, 0),
            "Date": datetime.now().date()
        }

    except:
        return {
            "URL": url,
            "Device": strategy,
            "Error": "Failed"
        }

uploaded_file = st.file_uploader("Upload CSV (Column name must be: url)", type=["csv"])

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
