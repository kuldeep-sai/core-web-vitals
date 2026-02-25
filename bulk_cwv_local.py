import requests
import pandas as pd
import time

urls = pd.read_csv("urls.csv")["url"].tolist()

strategies = ["mobile","desktop"]

results = []

for url in urls:
    for strategy in strategies:

        endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

        params = {
            "url": url,
            "strategy": strategy,
            "category": "performance"
        }

        try:
            r = requests.get(endpoint, params=params)

            if r.status_code != 200:
                print("Blocked:",url)
                continue

            data = r.json()

            if "lighthouseResult" not in data:
                continue

            audits = data["lighthouseResult"]["audits"]
            score = data["lighthouseResult"]["categories"]["performance"]["score"] * 100

            lcp = audits["largest-contentful-paint"]["numericValue"]/1000
            cls = audits["cumulative-layout-shift"]["numericValue"]

            results.append({
                "URL":url,
                "Device":strategy,
                "Performance Score":score,
                "LCP":lcp,
                "CLS":cls
            })

            print("Done:",url,strategy)

        except:
            print("Error:",url)

        time.sleep(2)

df=pd.DataFrame(results)
df.to_csv("cwv_report.csv",index=False)
print("REPORT READY")
