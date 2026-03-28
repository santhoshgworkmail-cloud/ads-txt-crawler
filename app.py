from flask import Flask, request, render_template, Response
import requests
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

# ✅ Environment variables for email credentials
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form.get("urls", "").split("\n")
        lines = request.form.get("lines", "").split("\n")
        email = request.form.get("email")

        for url in urls:
            url = url.strip()
            if not url:
                continue

            try:
                response = requests.get(url, timeout=5)
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

        # ✅ CSV Download
        if request.form.get("download") == "csv":
            return generate_csv(results)

        # ✅ Send email report if email is valid and credentials exist
        if email and "@" in email and EMAIL and PASSWORD:
            send_email_report(email.strip(), results)

    return render_template("index.html", results=results)

# ✅ Email sending function (secured)
def send_email_report(to_email, results):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)

        message_text = "\n".join(
            [f"URL: {r['url']}, Line: {r['line']}, Found: {r['status']}" for r in results]
        )

        msg = MIMEText(message_text)
        msg["Subject"] = "Your ads.txt report"
        msg["From"] = EMAIL
        msg["To"] = to_email

        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("Email failed:", e)

# ✅ CSV generation function
def generate_csv(results):
    def generate():
        data = [["URL", "Line", "Status"]]
        for row in results:
            data.append([
                row["url"],
                row["line"],
                "FOUND" if row["status"] else "MISSING"
            ])
        for row in data:
            yield ",".join(row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=report.csv"}
    )

# ✅ Main block for Render deployment
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
