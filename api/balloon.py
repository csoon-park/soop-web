from http.server import BaseHTTPRequestHandler
from api._db import get_conn, init_db
import json
import urllib.parse


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Save balloon record(s)"""
        try:
            init_db()
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}

            streamer_id = body.get("streamer_id")
            records = body.get("records", [])

            if not streamer_id or not records:
                self._json(400, {"error": "streamer_id and records are required"})
                return

            conn = get_conn()
            cur = conn.cursor()

            inserted = 0
            for rec in records:
                cur.execute("""
                    INSERT INTO balloon_records
                    (streamer_id, user_id, user_nickname, count, tag, recorded_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    streamer_id,
                    rec.get("user_id", ""),
                    rec.get("user_nickname", ""),
                    rec.get("count", 0),
                    rec.get("tag", ""),
                    rec.get("recorded_at"),
                ))
                inserted += 1

            conn.commit()
            cur.close()
            conn.close()

            self._json(200, {"ok": True, "inserted": inserted})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_GET(self):
        """Get balloon records with filtering"""
        try:
            init_db()
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)

            streamer_id = params.get("streamer_id", [None])[0]
            if not streamer_id:
                self._json(400, {"error": "streamer_id is required"})
                return

            tag_filter = params.get("tag", [None])[0]
            page = int(params.get("page", ["1"])[0])
            limit = int(params.get("limit", ["100"])[0])
            offset = (page - 1) * limit

            conn = get_conn()
            cur = conn.cursor()

            # Build query
            where = "WHERE streamer_id = %s"
            query_params = [int(streamer_id)]

            if tag_filter:
                where += " AND tag = %s"
                query_params.append(tag_filter)

            # Get total count
            cur.execute(f"SELECT COUNT(*) as cnt FROM balloon_records {where}", query_params)
            total = cur.fetchone()["cnt"]

            # Get records
            cur.execute(f"""
                SELECT id, user_id, user_nickname, count, tag, memo, recorded_at
                FROM balloon_records
                {where}
                ORDER BY recorded_at DESC
                LIMIT %s OFFSET %s
            """, query_params + [limit, offset])
            rows = cur.fetchall()

            # Serialize datetimes
            for row in rows:
                if row.get("recorded_at"):
                    row["recorded_at"] = row["recorded_at"].isoformat()

            # Get summary (user totals)
            cur.execute(f"""
                SELECT user_id, user_nickname,
                       SUM(count) as total_count,
                       COUNT(*) as donation_count,
                       MAX(recorded_at) as last_donated
                FROM balloon_records
                {where}
                GROUP BY user_id, user_nickname
                ORDER BY total_count DESC
            """, query_params)
            summary = cur.fetchall()
            for s in summary:
                if s.get("last_donated"):
                    s["last_donated"] = s["last_donated"].isoformat()
                s["total_count"] = int(s["total_count"])

            cur.close()
            conn.close()

            self._json(200, {
                "ok": True,
                "records": rows,
                "summary": summary,
                "total": total,
                "page": page,
                "limit": limit,
            })
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
