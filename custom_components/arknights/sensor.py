"""明日方舟传感器实体。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_UID, CONF_NICKNAME
from .coordinator import ArknightsDataUpdateCoordinator
from .api.models import PlayerStatus


SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="sanity",
        name="理智",
        icon="mdi:brain",
        native_unit_of_measurement="点",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="sanity_max",
        name="最大理智",
        icon="mdi:brain",
        native_unit_of_measurement="点",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="sanity_recovery_time",
        name="理智恢复时间",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="sanity_minutes_to_full",
        name="理智恢复剩余",
        icon="mdi:timer-sand",
        native_unit_of_measurement="分钟",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="level",
        name="等级",
        icon="mdi:account-star",
        native_unit_of_measurement="级",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="char_count",
        name="干员数量",
        icon="mdi:account-group",
        native_unit_of_measurement="人",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="sanity_status",
        name="理智状态",
        icon="mdi:alert-circle",
        translation_key="sanity_status",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ArknightsDataUpdateCoordinator = data["coordinator"]

    entities = [
        ArknightsSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class ArknightsSensor(CoordinatorEntity[ArknightsDataUpdateCoordinator], SensorEntity):
    """明日方舟传感器实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ArknightsDataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """初始化传感器。"""
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
    def native_value(self) -> Any:
        """获取传感器值。"""
        if not self.coordinator.data:
            return None

        data: PlayerStatus = self.coordinator.data
        key = self.entity_description.key

        if key == "sanity":
            return data.sanity.current_now
        elif key == "sanity_max":
            return data.sanity.max
        elif key == "sanity_recovery_time":
            recovery_time = data.sanity.recovery_time
            # 如果已满，返回 None
            if recovery_time is None or data.sanity.current_now >= data.sanity.max:
                return None
            return recovery_time
        elif key == "sanity_minutes_to_full":
            if data.sanity.current_now >= data.sanity.max:
                return 0
            return data.sanity.minutes_to_full
        elif key == "level":
            return data.level
        elif key == "char_count":
            return data.char_count
        elif key == "sanity_status":
            if data.sanity.current_now >= data.sanity.max:
                return "full"
            return "not_full"

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """额外状态属性。"""
        if not self.coordinator.data:
            return None

        data: PlayerStatus = self.coordinator.data
        key = self.entity_description.key

        if key == "sanity":
            return {
                "current": data.sanity.current_now,
                "max": data.sanity.max,
                "percentage": round(data.sanity.current_now / data.sanity.max * 100, 1),
                "recovery_time": data.sanity.recovery_time.isoformat() if data.sanity.recovery_time else None,
                "minutes_to_full": data.sanity.minutes_to_full,
            }
        elif key == "level":
            return {
                "name": data.name,
                "uid": data.uid,
                "register_date": data.register_date,
                "main_stage_progress": data.main_stage_progress,
                "resume": data.resume,
            }
        elif key == "sanity_status":
            return {
                "sanity": data.sanity.current_now,
                "max_sanity": data.sanity.max,
            }

        return None
