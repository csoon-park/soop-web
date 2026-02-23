import re
from .types import UserFlag, Flag1, Flag2, User, UserList


def make_header(svc: int, payload_len: int, option: int = 0) -> bytes:
    """바이너리 프로토콜 헤더 생성
    [0x1B, 0x09] + 4자리 서비스코드 + 6자리 페이로드길이 + 2자리 옵션
    """
    header = bytes([0x1B, 0x09])
    header += f"{svc:04d}".encode()
    header += f"{payload_len:06d}".encode()
    header += f"{option:02d}".encode()
    return header


def make_buffer(parts: list[str]) -> bytes:
    """문자열 리스트를 바이트로 변환"""
    return b"".join(p.encode() for p in parts)


def get_service_code(message: bytes) -> int:
    """메시지에서 서비스 코드 추출 (바이트 2~6)"""
    return int(message[2:6].decode())


def remove_parentheses(s: str) -> str:
    """문자열에서 () 와 그 안의 내용 제거"""
    idx = s.find("(")
    if idx != -1:
        return s[:idx]
    return s


def get_flag1(flag: int) -> Flag1:
    return Flag1(
        admin=bool(flag & (1 << 0)),
        hidden=bool(flag & (1 << 1)),
        bj=bool(flag & (1 << 2)),
        dumb=bool(flag & (1 << 3)),
        guest=bool(flag & (1 << 4)),
        fanclub=bool(flag & (1 << 5)),
        auto_manager=bool(flag & (1 << 6)),
        manager_list=bool(flag & (1 << 7)),
        manager=bool(flag & (1 << 8)),
        female=bool(flag & (1 << 9)),
        auto_dumb=bool(flag & (1 << 10)),
        dumb_blind=bool(flag & (1 << 11)),
        dobae_blind=bool(flag & (1 << 12)),
        dobae_blind2=bool(flag & (1 << 24)),
        exit_user=bool(flag & (1 << 13)),
        mobile=bool(flag & (1 << 14)),
        top_fan=bool(flag & (1 << 15)),
        realname=bool(flag & (1 << 16)),
        no_direct=bool(flag & (1 << 17)),
        global_app=bool(flag & (1 << 18)),
        quick_view=bool(flag & (1 << 19)),
        sptr_sticker=bool(flag & (1 << 20)),
        chromecast=bool(flag & (1 << 21)),
        subscriber=bool(flag & (1 << 28)),
        noti_vod_balloon=bool(flag & (1 << 30)),
        noti_top_fan=bool(flag & (1 << 31)),
    )


def get_flag2(flag: int) -> Flag2:
    return Flag2(
        global_pc=bool(flag & (1 << 0)),
        clan=bool(flag & (1 << 1)),
        top_clan=bool(flag & (1 << 2)),
        top20=bool(flag & (1 << 3)),
        game_god=bool(flag & (1 << 4)),
        atag_allow=bool(flag & (1 << 5)),
        no_super_chat=bool(flag & (1 << 6)),
        no_recv_chat=bool(flag & (1 << 7)),
        flash=bool(flag & (1 << 8)),
        lg_game=bool(flag & (1 << 9)),
        employee=bool(flag & (1 << 10)),
        clean_ati=bool(flag & (1 << 11)),
        police=bool(flag & (1 << 12)),
        admin_chat=bool(flag & (1 << 13)),
        pc=bool(flag & (1 << 14)),
        specify=bool(flag & (1 << 15)),
    )


def set_flag(flags: list[str]) -> UserFlag:
    """플래그 문자열 리스트를 UserFlag로 변환"""
    try:
        f1 = int(flags[0]) if len(flags) > 0 else 0
        f2 = int(flags[1]) if len(flags) > 1 else 0
    except (ValueError, IndexError):
        f1, f2 = 0, 0
    return UserFlag(flag1=get_flag1(f1), flag2=get_flag2(f2))


def parse_multi_user_list(msg: list[str]) -> list[UserList]:
    """여러 유저 파싱 (최초 입장 시)"""
    users = []
    i = 2
    while i + 2 < len(msg):
        if msg[i] == "-1":
            i += 3
            continue
        flags = msg[i + 2].split("|") if len(msg) > i + 2 else ["0", "0"]
        user_flag = set_flag(flags)
        users.append(UserList(
            user=User(id=msg[i], name=msg[i + 1], flag=user_flag),
            status=True,
        ))
        i += 3
    return users


def parse_single_user_list(msg: list[str]) -> UserList:
    """단일 유저 입장/퇴장 파싱"""
    status = msg[1] == "1" if len(msg) > 1 else True
    user_flag = UserFlag()

    if status and len(msg) > 4:
        flags = msg[4].split("|")
        user_flag = set_flag(flags)

    return UserList(
        user=User(
            id=remove_parentheses(msg[2]) if len(msg) > 2 else "",
            name=msg[3] if len(msg) > 3 else "",
            flag=user_flag,
        ),
        status=status,
    )


def default_log() -> dict:
    return {
        "set_bps": "undefined",
        "view_bps": "NaN",
        "quality": "ori",
        "geo_cc": "undefined",
        "geo_rc": "undefined",
        "acpt_lang": "undefined",
        "svc_lang": "undefined",
        "join_cc": "410",
        "subscribe": "1",
    }


def default_info(password: str = "") -> dict:
    result = {}
    if password:
        result["pwd"] = password
    result["auth_info"] = "undefined"
    return result


def build_log_handshake(log_data: dict) -> bytes:
    """로그 핸드셰이크 데이터 생성"""
    result = b"log" + bytes([0x11])
    # 로그 값 생성
    log_bytes = b""
    for k, v in log_data.items():
        if v:
            entry = bytes([0x06]) + k.encode() + bytes([0x06, 0x3D, 0x06]) + v.encode() + bytes([0x06, 0x26])
            log_bytes += entry
    result += bytes([0x06, 0x26]) + log_bytes
    result += bytes([0x12])
    return result


def build_info_handshake(info_data: dict) -> bytes:
    """인포 핸드셰이크 데이터 생성"""
    result = b""
    for k, v in info_data.items():
        if v:
            entry = k.encode() + bytes([0x11]) + v.encode() + bytes([0x12])
            result += entry
    return result
