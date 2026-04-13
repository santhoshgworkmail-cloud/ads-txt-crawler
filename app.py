from flask import Flask, request, render_template, Response
import requests
from io import StringIO
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ✅ Clean function (VERY IMPORTANT FIX)
def clean(line):
    line = line.replace("\xa0", " ")  # fixes hidden spaces
    parts = [p.strip().lower() for p in line.split(",") if p.strip()]
    return parts[:3]  # domain, id, type

# ✅ Normalize URL
def normalize_url(url):
    url = url.strip()

    if not url.startswith("http"):
        url = "http://" + url

    if not url.endswith(".txt"):
        url = url.rstrip("/") + "/ads.txt"

    return url

# ✅ Fetch URL safely
def fetch(url):
    try:
        final_url = normalize_url(url)
        r = requests.get(final_url, headers=HEADERS, timeout=5, allow_redirects=True)
        return final_url, r.text
    except Exception:
        return url, ""

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        lines = request.form.get("lines", "").split("\n")

        urls = [u.strip() for u in urls if u.strip()]
        lines = [l.strip() for l in lines if l.strip()]

        # 🔥 Parallel fetch (fast for 1000 URLs)
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch, url) for url in urls]

            for future in as_completed(futures):
                final_url, content = future.result()

                # clean file lines
                file_lines = [
                    clean(l)
                    for l in content.splitlines()
                    if l.strip() and not l.strip().startswith("#")
                ]

                for line in lines:
                    input_line = clean(line)

                    found = False

                    for f in file_lines:
                        if len(f) >= 3 and len(input_line) >= 3:
                            if (
                                f[0] == input_line[0] and
                                f[1] == input_line[1] and
                                f[2] == input_line[2]
                            ):
                                found = True
                                break

                    results.append({
                        "url": final_url,
                        "line": line,
                        "status": found
                    })

    return render_template("index.html", results=results)

# ✅ CSV download
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
    app.run(host="0.0.0.0", port=10000, debug=True)