import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Core Web Vitals Diagnostic Tool")

API_KEY = "YOUR_API_KEY"

def get_psi_data(url, strategy):
    endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "key": API_KEY
    }
    response = requests.get(endpoint, params=params)
    return response.json()

def extract_metrics(data):
    audits = data['lighthouseResult']['audits']

    metrics = {
        "LCP": audits['largest-contentful-paint']['displayValue'],
        "CLS": audits['cumulative-layout-shift']['displayValue'],
        "INP": audits.get('interactive', {}).get('displayValue', "NA"),
        "FCP": audits['first-contentful-paint']['displayValue'],
        "TBT": audits['total-blocking-time']['displayValue'],
        "Speed Index": audits['speed-index']['displayValue']
    }

    scores = {
        "LCP": audits['largest-contentful-paint']['score'],
        "CLS": audits['cumulative-layout-shift']['score'],
        "INP": audits.get('interactive', {}).get('score', 0),
        "FCP": audits['first-contentful-paint']['score'],
        "TBT": audits['total-blocking-time']['score'],
        "Speed Index": audits['speed-index']['score']
    }

    return metrics, scores


def status_icon(score):
    if score >= 0.9:
        return "🟢"
    elif score >= 0.5:
        return "🟠"
    else:
        return "🔴"


def priority(score):
    if score >= 0.9:
        return 1
    elif score >= 0.5:
        return 2
    else:
        return 3


def create_table(metrics, scores):
    df = pd.DataFrame({
        "Metric": metrics.keys(),
        "Value": metrics.values(),
        "Status": [status_icon(scores[m]) for m in metrics.keys()],
        "Fix Priority": [priority(scores[m]) for m in metrics.keys()]
    }).sort_values(by="Fix Priority", ascending=False)

    return df


def root_cause(df):
    causes = []
    for _, row in df.iterrows():
        if row['Status'] == "🔴":
            if row['Metric'] == "LCP":
                causes.append(["LCP", "Heavy Images / Slow Server Response"])
            if row['Metric'] == "CLS":
                causes.append(["CLS", "Layout Shift due to Ads/Fonts"])
            if row['Metric'] == "INP":
                causes.append(["INP", "Heavy JS Execution"])
            if row['Metric'] == "TBT":
                causes.append(["TBT", "Render Blocking JS"])
            if row['Metric'] == "FCP":
                causes.append(["FCP", "Unused CSS/JS"])
            if row['Metric'] == "Speed Index":
                causes.append(["Speed Index", "Above the Fold Delay"])
    return pd.DataFrame(causes, columns=["Failing Metric", "Possible Cause"])


url = st.text_input("Enter URL")

if st.button("Run CWV Test"):

    mobile_data = get_psi_data(url, "mobile")
    desktop_data = get_psi_data(url, "desktop")

    mob_metrics, mob_scores = extract_metrics(mobile_data)
    desk_metrics, desk_scores = extract_metrics(desktop_data)

    mob_table = create_table(mob_metrics, mob_scores)
    desk_table = create_table(desk_metrics, desk_scores)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Mobile CWV Report")
        st.table(mob_table)

    with col2:
        st.subheader("Desktop CWV Report")
        st.table(desk_table)

    st.subheader("CWV Priority Chart")

    chart_data = pd.DataFrame({
        'Mobile': [priority(mob_scores[m]) for m in mob_metrics.keys()],
        'Desktop': [priority(desk_scores[m]) for m in desk_metrics.keys()]
    }, index=mob_metrics.keys())

    fig, ax = plt.subplots()
    chart_data.plot(kind='bar', ax=ax)
    st.pyplot(fig)

    st.subheader("Root Cause Detection")

    mob_causes = root_cause(mob_table)
    desk_causes = root_cause(desk_table)

    col3, col4 = st.columns(2)

    with col3:
        st.write("Mobile Issues")
        st.table(mob_causes)

    with col4:
        st.write("Desktop Issues")
        st.table(desk_causes)
