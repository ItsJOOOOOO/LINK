from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

@app.route("/")
def home():

    return jsonify({
        "status": "running"
    })


@app.route("/test")
def test():

    return jsonify({
        "playwright_browsers_path": os.environ.get("PLAYWRIGHT_BROWSERS_PATH"),
        "render": "working"
    })


@app.route("/fetch/<path:url>")
def fetch(url):

    if not url.startswith("http"):
        url = "https://" + url

    found_callback = None

    try:

        with sync_playwright() as p:

            # مهم جدًا
            browser = p.chromium.launch(
                headless=True,
                channel="chromium"
            )

            page = browser.new_page()

            def handle_response(response):

                nonlocal found_callback

                response_url = response.url

                if "callback" in response_url and not found_callback:

                    found_callback = response_url

            page.on("response", handle_response)

            page.goto(
                url,
                wait_until="networkidle",
                timeout=60000
            )

            browser.close()

        return jsonify({
            "callback": found_callback
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500
