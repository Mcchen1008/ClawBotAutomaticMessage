# ClawBot微信虚拟商品自动售卖机器人

## 项目简介

本项目是一个基于微信ClawBot API的虚拟商品自动售卖系统，采用Python开发，使用SQLite数据库存储数据，配套Web管理后台和RESTful API接口。

### 核心特性

- 🤖 微信机器人私聊交互 - 用户通过微信与机器人对话完成购买
- 👤 用户注册/登录体系 - 数字ID+密码的账号系统
- 📦 商品管理 - 上架、下架、批量导入卡密
- 💳 充值卡密核销 - 支持批量导入充值卡密
- 💰 余额消费 - 用户充值后使用余额购买商品
- 🎁 自动发密 - 购买后自动发送商品卡密
- 🌐 Web管理后台 - 商品、用户、订单、卡密全管理
- 🔌 RESTful API - 支持第三方系统集成

### 技术栈

- **Python 3.10+** - 编程语言
- **FastAPI** - Web框架和API接口
- **SQLite** - 轻量级数据库
- **httpx** - 异步HTTP客户端
- **Jinja2** - 模板引擎
- **bcrypt** - 密码哈希

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户端（微信）                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    微信机器人                         │   │
│  │  - 注册/登录                                          │   │
│  │  - 商品浏览/购买                                       │   │
│  │  - 充值/余额查询                                       │   │
│  │  - 账单/卡密记录                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      服务器端                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  微信ClawBot API                      │   │
│  │  - 二维码登录                                        │   │
│  │  - 消息收发                                          │   │
│  │  - 状态轮询                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↕                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              业务逻辑层（Python）                    │   │
│  │  - 会话管理                                          │   │
│  │  - 消息处理                                          │   │
│  │  - 业务逻辑                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↕                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  数据存储层                          │   │
│  │  - SQLite数据库                                      │   │
│  │  - 用户表                                            │   │
│  │  - 商品表                                            │   │
│  │  - 卡密表                                            │   │
│  │  - 订单表                                            │   │
│  │  - 流水表                                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    管理端（Web浏览器）                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Web管理后台（FastAPI）                 │   │
│  │  - 商品管理                                          │   │
│  │  - 卡密管理                                          │   │
│  │  - 用户管理                                          │   │
│  │  - 订单管理                                          │   │
│  │  - 流水对账                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  RESTful API                        │   │
│  │  - 数据查询接口                                      │   │
│  │  - 卡密管理接口                                      │   │
│  │  - 统计接口                                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
wechat-clawbot/
├── app/                          # 应用主目录
│   ├── bot/                      # 微信机器人模块
│   │   ├── client.py            # ClawBot API客户端
│   │   ├── session.py            # 会话管理
│   │   ├── dispatcher.py         # 消息分发器
│   │   └── handlers/             # 消息处理器
│   │       ├── auth_handler.py   # 注册/登录处理器
│   │       ├── product_handler.py # 商品/购买处理器
│   │       ├── recharge_handler.py # 充值处理器
│   │       └── query_handler.py  # 查询处理器
│   ├── db/                       # 数据库操作层
│   │   ├── user_db.py           # 用户CRUD
│   │   ├── product_db.py        # 商品CRUD
│   │   ├── card_db.py           # 卡密CRUD
│   │   ├── order_db.py          # 订单CRUD
│   │   └── transaction_db.py    # 流水CRUD
│   ├── models/                   # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── product.py          # 商品模型
│   │   ├── card.py             # 卡密模型
│   │   ├── order.py            # 订单模型
│   │   └── transaction.py      # 流水模型
│   ├── web/                      # Web管理后台
│   │   ├── app.py              # FastAPI应用
│   │   └── templates/           # HTML模板
│   │       ├── base.html       # 基础模板
│   │       ├── dashboard.html  # 仪表盘
│   │       ├── products.html   # 商品管理
│   │       ├── recharge_cards.html # 充值卡密
│   │       ├── users.html      # 用户管理
│   │       ├── orders.html     # 订单管理
│   │       └── transactions.html # 流水记录
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   └── main.py                 # 应用入口
├── data/                        # 数据目录（运行时创建）
│   └── bot.db                 # SQLite数据库文件
├── docs/                        # 文档目录
│   ├── README.md               # 项目说明
│   ├── ARCHITECTURE.md         # 架构文档
│   ├── API.md                  # API接口文档
│   ├── USER_GUIDE.md           # 用户使用指南
│   ├── ADMIN_GUIDE.md          # 管理员使用指南
│   └── DATABASE.md             # 数据库设计文档
├── .env.example                # 环境变量示例
├── pyproject.toml              # 项目配置
├── main.py                     # 启动脚本
├── uv.lock                     # 依赖锁定文件
└── README.md                   # 快速开始
```

---

## 数据库设计

### 数据表结构

#### 1. 用户表（users）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| user_id | TEXT | 用户ID（6位数字，唯一） |
| password_hash | TEXT | 密码哈希 |
| balance | REAL | 账户余额 |
| wechat_id | TEXT | 微信ID（唯一） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 2. 商品表（products）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| name | TEXT | 商品名称 |
| description | TEXT | 商品描述 |
| price | REAL | 商品价格 |
| stock | INTEGER | 库存数量 |
| is_active | INTEGER | 是否上架（1是0否） |
| sort_order | INTEGER | 排序顺序 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 3. 商品卡密表（product_cards）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| product_id | INTEGER | 关联商品ID |
| card_code | TEXT | 卡号 |
| card_secret | TEXT | 卡密 |
| is_used | INTEGER | 是否已使用 |
| used_by | INTEGER | 使用者用户ID |
| used_at | TEXT | 使用时间 |
| order_id | INTEGER | 关联订单ID |
| created_at | TEXT | 创建时间 |

#### 4. 充值卡密表（recharge_cards）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| card_code | TEXT | 卡号（唯一） |
| amount | REAL | 面值金额 |
| is_used | INTEGER | 是否已使用 |
| used_by | INTEGER | 使用者用户ID |
| used_at | TEXT | 使用时间 |
| created_at | TEXT | 创建时间 |

#### 5. 订单表（orders）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| order_no | TEXT | 订单号（唯一） |
| user_id | INTEGER | 用户ID |
| product_id | INTEGER | 商品ID |
| product_name | TEXT | 商品名称 |
| price | REAL | 成交价格 |
| status | TEXT | 订单状态 |
| card_id | INTEGER | 关联卡密ID |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 6. 流水表（transactions）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| user_id | INTEGER | 用户ID |
| trans_type | TEXT | 交易类型（recharge/purchase） |
| amount | REAL | 交易金额 |
| balance_before | REAL | 变动前余额 |
| balance_after | REAL | 变动后余额 |
| description | TEXT | 交易说明 |
| order_id | INTEGER | 关联订单ID |
| recharge_card_id | INTEGER | 关联充值卡密ID |
| created_at | TEXT | 创建时间 |

---

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- Linux/macOS/Windows 系统
- 网络连接（用于访问微信API）

### 安装步骤

#### 1. 克隆或下载项目

```bash
cd wechat-clawbot
```

#### 2. 安装依赖

推荐使用 uv 包管理器：

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

或者使用 pip：

```bash
pip install -e .
```

#### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件
vim .env
```

