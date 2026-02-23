import asyncio
import ssl
import logging
from typing import Callable, Optional

import websockets

from .api import ApiService
from .constants import *
from .types import (
    User, ChatMessage, UserList, Balloon, Adballoon,
    Subscription, Mission,
)
from .utils import (
    make_header, make_buffer, get_service_code,
    default_log, default_info,
    build_log_handshake, build_info_handshake,
)
from .messages import (
    parse_join_channel, parse_user_join, parse_chat_message,
    parse_balloon, parse_adballoon, parse_subscription,
    parse_admin_notice, parse_mission,
)

logger = logging.getLogger("soopchat")


class SoopChat:
    """SOOP 채팅 클라이언트 (비공식)

    스트리머 ID만으로 채팅 서버에 접속하여
    별풍선, 채팅, 구독 등의 이벤트를 실시간 수신합니다.

    사용법:
        client = SoopChat("streamer_id")
        client.on_balloon(lambda b: print(f"{b.user.name}: {b.count}개"))
        await client.connect()

    로그인 (채팅 보내기):
        client = SoopChat("streamer_id", user_id="id", password="pw")
        await client.connect()
        await client.send_chat("안녕하세요!")
    """

    def __init__(
        self,
        streamer_id: str,
        user_id: str = "",
        password: str = "",
        channel_password: str = "",
    ):
        if not streamer_id:
            raise ValueError("streamer_id는 필수입니다")

        self.streamer_id = streamer_id
        self.user_id = user_id
        self.password = password
        self.channel_password = channel_password

        # 내부 상태
        self._socket_address = ""
        self._chat_room = ""
        self._auth_ticket = ""
        self._fan_ticket = ""
        self._flag = ""
        self._ws = None
        self._running = False
        self._api = ApiService()

        # 콜백
        self._on_error: Optional[Callable] = None
        self._on_connect: Optional[Callable] = None
        self._on_join_channel: Optional[Callable] = None
        self._on_raw_message: Optional[Callable] = None
        self._on_chat_message: Optional[Callable] = None
        self._on_user_lists: Optional[Callable] = None
        self._on_balloon: Optional[Callable] = None
        self._on_adballoon: Optional[Callable] = None
        self._on_subscription: Optional[Callable] = None
        self._on_admin_notice: Optional[Callable] = None
        self._on_mission: Optional[Callable] = None
        self._on_login: Optional[Callable] = None

    # ─── 콜백 등록 ───

    def on_error(self, callback: Callable):
        self._on_error = callback
        return self

    def on_connect(self, callback: Callable):
        self._on_connect = callback
        return self

    def on_join_channel(self, callback: Callable):
        self._on_join_channel = callback
        return self

    def on_raw_message(self, callback: Callable):
        self._on_raw_message = callback
        return self

    def on_chat_message(self, callback: Callable):
        self._on_chat_message = callback
        return self

    def on_user_lists(self, callback: Callable):
        self._on_user_lists = callback
        return self

    def on_balloon(self, callback: Callable):
        self._on_balloon = callback
        return self

    def on_adballoon(self, callback: Callable):
        self._on_adballoon = callback
        return self

    def on_subscription(self, callback: Callable):
        self._on_subscription = callback
        return self

    def on_admin_notice(self, callback: Callable):
        self._on_admin_notice = callback
        return self

    def on_mission(self, callback: Callable):
        self._on_mission = callback
        return self

    def on_login(self, callback: Callable):
        self._on_login = callback
        return self

    # ─── 메인 연결 ───

    async def connect(self):
        """채팅 서버에 연결하고 이벤트 수신을 시작합니다.

        이 메서드는 연결이 끊어질 때까지 블로킹됩니다.
        """
        # 로그인 (선택)
        if self.user_id and self.password:
            try:
                success = self._api.login(self.user_id, self.password)
                if self._on_login:
                    self._on_login(success)
                if not success:
                    raise Exception("로그인 실패")
            except Exception as e:
                if self._on_error:
                    self._on_error(e)
                raise

        # 채팅 서버 정보 가져오기
        try:
            data = self._api.get_socket_data(self.streamer_id)
            self._socket_address = data["socket_address"]
            self._chat_room = data["chat_room"]
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise

        # WebSocket 연결
        try:
            await self._connect_websocket()
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise

    async def _connect_websocket(self):
        """WebSocket 연결 및 핸드셰이크, 메시지 루프"""
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        async with websockets.connect(
            self._socket_address,
            ssl=ssl_ctx,
            subprotocols=["chat"],
            open_timeout=10,
            max_size=None,
            ping_interval=None,   # SOOP 자체 keepalive 사용, 자동 ping 비활성화
            ping_timeout=None,    # 자동 pong 타임아웃 비활성화
            close_timeout=5,
        ) as ws:
            self._ws = ws
            self._running = True

            # 1) Login 핸드셰이크 전송
            login_packet = self._build_login_handshake()
            await ws.send(login_packet)

            # 2) Ping 태스크 시작
            ping_task = asyncio.create_task(self._ping_loop())

            try:
                # 3) 메시지 수신 루프
                async for raw in ws:
                    if isinstance(raw, str):
                        raw = raw.encode()

                    if self._on_raw_message:
                        self._on_raw_message(repr(raw))

                    try:
                        await self._dispatch(raw)
                    except Exception as e:
                        if self._on_error:
                            self._on_error(e)
                        logger.debug(f"dispatch error: {e}")

            except websockets.ConnectionClosed as e:
                logger.warning(f"WebSocket 연결 종료: code={e.code}, reason={e.reason}")
                if self._on_error:
                    self._on_error(f"WebSocket 연결 종료: code={e.code}, reason={e.reason}")
            except Exception as e:
                logger.error(f"WebSocket 수신 루프 오류: {e}")
                if self._on_error:
                    self._on_error(e)
            finally:
                self._running = False
                ping_task.cancel()
                if self._on_connect:
                    self._on_connect(False)

    async def _dispatch(self, msg: bytes):
        """메시지 서비스 코드에 따라 콜백 호출"""
        if len(msg) < 6:
            return

        try:
            svc = get_service_code(msg)
        except (ValueError, IndexError):
            return

        if svc == SVC_KEEPALIVE:
            # 서버 pong 응답 → 무시 (연결 유지 확인)
            logger.debug("keepalive pong received")
            return

        elif svc == SVC_LOGIN:
            # 로그인 응답 → JOIN 핸드셰이크 전송
            join_packet = self._build_join_handshake()
            await self._ws.send(join_packet)

            if self._on_connect:
                self._on_connect(True)

        elif svc == SVC_JOINCH:
            if self._on_join_channel:
                success = parse_join_channel(msg)
                self._on_join_channel(success)

        elif svc == SVC_CHUSER:
            if self._on_user_lists:
                users = parse_user_join(msg)
                self._on_user_lists(users)

        elif svc == SVC_CHATMESG:
            if self._on_chat_message:
                try:
                    cm = parse_chat_message(msg)
                    self._on_chat_message(cm)
                except ValueError as e:
                    if self._on_error:
                        self._on_error(e)

        elif svc == SVC_SENDBALLOON:
            if self._on_balloon:
                try:
                    b = parse_balloon(msg)
                    self._on_balloon(b)
                except ValueError as e:
                    if self._on_error:
                        self._on_error(e)

        elif svc == SVC_ADCON_EFFECT:
            if self._on_adballoon:
                try:
                    ab = parse_adballoon(msg)
                    self._on_adballoon(ab)
                except ValueError as e:
                    if self._on_error:
                        self._on_error(e)

        elif svc in (SVC_FOLLOW_ITEM, SVC_FOLLOW_ITEM_EFFECT):
            if self._on_subscription:
                try:
                    sub = parse_subscription(msg, svc)
                    self._on_subscription(sub)
                except ValueError as e:
                    if self._on_error:
                        self._on_error(e)

        elif svc == SVC_SENDADMINNOTICE:
            if self._on_admin_notice:
                try:
                    notice = parse_admin_notice(msg)
                    self._on_admin_notice(notice)
                except ValueError as e:
                    if self._on_error:
                        self._on_error(e)

        elif svc == SVC_MISSION:
            if self._on_mission:
                try:
                    m = parse_mission(msg)
                    self._on_mission(m)
                except ValueError as e:
                    if self._on_error:
                        self._on_error(e)

    # ─── 채팅 보내기 ───

    async def send_chat(self, message: str):
        """채팅 메시지를 전송합니다 (로그인 필요)"""
        if not self._auth_ticket:
            raise Exception("로그인하지 않은 상태에서는 채팅을 보낼 수 없습니다")
        if not self._ws:
            raise Exception("WebSocket이 연결되지 않았습니다")

        body = make_buffer(["\f", message, "\f", "0", "\f"])
        header = make_header(SVC_CHATMESG, len(body), 0)
        await self._ws.send(header + body)

    # ─── 연결 해제 ───

    async def disconnect(self):
        """연결을 종료합니다"""
        self._running = False
        if self._ws:
            await self._ws.close()

    # ─── 핸드셰이크 빌드 ───

    def _build_login_handshake(self) -> bytes:
        """Login 핸드셰이크 패킷 생성"""
        body = make_buffer([
            "\f", self._auth_ticket, "\f", "\f", self._flag, "\f"
        ])
        header = make_header(SVC_LOGIN, len(body), 0)
        return header + body

    def _build_join_handshake(self) -> bytes:
        """Join 핸드셰이크 패킷 생성"""
        log_bytes = build_log_handshake(default_log())
        info_bytes = build_info_handshake(default_info(self.channel_password))
        info_packet = log_bytes + info_bytes

        body = make_buffer([
            "\f",
            self._chat_room,
            "\f",
            "\f",
            self._fan_ticket + "0",
            "\f",
            "",
            "\f",
        ]) + info_packet + b"\f"

        header = make_header(SVC_JOINCH, len(body), 0)
        return header + body

    # ─── Ping ───

    async def _ping_loop(self):
        """20초마다 keepalive 패킷 전송 (SOOP 서버 타임아웃 방지)"""
        try:
            while self._running:
                await asyncio.sleep(20)
                if self._ws and self._running:
                    body = make_buffer(["\f"])
                    header = make_header(SVC_KEEPALIVE, len(body), 0)
                    await self._ws.send(header + body)
                    logger.debug("keepalive sent")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self._on_error:
                self._on_error(e)
