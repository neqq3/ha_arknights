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

import httpx

from ..const import SKLAND_BASE_URL, USER_AGENT
from .models import Credential, PlayerStatus, SanityInfo, SignResult, BindingCharacter

_LOGGER = logging.getLogger(__name__)


class RequestError(Exception):
    """请求错误。"""

    pass


class UnauthorizedError(RequestError):
    """认证过期错误。"""

    pass


class SklandClient:
    """森空岛 API 客户端。"""

    def __init__(self, credential: Credential) -> None:
        """初始化客户端。

        Args:
            credential: 森空岛凭证
        """
        self._credential = credential
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

        async with httpx.AsyncClient() as client:
            try:
                if method.lower() == "get":
                    response = await client.get(url, headers=headers, timeout=15.0)
                else:
                    json_body = json.dumps(body, ensure_ascii=False, separators=(", ", ": ")) if body else None
                    response = await client.post(
                        url,
                        headers={**headers, "Content-Type": "application/json"},
                        content=json_body,
                        timeout=15.0,
                    )

                data = response.json()
                code = data.get("code", 0)

                if code == 10000:
                    raise UnauthorizedError(data.get("message", "认证过期"))
                elif code == 10002:
                    raise UnauthorizedError(data.get("message", "凭证无效"))
                elif code != 0:
                    raise RequestError(data.get("message", f"请求失败，错误码: {code}"))

                return data

            except httpx.HTTPError as e:
                raise RequestError(f"网络请求失败: {e}") from e

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
        _LOGGER.debug("Raw player data: %s", player_data)
        status = player_data["status"]
        ap = status["ap"]
        secretary = status.get("secretary", {})
        avatar = status.get("avatar", {})

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
            char_count=status.get("charCnt", 0),
            furniture_count=status.get("furnitureCnt", 0),
            skin_count=status.get("skinCnt", 0),
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
