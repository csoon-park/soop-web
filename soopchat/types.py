from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Flag1:
    admin: bool = False
    hidden: bool = False
    bj: bool = False
    dumb: bool = False
    guest: bool = False
    fanclub: bool = False
    auto_manager: bool = False
    manager_list: bool = False
    manager: bool = False
    female: bool = False
    auto_dumb: bool = False
    dumb_blind: bool = False
    dobae_blind: bool = False
    dobae_blind2: bool = False
    exit_user: bool = False
    mobile: bool = False
    top_fan: bool = False
    realname: bool = False
    no_direct: bool = False
    global_app: bool = False
    quick_view: bool = False
    sptr_sticker: bool = False
    chromecast: bool = False
    subscriber: bool = False
    noti_vod_balloon: bool = False
    noti_top_fan: bool = False


@dataclass
class Flag2:
    global_pc: bool = False
    clan: bool = False
    top_clan: bool = False
    top20: bool = False
    game_god: bool = False
    atag_allow: bool = False
    no_super_chat: bool = False
    no_recv_chat: bool = False
    flash: bool = False
    lg_game: bool = False
    employee: bool = False
    clean_ati: bool = False
    police: bool = False
    admin_chat: bool = False
    pc: bool = False
    specify: bool = False


@dataclass
class UserFlag:
    flag1: Flag1 = field(default_factory=Flag1)
    flag2: Flag2 = field(default_factory=Flag2)


@dataclass
class User:
    id: str = ""
    name: str = ""
    subscribe_month: int = 0
    flag: UserFlag = field(default_factory=UserFlag)


@dataclass
class ChatMessage:
    user: User = field(default_factory=User)
    message: str = ""


@dataclass
class UserList:
    user: User = field(default_factory=User)
    status: bool = True  # True=입장, False=퇴장


@dataclass
class Balloon:
    user: User = field(default_factory=User)
    count: int = 0
    message: str = ""


@dataclass
class Adballoon:
    user: User = field(default_factory=User)
    count: int = 0


@dataclass
class Subscription:
    user: User = field(default_factory=User)
    count: int = 0


@dataclass
class Mission:
    user: User = field(default_factory=User)
    title: str = ""
    count: int = 0
