"""明日方舟 WebSocket API。

为前端卡片提供数据接口。
"""

import logging
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_register_websocket_api(hass: HomeAssistant) -> None:
    """注册 WebSocket API 命令。"""
    websocket_api.async_register_command(hass, ws_list_accounts)
    websocket_api.async_register_command(hass, ws_get_account_data)
    _LOGGER.debug("WebSocket API 已注册")


@websocket_api.websocket_command(
    {
        vol.Required("type"): "arknights/list_accounts",
    }
)
@callback
def ws_list_accounts(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """列出所有已配置的明日方舟账号。

    返回格式:
    {
        "accounts": [
            {"uid": "12345678", "name": "Dr.Doctor", "level": 120},
            ...
        ]
    }
    """
    accounts = []

    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        coordinator = data.get("coordinator")
        if not coordinator:
            continue

        player = coordinator.data
        if player:
            accounts.append({
                "uid": player.uid,
                "name": player.name,
                "level": player.level,
            })

    connection.send_result(msg["id"], {"accounts": accounts})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "arknights/get_account_data",
        vol.Required("uid"): str,
    }
)
@callback
def ws_get_account_data(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """获取账号完整数据。

    返回格式:
    {
        "uid": "12345678",
        "name": "Dr.Doctor",
        "level": 120,
        "sanity": { "current": 100, "max": 135, "minutes_to_full": 0 },
        "building": { ... } | null,
        ...
    }
    """
    uid = msg["uid"]

    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        coordinator = data.get("coordinator")
        if not coordinator:
            continue

        player = coordinator.data
        if player and player.uid == uid:
            # 构建响应数据
            response = {
                "uid": player.uid,
                "name": player.name,
                "level": player.level,
                "avatar_url": player.avatar_url,
                "secretary_id": player.secretary_id,
                "secretary_skin_id": player.secretary_skin_id,
                "resume": player.resume,
                "main_stage_progress": player.main_stage_progress,
                "char_count": player.char_count,
                "furniture_count": player.furniture_count,
                "skin_count": player.skin_count,
                "register_ts": player.register_ts,
                "last_online_ts": player.last_online_ts,
                # 理智
                "sanity": {
                    "current": player.sanity.current_now,
                    "max": player.sanity.max,
                    "minutes_to_full": player.sanity.minutes_to_full,
                    "complete_recovery_time": player.sanity.complete_recovery_time,
                },
            }

            # 基建信息（可能为 None）
            if player.building:
                response["building"] = {
                    "trading_stock": player.building.trading_stock,
                    "trading_stock_limit": player.building.trading_stock_limit,
                    "manufacture_complete": player.building.manufacture_complete,
                    "manufacture_capacity": player.building.manufacture_capacity,
                    "drone_current": player.building.drone_current,
                    "drone_max": player.building.drone_max,
                    "training_state": player.building.training_state,
                    "training_remaining_secs": player.building.training_remaining_secs,
                    "trainee_char_id": player.building.trainee_char_id,
                    "hire_refresh_count": player.building.hire_refresh_count,
                    "recruit_finished": player.building.recruit_finished,
                    "recruit_total": player.building.recruit_total,
                    "resting_count": player.building.resting_count,
                    "rested_count": player.building.rested_count,
                    "clue_own": player.building.clue_own,
                    "clue_received": player.building.clue_received,
                    "clue_collected": player.building.clue_collected,
                    "tired_count": player.building.tired_count,
                }
            else:
                response["building"] = None

            connection.send_result(msg["id"], response)
            return

    # 未找到账号
    connection.send_error(msg["id"], "not_found", f"账号 {uid} 未找到")