配置项说明：

```env
# ClawBot API配置
CLAWBOT_BASE_URL=https://ilinkai.weixin.qq.com
BOT_TYPE=3

# Web管理后台配置
WEB_HOST=0.0.0.0
WEB_PORT=8000
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# 分页配置
PAGE_SIZE=10

# 日志级别
LOG_LEVEL=INFO
```

#### 4. 初始化数据库

首次运行会自动创建数据库和表结构，无需手动操作。

#### 5. 启动服务

**启动Web管理后台：**

```bash
uv run python main.py web
# 或者
python main.py web
```

访问地址：http://localhost:8000/admin
默认管理员账号：admin / admin123

**启动微信机器人：**

```bash
uv run python main.py
# 或者
python main.py
```

终端会显示登录二维码，用微信扫描即可登录。

---

## 使用指南

### 管理员操作流程

#### 1. 添加商品

1. 登录Web管理后台
2. 进入"商品管理"页面
3. 点击"新增商品"按钮
4. 填写商品信息：
   - 商品名称
   - 价格（元）
   - 排序（数字越小越靠前）
   - 商品描述
5. 点击"提交"

#### 2. 导入商品卡密

1. 进入商品管理页面
2. 点击某个商品的"卡密"按钮
3. 点击"批量添加卡密"
4. 输入卡密数据（格式：卡号----卡密）：
   ```
   VIP001----secret123
   VIP002----secret456
   VIP003----secret789
   ```
