from http.server import BaseHTTPRequestHandler
from api._db import get_conn, init_db
import json
import urllib.parse
import io
from openpyxl import Workbook


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Export balloon records as Excel"""
        try:
            init_db()
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)

            streamer_id = params.get("streamer_id", [None])[0]
            if not streamer_id:
                self._json(400, {"error": "streamer_id is required"})
                return

            tag_filter = params.get("tag", [None])[0]
            export_type = params.get("type", ["records"])[0]  # records or summary

            conn = get_conn()
            cur = conn.cursor()

            where = "WHERE streamer_id = %s"
            query_params = [int(streamer_id)]

            if tag_filter:
                where += " AND tag = %s"
                query_params.append(tag_filter)

            wb = Workbook()
            ws = wb.active

            if export_type == "summary":
                ws.title = "후원 요약"
                ws.append(["유저ID", "닉네임", "총 별풍선", "후원 횟수", "마지막 후원일", "메모"])

                cur.execute(f"""
                    SELECT user_id, user_nickname,
                           SUM(count) as total_count,
                           COUNT(*) as donation_count,
                           MAX(recorded_at) as last_donated,
                           STRING_AGG(DISTINCT memo, ' / ') FILTER (WHERE memo != '') as memos
                    FROM balloon_records
                    {where}
                    GROUP BY user_id, user_nickname
                    ORDER BY total_count DESC
                """, query_params)

                for row in cur.fetchall():
                    ws.append([
                        row["user_id"],
                        row["user_nickname"],
                        int(row["total_count"]),
                        row["donation_count"],
                        str(row["last_donated"]) if row["last_donated"] else "",
                        row["memos"] or "",
                    ])
            else:
                ws.title = "후원 기록"
                ws.append(["ID", "유저ID", "닉네임", "개수", "태그", "메모", "일시"])

                cur.execute(f"""
                    SELECT id, user_id, user_nickname, count, tag, memo, recorded_at
                    FROM balloon_records
                    {where}
                    ORDER BY recorded_at DESC
                """, query_params)

                for row in cur.fetchall():
                    ws.append([
                        row["id"],
                        row["user_id"],
                        row["user_nickname"],
                        row["count"],
                        row["tag"],
                        row["memo"] or "",
                        str(row["recorded_at"]) if row["recorded_at"] else "",
                    ])

            cur.close()
            conn.close()

            # Write to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            data = output.getvalue()

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", "attachment; filename=balloon_records.xlsx")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
