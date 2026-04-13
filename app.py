from flask import Flask, request, render_template, Response
import requests
from io import StringIO
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 🔥 Fetch function (parallel-safe)
def fetch_url(url):
    try:
        if not url.endswith("/ads.txt"):
            url = url.rstrip("/") + "/ads.txt"

        response = requests.get(url, headers=HEADERS, timeout=2)
        return url, response.text.lower()
    except:
        return url, ""

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        lines = request.form.get("lines", "").split("\n")

        urls = [u.strip() for u in urls if u.strip()]

        # 🔥 Parallel execution (IMPORTANT)
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_url = {executor.submit(fetch_url, url): url for url in urls}

            for future in as_completed(future_to_url):
                url, content = future.result()

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    results.append({
                        "url": url,
                        "line": line,
                        "status": line.lower() in content
                    })

        # ✅ CSV download
        if request.form.get("download") == "csv":
            return generate_csv(results)

    return render_template("index.html", results=results)

# ✅ CSV generation
def generate_csv(results):
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    writer.writerow(["URL", "Line", "Status"])

    for r in results:
        writer.writerow([
            r["url"],
            r["line"],
            "FOUND" if r["status"] else "MISSING"
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ads-txt-report.csv"}
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)