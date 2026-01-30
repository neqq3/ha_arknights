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
                # 线索板详情：显示1-7哪个有哪个没有
                clue_map = {
                    "RHINE": 1,
                    "PENGUIN": 2,
                    "BLACKSTEEL": 3,
                    "URSUS": 4,
                    "GLASGOW": 5,
                    "KJERAG": 6,
                    "RHODES": 7,
                }
                clue_board_status = {}
                for name, slot_id in clue_map.items():
                    clue_board_status[slot_id] = name in player.building.clue_board

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
                    "clue_board": clue_board_status,
                    "tired_count": player.building.tired_count,
                }
            else:
                response["building"] = None

            # 蚀刻章
            response["medal_count"] = player.medal_count

            # 剿灭
            if player.campaign:
                response["campaign"] = {
                    "current": player.campaign.current,
                    "total": player.campaign.total,
                }
            else:
                response["campaign"] = None

            # 日/周常任务
            if player.routine:
                response["routine"] = {
                    "daily_current": player.routine.daily_current,
                    "daily_total": player.routine.daily_total,
                    "weekly_current": player.routine.weekly_current,
                    "weekly_total": player.routine.weekly_total,
                }
            else:
                response["routine"] = None

            # 保全派驻
            if player.tower:
                response["tower"] = {
                    "higher_current": player.tower.higher_current,
                    "higher_total": player.tower.higher_total,
                    "lower_current": player.tower.lower_current,
                    "lower_total": player.tower.lower_total,
                    "term_ts": player.tower.term_ts,
                }
            else:
                response["tower"] = None

            # 助战干员
            response["assist_chars"] = [
                {
                    "char_id": ac.char_id,
                    "skin_id": ac.skin_id,
                    "level": ac.level,
                    "evolve_phase": ac.evolve_phase,
                    "potential_rank": ac.potential_rank,
                    "skill_id": ac.skill_id,
                    "skill_level": ac.skill_level,
                    "specialize_level": ac.specialize_level,
                }
                for ac in player.assist_chars
            ]

            connection.send_result(msg["id"], response)
            return

    # 未找到账号
    connection.send_error(msg["id"], "not_found", f"账号 {uid} 未找到")
