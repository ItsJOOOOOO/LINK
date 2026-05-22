from flask import Flask, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route('/')
def home():

    return jsonify({
        "status": "running",
        "usage": "/fetch/<url>"
    })


@app.route('/fetch/<path:url>')
def fetch(url):

    # إضافة https لو مش موجود
    if not url.startswith("http"):
        url = "https://" + url

    found_callback = None

    try:

        with sync_playwright() as p:

            # تشغيل Chromium الموجود على Render
            browser = p.chromium.launch(
                headless=True,
                executable_path="/usr/bin/chromium",
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

            page = browser.new_page()

            # مراقبة الـ responses
            def handle_response(response):

                nonlocal found_callback

                response_url = response.url

                # لو فيه callback
                if "callback" in response_url and not found_callback:

                    found_callback = response_url

            page.on("response", handle_response)

            try:

                page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=60000
                )

            except:
                pass

            browser.close()

        return jsonify({
            "callback": found_callback
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
