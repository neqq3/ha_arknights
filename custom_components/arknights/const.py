"""明日方舟 Home Assistant 集成常量定义。"""

from datetime import timedelta

# 集成域名
DOMAIN = "arknights"

# API 端点
SKLAND_BASE_URL = "https://zonai.skland.com/api/v1"
HYPERGRYPH_BASE_URL = "https://as.hypergryph.com"

# 应用代码
SKLAND_APP_CODE = "4ca99fa6b56cc2ba"

# 默认更新间隔
DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)

# 配置键
CONF_TOKEN = "token"
CONF_CRED = "cred"
CONF_CRED_TOKEN = "cred_token"
CONF_UID = "uid"
CONF_NICKNAME = "nickname"
CONF_CHANNEL_MASTER_ID = "channel_master_id"

# 理智恢复速率：每 6 分钟恢复 1 点
SANITY_RECOVERY_RATE = 360  # 秒

# 平台
PLATFORMS = ["sensor", "binary_sensor"]

# User-Agent
USER_AGENT = "Skland/1.32.1 (com.hypergryph.skland; build:103201004; Android 33; ) Okhttp/4.11.0"
