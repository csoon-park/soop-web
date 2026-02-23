import json
from .types import (
    User, ChatMessage, UserList, Balloon, Adballoon,
    Subscription, Mission,
)
from .utils import (
    remove_parentheses, set_flag,
    parse_multi_user_list, parse_single_user_list,
)
from .constants import SVC_FOLLOW_ITEM, SVC_FOLLOW_ITEM_EFFECT


def parse_join_channel(message: bytes) -> bool:
    """채널 입장 응답 파싱"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) > 1:
        return msg[1] != "비밀번호가 틀렸습니다."
    return True


def parse_user_join(message: bytes) -> list[UserList]:
    """유저 입장/퇴장 파싱"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) > 10:
        return parse_multi_user_list(msg)
    return [parse_single_user_list(msg)]


def parse_chat_message(message: bytes) -> ChatMessage:
    """채팅 메시지 파싱 (svc=5)"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) < 9:
        raise ValueError("message splitting failure [5]")

    flags = msg[7].split("|")
    user_flag = set_flag(flags)

    try:
        sub_month = int(msg[8])
    except (ValueError, IndexError):
        sub_month = 0

    if sub_month == -1:
        sub_month = 0

    return ChatMessage(
        user=User(
            id=remove_parentheses(msg[2].strip()),
            name=msg[6].strip(),
            subscribe_month=sub_month,
            flag=user_flag,
        ),
        message=msg[1].strip(),
    )


def parse_balloon(message: bytes) -> Balloon:
    """별풍선 파싱 (svc=18)
    필드: msg[1]=BJ메타, msg[2]=유저ID, msg[3]=유저닉네임, msg[4]=개수
    ※ 별풍선과 함께 보낸 채팅은 별도의 SVC_CHATMESG(5)로 수신됨
    """
    msg = message.decode(errors="replace").split("\f")
    if len(msg) < 5:
        raise ValueError("message splitting failure [18]")

    try:
        count = int(msg[4])
    except (ValueError, IndexError):
        count = 0

    return Balloon(
        user=User(id=msg[2], name=msg[3]),
        count=count,
    )


def parse_adballoon(message: bytes) -> Adballoon:
    """애드벌룬 파싱 (svc=87)"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) < 11:
        raise ValueError("message splitting failure [87]")

    try:
        count = int(msg[10])
    except (ValueError, IndexError):
        count = 0

    return Adballoon(
        user=User(id=msg[3], name=msg[4]),
        count=count,
    )


def parse_subscription(message: bytes, svc: int) -> Subscription:
    """구독 파싱 (svc=91, 93)"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) < 8:
        raise ValueError("message splitting failure [91]")

    user = User()
    count = 1

    if svc == SVC_FOLLOW_ITEM:
        user.id = remove_parentheses(msg[3])
        user.name = msg[4]
        try:
            count = int(msg[5])
        except (ValueError, IndexError):
            count = 1
    elif svc == SVC_FOLLOW_ITEM_EFFECT:
        user.id = remove_parentheses(msg[2])
        user.name = msg[3]
        try:
            count = int(msg[4])
        except (ValueError, IndexError):
            count = 1

    return Subscription(user=user, count=count)


def parse_admin_notice(message: bytes) -> str:
    """어드민 메시지 파싱 (svc=58)"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) > 1:
        return msg[1]
    raise ValueError("message splitting failure [58]")


def parse_mission(message: bytes) -> Mission:
    """도전미션 파싱 (svc=121)"""
    msg = message.decode(errors="replace").split("\f")
    if len(msg) < 2:
        raise ValueError("message splitting failure [121]")

    try:
        data = json.loads(msg[1])
    except json.JSONDecodeError:
        raise ValueError("json unmarshal failure [121]")

    count = data.get("gift_count", 0)
    if isinstance(count, float):
        count = int(count)

    return Mission(
        user=User(
            id=data.get("user_id", ""),
            name=data.get("user_nick", ""),
        ),
        title=data.get("title", ""),
        count=count,
    )
