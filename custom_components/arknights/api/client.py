"""森空岛 API 客户端。

部分代码参考自 nonebot-plugin-skland
Copyright (c) 2025 FrostN0v0
MIT License
"""

import hmac
import json
import hashlib
import logging
from datetime import datetime
from urllib.parse import urlparse

import aiohttp

from ..const import SKLAND_BASE_URL, USER_AGENT
from .models import Credential, PlayerStatus, SanityInfo, SignResult, BindingCharacter, BuildingInfo

_LOGGER = logging.getLogger(__name__)


class RequestError(Exception):
    """请求错误。"""

    pass


class UnauthorizedError(RequestError):
    """认证过期错误。"""

    pass


class SklandClient:
    """森空岛 API 客户端。"""

    def __init__(self, credential: Credential, session: aiohttp.ClientSession) -> None:
        """初始化客户端。

        Args:
            credential: 森空岛凭证
            session: aiohttp 会话
        """
        self._credential = credential
        self._session = session
        self._headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip",
            "Connection": "close",
        }
        self._header_for_sign = {
            "platform": "",
            "timestamp": "",
            "dId": "",
            "vName": "",
        }

    @property
    def credential(self) -> Credential:
        """获取当前凭证。"""
        return self._credential

    def update_credential(self, credential: Credential) -> None:
        """更新凭证。"""
        self._credential = credential

    def _get_sign_header(
        self,
        url: str,
        method: str,
        body: dict | None = None,
    ) -> dict:
        """生成带签名的请求头。

        签名算法:
        1. 构建 header_ca 字典（包含 timestamp）
        2. 拼接 secret = path + query/body + timestamp + header_ca_json
        3. secret 进行 HMAC-SHA256（使用 token 作为 key）
        4. 结果再进行 MD5 得到最终签名

        Args:
            url: 请求 URL
            method: 请求方法（get/post）
            body: POST 请求体

        Returns:
            带签名的请求头字典
        """
        timestamp = int(datetime.now().timestamp()) - 1
        header_ca = {**self._header_for_sign, "timestamp": str(timestamp)}

        parsed_url = urlparse(url)
        if method.lower() == "post":
            query_params = json.dumps(body, separators=(",", ":")) if body else ""
        else:
            query_params = parsed_url.query

        header_ca_str = json.dumps(header_ca, separators=(",", ":"))
        secret = f"{parsed_url.path}{query_params}{timestamp}{header_ca_str}"

        # HMAC-SHA256
        hex_secret = hmac.new(
            self._credential.token.encode("utf-8"),
            secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # MD5
        signature = hashlib.md5(hex_secret.encode("utf-8")).hexdigest()

        return {
            "cred": self._credential.cred,
            **self._headers,
            "sign": signature,
            **header_ca,
        }

    async def _request(
        self,
        method: str,
        url: str,
        body: dict | None = None,
    ) -> dict:
        """发送带签名的请求。

        Args:
            method: 请求方法
            url: 请求 URL
            body: 请求体

        Returns:
            响应数据

        Raises:
            UnauthorizedError: Token 过期
            RequestError: 请求失败
        """
        headers = self._get_sign_header(url, method, body)

        try:
            if method.lower() == "post":
                # Ensure JSON format matches the one used in _get_sign_header for signature calculation
                # _get_sign_header uses separators=(",", ":") and default ensure_ascii=True
                json_body = json.dumps(body, separators=(",", ":")) if body else None
                async with self._session.post(
                    url,
                    headers={**headers, "Content-Type": "application/json"},
                    data=json_body.encode("utf-8") if json_body else None,
                    timeout=aiohttp.ClientTimeout(total=15.0),
                ) as response:
                    data = await response.json()
            else:
                async with self._session.get(
                    url, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=15.0)
                ) as response:
                    data = await response.json()

            code = data.get("code", 0)

            if code == 10000:
                raise UnauthorizedError(data.get("message", "认证过期"))
            elif code == 10002:
                raise UnauthorizedError(data.get("message", "凭证无效"))
            elif code != 0:
                raise RequestError(data.get("message", f"请求失败，错误码: {code}"))

            return data

        except aiohttp.ClientError as e:
            _LOGGER.exception("Network error during request to %s", url)
            raise RequestError(f"网络请求失败: {e}") from e
        except (UnauthorizedError, RequestError):
            # 让这些错误直接传播，不要重新包装
            raise
        except Exception as e:
             _LOGGER.exception("Unexpected error during request to %s", url)
             # Catch other unexpected errors
             raise RequestError(f"请求发生错误: {type(e).__name__}: {e}") from e

    async def get_binding(self) -> list[BindingCharacter]:
        """获取绑定的游戏角色列表。

        Returns:
            绑定角色列表
        """
        url = f"{SKLAND_BASE_URL}/game/player/binding"
        data = await self._request("get", url)

        characters = []
        for app in data["data"]["list"]:
            # 只处理明日方舟 (appCode 可能是 arknights)
            if app.get("appCode") != "arknights":
                continue

            for binding in app.get("bindingList", []):
                characters.append(
                    BindingCharacter(
                        uid=binding["uid"],
                        nickname=binding.get("nickName", ""),
                        channel_master_id=binding.get("channelMasterId", "1"),
                        channel_name=binding.get("channelName", "官服"),
                        is_official=binding.get("isOfficial", True),
                        is_default=binding.get("isDefault", False),
                    )
                )

        return characters

    async def get_player_info(self, uid: str) -> PlayerStatus:
        """获取玩家信息。

        Args:
            uid: 角色 UID

        Returns:
            玩家状态信息
        """
        url = f"{SKLAND_BASE_URL}/game/player/info?uid={uid}"
        data = await self._request("get", url)

        player_data = data["data"]
        status = player_data["status"]
        ap = status["ap"]
        secretary = status.get("secretary", {})
        avatar = status.get("avatar", {})
        
        # 优先使用 API 返回的 charCnt，如果为 0 则用 chars 数组长度
        # 注意：chars 数组包含阿米娅的升变形态（char_1001_amiya2），
        # 但游戏/森空岛只计算为1人，所以需要排除
        chars = player_data.get("chars", [])
        char_count = status.get("charCnt", 0)
        if char_count == 0:
            # 统计时排除阿米娅升变形态
            char_count = sum(1 for c in chars if not c.get("charId", "").startswith("char_1001_amiya"))
        
        # 解析基建数据
        building_info = self._parse_building_data(player_data)

        return PlayerStatus(
            uid=status["uid"],
            name=status["name"],
            level=status["level"],
            sanity=SanityInfo(
                current=ap["current"],
                max=ap["max"],
                last_ap_add_time=ap.get("lastApAddTime", 0),
                complete_recovery_time=ap.get("completeRecoveryTime", 0),
            ),
            register_ts=status.get("registerTs", 0),
            last_online_ts=status.get("lastOnlineTs", 0),
            secretary_id=secretary.get("charId", ""),
            secretary_skin_id=secretary.get("skinId", ""),
            avatar_url=avatar.get("url", ""),
            resume=status.get("resume", ""),
            main_stage_progress=status.get("mainStageProgress", ""),
            char_count=char_count,
            furniture_count=status.get("furnitureCnt", 0),
            skin_count=status.get("skinCnt", 0),
            building=building_info,
        )

    async def sign(self, uid: str, channel_master_id: str) -> SignResult:
        """执行签到。

        Args:
            uid: 角色 UID
            channel_master_id: 渠道 ID

        Returns:
            签到结果
        """
        url = f"{SKLAND_BASE_URL}/game/attendance"
        body = {"uid": uid, "gameId": channel_master_id}

        try:
            data = await self._request("post", url, body)
            awards = []
            for award in data["data"].get("awards", []):
                awards.append({
                    "name": award.get("resource", {}).get("name", "未知"),
                    "count": award.get("count", 0),
                })

            award_text = ", ".join([f"{a['name']} x{a['count']}" for a in awards])
            return SignResult(
                success=True,
                message=f"签到成功！获得: {award_text}" if awards else "签到成功！",
                awards=awards,
            )

        except RequestError as e:
            # 检查是否是"已签到"的情况
            error_msg = str(e)
            if "已经" in error_msg or "签到" in error_msg:
                return SignResult(
                    success=True,
                    message="今日已签到",
                    awards=[],
                )
            return SignResult(
                success=False,
                message=f"签到失败: {error_msg}",
                awards=[],
            )

    def _parse_building_data(self, player_data: dict) -> BuildingInfo:
        """解析基建数据。

        Args:
            player_data: API 返回的玩家数据

        Returns:
            基建信息
        """
        building = player_data.get("building", {})
        if not building:
            return BuildingInfo()

        # 解析贸易站
        trading_stock = 0
        trading_stock_limit = 0
        tradings = building.get("tradings", [])
        current_time = datetime.now().timestamp()
        for trading in tradings:
            # 库存上限
            trading_stock_limit += trading.get("stockLimit", 0)
            # 已有库存
            stock = trading.get("stock", [])
            trading_stock += len(stock)
            # 如果订单正在生产中且已完成
            complete_work_time = trading.get("completeWorkTime", 0)
            if complete_work_time > 0 and current_time >= complete_work_time:
                trading_stock += 1

        # 解析制造站
        manufacture_complete = 0
        manufacture_capacity = 0
        manufactures = building.get("manufactures", [])
        for manu in manufactures:
            # 已完成数量
            manufacture_complete += manu.get("complete", 0)
            # 容量（简化计算，使用容量/重量）
            capacity = manu.get("capacity", 0)
            weight = manu.get("weight", 1)
            if weight > 0:
                manufacture_capacity += capacity // weight

        # 解析无人机
        labor = building.get("labor", {})
        drone_current = labor.get("value", 0)
        drone_max = labor.get("maxValue", 0)
        # 计算实时无人机数量
        if drone_current < drone_max:
            last_update = labor.get("lastUpdateTime", 0)
            remain_secs = labor.get("remainSecs", 0)
            if last_update > 0 and remain_secs > 0:
                elapsed = current_time - last_update
                recovery_rate = remain_secs / max(drone_max - drone_current, 1)
                if recovery_rate > 0:
                    additional = int(elapsed / recovery_rate)
                    drone_current = min(drone_current + additional, drone_max)

        # 解析训练室
        training = building.get("training", {})
        training_state = "空闲"
        training_remaining_secs = 0
        trainee_char_id = ""
        if training:
            trainee = training.get("trainee", {})
            if trainee and trainee.get("charId"):
                trainee_char_id = trainee.get("charId", "")
                target_skill = trainee.get("targetSkill", -1)
                if target_skill >= 0:
                    skill_names = ["1技能", "2技能", "3技能"]
                    skill_name = skill_names[target_skill] if target_skill < 3 else f"{target_skill + 1}技能"
                    training_state = f"训练中 ({skill_name})"
                    training_remaining_secs = max(0, training.get("remainSecs", 0))

        # 解析公招
        hire = building.get("hire", {})
        hire_refresh_count = hire.get("refreshCount", 0) if hire else 0
        hire_complete_time = hire.get("completeWorkTime", 0) if hire else 0

        # 解析公招槽位
        recruit = player_data.get("recruit", [])
        recruit_finished = 0
        recruit_total = len(recruit)
        for slot in recruit:
            # state == 1 表示已完成
            if slot.get("state", 0) == 1:
                recruit_finished += 1

        # 解析宿舍/休息进度
        dormitories = building.get("dormitories", [])
        resting_count = 0
        rested_count = 0
        for dorm in dormitories:
            dorm_chars = dorm.get("chars", [])
            dorm_level = dorm.get("level", 1)
            dorm_comfort = dorm.get("comfort", 0)
            for char in dorm_chars:
                resting_count += 1
                # 计算是否休息完成（ap >= 8640000 表示满体力）
                char_ap = char.get("ap", 0)
                last_ap_add_time = char.get("lastApAddTime", 0)
                # 简化计算：ap 恢复速率约 1.5 + level*0.1 + comfort*0.0004
                if last_ap_add_time > 0:
                    ap_gain_rate = 1.5 + dorm_level * 0.1 + 0.0004 * dorm_comfort
                    time_elapsed = current_time - last_ap_add_time
                    ap_now = min(char_ap + time_elapsed * ap_gain_rate, 8640000)
                    if ap_now >= 8640000:
                        rested_count += 1

        # 解析线索
        meeting = building.get("meeting", {})
        clue = meeting.get("clue", {}) if meeting else {}
        clue_own = clue.get("own", 0)
        clue_received = clue.get("received", 0)
        clue_board = clue.get("board", [])

        # 解析疲劳干员
        tired_chars = building.get("tiredChars", [])
        tired_count = len(tired_chars)

        return BuildingInfo(
            trading_stock=trading_stock,
            trading_stock_limit=trading_stock_limit,
            manufacture_complete=manufacture_complete,
            manufacture_capacity=manufacture_capacity,
            drone_current=drone_current,
            drone_max=drone_max,
            training_state=training_state,
            training_remaining_secs=training_remaining_secs,
            trainee_char_id=trainee_char_id,
            hire_refresh_count=hire_refresh_count,
            hire_complete_time=hire_complete_time,
            recruit_finished=recruit_finished,
            recruit_total=recruit_total,
            resting_count=resting_count,
            rested_count=rested_count,
            clue_own=clue_own,
            clue_received=clue_received,
            clue_board=clue_board,
            tired_count=tired_count,
        )
