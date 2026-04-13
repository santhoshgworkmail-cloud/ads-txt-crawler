from flask import Flask, request, render_template, Response
import requests
import smtplib
from email.mime.text import MIMEText
import os
from io import StringIO
import csv

app = Flask(__name__)

# ✅ Environment variables for email credentials
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")

# ✅ Common headers to avoid bot blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        lines = request.form.get("lines", "").split("\n")
        user_email = request.form.get("email")

        for url in urls:
            url = url.strip()
            if not url:
                continue

            # 👉 Ensure ads.txt path
            if not url.endswith("/ads.txt"):
                url = url.rstrip("/") + "/ads.txt"

            try:
                response = requests.get(url, headers=HEADERS, timeout=5)
                content = response.text.lower()

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    results.append({
                        "url": url,
                        "line": line,
                        "status": line.lower() in content
                    })

            except Exception as e:
                print(f"Error fetching {url}: {e}")

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    results.append({
                        "url": url,
                        "line": line,
                        "status": False
                    })

        # ✅ CSV download
        if request.form.get("download") == "csv":
            return generate_csv(results)

        # ✅ Send email (only if credentials exist)
        if user_email and "@" in user_email and EMAIL and PASSWORD:
            send_email_report(user_email.strip(), results)

    return render_template("index.html", results=results)

# ✅ Email function
def send_email_report(to_email, results):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)

        message_text = "\n".join(
            [
                f"URL: {r['url']}\nLine: {r['line']}\nStatus: {'FOUND' if r['status'] else 'MISSING'}\n"
                for r in results
            ]
        )

        msg = MIMEText(message_text)
        msg["Subject"] = "Your ads.txt report"
        msg["From"] = EMAIL
        msg["To"] = to_email

        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()

        print(f"Email successfully sent to {to_email}")

    except Exception as e:
        print("Email failed:", e)

# ✅ CSV generation (FIXED)
def generate_csv(results):
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Header
    writer.writerow(["URL", "Line", "Status"])

    # Data
    for r in results:
        writer.writerow([
            r["url"],
            r["line"],
            "FOUND" if r["status"] else "MISSING"
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ads-txt-report.csv"}
    )

    return response

# ✅ Local run (Render will ignore this and use Gunicorn)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)