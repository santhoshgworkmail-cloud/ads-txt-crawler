from flask import Flask, request, render_template, Response
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        urls = request.form["urls"].split("\n")
        lines = request.form["lines"].split("\n")
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

            except:
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

        # ✅ Email भेजना (optional)
        if email and "@" in email:
            send_email_report(email.strip(), results)

    return render_template("index.html", results=results)


# ✅ Email Function
def send_email_report(to_email, results):
    body = "Ads.txt Scan Report\n\n"

    current_url = ""
    for row in results:
        if row["url"] != current_url:
            current_url = row["url"]
            body += f"\nURL: {current_url}\n"

        status = "FOUND" if row["status"] else "MISSING"
        body += f"  - {row['line']} → {status}\n"

    msg = MIMEText(body)
    msg["Subject"] = "Ads.txt Scan Report"
    msg["From"] = "Santhoshg.workmail@gmail.com"
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("Santhoshg.workmail@gmail.com", "hofa hkra tekl ltbl")
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email failed:", e)


# ✅ CSV Function
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


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
