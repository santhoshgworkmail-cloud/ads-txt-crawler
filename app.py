from flask import Flask, request, render_template, Response
import requests
from io import StringIO
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# ✅ Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ✅ Function to normalize URL
def normalize_url(url):
    url = url.strip()
    if not url:
        return None

    # Add protocol if missing
    if not url.startswith("http"):
        url = "http://" + url

    # Only append ads.txt if not already a .txt file
    if not url.endswith(".txt"):
        url = url.rstrip("/") + "/ads.txt"

    return url

# ✅ Fetch function (parallel)
def fetch_url(url):
    try:
        final_url = normalize_url(url)
        if not final_url:
            return url, ""

        response = requests.get(final_url, headers=HEADERS, timeout=2)
        return final_url, response.text.lower()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return url, ""

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        lines = request.form.get("lines", "").split("\n")

        urls = [u.strip() for u in urls if u.strip()]

        # 🔥 Parallel execution
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_url, url) for url in urls]

            for future in as_completed(futures):
                final_url, content = future.result()

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    results.append({
                        "url": final_url,
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

# ✅ Run locally
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)