5. 点击"批量导入"

#### 3. 导入充值卡密

1. 进入"充值卡密"页面
2. 点击"批量添加"按钮
3. 输入默认值（面额）
4. 输入卡密列表（格式：卡号,面额）：
   ```
   RECHARGE001,50
   RECHARGE002,100
   RECHARGE003,200
   ```
5. 点击"批量导入"

#### 4. 查看数据

- **仪表盘**：查看用户总数、订单总数、充值/消费总额
- **用户管理**：查看所有用户及其余额
- **订单管理**：查看所有订单
- **流水记录**：查看所有资金流水

### 用户操作流程

#### 1. 注册

1. 添加机器人微信账号
2. 发送任意消息
3. 输入"1"选择注册
4. 设置登录密码（6-20位）
5. 系统返回用户ID，**请妥善保存**

#### 2. 登录

1. 发送任意消息
2. 输入"2"选择登录
3. 输入用户ID
4. 输入登录密码
5. 登录成功

#### 3. 购买商品

1. 输入"主页"打开商品列表
2. 输入数字选择商品
3. 查看商品详情
4. 输入"购买"
5. 输入"确认"
6. 系统自动发送卡密

#### 4. 充值

1. 输入"充值"
2. 输入充值卡密
3. 系统自动增加余额

---

## API接口文档

### 二维码接口

#### 获取登录二维码

```
GET /api/v1/qrcode
```

响应示例：
```json
{
  "success": true,
  "data": {
    "qrcode": "qrcode_token_xxx",
    "qrcode_url": "https://liteapp.weixin.qq.com/q/xxx"
  }
}
```

#### 查询二维码状态

```
GET /api/v1/qrcode/status?qrcode={qrcode}
```

响应示例：
```json
{
  "success": true,
  "data": {
    "status": "confirmed",
    "bot_token": "xxx",
    "ilink_bot_id": "xxx",
    "ilink_user_id": "xxx"
  }
}
```

状态值：
- `wait` - 等待扫码
- `scaned` - 已扫码
- `confirmed` - 已确认（登录成功）
- `expired` - 已过期

### 数据查询接口

#### 获取用户列表

```
GET /api/v1/users?page=1&page_size=20
```

响应示例：
```json
{
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "list": [
      {
        "id": 1,
        "user_id": "123456",
        "balance": 100.00,
        "wechat_id": "wx_xxx",
        "created_at": "2024-01-01 12:00:00"
      }
    ]
  }
}
```

#### 获取商品列表

```
GET /api/v1/products
```

响应示例：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "VIP会员月卡",
      "description": "VIP特权",
      "price": 29.90,
      "stock": 10,
      "is_active": true
    }
  ]
}
```

#### 获取订单列表

```
GET /api/v1/orders?page=1&page_size=20
```

响应示例：
```json
{
  "success": true,
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "list": [
      {
        "id": 1,
        "order_no": "ORD1234567890ABCDEF",
        "user_id": 1,
        "product_name": "VIP会员月卡",
        "price": 29.90,
        "status": "completed",
        "created_at": "2024-01-01 12:00:00"
      }
    ]
  }
}
```

#### 获取统计数据

```
GET /api/v1/stats
```

响应示例：
```json
{
  "success": true,
  "data": {
    "total_recharge": 10000.00,
    "total_purchase": 8000.00,
    "user_count": 100,
    "order_count": 500
  }
}
```

### 数据管理接口

#### 新增商品

```
POST /api/v1/products
Content-Type: application/json

{
  "name": "VIP会员月卡",
  "description": "VIP特权",
  "price": 29.90,
  "sort_order": 1
}
```

#### 批量导入商品卡密

```
POST /api/v1/products/{product_id}/cards/batch
Content-Type: application/json

