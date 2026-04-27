"""
Web app for hosting the HCMC Real Estate Dashboard.
Serves the dashboard and provides API for crawl refresh.
Deploy to Render, Railway, or any Python hosting.
"""
import os
import sys
import json
import threading
from datetime import datetime

sys.dont_write_bytecode = True
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_file, jsonify, request

app = Flask(__name__)

# State tracking for refresh
refresh_state = {"running": False, "last_run": None, "last_count": 0, "error": None}


@app.route("/")
def index():
    """Serve the dashboard."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    return "<h1>Dashboard not generated yet. Click Refresh to crawl data.</h1>", 200


@app.route("/api/refresh", methods=["POST", "GET"])
def refresh():
    """Trigger a crawl and regenerate the dashboard."""
    if refresh_state["running"]:
        return jsonify({"status": "already_running"})

    def do_refresh():
        refresh_state["running"] = True
        refresh_state["error"] = None
        try:
            # Import here to avoid circular issues
            from crawl import run_crawl
            from generate_dashboard import main as generate_dashboard

            # Full crawl — all districts, same as local run.py
            df = run_crawl()
            generate_dashboard()

            refresh_state["last_run"] = datetime.now().isoformat()
            refresh_state["last_count"] = len(df)
        except Exception as e:
            refresh_state["error"] = str(e)
            print(f"Refresh error: {e}")
        finally:
            refresh_state["running"] = False

    thread = threading.Thread(target=do_refresh)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/api/status")
def status():
    """Check refresh status."""
    return jsonify(refresh_state)


@app.route("/api/data")
def data():
    """Return the listing data as JSON."""
    json_path = os.path.join(os.path.dirname(__file__), "data", "listings_latest.json")
    if os.path.exists(json_path):
        return send_file(json_path, mimetype="application/json")
    return jsonify([])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8686))
    # Generate dashboard on startup if data exists
    data_path = os.path.join("data", "listings_latest.json")
    if os.path.exists(data_path) and not os.path.exists("dashboard.html"):
        try:
            from generate_dashboard import main as generate_dashboard
            generate_dashboard()
        except Exception:
            pass
    
    print(f"Starting server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
