from http.server import BaseHTTPRequestHandler
from api._db import get_conn, init_db
import json
import os
import urllib.request
import urllib.parse


CLIENT_ID = os.environ.get("SOOP_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SOOP_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("SOOP_REDIRECT_URI", "")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            init_db()
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            code = body.get("code", "")

            if not code:
                self._json(400, {"error": "code is required"})
                return

            # Exchange code for tokens via SOOP OAuth
            token_data = urllib.parse.urlencode({
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            }).encode()

            req = urllib.request.Request(
                "https://openapi.sooplive.co.kr/auth/token",
                data=token_data,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req) as resp:
                tokens = json.loads(resp.read())

            access_token = tokens.get("access_token", "")
            refresh_token = tokens.get("refresh_token", "")

            if not access_token:
                self._json(400, {"error": "Failed to get access_token", "detail": tokens})
                return

            # Get user info
            user_req = urllib.request.Request(
                "https://openapi.sooplive.co.kr/user/info",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            with urllib.request.urlopen(user_req) as resp:
                user_info = json.loads(resp.read())

            soop_id = user_info.get("user_id", "")
            nickname = user_info.get("user_nick", "")

            if not soop_id:
                self._json(400, {"error": "Failed to get user info", "detail": user_info})
                return

            # Upsert streamer
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO streamers (soop_id, nickname, access_token, refresh_token)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (soop_id) DO UPDATE
                SET nickname = EXCLUDED.nickname,
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token
                RETURNING id
            """, (soop_id, nickname, access_token, refresh_token))
            streamer_id = cur.fetchone()["id"]
            conn.commit()
            cur.close()
            conn.close()

            self._json(200, {
                "ok": True,
                "streamer_id": streamer_id,
                "soop_id": soop_id,
                "nickname": nickname,
                "access_token": access_token,
            })

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
