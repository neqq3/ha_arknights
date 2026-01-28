"""明日方舟数据协调器。"""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .api import SklandClient, Credential, PlayerStatus
from .api.client import UnauthorizedError, RequestError
from .api.auth import SklandAuth

_LOGGER = logging.getLogger(__name__)


class ArknightsDataUpdateCoordinator(DataUpdateCoordinator[PlayerStatus]):
    """明日方舟数据协调器。

    负责定时从森空岛 API 获取玩家数据，并在 token 过期时自动刷新。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: SklandClient,
        uid: str,
        nickname: str,
        update_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """初始化协调器。

        Args:
            hass: Home Assistant 实例
            client: API 客户端
            uid: 角色 UID
            nickname: 角色昵称
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

    async def _async_update_data(self) -> PlayerStatus:
        """从 API 获取最新数据。

        Returns:
            玩家状态信息

        Raises:
            UpdateFailed: 更新失败
            ConfigEntryAuthFailed: 认证失败
        """
        try:
            return await self.client.get_player_info(self.uid)

        except UnauthorizedError as e:
            _LOGGER.warning("Token 过期，尝试刷新: %s", e)

            try:
                # 尝试刷新 token
                new_token = await self._auth.refresh_token(self.client.credential.cred)
                new_cred = Credential(
                    cred=self.client.credential.cred,
                    token=new_token,
                    user_id=self.client.credential.user_id,
                )
                self.client.update_credential(new_cred)
                _LOGGER.info("Token 刷新成功")

                # 重试请求
                return await self.client.get_player_info(self.uid)

            except Exception as refresh_error:
                _LOGGER.error("Token 刷新失败: %s", refresh_error)
                raise ConfigEntryAuthFailed("认证已过期，请重新配置") from refresh_error

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
        except Exception as e:
            _LOGGER.error("签到失败: %s", e)
            return {
                "success": False,
                "message": str(e),
                "awards": [],
            }
