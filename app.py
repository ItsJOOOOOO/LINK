from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import threading
import uuid
import time

app = Flask(__name__)

sessions = {}


@app.route("/")
def home():
    return jsonify({
        "status": "running"
    })


def run_browser(session_id, url):

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

            page.set_default_navigation_timeout(120000)

            def handle_response(response):

                nonlocal found_callback

                response_url = response.url

                print("Response:", response_url)

                if "callback" in response_url:

                    found_callback = response_url

                    sessions[session_id]["status"] = "completed"
                    sessions[session_id]["callback"] = found_callback

            page.on("response", handle_response)

            try:

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=120000
                )

                page.wait_for_timeout(30000)

            except Exception as nav_error:

                print("Navigation Error:", str(nav_error))

            browser.close()

        if not found_callback:

            sessions[session_id]["status"] = "not_found"

    except Exception as e:

        sessions[session_id]["status"] = "error"
        sessions[session_id]["error"] = str(e)


@app.route("/start")
def start():

    url = request.args.get("url")

    if not url:

        return jsonify({
            "success": False,
            "error": "Missing url parameter"
        }), 400

    if not url.startswith("http"):

        url = "https://" + url

    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "status": "processing",
        "callback": None,
        "created_at": time.time()
    }

    thread = threading.Thread(
        target=run_browser,
        args=(session_id, url)
    )

    thread.start()

    return jsonify({
        "success": True,
        "session_id": session_id
    })


@app.route("/result/<session_id>")
def result(session_id):

    session = sessions.get(session_id)

    if not session:

        return jsonify({
            "success": False,
            "error": "Invalid session id"
        }), 404

    return jsonify({
        "success": True,
        "status": session["status"],
        "callback": session.get("callback"),
        "error": session.get("error")
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
