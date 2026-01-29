"""明日方舟按钮实体。"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_UID, CONF_NICKNAME
from .coordinator import ArknightsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置按钮实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ArknightsDataUpdateCoordinator = data["coordinator"]
    channel_master_id = data["channel_master_id"]

    async_add_entities([ArknightsSignButton(coordinator, entry, channel_master_id)])


class ArknightsSignButton(CoordinatorEntity[ArknightsDataUpdateCoordinator], ButtonEntity):
    """明日方舟签到按钮。"""

    _attr_has_entity_name = True
    _attr_name = "签到"
    _attr_icon = "mdi:calendar-check"
    _attr_translation_key = "sign_in"

    def __init__(
        self,
        coordinator: ArknightsDataUpdateCoordinator,
        entry: ConfigEntry,
        channel_master_id: str,
    ) -> None:
        """初始化按钮。"""
        super().__init__(coordinator)
        self.entry = entry
        self.channel_master_id = channel_master_id
        self._attr_unique_id = f"{entry.data[CONF_UID]}_sign_button"
        
        # 记录上次签到结果
        self._last_sign_result: dict[str, Any] | None = None

        # 设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_UID])},
            name=f"Arknights - {entry.data[CONF_NICKNAME]}",
            manufacturer="Arknights HA Integration",
            model="Skland API Client",
            sw_version="1.0.0",
        )

    async def async_press(self) -> None:
        """按下按钮触发签到。"""
        _LOGGER.debug("手动触发签到: %s", self.coordinator.nickname)
        
        result = await self.coordinator.async_sign(self.channel_master_id)
        self._last_sign_result = result
        
        # 记录日志
        if result["success"]:
            _LOGGER.info("签到成功 [%s]: %s", self.coordinator.nickname, result["message"])
        else:
            _LOGGER.error("签到失败 [%s]: %s", self.coordinator.nickname, result["message"])

        # 发送持久化通知
        from homeassistant.components import persistent_notification
        persistent_notification.async_create(
            self.hass,
            f"角色: {self.coordinator.nickname}\n结果: {result['message']}",
            title="明日方舟签到结果",
            notification_id=f"arknights_sign_{self.entry.entry_id}"
        )
        
        # 更新实体状态属性以便在 UI 显示
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """额外状态属性。"""
        if self._last_sign_result:
            return {
                "last_sign_success": self._last_sign_result.get("success"),
                "last_sign_message": self._last_sign_result.get("message"),
                "last_sign_awards": self._last_sign_result.get("awards"),
            }
        return None
