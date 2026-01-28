"""森空岛认证模块。

部分代码参考自 nonebot-plugin-skland
Copyright (c) 2025 FrostN0v0
MIT License
"""

import logging

import httpx

from ..const import HYPERGRYPH_BASE_URL, SKLAND_BASE_URL, SKLAND_APP_CODE, USER_AGENT
from .models import Credential

_LOGGER = logging.getLogger(__name__)


class AuthError(Exception):
    """认证错误。"""

    pass


class SklandAuth:
    """森空岛认证客户端。"""

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip",
            "Connection": "close",
        }

    async def get_grant_code(self, token: str) -> str:
        """使用 token 获取认证代码。

        Args:
            token: 用户 token（从森空岛 App 获取）

        Returns:
            认证代码 (grant_code)

        Raises:
            AuthError: 认证失败
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{HYPERGRYPH_BASE_URL}/user/oauth2/v2/grant",
                    json={
                        "appCode": SKLAND_APP_CODE,
                        "token": token,
                        "type": 0,
                    },
                    headers=self._headers,
                    timeout=10.0,
                )
                data = response.json()

                if data.get("status") != 0:
                    msg = data.get("msg", "未知错误")
                    raise AuthError(f"获取认证代码失败: {msg}")

                return data["data"]["code"]

            except httpx.HTTPError as e:
                raise AuthError(f"网络请求失败: {e}") from e

    async def get_cred(self, grant_code: str) -> Credential:
        """使用认证代码获取凭证。

        Args:
            grant_code: 认证代码

        Returns:
            凭证对象

        Raises:
            AuthError: 认证失败
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SKLAND_BASE_URL}/user/auth/generate_cred_by_code",
                    json={"code": grant_code, "kind": 1},
                    headers=self._headers,
                    timeout=10.0,
                )
                data = response.json()

                if data.get("code") != 0:
                    msg = data.get("message", "未知错误")
                    raise AuthError(f"获取凭证失败: {msg}")

                cred_data = data["data"]
                return Credential(
                    cred=cred_data["cred"],
                    token=cred_data["token"],
                    user_id=cred_data.get("userId"),
                )

            except httpx.HTTPError as e:
                raise AuthError(f"网络请求失败: {e}") from e

    async def refresh_token(self, cred: str) -> str:
        """刷新 token。

        Args:
            cred: 当前凭证

        Returns:
            新的 token

        Raises:
            AuthError: 刷新失败
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{SKLAND_BASE_URL}/auth/refresh",
                    headers={**self._headers, "cred": cred},
                    timeout=10.0,
                )
                data = response.json()

                if data.get("code") != 0:
                    msg = data.get("message", "未知错误")
                    raise AuthError(f"刷新 token 失败: {msg}")

                return data["data"]["token"]

            except httpx.HTTPError as e:
                raise AuthError(f"网络请求失败: {e}") from e

    async def authenticate(self, token: str) -> Credential:
        """完整的认证流程：token -> grant_code -> cred。

        Args:
            token: 用户 token

        Returns:
            凭证对象

        Raises:
            AuthError: 认证失败
        """
        _LOGGER.debug("开始认证流程")

        # 获取认证代码
        grant_code = await self.get_grant_code(token)
        _LOGGER.debug("已获取认证代码")

        # 获取凭证
        cred = await self.get_cred(grant_code)
        _LOGGER.debug("已获取凭证")

        return cred
