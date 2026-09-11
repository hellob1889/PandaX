"""Tiny static HTTP server for previewing social-preview.svg in the browser.
Run: python preview-server.py [port]
"""
import sys
import http.server
import socketserver
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18765
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"Serving {ROOT} at http://127.0.0.1:{port}/")
        httpd.serve_forever()
