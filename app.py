from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "status": "running"
    })


@app.route("/fetch")
def fetch():

    url = request.args.get("url")

    if not url:
        return jsonify({
            "success": False,
            "error": "Missing url parameter"
        }), 400

    if not url.startswith("http"):
        url = "https://" + url

    found_callback = None

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                executable_path="/ms-playwright/chromium-1223/chrome-linux64/chrome",
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )

            page = browser.new_page()

            def handle_response(response):

                nonlocal found_callback

                response_url = response.url

                if "callback" in response_url:
                    found_callback = response_url

            page.on("response", handle_response)

            page.goto(
                url,
                wait_until="load",
                timeout=60000
            )

            page.wait_for_timeout(8000)

            browser.close()

        return jsonify({
            "success": True,
            "callback": found_callback
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
