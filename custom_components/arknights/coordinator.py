"""明日方舟数据协调器。"""

import logging
from datetime import timedelta
from typing import Callable, Awaitable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .api import SklandClient, Credential, PlayerStatus
from .api.client import UnauthorizedError, RequestError
from .api.auth import SklandAuth, AuthError

_LOGGER = logging.getLogger(__name__)


class ArknightsDataUpdateCoordinator(DataUpdateCoordinator[PlayerStatus]):
    """明日方舟数据协调器。

    负责定时从森空岛 API 获取玩家数据，并在 token 过期时自动刷新。
    支持完整的认证恢复：当 refresh_token 失败时，使用原始 token 重新认证。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: SklandClient,
        uid: str,
        nickname: str,
        original_token: str,
        on_credential_update: Callable[[Credential], Awaitable[None]] | None = None,
        update_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """初始化协调器。

        Args:
            hass: Home Assistant 实例
            client: API 客户端
            uid: 角色 UID
            nickname: 角色昵称
            original_token: 用户原始 token（用于重新认证）
            on_credential_update: 凭证更新回调（用于持久化新凭证）
            update_interval: 更新间隔
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{uid}",
            update_interval=update_interval,
        )
        self.client = client
        self.uid = uid
        self.nickname = nickname
        self._auth = SklandAuth()
        self._original_token = original_token
        self._on_credential_update = on_credential_update

    async def _try_refresh_token(self) -> bool:
        """尝试刷新 token。

        Returns:
            是否刷新成功
        """
        try:
            new_token = await self._auth.refresh_token(self.client.credential.cred)
            new_cred = Credential(
                cred=self.client.credential.cred,
                token=new_token,
                user_id=self.client.credential.user_id,
            )
            await self._update_credential(new_cred)
            _LOGGER.info("Token 刷新成功")
            return True
        except Exception as e:
            _LOGGER.warning("Token 刷新失败，将尝试重新认证: %s", e)
            return False

    async def _try_reauthenticate(self) -> bool:
        """使用原始 token 重新进行完整认证。

        Returns:
            是否重新认证成功
        """
        try:
            _LOGGER.info("正在使用原始 token 重新认证...")
            new_cred = await self._auth.authenticate(self._original_token)
            await self._update_credential(new_cred)
            _LOGGER.info("重新认证成功")
            return True
        except AuthError as e:
            _LOGGER.error("重新认证失败: %s", e)
            return False

    async def _update_credential(self, new_cred: Credential) -> None:
        """更新凭证并持久化。

        Args:
            new_cred: 新凭证
        """
        self.client.update_credential(new_cred)

        # 调用回调函数持久化凭证
        if self._on_credential_update:
            try:
                await self._on_credential_update(new_cred)
                _LOGGER.debug("凭证已持久化到 config_entry")
            except Exception as e:
                _LOGGER.warning("凭证持久化失败（不影响运行）: %s", e)

    async def _async_update_data(self) -> PlayerStatus:
        """从 API 获取最新数据。

        认证恢复策略：
        1. 首先尝试正常请求
        2. 若 Token 过期，尝试 refresh_token
        3. 若 refresh 失败，使用原始 token 重新完整认证
        4. 若仍失败，抛出 ConfigEntryAuthFailed

        Returns:
            玩家状态信息

        Raises:
            UpdateFailed: 更新失败（可重试）
            ConfigEntryAuthFailed: 认证彻底失败（需要重新配置）
        """
        try:
            return await self.client.get_player_info(self.uid)

        except UnauthorizedError as e:
            _LOGGER.warning("Token 过期，开始恢复流程: %s", e)

            # 第一步：尝试刷新 token
            if await self._try_refresh_token():
                try:
                    return await self.client.get_player_info(self.uid)
                except UnauthorizedError:
                    _LOGGER.warning("刷新后仍然失败，尝试完整重新认证")

            # 第二步：使用原始 token 重新完整认证
            if await self._try_reauthenticate():
                try:
                    return await self.client.get_player_info(self.uid)
                except UnauthorizedError as final_error:
                    _LOGGER.error("重新认证后仍然失败: %s", final_error)
                    raise ConfigEntryAuthFailed(
                        "认证已过期且无法恢复，请检查原始 Token 是否仍有效，或重新配置"
                    ) from final_error

            # 第三步：彻底失败
            raise ConfigEntryAuthFailed(
                "认证已过期，原始 Token 可能已失效，请重新配置"
            ) from e

        except RequestError as e:
            raise UpdateFailed(f"获取数据失败: {e}") from e

    async def async_sign(self, channel_master_id: str) -> dict:
        """执行签到。

        Args:
            channel_master_id: 渠道 ID

        Returns:
            签到结果
        """
        try:
            result = await self.client.sign(self.uid, channel_master_id)
            return {
                "success": result.success,
                "message": result.message,
                "awards": result.awards,
            }
        except UnauthorizedError:
            # 签到时遇到认证问题，触发一次数据刷新来恢复认证
            _LOGGER.warning("签到时遇到认证问题，尝试恢复...")
            try:
                await self.async_refresh()
                # 重试签到
                result = await self.client.sign(self.uid, channel_master_id)
                return {
                    "success": result.success,
                    "message": result.message,
                    "awards": result.awards,
                }
            except Exception as retry_error:
                _LOGGER.error("签到重试失败: %s", retry_error)
                return {
                    "success": False,
                    "message": f"认证失败: {retry_error}",
                    "awards": [],
                }
        except Exception as e:
            _LOGGER.error("签到失败: %s", e)
            return {
                "success": False,
                "message": str(e),
                "awards": [],
            }