{
  "cards": [
    {"code": "VIP001", "secret": "secret123"},
    {"code": "VIP002", "secret": "secret456"}
  ]
}
```

#### 批量导入充值卡密

```
POST /api/v1/recharge-cards/batch
Content-Type: application/json

{
  "cards": [
    {"code": "RECHARGE001", "amount": 50},
    {"code": "RECHARGE002", "amount": 100}
  ]
}
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| CLAWBOT_BASE_URL | https://ilinkai.weixin.qq.com | ClawBot API地址 |
| BOT_TYPE | 3 | 机器人类型 |
| WEB_HOST | 0.0.0.0 | Web服务监听地址 |
| WEB_PORT | 8000 | Web服务监听端口 |
| ADMIN_USERNAME | admin | 管理员用户名 |
| ADMIN_PASSWORD | admin123 | 管理员密码 |
| PAGE_SIZE | 10 | 分页大小 |
| LOG_LEVEL | INFO | 日志级别 |

### 安全建议

1. **修改默认密码**：首次部署后立即修改管理员密码
2. **使用HTTPS**：生产环境建议使用Nginx反向代理并配置HTTPS
3. **限制访问**：通过防火墙限制Web后台的访问IP
4. **定期备份**：定期备份数据库文件 `data/bot.db`

---

## 常见问题

### Q: 微信机器人登录失败怎么办？

A: 检查以下几点：
1. 网络连接是否正常
2. ClawBot API地址是否正确
3. 是否有设备数量限制

### Q: 商品卡密导入失败怎么办？

A: 检查卡密格式：
- 每行一个卡密
- 卡号和卡密之间用 `----` 分隔
- 确保卡号唯一不重复

### Q: 用户无法充值怎么办？

A: 检查：
1. 充值卡密是否存在
2. 充值卡密是否已被使用
3. 充值卡密面额是否正确

### Q: 购买时提示余额不足？

A: 用户需要先充值：
1. 用户发送"充值"
2. 输入充值卡密
3. 系统自动增加余额

---

## 开发指南

### 添加新功能

#### 1. 添加新的消息处理器

```python
# app/bot/handlers/my_handler.py
from ..session import UserSession

class MyHandler:
    @staticmethod
    def get_help() -> str:
        return "新功能帮助信息"

    @classmethod
    async def handle(cls, session: UserSession, message: str) -> str:
        # 处理逻辑
        return "处理结果"
```

#### 2. 在分发器中注册

```python
# app/bot/dispatcher.py

# 添加新指令处理
if content == "新指令":
    return await MyHandler.handle(session, content)
```

#### 3. 添加Web管理页面

```python
# app/web/app.py

@app.get("/admin/my-page")
async def my_page(request: Request):
    # 获取数据
    return templates.TemplateResponse("my_page.html", {
        "request": request
    })
```

### 数据库迁移

当需要修改数据库结构时：

```python
# app/database.py
def upgrade_db():
    conn = get_connection()
    # 添加新字段
    conn.execute("ALTER TABLE users ADD COLUMN new_field TEXT")
    conn.commit()
```

---

## 部署指南

### 生产环境部署

#### 1. 使用Systemd服务（Linux）

创建服务文件：
```bash
sudo vim /etc/systemd/system/wechat-bot.service
```

内容：
```ini
[Unit]
Description=WeChat ClawBot Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/wechat-clawbot
ExecStart=/path/to/wechat-clawbot/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable wechat-bot
sudo systemctl start wechat-bot
```

#### 2. 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. 使用Docker部署

创建 Dockerfile：
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000
CMD ["python", "main.py", "web"]
```

构建和运行：
```bash
docker build -t wechat-clawbot .
docker run -d -p 8000:8000 wechat-clawbot
```

---

## 更新日志

### v1.0.0 (2024-01-01)

- ✨ 初始版本发布
- ✅ 用户注册/登录系统
- ✅ 商品浏览/购买
- ✅ 充值卡密核销
- ✅ 自动发密
- ✅ Web管理后台
- ✅ RESTful API

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件至：support@example.com

---

感谢使用本系统！
