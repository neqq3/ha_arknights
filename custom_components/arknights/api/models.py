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
    medal_count: int = 0
    """蚀刻章数量"""
    building: "BuildingInfo | None" = None
    """基建信息"""
    campaign: "CampaignInfo | None" = None
    """剿灭信息"""
    routine: "RoutineInfo | None" = None
    """日/周常任务"""
    tower: "TowerInfo | None" = None
    """保全派驻"""
    assist_chars: list = field(default_factory=list)
    """助战干员列表"""

    @property
    def register_date(self) -> str:
        """注册日期。"""
        return datetime.fromtimestamp(self.register_ts).strftime("%Y-%m-%d")


@dataclass
class CampaignInfo:
    """剿灭作战信息。"""

    current: int = 0
    """当前已领取合成玉"""
    total: int = 1800
    """本周可领取上限"""


@dataclass
class RoutineInfo:
    """日/周常任务进度。"""

    daily_current: int = 0
    """每日任务完成数"""
    daily_total: int = 0
    """每日任务总数"""
    weekly_current: int = 0
    """每周任务完成数"""
    weekly_total: int = 0
    """每周任务总数"""


@dataclass
class TowerInfo:
    """保全派驻信息。"""

    higher_current: int = 0
    """数据增补仪当前"""
    higher_total: int = 0
    """数据增补仪上限"""
    lower_current: int = 0
    """数据增补条当前"""
    lower_total: int = 0
    """数据增补条上限"""
    term_ts: int = 0
    """刷新时间戳"""


@dataclass
class AssistCharInfo:
    """助战干员信息。"""

    char_id: str
    """干员 ID"""
    skin_id: str
    """皮肤 ID"""
    level: int
    """等级"""
    evolve_phase: int
    """精英化阶段"""
    potential_rank: int
    """潜能等级"""
    skill_id: str = ""
    """选择的技能 ID"""
    skill_level: int = 0
    """技能等级"""
    specialize_level: int = 0
    """专精等级"""


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


@dataclass
class BuildingInfo:
    """基建信息。"""

    # 贸易站
    trading_stock: int = 0
    """贸易站当前库存订单数"""
    trading_stock_limit: int = 0
    """贸易站库存上限"""

    # 制造站
    manufacture_complete: int = 0
    """制造站已完成数量"""
    manufacture_capacity: int = 0
    """制造站总产能"""

    # 无人机
    drone_current: int = 0
    """当前无人机数量"""
    drone_max: int = 0
    """最大无人机数量"""

    # 训练室
    training_state: str = "空闲"
    """训练室状态"""
    training_remaining_secs: int = 0
    """训练剩余秒数"""
    trainee_char_id: str = ""
    """正在训练的干员 ID"""

    # 公招
    hire_refresh_count: int = 0
    """公招可刷新次数"""
    hire_complete_time: int = 0
    """公招刷新恢复时间戳"""

    # 公招槽位
    recruit_finished: int = 0
    """已完成的公招数量"""
    recruit_total: int = 0
    """公招槽位总数"""

    # 宿舍/休息
    resting_count: int = 0
    """正在休息的干员数量"""
    rested_count: int = 0
    """已休息完成的干员数量"""

    # 线索
    clue_own: int = 0
    """自有线索数量"""
    clue_received: int = 0
    """收到的线索数量"""
    clue_board: list = None  # type: ignore
    """线索板状态 (7个位置)"""

    # 干员疲劳
    tired_count: int = 0
    """疲劳干员数量"""

    def __post_init__(self):
        if self.clue_board is None:
            self.clue_board = []

    @property
    def training_remaining_minutes(self) -> int:
        """训练剩余分钟数。"""
        return max(0, int(self.training_remaining_secs / 60))

    @property
    def hire_refresh_remaining_minutes(self) -> int:
        """公招刷新恢复剩余分钟。"""
        if self.hire_refresh_count >= 3:
            return 0
        remaining = self.hire_complete_time - datetime.now().timestamp()
        return max(0, int(remaining / 60))

    @property
    def clue_collected(self) -> int:
        """已收集的线索数量（7个中的几个）。"""
        return len([c for c in self.clue_board if c])

