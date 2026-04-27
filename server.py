"""
Local dashboard server with live refresh.
Run: python server.py
Then open http://localhost:8686 in your browser.
Click the Refresh button to re-crawl + regenerate.
"""
import os
import sys
import json
import threading
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

sys.dont_write_bytecode = True
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = 8686
is_refreshing = False


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/' or parsed.path == '/index.html':
            # Serve the dashboard
            dash_path = os.path.join(os.getcwd(), 'dashboard.html')
            if os.path.exists(dash_path):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(dash_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Dashboard not found. Run: python run.py --demo')
            return

        if parsed.path == '/api/refresh':
            self._handle_refresh()
            return

        if parsed.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"refreshing": is_refreshing}).encode())
            return

        # Serve static files
        super().do_GET()

    def _handle_refresh(self):
        global is_refreshing
        if is_refreshing:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "already_running"}).encode())
            return

        is_refreshing = True
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "started"}).encode())

        def do_refresh():
            global is_refreshing
            try:
                print("\n[Server] Refresh triggered — crawling fresh data...")
                subprocess.run(
                    [sys.executable, '-B', 'run.py', '--quick'],
                    cwd=os.getcwd(),
                    timeout=300,
                )
                print("[Server] Refresh complete!")
            except Exception as e:
                print(f"[Server] Refresh error: {e}")
            finally:
                is_refreshing = False

        threading.Thread(target=do_refresh, daemon=True).start()

    def log_message(self, format, *args):
        if '/api/status' not in str(args):
            super().log_message(format, *args)


def main():
    # Generate dashboard if it doesn't exist
    if not os.path.exists('dashboard.html'):
        print("No dashboard found. Generating with demo data...")
        subprocess.run([sys.executable, '-B', 'run.py', '--demo'], cwd=os.getcwd())

    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f"\n{'='*50}")
    print(f"  HCMC Real Estate Dashboard Server")
    print(f"  Open: http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*50}\n")

    try:
        import webbrowser
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == '__main__':
    main()
