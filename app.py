from flask import Flask, request, render_template, Response
import requests
import os
from io import StringIO
import csv

app = Flask(__name__)

# ✅ Headers to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        urls = urls[:10]  # ✅ limit to avoid timeout

        lines = request.form.get("lines", "").split("\n")

        for url in urls:
            url = url.strip()
            if not url:
                continue

            # ✅ Ensure ads.txt path
            if not url.endswith("/ads.txt"):
                url = url.rstrip("/") + "/ads.txt"

            try:
                response = requests.get(url, headers=HEADERS, timeout=2)
                content = response.text.lower()
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                content = ""

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

# ✅ Local run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)