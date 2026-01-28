"""明日方舟二进制传感器实体。"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_UID, CONF_NICKNAME
from .coordinator import ArknightsDataUpdateCoordinator
from .api.models import PlayerStatus


BINARY_SENSOR_DESCRIPTIONS: list[BinarySensorEntityDescription] = []


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置二进制传感器实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ArknightsDataUpdateCoordinator = data["coordinator"]

    entities = [
        ArknightsBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class ArknightsBinarySensor(
    CoordinatorEntity[ArknightsDataUpdateCoordinator], BinarySensorEntity
):
    """明日方舟二进制传感器实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ArknightsDataUpdateCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """初始化二进制传感器。"""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_UID]}_{description.key}"

        # 设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_UID])},
            name=f"Arknights - {entry.data[CONF_NICKNAME]}",
            manufacturer="Arknights HA Integration",
            model="Skland API Client",
            sw_version="1.0.0",
        )

    @property
    def is_on(self) -> bool | None:
        """获取传感器状态。"""
        if not self.coordinator.data:
            return None

        data: PlayerStatus = self.coordinator.data
        key = self.entity_description.key

        if key == "sanity_full":
            return data.sanity.current_now >= data.sanity.max

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """额外状态属性。"""
        if not self.coordinator.data:
            return None

        data: PlayerStatus = self.coordinator.data
        key = self.entity_description.key

        if key == "sanity_full":
            return {
                "sanity": data.sanity.current_now,
                "max_sanity": data.sanity.max,
            }

        return None
