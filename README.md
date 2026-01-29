# 明日方舟 Home Assistant 集成

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

通过 [森空岛](https://skland.com/) API 在 Home Assistant 中查看明日方舟游戏数据。

## ✨ 功能

- 📊 **理智监控** - 实时显示当前理智值、最大理智、恢复时间
- 📈 **玩家信息** - 显示博士等级、干员数量等
- 🔔 **自动化支持** - 提供传感器和服务供自动化使用

## 📦 安装

### 方法一：HACS（推荐）

1. 打开 HACS
2. 点击右上角菜单 → **自定义存储库 (Custom repositories)**
3. 输入本仓库地址，类别选择 **Integration**
4. 在 HACS 中搜索 **Arknights** 并下载
5. 重启 Home Assistant

### 方法二：手动安装

1. 下载本仓库
2. 将 `custom_components/arknights` 文件夹复制到 Home Assistant 的 `config/custom_components/` 目录
3. 重启 Home Assistant

## ⚙️ 配置

1. 进入 **设置** → **设备与服务** → **添加集成**
2. 搜索 **Arknights** 或 **明日方舟**
3. 输入您的森空岛 Token

### 获取 Token

1. 打开森空岛 App
2. 进入 **设置** → **账号管理**
3. 复制 Token（可能需要使用抓包工具）

> ⚠️ **安全提示**：Token 是您账号的登录凭证，请勿泄露给他人！

## 📊 实体

配置完成后，将创建以下实体：

| 实体 | 类型 | 描述 |
|---|---|---|
| `sensor.arknights_sanity` | 传感器 | 当前理智值 |
| `sensor.arknights_sanity_recovery_time` | 传感器 | 理智完全恢复时间 |
| `sensor.arknights_sanity_minutes_to_full` | 传感器 | 理智恢复剩余分钟 |
| `sensor.arknights_level` | 传感器 | 博士等级 |
| `sensor.arknights_sanity_status` | 传感器 | 理智状态（已满/未满） |
| `sensor.arknights_sanity_max` | 传感器 | 最大理智（默认禁用） |
| `sensor.arknights_char_count` | 传感器 | 干员数量（默认禁用） |
| `sensor.arknights_trading_stock` | 传感器 | 贸易站库存 |
| `sensor.arknights_manufacture_complete` | 传感器 | 制造站产出 |
| `sensor.arknights_drone` | 传感器 | 无人机数量 |
| `sensor.arknights_training_state` | 传感器 | 训练室状态 |
| `sensor.arknights_hire_refresh_count` | 传感器 | 公招刷新次数 |
| `sensor.arknights_recruit_finished` | 传感器 | 公招完成数 |
| `sensor.arknights_clue_collected` | 传感器 | 线索收集进度 |
| `sensor.arknights_dormitory_rested` | 传感器 | 宿舍休息人数 |
| `sensor.arknights_tired_char_count` | 传感器 | 疲劳干员数量 |

## 🎮 服务

### arknights.sign
执行森空岛每日签到。如果不指定 `entry_id`，将对所有配置的角色执行签到。

**参数**：
- `entry_id` (可选): 配置条目 ID。

**自动化示例**：

```yaml
automation:
  - alias: "每日自动签到"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: arknights.sign
```

## 📱 自动化示例

### 理智满时通知

```yaml
automation:
  - alias: "理智满通知"
    trigger:
      - platform: state
        entity_id: sensor.arknights_sanity_status
        to: "full"
    action:
      - service: notify.mobile_app
        data:
          title: "明日方舟"
          message: "博士，理智已满！该上线了！"
```

### 理智快满时亮灯提醒

```yaml
automation:
  - alias: "理智快满亮灯"
    trigger:
      - platform: numeric_state
        entity_id: sensor.arknights_sanity
        above: 125
    action:
      - service: light.turn_on
        target:
          entity_id: light.desk_lamp
        data:
          color_name: yellow
```

### 基建满仓通知

```yaml
automation:
  - alias: "基建满仓通知"
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.arknights_trading_stock') | int >= 
             state_attr('sensor.arknights_trading_stock', 'limit') | int }}
    action:
      - service: notify.mobile_app
        data:
          title: "明日方舟"
          message: "博士，贸易站满仓了！快来收菜！"
```

## 🙏 致谢

本项目的 API 调用逻辑参考了 [nonebot-plugin-skland](https://github.com/FrostN0v0/nonebot-plugin-skland)。

```
部分代码参考自 nonebot-plugin-skland
Copyright (c) 2025 FrostN0v0
MIT License
```

## 📄 许可证

MIT License

## ⚠️ 免责声明

- 本项目仅供学习交流使用
- 数据由 [森空岛](https://skland.com/) 提供
- 请勿用于商业用途
- 使用本项目产生的任何风险由用户自行承担
