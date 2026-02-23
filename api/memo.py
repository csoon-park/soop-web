from http.server import BaseHTTPRequestHandler
from api._db import get_conn, init_db
import json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Update memo for a balloon record"""
        try:
            init_db()
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}

            record_id = body.get("record_id")
            memo = body.get("memo", "")

            if not record_id:
                self._json(400, {"error": "record_id is required"})
                return

            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE balloon_records SET memo = %s WHERE id = %s
            """, (memo, record_id))
            conn.commit()
            cur.close()
            conn.close()

            self._json(200, {"ok": True})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
