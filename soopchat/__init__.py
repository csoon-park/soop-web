"""
soopchat - SOOP 채팅 Python 클라이언트 (비공식)

원본: https://github.com/halfdogs/soopchat (Go)
Python 포팅 버전

사용법:
    import asyncio
    from soopchat import SoopChat

    async def main():
        client = SoopChat("streamer_id")

        def on_balloon(balloon):
            print(f"{balloon.user.name}님이 {balloon.count}개 별풍선!")

        def on_chat(msg):
            print(f"[{msg.user.name}] {msg.message}")

        client.on_balloon(on_balloon)
        client.on_chat_message(on_chat)

        await client.connect()

    asyncio.run(main())
"""

from .client import SoopChat
from .types import (
    User,
    UserFlag,
    Flag1,
    Flag2,
    ChatMessage,
    UserList,
    Balloon,
    Adballoon,
    Subscription,
    Mission,
)
from .constants import *

__version__ = "1.0.0"
__all__ = [
    "SoopChat",
    "User",
    "UserFlag",
    "Flag1",
    "Flag2",
    "ChatMessage",
    "UserList",
    "Balloon",
    "Adballoon",
    "Subscription",
    "Mission",
]
