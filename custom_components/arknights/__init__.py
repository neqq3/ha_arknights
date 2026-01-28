"""明日方舟 Home Assistant 集成。

通过森空岛 API 获取明日方舟游戏数据。

API 调用逻辑参考自 nonebot-plugin-skland
https://github.com/FrostN0v0/nonebot-plugin-skland
Copyright (c) 2025 FrostN0v0
MIT License
"""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_CRED,
    CONF_CRED_TOKEN,
    CONF_UID,
    CONF_NICKNAME,
    CONF_CHANNEL_MASTER_ID,
    PLATFORMS,
)
from .api import SklandClient, Credential
from .coordinator import ArknightsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """设置集成。"""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置配置条目。"""
    _LOGGER.info("设置明日方舟集成: %s", entry.title)

    # 从配置中获取凭证
    cred = Credential(
        cred=entry.data[CONF_CRED],
        token=entry.data[CONF_CRED_TOKEN],
    )

    # 创建 API 客户端
    client = SklandClient(cred)

    # 获取更新间隔
    scan_interval = entry.options.get("scan_interval", 10)
    update_interval = timedelta(minutes=scan_interval)

    # 创建数据协调器
    coordinator = ArknightsDataUpdateCoordinator(
        hass,
        client,
        uid=entry.data[CONF_UID],
        nickname=entry.data[CONF_NICKNAME],
        update_interval=update_interval,
    )

    # 首次获取数据
    await coordinator.async_config_entry_first_refresh()

    # 保存协调器
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "channel_master_id": entry.data[CONF_CHANNEL_MASTER_ID],
    }

    # 设置平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 注册服务
    await _async_setup_services(hass)

    # 监听选项更新
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目。"""
    _LOGGER.info("卸载明日方舟集成: %s", entry.title)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """重新加载配置条目。"""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_setup_services(hass: HomeAssistant) -> None:
    """注册服务。"""

    async def async_sign_service(call: ServiceCall) -> None:
        """签到服务处理器。"""
        entry_id = call.data.get("entry_id")

        # 如果没有指定 entry_id，对所有角色签到
        if entry_id:
            entries = [entry_id]
        else:
            entries = list(hass.data[DOMAIN].keys())

        for eid in entries:
            if eid not in hass.data[DOMAIN]:
                continue

            data = hass.data[DOMAIN][eid]
            coordinator = data["coordinator"]
            channel_master_id = data["channel_master_id"]

            result = await coordinator.async_sign(channel_master_id)
            _LOGGER.info("签到结果 [%s]: %s", coordinator.nickname, result["message"])

    # 只注册一次服务
    if not hass.services.has_service(DOMAIN, "sign"):
        hass.services.async_register(
            DOMAIN,
            "sign",
            async_sign_service,
            schema=vol.Schema(
                {
                    vol.Optional("entry_id"): cv.string,
                }
            ),
        )
