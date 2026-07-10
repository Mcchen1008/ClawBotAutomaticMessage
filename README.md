# ClawBot微信虚拟商品自动售卖机器人

基于微信ClawBot的虚拟商品自动售卖系统，支持卡密充值、余额消费、自动发卡密。

## 功能特性

- 🤖 微信机器人私聊交互
- 👤 用户注册/登录体系（数字ID+密码）
- 📦 商品浏览、购买、自动发密
- 💳 充值卡密核销
- 💰 余额消费、账单记录
- 🌐 Web管理后台
- 🔌 API接口

## 项目结构

```
wechat-clawbot/
├── app/
│   ├── bot/              # 微信机器人模块
│   │   ├── client.py     # ClawBot API客户端
│   │   ├── session.py    # 会话管理
│   │   ├── dispatcher.py # 消息分发
│   │   └── handlers/     # 消息处理器
│   ├── db/               # 数据库操作层
│   ├── models/           # 数据模型
│   ├── web/              # Web管理后台
│   ├── config.py         # 配置
│   ├── database.py       # 数据库连接
│   └── main.py           # 入口
├── data/                 # 数据目录
└── main.py               # 启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 启动Web管理后台

```bash
uv run python main.py web
```

访问 http://localhost:8000/admin
默认账号：admin / admin123

### 4. 启动微信机器人

```bash
uv run python main.py
```

扫码登录微信机器人

## 用户指令

| 指令 | 说明 |
|------|------|
| 主页/菜单/帮助 | 打开商品面板 |
| 充值 | 进入充值通道 |
| 余额 | 查看账户余额 |
| 账单 | 查看消费/充值流水 |
| 卡密记录 | 查看已购买的卡密 |
| p | 上一页 |
| q | 下一页 |
| 退出登录 | 退出当前账号 |
| 说明/指令 | 查看帮助 |
| 客服/人工 | 联系客服 |
| 重置 | 重置会话状态 |

## Web管理功能

- 📊 数据概览（用户数、订单数、充值/消费总额）
- 📦 商品管理（增删改查、上下架）
- 🎫 商品卡密管理（批量导入）
- 💳 充值卡密管理（批量导入）
- 👥 用户管理
- 📋 订单管理
- 💰 流水记录

## API接口

| 接口 | 说明 |
|------|------|
| GET /api/v1/qrcode | 获取机器人登录二维码 |
| GET /api/v1/qrcode/status | 查询二维码状态 |
| GET /api/v1/users | 用户列表 |
| GET /api/v1/products | 商品列表 |
| POST /api/v1/products | 新增商品 |
| POST /api/v1/products/{id}/cards/batch | 批量导入商品卡密 |
| POST /api/v1/recharge-cards/batch | 批量导入充值卡密 |
| GET /api/v1/orders | 订单列表 |
| GET /api/v1/stats | 统计数据 |

## 数据库表

- users - 用户表
- products - 商品表
- product_cards - 商品卡密表
- recharge_cards - 充值卡密表
- orders - 订单表
- transactions - 流水表
