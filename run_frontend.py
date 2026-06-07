import http.server
import socketserver
import webbrowser
import threading
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def open_browser():
    webbrowser.open_new_tab(f"http://127.0.0.1:{PORT}/index.html")

if __name__ == "__main__":
    print("CodeGuard AI (CodeSense) Frontend Server starting...")
    print(f"Serving directory: {DIRECTORY}")
    print(f"Local URL: http://127.0.0.1:{PORT}/index.html")
    print(f"Press Ctrl+C to stop the server.")
    
    # Open default browser after 1 second
    threading.Timer(1.0, open_browser).start()
    
    # Enable reuse address to avoid port blocking errors
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        sys.exit(0)
