# WebSocket API 参考文档

本文档描述了 `arknights` 集成提供的 WebSocket API 接口。前端卡片可通过 Home Assistant 的 WebSocket 连接调用这些接口以获取数据。

## 概述

所有命令均需通过 Home Assistant WebSocket 协议发送。调用方需经过身份验证。

## 接口列表

### 1. 列出账号 (List Accounts)

获取当前 Home Assistant 实例中已配置的所有明日方舟账号摘要信息。

**命令类型 (Type):** `arknights/list_accounts`

**请求参数:**

无

**请求示例:**

```json
{
  "id": 24,
  "type": "arknights/list_accounts"
}
```

**响应数据:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `accounts` | Array | 账号列表 |

**Account 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `uid` | String | 游戏内 UID (唯一标识符) |
| `name` | String | 游戏内昵称 |
| `level` | Integer | 博士等级 |

**响应示例:**

```json
{
  "id": 24,
  "type": "result",
  "success": true,
  "result": {
    "accounts": [
      {
        "uid": "12345678",
        "name": "Dr.Example",
        "level": 120
      },
      {
        "uid": "87654321",
        "name": "Dr.Test",
        "level": 85
      }
    ]
  }
}
```

---

### 2. 获取账号数据 (Get Account Data)

获取指定账号的详细游戏数据，包括理智、基建、干员统计等。

**命令类型 (Type):** `arknights/get_account_data`

**请求参数:**

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `uid` | String | 是 | 目标账号的 UID |

**请求示例:**

```json
{
  "id": 25,
  "type": "arknights/get_account_data",
  "uid": "12345678"
}
```

**响应数据:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `uid` | String | 游戏 UID |
| `name` | String | 昵称 |
| `level` | Integer | 等级 |
| `avatar_url` | String | 头像 URL |
| `secretary_id` | String | 助理干员 ID |
| `sanity` | Object | 理智信息 |
| `building` | Object \| Null | 基建信息 (若未开通或获取失败则为 null) |
| ... | ... | 其他基础统计字段 (如 `skin_count`, `char_count`) |

**Sanity 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `current` | Integer | 当前计算后的理智值 |
| `max` | Integer | 理智上限 |
| `minutes_to_full` | Integer | 距离回满剩余分钟数 |
| `complete_recovery_time` | Integer | 预计回满时间戳 (秒) |

**Building 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `trading_stock` | Integer | 贸易站待收取订单数 |
| `manufacture_complete` | Integer | 制造站已完成产物数 |
| `drone_current` | Integer | 当前无人机数量 |
| `training_state` | String | 训练室状态 |
| `labor_meeting` | ... | (见响应示例) |

**响应示例:**

```json
{
  "id": 25,
  "type": "result",
  "success": true,
  "result": {
    "uid": "12345678",
    "name": "Dr.Example",
    "level": 120,
    "sanity": {
      "current": 125,
      "max": 135,
      "minutes_to_full": 60,
      "complete_recovery_time": 1706680000
    },
    "building": {
      "trading_stock": 5,
      "manufacture_complete": 12,
      "drone_current": 180,
      "training_state": "训练中",
      "tired_count": 0
    }
  }
}
```

## 错误码

若请求失败，将返回标准的 Home Assistant WebSocket 错误响应。

- `not_found`: 指定 UID 的账号不存在。
