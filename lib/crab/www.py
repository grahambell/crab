from BaseHTTPServer import BaseHTTPRequestHandler

class CrabWWW(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
            <html><head><title>crab</title></head><body>
            <h1>crab</h1>
            <p>No web interface yet.</p>
            </body></html>
        """)

