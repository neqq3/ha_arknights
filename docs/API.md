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
| `medal_count` | Integer | 蚀刻章数量 |
| `sanity` | Object | 理智信息 |
| `building` | Object \| Null | 基建信息 |
| `campaign` | Object \| Null | 剿灭作战信息 |
| `routine` | Object \| Null | 日常/周常任务 |
| `tower` | Object \| Null | 保全派驻信息 |
| `assist_chars` | Array | 助战干员列表 |

**Sanity 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `current` | Integer | 当前理智 |
| `max` | Integer | 理智上限 |
| `minutes_to_full` | Integer | 距离回满剩余分钟 |
| `complete_recovery_time` | Integer | 预计回满时间戳 (秒) |

**Building 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `trading_stock` | Integer | 贸易站订单数 |
| `manufacture_complete` | Integer | 制造站产出数 |
| `drone_current` | Integer | 无人机数量 |
| `training_state` | String | 训练室状态 ("空闲中", "训练中", "未建造") |
| `clue_board` | Object | 线索板状态, Key 为 "1"-"7", Value 为 Boolean (true=已搜集) |
| ... | ... | (其他基础字段) |

**Campaign (剿灭) 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `current` | Integer | 当前已获取合成玉 |
| `total` | Integer | 本周合成玉上限 (通常为 1800) |

**Routine (任务) 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `daily_current` | Integer | 日常任务完成数 |
| `daily_total` | Integer | 日常任务总数 |
| `weekly_current` | Integer | 周常任务完成数 |
| `weekly_total` | Integer | 周常任务总数 |

**Tower (保全) 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `higher_current` | Integer | 数据增补仪当前值 |
| `higher_total` | Integer | 数据增补仪上限 |
| `lower_current` | Integer | 数据增补条当前值 |
| `lower_total` | Integer | 数据增补条上限 |
| `term_ts` | Integer | 周期结束时间戳 |

**AssistChar (助战) 对象接口:**

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `char_id` | String | 干员 ID |
| `skin_id` | String | 皮肤 ID |
| `level` | Integer | 等级 |
| `evolve_phase` | Integer | 精英化阶段 (0-2) |
| `potential_rank` | Integer | 潜能等级 (0-5) |
| `skill_id` | String | 携带技能 ID |
| `skill_level` | Integer | 技能等级 |
| `specialize_level` | Integer | 专精等级 (0-3) |

**响应示例:**

```json
{
  "id": 25,
  "type": "result",
  "success": true,
  "result": {
    "uid": "12345678",
    "name": "Dr.Doctor",
    "level": 120,
    "medal_count": 500,
    "sanity": {
      "current": 130,
      "max": 135,
      "minutes_to_full": 30,
      "complete_recovery_time": 1706680000
    },
    "building": {
      "trading_stock": 5,
      "manufacture_complete": 12,
      "drone_current": 180,
      "clue_board": {
        "1": true, "2": false, "3": true, "4": true,
        "5": false, "6": true, "7": true
      }
    },
    "campaign": {
      "current": 1200,
      "total": 1800
    },
    "routine": {
      "daily_current": 10,
      "daily_total": 10,
      "weekly_current": 5,
      "weekly_total": 15
    },
    "tower": {
      "higher_current": 30,
      "higher_total": 30,
      "term_ts": 1707000000
    },
    "assist_chars": [
      {
        "char_id": "char_103_angel",
        "level": 90,
        "evolve_phase": 2,
        "specialize_level": 3
      }
    ]
  }
}
```

## 错误码

若请求失败，将返回标准的 Home Assistant WebSocket 错误响应。

- `not_found`: 指定 UID 的账号不存在。
