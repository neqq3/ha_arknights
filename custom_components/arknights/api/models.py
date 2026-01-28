"""明日方舟数据模型定义。

部分代码参考自 nonebot-plugin-skland
Copyright (c) 2025 FrostN0v0
MIT License
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math


@dataclass
class Credential:
    """森空岛凭证。"""

    cred: str
    """登录凭证"""
    token: str
    """登录凭证对应的 token（用于签名）"""
    user_id: str | None = None
    """用户 ID"""


@dataclass
class SanityInfo:
    """理智信息。"""

    current: int
    """当前理智（API 返回的快照值）"""
    max: int
    """最大理智"""
    last_ap_add_time: int
    """上次恢复时间戳"""
    complete_recovery_time: int
    """完全恢复时间戳"""

    @property
    def current_now(self) -> int:
        """计算当前实际理智值。"""
        if self.complete_recovery_time <= 0:
            return self.current

        current_time = datetime.now().timestamp()
        if current_time >= self.complete_recovery_time:
            return self.max

        # 每 6 分钟（360 秒）恢复 1 点
        ap_now = self.max - math.ceil((self.complete_recovery_time - current_time) / 360)
        return min(max(ap_now, 0), self.max)

    @property
    def recovery_time(self) -> datetime | None:
        """理智完全恢复时间。"""
        if self.complete_recovery_time <= 0:
            return None
        return datetime.fromtimestamp(self.complete_recovery_time, tz=timezone.utc)

    @property
    def minutes_to_full(self) -> int:
        """距离理智满还需多少分钟。"""
        if self.complete_recovery_time <= 0:
            return 0
        remaining = self.complete_recovery_time - datetime.now().timestamp()
        return max(0, int(remaining / 60))


@dataclass
class PlayerStatus:
    """玩家状态信息。"""

    uid: str
    """角色 UID"""
    name: str
    """角色名称"""
    level: int
    """等级"""
    sanity: SanityInfo
    """理智信息"""
    register_ts: int
    """注册时间戳"""
    last_online_ts: int
    """最后在线时间戳"""
    secretary_id: str
    """助理干员 ID"""
    secretary_skin_id: str
    """助理干员皮肤 ID"""
    avatar_url: str
    """头像 URL"""
    resume: str
    """个人简介"""
    main_stage_progress: str
    """主线进度"""
    char_count: int
    """干员数量"""
    furniture_count: int
    """家具数量"""
    skin_count: int
    """皮肤数量"""

    @property
    def register_date(self) -> str:
        """注册日期。"""
        return datetime.fromtimestamp(self.register_ts).strftime("%Y-%m-%d")


@dataclass
class SignResult:
    """签到结果。"""

    success: bool
    """是否成功"""
    message: str
    """结果消息"""
    awards: list[dict] = field(default_factory=list)
    """获得的奖励"""


@dataclass
class BindingCharacter:
    """绑定的游戏角色。"""

    uid: str
    """角色 UID"""
    nickname: str
    """昵称"""
    channel_master_id: str
    """渠道 ID（用于签到）"""
    channel_name: str
    """渠道名称"""
    is_official: bool
    """是否官服"""
    is_default: bool
    """是否默认角色"""
