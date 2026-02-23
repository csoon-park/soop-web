import requests

DATA_URL = "https://live.sooplive.co.kr/afreeca/player_live_api.php?bjId={}"
LOGIN_URL = "https://login.sooplive.co.kr/app/LoginAction.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"


class ApiService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.session.timeout = 5

    def get_socket_data(self, streamer_id: str) -> dict:
        """채팅 서버 주소, 포트, 방 번호를 가져온다.

        Returns:
            dict: {
                "socket_address": "wss://...",
                "chat_room": "...",
            }

        Raises:
            Exception: 방송 정보를 가져올 수 없는 경우
        """
        resp = self.session.post(
            DATA_URL.format(streamer_id),
            data={
                "bid": streamer_id,
                "player_type": "html5",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        channel = data.get("CHANNEL", {})
        result = channel.get("RESULT")

        if result == -6:
            raise Exception("로그인이 필요합니다")
        if result == 0:
            raise Exception("방송 중이 아닙니다")

        domain = channel.get("CHDOMAIN", "")
        port = int(channel.get("CHPT", 0)) + 1
        chat_room = str(channel.get("CHATNO", ""))

        if not domain:
            raise Exception("채팅 서버 정보를 가져올 수 없습니다")

        socket_address = f"wss://{domain}:{port}/Websocket"

        return {
            "socket_address": socket_address,
            "chat_room": chat_room,
        }

    def login(self, user_id: str, password: str) -> bool:
        """SOOP 계정으로 로그인

        Returns:
            bool: 로그인 성공 여부
        """
        resp = self.session.post(
            LOGIN_URL,
            data={
                "szWork": "login",
                "szType": "json",
                "szUid": user_id,
                "szPassword": password,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("RESULT") == 1
