from flask import Flask, request, render_template, Response
import requests
from io import StringIO
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# ✅ Headers to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ✅ Normalize URL
def normalize_url(url):
    url = url.strip()
    if not url:
        return None

    if not url.startswith("http"):
        url = "http://" + url

    if not url.endswith(".txt"):
        url = url.rstrip("/") + "/ads.txt"

    return url

# ✅ Normalize text (important for matching)
def normalize_text(text):
    return text.lower().replace(" ", "").replace("\t", "")

# ✅ Fetch content
def fetch_url(url):
    try:
        final_url = normalize_url(url)
        if not final_url:
            return url, ""

        response = requests.get(final_url, headers=HEADERS, timeout=3)
        return final_url, response.text
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
        lines = [l.strip() for l in lines if l.strip()]

        # 🔥 Parallel processing
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_url, url) for url in urls]

            for future in as_completed(futures):
                final_url, content = future.result()

                # Normalize content lines once
                content_lines = [
                    normalize_text(line)
                    for line in content.splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]

                for line in lines:
                    clean_line = normalize_text(line)

                    # ✅ Improved matching logic
                    found = any(clean_line in cl for cl in content_lines)

                    results.append({
                        "url": final_url,
                        "line": line,
                        "status": found
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
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)