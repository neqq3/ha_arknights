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
    # 基建传感器
    SensorEntityDescription(
        key="trading_stock",
        name="贸易站库存",
        icon="mdi:package-variant",
        native_unit_of_measurement="单",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="manufacture_complete",
        name="制造站产出",
        icon="mdi:factory",
        native_unit_of_measurement="个",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="drone",
        name="无人机",
        icon="mdi:quadcopter",
        native_unit_of_measurement="架",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="training_state",
        name="训练室状态",
        icon="mdi:arm-flex",
        translation_key="training_state",
    ),
    SensorEntityDescription(
        key="training_remaining",
        name="训练剩余时间",
        icon="mdi:timer",
        native_unit_of_measurement="分钟",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="hire_refresh_count",
        name="公招刷新次数",
        icon="mdi:refresh",
        native_unit_of_measurement="次",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="recruit_finished",
        name="公招完成数",
        icon="mdi:account-check",
        native_unit_of_measurement="个",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="clue_collected",
        name="线索收集",
        icon="mdi:puzzle",
        native_unit_of_measurement="个",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="dormitory_rested",
        name="宿舍休息完成",
        icon="mdi:bed",
        native_unit_of_measurement="人",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="tired_char_count",
        name="疲劳干员",
        icon="mdi:sleep-off",
        native_unit_of_measurement="人",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # 剿灭与任务
    SensorEntityDescription(
        key="campaign_reward",
        name="剿灭进度",
        icon="mdi:skull-crossbones",
        native_unit_of_measurement="合成玉",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="daily_task",
        name="日常任务",
        icon="mdi:calendar-check",
    ),
    SensorEntityDescription(
        key="weekly_task",
        name="周常任务",
        icon="mdi:calendar-week",
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
        # 基建传感器
        elif key == "trading_stock":
            return data.building.trading_stock if data.building else 0
        elif key == "manufacture_complete":
            return data.building.manufacture_complete if data.building else 0
        elif key == "drone":
            return data.building.drone_current if data.building else 0
        elif key == "training_state":
            return data.building.training_state if data.building else "空闲"
        elif key == "training_remaining":
            return data.building.training_remaining_minutes if data.building else 0
        elif key == "hire_refresh_count":
            return data.building.hire_refresh_count if data.building else 0
        elif key == "recruit_finished":
            return data.building.recruit_finished if data.building else 0
        elif key == "clue_collected":
            return data.building.clue_collected if data.building else 0
        elif key == "dormitory_rested":
            return data.building.rested_count if data.building else 0
        elif key == "tired_char_count":
            return data.building.tired_count if data.building else 0

        # 剿灭与任务
        elif key == "campaign_reward":
            return data.campaign.current if data.campaign else 0
        elif key == "daily_task":
            if data.routine:
                return f"{data.routine.daily_current}/{data.routine.daily_total}"
            return "0/0"
        elif key == "weekly_task":
            if data.routine:
                return f"{data.routine.weekly_current}/{data.routine.weekly_total}"
            return "0/0"

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
        # 基建传感器额外属性
        elif key == "trading_stock" and data.building:
            return {
                "current": data.building.trading_stock,
                "limit": data.building.trading_stock_limit,
                "percentage": round(data.building.trading_stock / max(data.building.trading_stock_limit, 1) * 100, 1),
            }
        elif key == "manufacture_complete" and data.building:
            return {
                "current": data.building.manufacture_complete,
                "capacity": data.building.manufacture_capacity,
                "percentage": round(data.building.manufacture_complete / max(data.building.manufacture_capacity, 1) * 100, 1),
            }
        elif key == "drone" and data.building:
            return {
                "current": data.building.drone_current,
                "max": data.building.drone_max,
                "percentage": round(data.building.drone_current / max(data.building.drone_max, 1) * 100, 1),
            }
        elif key == "training_state" and data.building:
            return {
                "remaining_minutes": data.building.training_remaining_minutes,
                "trainee_char_id": data.building.trainee_char_id,
            }
        elif key == "recruit_finished" and data.building:
            return {
                "finished": data.building.recruit_finished,
                "total": data.building.recruit_total,
            }
        elif key == "clue_collected" and data.building:
            return {
                "own": data.building.clue_own,
                "received": data.building.clue_received,
                "total": 7,
                # 哪些线索已拥有
                "board": [bool(c) for c in data.building.clue_board],
            }
        elif key == "dormitory_rested" and data.building:
            return {
                "rested": data.building.rested_count,
                "resting": data.building.resting_count,
            }
        # 剿灭与任务额外属性
        elif key == "campaign_reward" and data.campaign:
            return {
                "current": data.campaign.current,
                "total": data.campaign.total,
                "missing": data.campaign.total - data.campaign.current,
            }
        elif key == "daily_task" and data.routine:
            return {
                "current": data.routine.daily_current,
                "total": data.routine.daily_total,
                "percentage": round(data.routine.daily_current / max(data.routine.daily_total, 1) * 100, 1),
            }
        elif key == "weekly_task" and data.routine:
            return {
                "current": data.routine.weekly_current,
                "total": data.routine.weekly_total,
                "percentage": round(data.routine.weekly_current / max(data.routine.weekly_total, 1) * 100, 1),
            }

        return None
