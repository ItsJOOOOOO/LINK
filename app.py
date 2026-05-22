from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "status": "running"
    })


@app.route("/fetch", methods=["GET", "POST"])
def fetch():

    if request.method == "POST":

        data = request.get_json(silent=True)

        if not data or "url" not in data:
            return jsonify({
                "success": False,
                "error": "URL is required"
            }), 400

        url = data["url"]

    else:

        url = request.args.get("url")

        if not url:
            return jsonify({
                "success": False,
                "error": "URL parameter is required"
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

                if "callback" in response_url and not found_callback:
                    found_callback = response_url

            page.on("response", handle_response)

            try:

                page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=60000
                )

                page.wait_for_timeout(5000)

            except Exception:
                pass

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
