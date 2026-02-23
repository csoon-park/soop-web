"""
별풍선 기록 예제

스트리머 ID만 넣으면 별풍선 이벤트를 실시간으로 수신합니다.
Client ID, Client Secret, OAuth 인증 필요 없음!

사용법:
    pip install websockets requests
    python example_balloon.py
"""
import asyncio
from soopchat import SoopChat, Balloon, ChatMessage, Subscription, Adballoon, Mission


# ▼▼▼ 여기에 스트리머 ID 입력 ▼▼▼
STREAMER_ID = "ecvhao"  # 원하는 스트리머 ID로 변경


async def main():
    client = SoopChat(STREAMER_ID)

    # 연결 상태
    def on_connect(connected: bool):
        if connected:
            print(f"[연결] {STREAMER_ID} 채팅 서버 연결 성공!")
        else:
            print("[연결 해제] 채팅 서버 연결이 끊어졌습니다.")

    # 채널 입장
    def on_join(success: bool):
        if success:
            print("[입장] 채팅방 입장 성공! 이벤트 수신 대기 중...")
        else:
            print("[입장 실패] 비밀번호가 틀렸거나 입장할 수 없습니다.")

    # ⭐ 별풍선
    def on_balloon(b: Balloon):
        print(f"⭐ [별풍선] {b.user.name}({b.user.id}) → {b.count}개")

    # 🎈 애드벌룬
    def on_adballoon(ab: Adballoon):
        print(f"🎈 [애드벌룬] {ab.user.name}({ab.user.id}) → {ab.count}개")

    # 💬 채팅
    def on_chat(msg: ChatMessage):
        print(f"💬 [{msg.user.name}] {msg.message}")

    # 🔔 구독
    def on_subscription(sub: Subscription):
        print(f"🔔 [구독] {sub.user.name}({sub.user.id}) → {sub.count}개월")

    # 🎯 미션
    def on_mission(m: Mission):
        print(f"🎯 [미션] {m.user.name} - {m.title} ({m.count}개)")

    # 에러
    def on_error(err: Exception):
        print(f"[에러] {err}")

    # 콜백 등록
    client.on_connect(on_connect)
    client.on_join_channel(on_join)
    client.on_balloon(on_balloon)
    client.on_adballoon(on_adballoon)
    client.on_chat_message(on_chat)
    client.on_subscription(on_subscription)
    client.on_mission(on_mission)
    client.on_error(on_error)

    print(f"[시작] {STREAMER_ID} 방송 채팅 연결 중...")
    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())
