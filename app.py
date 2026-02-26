import streamlit as st
import requests
import pandas as pd
import concurrent.futures
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="CWV Monitor", layout="wide")
st.title("🚀 Core Web Vitals Monitor")

# ---------------- SAFE SECRET LOADER ---------------- #

API_KEY = None
try:
    API_KEY = st.secrets["PAGESPEED_API_KEY"]
except:
    st.error("❌ PageSpeed API Key NOT FOUND")
    st.stop()

# ---------------------------------------------------- #

# ----------- INPUT OPTIONS BACK AGAIN ----------- #

st.subheader("Upload URLs")

upload_col, paste_col = st.columns(2)

urls = []

with upload_col:
    uploaded_file = st.file_uploader("Upload CSV (Column name must be: url)", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        if "url" in df_upload.columns:
            urls = df_upload["url"].dropna().tolist()
        else:
            st.error("CSV must contain 'url' column")

with paste_col:
    text_urls = st.text_area("OR Paste URLs (one per line)")
    if text_urls:
        urls.extend(text_urls.split("\n"))

urls = list(set([u.strip() for u in urls if u.strip() != ""]))

# ---------------------------------------------- #

strategies = ["mobile", "desktop"]

def get_priority(lcp, cls, inp):
    score = 0
    if lcp > 4: score += 3
    elif lcp > 2.5: score += 2

    if cls > 0.25: score += 3
    elif cls > 0.1: score += 2

    if inp > 500: score += 3
    elif inp > 200: score += 2

    if score >= 6: return "🔥 High"
    elif score >= 3: return "⚠️ Medium"
    else: return "✅ Low"

def root_cause(lcp, cls, inp):
    issues = []
    if lcp > 2.5:
        issues.append("Slow LCP → Optimize images/server")
    if cls > 0.1:
        issues.append("Layout Shift → Fix dimensions/fonts")
    if inp > 200:
        issues.append("High INP → Reduce JS execution")
    return ", ".join(issues)

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

        return {
            "URL": url,
            "Device": strategy,
            "Score": round(score, 0),
            "LCP": round(lcp, 2),
            "CLS": round(cls, 2),
            "INP": round(inp, 0),
            "LCP ❌": "❌" if lcp > 2.5 else "✅",
            "CLS ❌": "❌" if cls > 0.1 else "✅",
            "INP ❌": "❌" if inp > 200 else "✅",
            "Fix Priority": get_priority(lcp, cls, inp),
            "Issue Caused By": root_cause(lcp, cls, inp),
            "Date": datetime.now().date()
        }

    except:
        return {"URL": url, "Device": strategy, "Score": 0}

if urls:
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

    mobile_df = df[df["Device"]=="mobile"]
    desktop_df = df[df["Device"]=="desktop"]

    # Display one after another
    st.subheader("📱 Mobile Report")
    st.dataframe(mobile_df)

    st.subheader("💻 Desktop Report")
    st.dataframe(desktop_df)

    st.subheader("📊 Average Performance Score")
    st.bar_chart(df.groupby("Device")["Score"].mean())

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV Report",
        csv,
        f"cwv_report_{datetime.now().date()}.csv",
        "text/csv"
    )
