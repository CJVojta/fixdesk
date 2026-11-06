"""Run a local issue tracker backed by SQLite."""

from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parent
DB = ROOT / "issues.sqlite3"


def init_db():
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                resolved INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1))
            )
        """)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        self.send_body(status, "application/json", json.dumps(payload).encode())

    def send_body(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send_body(200, "text/html; charset=utf-8", (ROOT / "index.html").read_bytes())
        elif self.path == "/api/issues":
            with closing(sqlite3.connect(DB)) as db:
                db.row_factory = sqlite3.Row
                rows = db.execute("SELECT * FROM issues ORDER BY id DESC").fetchall()
            self.send_json(200, [dict(row) for row in rows])
        else:
            self.send_json(404, {"error": "Page not found."})

    def do_POST(self):
        if self.path != "/api/issues":
            self.send_json(404, {"error": "Endpoint not found."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 4096:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            title = payload.get("title") if isinstance(payload, dict) else None
            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
                raise ValueError
            title = title.strip()
            title.encode("utf-8")
        except ValueError:
            self.send_json(400, {"error": "Enter a title between 1 and 120 characters."})
            return

        with closing(sqlite3.connect(DB)) as db, db:
            row = db.execute("INSERT INTO issues (title) VALUES (?)", (title,))
        self.send_json(201, {"id": row.lastrowid, "title": title, "resolved": 0})

    def do_PATCH(self):
        match = re.fullmatch(r"/api/issues/([1-9][0-9]{0,17})/resolve", self.path)
        if not match:
            self.send_json(404, {"error": "Endpoint not found."})
            return

        with closing(sqlite3.connect(DB)) as db, db:
            row = db.execute("UPDATE issues SET resolved = 1 WHERE id = ?", (int(match[1]),))
        if row.rowcount:
            self.send_json(200, {"resolved": 1})
        else:
            self.send_json(404, {"error": "Issue not found."})


if __name__ == "__main__":
    init_db()
    with ThreadingHTTPServer(("127.0.0.1", 8000), Handler) as server:
        print("FixDesk is available at http://127.0.0.1:8000")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
