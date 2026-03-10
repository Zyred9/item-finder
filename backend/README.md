# 寻物记 - 后端 API

FastAPI + SQLAlchemy + SQLite

## 快速开始

### 环境配置

- **开发环境**：使用根目录下的 `.env`，已包含核心参数；把 API Key 等敏感项填好后即可本地运行。
- **正式环境**：复制 `.env.production` 为 `.env` 或在启动时指定 `ENV_FILE=.env.production`，并改为生产数据库、正式微信配置，且 `DEBUG=false`。
- `.env` 已加入 `.gitignore`，请勿提交；`.env.example`、`.env.production` 为模板可提交。
- **全部 AI 能力均接入百炼**：在 [百炼控制台](https://bailian.console.aliyun.com/) 创建 API Key，配置 `BAILIAN_API_KEY`。
  - **TTS**：文字转语音（找物结果播报）
  - **Qwen-VL**：存物主图理解（拍照识物、建议名称/分类）
  - **qwen-vl-ocr**：扩展凭证 OCR（说明书、发票、药盒）
  - **Fun-ASR**：语音识别（找物/存物语音转文字），需额外配置 `BACKEND_PUBLIC_URL`（本服务公网地址，本地可用 cpolar/ngrok）。微信语音可能上传为 `audio/silk`，后端会先用 `silk-python` 解码，再转为 16k 单声道 wav 交给百炼识别；音频转 wav 仍需系统安装 `ffmpeg`。
- **对话总结 + 找物意图解析**：优先使用 [百炼 Coding Plan](https://help.aliyun.com/zh/model-studio/coding-plan-quickstart)，配置 `CODING_PLAN_ENV_KEY_NAME` + `CODING_PLAN_BASE_URL`；未配置时使用 DeepSeek。

**按环境启动**：通过环境变量 `ENV_FILE` 指定要加载的配置文件（相对于 `backend` 目录）。

```bash
cd backend

# 开发（默认加载 .env）
python main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 正式环境（加载 .env.production）
# Windows CMD
set ENV_FILE=.env.production && python main.py

# Windows PowerShell
$env:ENV_FILE=".env.production"; python main.py

# Linux / macOS
ENV_FILE=.env.production python main.py
# 或
ENV_FILE=.env.production uvicorn main:app --host 0.0.0.0 --port 8000
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
cd backend
python main.py
```

或指定监听所有网卡（小程序用本机 IP 访问时必须）：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问：
- API 地址：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 小程序请求 502 排查

前端请求 `http://本机IP:8000/api/...` 出现 **502 Bad Gateway** 时，多半是本机防火墙拦截了 8000 端口入站。

**步骤 1：放行 8000 端口（Windows）**

以**管理员身份**打开 PowerShell，在项目根目录执行：

```powershell
cd backend
.\scripts\allow-port-8000.ps1
```

**步骤 2：确认后端监听 0.0.0.0**

启动日志中需为 `Uvicorn running on http://0.0.0.0:8000`，否则只能本机访问。若用 `python main.py`，请确认 `main.py` 里 `uvicorn.run(..., host="0.0.0.0")`。

**步骤 3：验证后端是否可达**

在同一局域网的另一台设备（或手机）浏览器访问：`http://你的电脑IP:8000/health`，若返回 `{"status":"ok"}` 说明端口已通。

## 项目结构

```
backend/
├── main.py              # 入口文件
├── requirements.txt     # 依赖
├── .env.example         # 环境变量示例
│
├── config/              # 配置模块
│   └── settings.py      # 配置管理
│
├── models/              # 数据库模型
│   ├── base.py          # 基础配置
│   ├── family.py        # 家庭模型
│   ├── user.py          # 用户模型
│   ├── item.py          # 物品模型
│   ├── category.py      # 分类模型
│   ├── reminder.py      # 提醒模型
│   ├── chat.py          # 对话模型
│   └── location.py      # 位置模型
│
├── schemas/             # Pydantic 模式
│   ├── common.py        # 通用响应
│   ├── family.py        # 家庭 Schema
│   ├── user.py          # 用户 Schema
│   ├── item.py          # 物品 Schema
│   ├── category.py      # 分类 Schema
│   ├── reminder.py      # 提醒 Schema
│   └── chat.py          # 对话 Schema
│
├── services/            # 业务逻辑层
│   ├── family_service.py
│   ├── user_service.py
│   ├── item_service.py
│   ├── reminder_service.py
│   └── chat_service.py
│
├── api/                 # API 路由层
│   ├── auth.py          # 认证接口
│   ├── families.py      # 家庭接口
│   ├── items.py         # 物品接口
│   ├── categories.py    # 分类接口
│   ├── reminders.py     # 提醒接口
│   └── chat.py          # 对话接口
│
├── utils/               # 工具函数
│   ├── security.py      # 安全相关
│   └── file_handler.py  # 文件处理
│
├── data/                # 数据库文件
└── uploads/             # 上传文件
    └── photos/          # 图片存储
```

## API 概览

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| 认证 | `/auth` | 微信登录 |
| 家庭 | `/families` | 创建/加入家庭 |
| 物品 | `/items` | CRUD + 搜索 |
| 分类 | `/categories` | 分类列表 |
| 提醒 | `/reminders` | 智能提醒 |
| 对话 | `/chat` | 对话找物 |

## 环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
cp .env.example .env
```

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 数据库连接 |
| `WECHAT_APPID` | 微信小程序 AppID |
| `WECHAT_SECRET` | 微信小程序 Secret |
| `BAIDU_APP_ID` | 百度语音 AppID |

## 开发说明

### 添加新模型

1. 在 `models/` 创建模型文件
2. 在 `models/__init__.py` 导出
3. 在 `schemas/` 创建对应 Schema
4. 在 `services/` 创建服务层
5. 在 `api/` 创建路由

### 数据库迁移

目前使用 SQLite，表会自动创建。如需迁移到 PostgreSQL：

1. 修改 `DATABASE_URL`
2. 安装 `alembic`
3. 配置迁移脚本