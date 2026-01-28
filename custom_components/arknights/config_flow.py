"""明日方舟配置流程。"""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_CRED,
    CONF_CRED_TOKEN,
    CONF_UID,
    CONF_NICKNAME,
    CONF_CHANNEL_MASTER_ID,
)
from .api import SklandAuth, SklandClient
from .api.auth import AuthError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
    }
)


class ArknightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """明日方舟配置流程处理器。"""

    VERSION = 1

    def __init__(self) -> None:
        """初始化配置流程。"""
        self._token: str | None = None
        self._cred: str | None = None
        self._cred_token: str | None = None
        self._characters: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理用户输入步骤。"""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]

            try:
                # 验证 token 并获取凭证
                auth = SklandAuth()
                cred = await auth.authenticate(token)

                self._token = token
                self._cred = cred.cred
                self._cred_token = cred.token

                # 获取绑定的角色列表
                client = SklandClient(cred)
                characters = await client.get_binding()

                if not characters:
                    errors["base"] = "no_characters"
                elif len(characters) == 1:
                    # 只有一个角色，直接创建配置条目
                    char = characters[0]
                    return await self._create_entry(char)
                else:
                    # 多个角色，让用户选择
                    self._characters = [
                        {
                            "uid": c.uid,
                            "nickname": c.nickname,
                            "channel_master_id": c.channel_master_id,
                            "channel_name": c.channel_name,
                        }
                        for c in characters
                    ]
                    return await self.async_step_select_character()

            except AuthError as e:
                _LOGGER.error("认证失败: %s", e)
                errors["base"] = "auth_failed"
            except Exception as e:
                _LOGGER.exception("配置失败: %s", e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "token_help": "从森空岛 App 获取 Token",
            },
        )

    async def async_step_select_character(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理角色选择步骤。"""
        if user_input is not None:
            uid = user_input["character"]
            # 找到选中的角色
            for char in self._characters:
                if char["uid"] == uid:
                    from .api.models import BindingCharacter
                    character = BindingCharacter(
                        uid=char["uid"],
                        nickname=char["nickname"],
                        channel_master_id=char["channel_master_id"],
                        channel_name=char["channel_name"],
                        is_official=True,
                        is_default=False,
                    )
                    return await self._create_entry(character)

        # 构建角色选择列表
        character_options = {
            char["uid"]: f"{char['nickname']} ({char['channel_name']})"
            for char in self._characters
        }

        return self.async_show_form(
            step_id="select_character",
            data_schema=vol.Schema(
                {
                    vol.Required("character"): vol.In(character_options),
                }
            ),
        )

    async def _create_entry(self, character) -> FlowResult:
        """创建配置条目。"""
        # 检查是否已配置该角色
        await self.async_set_unique_id(f"{DOMAIN}_{character.uid}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{character.nickname} ({character.uid})",
            data={
                CONF_TOKEN: self._token,
                CONF_CRED: self._cred,
                CONF_CRED_TOKEN: self._cred_token,
                CONF_UID: character.uid,
                CONF_NICKNAME: character.nickname,
                CONF_CHANNEL_MASTER_ID: character.channel_master_id,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """获取选项流程。"""
        return ArknightsOptionsFlow(config_entry)


class ArknightsOptionsFlow(config_entries.OptionsFlow):
    """选项流程处理器。"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """初始化选项流程。"""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理选项配置。"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", 10),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
                }
            ),
        )
