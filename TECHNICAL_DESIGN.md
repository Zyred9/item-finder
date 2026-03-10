# 寻物记 - 技术设计文档

**版本：** v1.0  
**创建日期：** 2026-03-03  
**状态：** 待开发

---

## 目录

1. [系统架构](#一系统架构)
2. [技术栈](#二技术栈)
3. [目录结构](#三目录结构)
4. [数据库设计](#四数据库设计)
5. [API 设计](#五 api 设计)
6. [前端设计](#六前端设计)
7. [部署方案](#七部署方案)
8. [开发规范](#八开发规范)

---

## 一、系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    微信小程序（前端）                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   首页      │  │   存物页    │  │   搜索页    │     │
│  │  index.js   │  │   store.js  │  │  search.js  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS / JSON
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI 后端服务                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │              API Router Layer                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │ /api/auth│  │/api/items│  │/api/family│      │   │
│  │  └──────────┘  └──────────┘  └──────────┘      │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Service Layer                       │   │
│  │  AuthService  │  ItemService  │  FamilyService  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Repository Layer                    │   │
│  │        SQLAlchemy ORM + SQLite Database          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    文件系统                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  /uploads/photos/  - 物品照片存储                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 数据流

**存物流程：**
```
小程序 → POST /api/items → FastAPI → 验证 → Service → Repository → SQLite
                                              ↓
                                          保存照片 → 文件系统
```

**搜索流程：**
```
小程序 → GET /api/items/search?q=xxx → FastAPI → Service → Repository → SQLite
                                              ↓
                                          返回 JSON 结果
```

---

## 二、技术栈

### 2.1 前端（微信小程序）

| 技术 | 版本 | 说明 |
|------|------|------|
| 小程序基础库 | 2.19.0+ | 微信官方 |
| 开发工具 | 微信开发者工具 | 最新稳定版 |
| UI 组件 | 原生组件 + 自定义 | 保持最小依赖 |
| 网络请求 | wx.request | 原生 API |
| 状态管理 | 全局数据 + Storage | 简单场景够用 |

### 2.2 后端（Python FastAPI）

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 稳定版本 |
| Web 框架 | FastAPI 0.109+ | 异步、自动文档 |
| ORM | SQLAlchemy 2.0+ | 数据库操作 |
| 数据库 | SQLite 3.35+ | 轻量级 |
| 验证 | Pydantic 2.5+ | 数据验证 |
| 文件上传 | python-multipart | 表单处理 |
| 服务器 | Uvicorn 0.27+ | ASGI 服务器 |

### 2.3 开发工具

| 工具 | 用途 |
|------|------|
| Git | 版本控制 |
| VS Code | 代码编辑器 |
| Postman | API 测试 |
| 微信开发者工具 | 小程序开发调试 |

---

## 三、目录结构

### 3.1 整体结构

```
item-finder/
├── README.md                 # 项目说明
├── PRD.md                    # 产品需求文档
├── TECHNICAL_DESIGN.md       # 技术设计文档（本文件）
├── TODO.md                   # 开发任务清单
│
├── backend/                  # 后端项目
│   ├── main.py               # FastAPI 入口
│   ├── requirements.txt      # Python 依赖
│   ├── start.bat             # Windows 启动脚本
│   ├── README.md             # 后端说明
│   │
│   ├── config/               # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py       # 配置管理
│   │
│   ├── models/               # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py           # 基类
│   │   ├── family.py         # 家庭模型
│   │   ├── user.py           # 用户模型
│   │   └── item.py           # 物品模型
│   │
│   ├── schemas/              # Pydantic 模式
│   │   ├── __init__.py
│   │   ├── family.py         # 家庭 schema
│   │   ├── user.py           # 用户 schema
│   │   └── item.py           # 物品 schema
│   │
│   ├── services/             # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py   # 认证服务
│   │   ├── family_service.py # 家庭服务
│   │   └── item_service.py   # 物品服务
│   │
│   ├── api/                  # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py           # 依赖注入
│   │   ├── auth.py           # 认证路由
│   │   ├── families.py       # 家庭路由
│   │   └── items.py          # 物品路由
│   │
│   ├── utils/                # 工具函数
│   │   ├── __init__.py
│   │   ├── security.py       # 安全相关
│   │   └── file_handler.py   # 文件处理
│   │
│   ├── uploads/              # 上传文件存储
│   │   └── photos/           # 物品照片
│   │
│   └── data/                 # 数据库文件
│       └── itemfinder.db     # SQLite 数据库
│
└── miniprogram/              # 微信小程序项目
    ├── app.js                # 小程序入口
    ├── app.json              # 小程序配置
    ├── app.wxss              # 全局样式
    ├── project.config.json   # 项目配置
    ├── sitemap.json          # sitemap 配置
    │
    ├── pages/                # 页面
    │   ├── index/            # 首页
    │   │   ├── index.js
    │   │   ├── index.json
    │   │   ├── index.wxml
    │   │   └── index.wxss
    │   │
    │   ├── store/            # 存物页
    │   │   ├── store.js
    │   │   ├── store.json
    │   │   ├── store.wxml
    │   │   └── store.wxss
    │   │
    │   ├── search/           # 搜索页
    │   │   ├── search.js
    │   │   ├── search.json
    │   │   ├── search.wxml
    │   │   └── search.wxss
    │   │
    │   ├── detail/           # 详情页
    │   │   ├── detail.js
    │   │   ├── detail.json
    │   │   ├── detail.wxml
    │   │   └── detail.wxss
    │   │
    │   ├── family/           # 家庭页
    │   │   ├── family.js
    │   │   ├── family.json
    │   │   ├── family.wxml
    │   │   └── family.wxss
    │   │
    │   └── login/            # 登录页
    │       ├── login.js
    │       ├── login.json
    │       ├── login.wxml
    │       └── login.wxss
    │
    ├── components/           # 自定义组件
    │   └── item-card/        # 物品卡片组件
    │       ├── item-card.js
    │       ├── item-card.json
    │       ├── item-card.wxml
    │       └── item-card.wxss
    │
    ├── utils/                # 工具函数
    │   ├── api.js            # API 请求封装
    │   ├── auth.js           # 认证工具
    │   └── util.js           # 通用工具
    │
    └── images/               # 图片资源
        └── icons/            # 图标
```

### 3.2 后端模块说明

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| `config/` | 配置管理 | `settings.py` - 环境变量、数据库配置 |
| `models/` | 数据库模型 | `family.py`, `user.py`, `item.py` |
| `schemas/` | 数据验证 | 请求/响应数据格式定义 |
| `services/` | 业务逻辑 | 核心业务处理 |
| `api/` | HTTP 路由 | API 端点定义 |
| `utils/` | 工具函数 | 文件处理、安全等 |

### 3.3 前端模块说明

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| `pages/` | 页面 | 6 个核心页面 |
| `components/` | 可复用组件 | 物品卡片等 |
| `utils/` | 工具函数 | API 封装、认证等 |
| `images/` | 静态资源 | 图标、图片 |

---

## 四、数据库设计

### 4.1 DDL 语句

```sql
-- 启用外键支持
PRAGMA foreign_keys = ON;

-- ========================================
-- 1. 家庭表 (families)
-- ========================================
CREATE TABLE IF NOT EXISTS families (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    invite_code     TEXT UNIQUE NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_families_invite_code ON families(invite_code);

-- ========================================
-- 2. 用户表 (users)
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    family_id       TEXT NOT NULL,
    wechat_openid   TEXT UNIQUE NOT NULL,
    nickname        TEXT,
    avatar_url      TEXT,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_users_family_id ON users(family_id);
CREATE INDEX IF NOT EXISTS idx_users_openid ON users(wechat_openid);

-- ========================================
-- 3. 物品表 (items)
-- ========================================
CREATE TABLE IF NOT EXISTS items (
    id              TEXT PRIMARY KEY,
    family_id       TEXT NOT NULL,
    creator_id      TEXT NOT NULL,
    name            TEXT NOT NULL,
    location        TEXT NOT NULL,
    description     TEXT,
    photo_path      TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_items_family_id ON items(family_id);
CREATE INDEX IF NOT EXISTS idx_items_creator_id ON items(creator_id);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at DESC);

-- ========================================
-- 4. 物品扩展表 (item_extensions) - 分类扩展字段
-- ========================================
CREATE TABLE IF NOT EXISTS item_extensions (
    id              TEXT PRIMARY KEY,
    item_id         TEXT NOT NULL UNIQUE,
    
    -- 药品相关
    expire_date     DATE,                    -- 过期日期
    production_date DATE,                    -- 生产日期
    shelf_life_days INTEGER,                 -- 保质期（天）
    open_date       DATE,                    -- 开封日期
    open_shelf_life INTEGER,                 -- 开封后保质期（天）
    dosage          TEXT,                    -- 用法用量
    
    -- 证件相关
    document_number TEXT,                    -- 证件号码（加密存储）
    issuer          TEXT,                    -- 发证机关
    
    -- 电器相关
    brand           TEXT,                    -- 品牌
    model           TEXT,                    -- 型号
    purchase_date   DATE,                    -- 购买日期
    warranty_date   DATE,                    -- 保修到期日
    accessories     TEXT,                    -- 配件清单（JSON）
    
    -- 衣物相关
    size            TEXT,                    -- 尺码
    color           TEXT,                    -- 颜色
    season          TEXT,                    -- 季节
    material        TEXT,                    -- 材质
    
    -- 食品相关
    storage_condition TEXT,                  -- 储存条件（冷藏/常温/冷冻）
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_extensions_item_id ON item_extensions(item_id);
CREATE INDEX IF NOT EXISTS idx_extensions_expire ON item_extensions(expire_date);
CREATE INDEX IF NOT EXISTS idx_extensions_warranty ON item_extensions(warranty_date);

-- ========================================
-- 5. 物品分类表 (categories) - 分类体系
-- ========================================
CREATE TABLE IF NOT EXISTS categories (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,           -- 分类名称
    icon            TEXT,                    -- 图标（emoji）
    parent_id       TEXT,                    -- 父分类ID（支持多级）
    sort_order      INTEGER DEFAULT 0,       -- 排序
    extension_fields TEXT,                   -- 扩展字段配置（JSON）
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);

-- ========================================
-- 6. 智能提醒表 (reminders)
-- ========================================
CREATE TABLE IF NOT EXISTS reminders (
    id              TEXT PRIMARY KEY,
    family_id       TEXT NOT NULL,
    item_id         TEXT NOT NULL,
    
    type            TEXT NOT NULL,           -- 提醒类型: expire/open/warranty/document/custom
    level           TEXT DEFAULT 'normal',   -- 紧急级别: urgent/warning/normal
    
    title           TEXT NOT NULL,           -- 提醒标题
    content         TEXT,                    -- 提醒内容
    
    remind_at       DATE NOT NULL,           -- 提醒日期
    triggered_at    TIMESTAMP,               -- 实际触发时间
    
    status          TEXT DEFAULT 'pending',  -- pending/done/ignored/deferred
    deferred_to     DATE,                    -- 延期到
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reminders_family ON reminders(family_id);
CREATE INDEX IF NOT EXISTS idx_reminders_item ON reminders(item_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_reminders_type ON reminders(type);

-- ========================================
-- 7. 对话历史表 (chat_messages)
-- ========================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id              TEXT PRIMARY KEY,
    family_id       TEXT NOT NULL,
    user_id         TEXT NOT NULL,
    session_id      TEXT NOT NULL,           -- 会话ID（多轮对话）
    
    role            TEXT NOT NULL,           -- user/assistant
    content         TEXT NOT NULL,           -- 消息内容
    
    -- AI 响应相关
    intent          TEXT,                    -- 识别的意图: search/query_location/query_expire/...
    entities        TEXT,                    -- 提取的实体（JSON）
    matched_items   TEXT,                    -- 匹配的物品ID列表（JSON）
    
    -- 语音相关
    audio_path      TEXT,                    -- 语音文件路径
    audio_duration  INTEGER,                 -- 语音时长（秒）
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_family ON chat_messages(family_id);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages(created_at DESC);

-- ========================================
-- 8. 常用位置表 (locations) - 可选
-- ========================================
CREATE TABLE IF NOT EXISTS locations (
    id              TEXT PRIMARY KEY,
    family_id       TEXT NOT NULL,
    name            TEXT NOT NULL,           -- 位置名称
    parent_id       TEXT,                    -- 父位置（如：主卧 > 抽屉）
    usage_count     INTEGER DEFAULT 0,       -- 使用次数
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES locations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_locations_family ON locations(family_id);
CREATE INDEX IF NOT EXISTS idx_locations_usage ON locations(usage_count DESC);

-- ========================================
-- 9. 触发器 - 自动更新 updated_at
-- ========================================
CREATE TRIGGER IF NOT EXISTS update_items_updated_at
AFTER UPDATE ON items
BEGIN
    UPDATE items SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_extensions_updated_at
AFTER UPDATE ON item_extensions
BEGIN
    UPDATE item_extensions SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_reminders_updated_at
AFTER UPDATE ON reminders
BEGIN
    UPDATE reminders SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

### 4.2 表关系

```
families (1) ─────< (N) users
families (1) ─────< (N) items
families (1) ─────< (N) reminders
families (1) ─────< (N) chat_messages
families (1) ─────< (N) locations

users (1) ────────< (N) items (creator)
users (1) ────────< (N) chat_messages

items (1) ────────< (1) item_extensions
items (1) ────────< (N) reminders

categories (1) ───< (N) categories (parent-child self-reference)
locations (1) ────< (N) locations (parent-child self-reference)
```

### 4.3 表结构概览

| 表名 | 说明 | 核心字段 |
|------|------|----------|
| `families` | 家庭 | id, name, invite_code |
| `users` | 用户 | id, family_id, wechat_openid, nickname |
| `items` | 物品 | id, family_id, creator_id, name, location, category |
| `item_extensions` | 物品扩展 | item_id, expire_date, brand, warranty_date... |
| `categories` | 分类 | id, name, icon, parent_id, extension_fields |
| `reminders` | 提醒 | id, family_id, item_id, type, remind_at, status |
| `chat_messages` | 对话 | id, family_id, session_id, role, content, intent |
| `locations` | 位置 | id, family_id, name, parent_id, usage_count |

### 4.3 初始化脚本

```python
# init_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "itemfinder.db"

def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 读取 DDL 语句
    with open(Path(__file__).parent / "schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    
    # 执行 DDL
    cursor.executescript(schema)
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库初始化完成：{DB_PATH}")

if __name__ == "__main__":
    init_db()
```

---

## 五、API 设计

### 5.1 API 规范

**基础信息：**
- Base URL: `http://localhost:8000/api`
- 认证方式：Header 中携带 `X-User-Id`
- 响应格式：JSON
- 字符编码：UTF-8

**响应格式：**
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

**错误码：**
| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

### 5.2 认证接口

#### POST /api/auth/login

微信登录

**请求：**
```http
POST /api/auth/login HTTP/1.1
Content-Type: application/json

{
  "code": "微信登录 code"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "uuid",
    "nickname": "张三",
    "avatar_url": "https://...",
    "family_id": "uuid",
    "family_name": "张家"
  }
}
```

**错误响应：**
```json
{
  "code": 400,
  "message": "微信登录失败",
  "data": null
}
```

---

### 5.3 家庭接口

#### POST /api/families

创建家庭

**请求：**
```http
POST /api/families HTTP/1.1
Content-Type: application/json
X-User-Id: {user_id}

{
  "name": "张家"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "张家",
    "invite_code": "A3B9C2",
    "created_at": "2026-03-03T10:00:00"
  }
}
```

---

#### POST /api/families/join

加入家庭

**请求：**
```http
POST /api/families/join HTTP/1.1
Content-Type: application/json
X-User-Id: {user_id}

{
  "invite_code": "A3B9C2"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "family_id": "uuid",
    "family_name": "张家"
  }
}
```

**错误响应：**
```json
{
  "code": 404,
  "message": "邀请码无效",
  "data": null
}
```

---

#### GET /api/families/{family_id}

获取家庭信息

**请求：**
```http
GET /api/families/{family_id} HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "张家",
    "invite_code": "A3B9C2",
    "member_count": 3,
    "created_at": "2026-03-03T10:00:00"
  }
}
```

---

### 5.4 物品接口

#### POST /api/items

创建物品

**请求：**
```http
POST /api/items HTTP/1.1
Content-Type: multipart/form-data
X-User-Id: {user_id}

------WebKitFormBoundary
Content-Disposition: form-data; name="name"

吹风机
------WebKitFormBoundary
Content-Disposition: form-data; name="location"

主卧抽屉
------WebKitFormBoundary
Content-Disposition: form-data; name="description"

红色，戴森品牌
------WebKitFormBoundary
Content-Disposition: form-data; name="photo"; filename="photo.jpg"
Content-Type: image/jpeg

<binary data>
------WebKitFormBoundary--
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "吹风机",
    "location": "主卧抽屉",
    "description": "红色，戴森品牌",
    "photo_path": "/uploads/photos/xxx.jpg",
    "creator_id": "uuid",
    "creator_name": "张三",
    "created_at": "2026-03-03T10:00:00"
  }
}
```

---

#### GET /api/items/{item_id}

获取物品详情

**请求：**
```http
GET /api/items/{item_id} HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "吹风机",
    "location": "主卧抽屉",
    "description": "红色，戴森品牌",
    "photo_path": "/uploads/photos/xxx.jpg",
    "creator_id": "uuid",
    "creator_name": "张三",
    "created_at": "2026-03-03T10:00:00",
    "updated_at": "2026-03-03T10:00:00"
  }
}
```

---

#### PUT /api/items/{item_id}

更新物品

**请求：**
```http
PUT /api/items/{item_id} HTTP/1.1
Content-Type: application/json
X-User-Id: {user_id}

{
  "location": "次卧抽屉"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "吹风机",
    "location": "次卧抽屉",
    ...
  }
}
```

---

#### DELETE /api/items/{item_id}

删除物品

**请求：**
```http
DELETE /api/items/{item_id} HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

#### GET /api/families/{family_id}/items

获取家庭物品列表

**请求：**
```http
GET /api/families/{family_id}/items?limit=20&offset=0 HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 50,
    "items": [
      {
        "id": "uuid",
        "name": "吹风机",
        "location": "主卧抽屉",
        "photo_path": "/uploads/photos/xxx.jpg",
        "creator_name": "张三",
        "created_at": "2026-03-03T10:00:00"
      },
      ...
    ]
  }
}
```

---

#### GET /api/items/search

搜索物品

**请求：**
```http
GET /api/items/search?q=吹风机&family_id=uuid&limit=20 HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 2,
    "items": [
      {
        "id": "uuid",
        "name": "吹风机",
        "location": "主卧抽屉",
        "photo_path": "/uploads/photos/xxx.jpg",
        "creator_name": "张三",
        "created_at": "2026-03-03T10:00:00"
      },
      ...
    ]
  }
}
```

---

### 5.5 文件上传

#### POST /api/upload/photo

上传照片

**请求：**
```http
POST /api/upload/photo HTTP/1.1
Content-Type: multipart/form-data
X-User-Id: {user_id}

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="photo.jpg"
Content-Type: image/jpeg

<binary data>
------WebKitFormBoundary--
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "file_path": "/uploads/photos/2026/03/xxx.jpg",
    "file_url": "http://localhost:8000/uploads/photos/2026/03/xxx.jpg"
  }
}
```

**限制：**
- 文件大小：< 5MB
- 文件格式：jpg, jpeg, png
- 存储路径：`/uploads/photos/{year}/{month}/{uuid}.{ext}`

---

### 5.6 语音接口

#### POST /api/voice/recognize

语音识别（语音转文字）

**请求：**
```http
POST /api/voice/recognize HTTP/1.1
Content-Type: multipart/form-data
X-User-Id: {user_id}

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="voice.mp3"
Content-Type: audio/mpeg

<binary data>
------WebKitFormBoundary
Content-Disposition: form-data; name="format"

json
------WebKitFormBoundary--
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "text": "吹风机放主卧抽屉",
    "duration": 2.5,
    "entities": {
      "item_name": "吹风机",
      "location": "主卧抽屉"
    }
  }
}
```

**说明：**
- 支持格式：mp3, wav, m4a, amr
- 最大时长：60 秒
- 返回识别文本 + 提取的实体（物品名、位置等）

---

#### POST /api/voice/tts

文字转语音

**请求：**
```http
POST /api/voice/tts HTTP/1.1
Content-Type: application/json
X-User-Id: {user_id}

{
  "text": "护照在保险柜第二层",
  "speed": 5,
  "volume": 5
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "audio_url": "/uploads/tts/xxx.mp3",
    "duration": 2.1
  }
}
```

---

### 5.7 智能提醒接口

#### GET /api/reminders

获取提醒列表

**请求：**
```http
GET /api/reminders?family_id=uuid&status=pending&level=urgent HTTP/1.1
X-User-Id: {user_id}
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| family_id | string | 是 | 家庭 ID |
| status | string | 否 | pending/done/ignored |
| level | string | 否 | urgent/warning/normal |
| type | string | 否 | expire/open/warranty/document |

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 3,
    "urgent_count": 1,
    "warnings_count": 2,
    "reminders": [
      {
        "id": "uuid",
        "type": "expire",
        "level": "urgent",
        "title": "感冒药即将过期",
        "content": "还有 3 天过期",
        "remind_at": "2026-03-06",
        "item": {
          "id": "uuid",
          "name": "感冒药",
          "location": "药箱",
          "photo_path": "/uploads/xxx.jpg"
        },
        "status": "pending",
        "created_at": "2026-03-03T10:00:00"
      }
    ]
  }
}
```

---

#### PUT /api/reminders/{reminder_id}

处理提醒

**请求：**
```http
PUT /api/reminders/{reminder_id} HTTP/1.1
Content-Type: application/json
X-User-Id: {user_id}

{
  "action": "done"
}
```

**action 选项：**
| 值 | 说明 |
|------|------|
| `done` | 标记已处理 |
| `ignore` | 忽略本次提醒 |
| `defer` | 延期处理 |

**延期请求：**
```json
{
  "action": "defer",
  "defer_days": 7
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "status": "done",
    "updated_at": "2026-03-03T10:00:00"
  }
}
```

---

### 5.8 分类接口

#### GET /api/categories

获取分类列表

**请求：**
```http
GET /api/categories HTTP/1.1
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "medicine",
      "name": "药品健康",
      "icon": "💊",
      "children": [
        {
          "id": "prescription",
          "name": "处方药",
          "extension_fields": [
            {"name": "expire_date", "label": "有效期", "type": "date", "required": true},
            {"name": "open_date", "label": "开封日期", "type": "date", "required": false},
            {"name": "dosage", "label": "用法用量", "type": "text", "required": false}
          ]
        }
      ]
    },
    {
      "id": "food",
      "name": "食品饮料",
      "icon": "🍔",
      "children": [...]
    }
  ]
}
```

---

#### GET /api/categories/{category_id}

获取分类详情（含扩展字段配置）

**请求：**
```http
GET /api/categories/medicine HTTP/1.1
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "medicine",
    "name": "药品健康",
    "icon": "💊",
    "extension_fields": [
      {
        "name": "expire_date",
        "label": "有效期",
        "type": "date",
        "required": true,
        "reminder": true
      },
      {
        "name": "open_date",
        "label": "开封日期",
        "type": "date",
        "required": false
      },
      {
        "name": "open_shelf_life",
        "label": "开封后保质期（天）",
        "type": "number",
        "required": false,
        "default": 30
      },
      {
        "name": "dosage",
        "label": "用法用量",
        "type": "textarea",
        "required": false
      }
    ]
  }
}
```

---

### 5.9 对话接口

#### POST /api/chat

对话找物

**请求：**
```http
POST /api/chat HTTP/1.1
Content-Type: application/json
X-User-Id: {user_id}

{
  "family_id": "uuid",
  "session_id": "uuid",
  "message": "我的护照在哪？"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reply": "📄 护照在保险柜第二层，是张三于 3 月 1 日存放的。",
    "intent": "search",
    "matched_items": [
      {
        "id": "uuid",
        "name": "护照",
        "location": "保险柜第二层",
        "photo_path": "/uploads/xxx.jpg",
        "creator_name": "张三",
        "created_at": "2026-03-01T10:00:00"
      }
    ],
    "actions": [
      {"type": "navigate", "label": "📍 导航"},
      {"type": "photo", "label": "📷 查看照片"},
      {"type": "tts", "label": "🔊 播报"}
    ]
  }
}
```

---

#### GET /api/chat/history

获取对话历史

**请求：**
```http
GET /api/chat/history?family_id=uuid&session_id=uuid&limit=50 HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "uuid",
    "messages": [
      {
        "id": "uuid",
        "role": "user",
        "content": "我的护照在哪？",
        "created_at": "2026-03-03T10:00:00"
      },
      {
        "id": "uuid",
        "role": "assistant",
        "content": "📄 护照在保险柜第二层...",
        "created_at": "2026-03-03T10:00:01"
      }
    ]
  }
}
```

---

#### DELETE /api/chat/history

清空对话历史

**请求：**
```http
DELETE /api/chat/history?family_id=uuid&session_id=uuid HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

### 5.10 位置接口

#### GET /api/locations

获取常用位置列表

**请求：**
```http
GET /api/locations?family_id=uuid HTTP/1.1
X-User-Id: {user_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "uuid",
      "name": "主卧",
      "children": [
        {"id": "uuid", "name": "主卧抽屉", "usage_count": 15},
        {"id": "uuid", "name": "主卧衣柜", "usage_count": 8}
      ]
    },
    {
      "id": "uuid",
      "name": "客厅",
      "children": [
        {"id": "uuid", "name": "电视柜", "usage_count": 5}
      ]
    }
  ]
}
```

---

## 六、前端设计

### 6.1 页面路由

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | `/pages/index/index` | 默认首页 |
| 存物 | `/pages/store/store` | 存物页面 |
| 搜索 | `/pages/search/search` | 搜索结果 |
| 详情 | `/pages/detail/detail` | 物品详情 |
| 家庭 | `/pages/family/family` | 家庭管理 |
| 登录 | `/pages/login/login` | 登录页面 |

### 6.2 全局配置

**app.json：**
```json
{
  "pages": [
    "pages/index/index",
    "pages/store/store",
    "pages/search/search",
    "pages/detail/detail",
    "pages/family/family",
    "pages/login/login"
  ],
  "window": {
    "backgroundTextStyle": "light",
    "navigationBarBackgroundColor": "#FF6B5B",
    "navigationBarTitleText": "寻物记",
    "navigationBarTextStyle": "white"
  },
  "style": "v2",
  "sitemapLocation": "sitemap.json"
}
```

### 6.3 API 请求封装

**utils/api.js：**
```javascript
const API_BASE_URL = 'http://localhost:8000/api'

// 获取用户 ID（从 storage）
function getUserId() {
  return wx.getStorageSync('userId')
}

// 通用请求方法
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    const userId = getUserId()
    
    wx.request({
      url: `${API_BASE_URL}${url}`,
      method: method,
      data: data,
      header: {
        'Content-Type': 'application/json',
        'X-User-Id': userId
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data)
        } else {
          wx.showToast({
            title: res.data.message || '请求失败',
            icon: 'none'
          })
          reject(res.data)
        }
      },
      fail: (err) => {
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// API 方法封装
module.exports = {
  // 认证
  login: (code) => request('/auth/login', 'POST', { code }),
  
  // 家庭
  createFamily: (name) => request('/families', 'POST', { name }),
  joinFamily: (inviteCode) => request('/families/join', 'POST', { invite_code: inviteCode }),
  getFamily: (familyId) => request(`/families/${familyId}`),
  
  // 物品
  createItem: (data) => request('/items', 'POST', data),
  getItem: (itemId) => request(`/items/${itemId}`),
  updateItem: (itemId, data) => request(`/items/${itemId}`, 'PUT', data),
  deleteItem: (itemId) => request(`/items/${itemId}`, 'DELETE'),
  getFamilyItems: (familyId, limit = 20) => request(`/families/${familyId}/items?limit=${limit}`),
  searchItems: (query, familyId) => request(`/items/search?q=${query}&family_id=${familyId}`),
  
  // 分类
  getCategories: () => request('/categories'),
  getCategoryDetail: (categoryId) => request(`/categories/${categoryId}`),
  
  // 提醒
  getReminders: (familyId, status, level) => {
    let url = `/reminders?family_id=${familyId}`
    if (status) url += `&status=${status}`
    if (level) url += `&level=${level}`
    return request(url)
  },
  handleReminder: (reminderId, action, deferDays) => {
    const data = { action }
    if (deferDays) data.defer_days = deferDays
    return request(`/reminders/${reminderId}`, 'PUT', data)
  },
  
  // 对话
  chat: (familyId, sessionId, message) => request('/chat', 'POST', {
    family_id: familyId,
    session_id: sessionId,
    message: message
  }),
  getChatHistory: (familyId, sessionId, limit = 50) => 
    request(`/chat/history?family_id=${familyId}&session_id=${sessionId}&limit=${limit}`),
  clearChatHistory: (familyId, sessionId) => 
    request(`/chat/history?family_id=${familyId}&session_id=${sessionId}`, 'DELETE'),
  
  // 位置
  getLocations: (familyId) => request(`/locations?family_id=${familyId}`),
  
  // 上传
  uploadPhoto: (filePath) => {
    return new Promise((resolve, reject) => {
      const userId = getUserId()
      wx.uploadFile({
        url: `${API_BASE_URL}/upload/photo`,
        filePath: filePath,
        name: 'file',
        header: {
          'X-User-Id': userId
        },
        success: (res) => {
          const data = JSON.parse(res.data)
          if (data.code === 0) {
            resolve(data.data)
          } else {
            reject(data)
          }
        },
        fail: reject
      })
    })
  },
  
  // 语音
  uploadVoice: (filePath) => {
    return new Promise((resolve, reject) => {
      const userId = getUserId()
      wx.uploadFile({
        url: `${API_BASE_URL}/voice/recognize`,
        filePath: filePath,
        name: 'file',
        formData: { format: 'json' },
        header: {
          'X-User-Id': userId
        },
        success: (res) => {
          const data = JSON.parse(res.data)
          if (data.code === 0) {
            resolve(data.data)
          } else {
            reject(data)
          }
        },
        fail: reject
      })
    })
  },
  textToSpeech: (text, speed = 5, volume = 5) => 
    request('/voice/tts', 'POST', { text, speed, volume })
}
```

### 6.4 页面示例 - 首页

**pages/index/index.js：**
```javascript
const api = require('../../utils/api')

Page({
  data: {
    searchKeyword: '',
    recentItems: []
  },

  onLoad() {
    this.loadRecentItems()
  },

  onShow() {
    // 每次显示时刷新数据
    this.loadRecentItems()
  },

  // 加载最近物品
  async loadRecentItems() {
    try {
      const familyId = wx.getStorageSync('familyId')
      if (!familyId) return
      
      const data = await api.getFamilyItems(familyId, 10)
      this.setData({ recentItems: data.items })
    } catch (err) {
      console.error('加载最近物品失败', err)
    }
  },

  // 搜索输入
  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  // 搜索
  onSearch() {
    const keyword = this.data.searchKeyword
    if (!keyword) return
    
    wx.navigateTo({
      url: `/pages/search/search?q=${keyword}`
    })
  },

  // 去存物
  onStoreItem() {
    wx.navigateTo({
      url: '/pages/store/store'
    })
  },

  // 查看物品详情
  onItemClick(e) {
    const itemId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/detail/detail?id=${itemId}`
    })
  }
})
```

**pages/index/index.wxml：**
```xml
<view class="container">
  <!-- 导航栏 -->
  <view class="navbar">
    <text class="family-name">🏠 {{familyName}}</text>
    <text class="user-avatar" bindtap="goToFamily">👤</text>
  </view>

  <!-- 搜索框 -->
  <view class="search-box">
    <input 
      class="search-input" 
      placeholder="搜索物品..." 
      value="{{searchKeyword}}"
      bindinput="onSearchInput"
    />
  </view>

  <!-- 快捷入口 -->
  <view class="quick-actions">
    <view class="action-btn" bindtap="onStoreItem">
      <text class="icon">📷</text>
      <text class="text">拍照存物</text>
    </view>
    <view class="action-btn" bindtap="onStoreItem">
      <text class="icon">📝</text>
      <text class="text">文本存物</text>
    </view>
  </view>

  <!-- 最近物品 -->
  <view class="recent-section">
    <view class="section-title">🕐 最近存放</view>
    
    <view wx:if="{{recentItems.length === 0}}" class="empty-state">
      <text>还没有物品，去存第一个吧~</text>
    </view>
    
    <view wx:for="{{recentItems}}" wx:key="id" class="item-card" bindtap="onItemClick" data-id="{{item.id}}">
      <image wx:if="{{item.photo_path}}" class="item-thumb" src="{{item.photo_path}}" mode="aspectFill" />
      <view wx:else class="item-thumb-empty">📦</view>
      
      <view class="item-info">
        <view class="item-name">{{item.name}}</view>
        <view class="item-location">📍 {{item.location}}</view>
        <view class="item-meta">
          <text>{{item.creator_name}}</text>
          <text>{{item.created_at}}</text>
        </view>
      </view>
    </view>
  </view>
</view>
```

---

## 七、部署方案

### 7.1 本地开发

**启动后端：**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

**启动小程序：**
1. 打开微信开发者工具
2. 导入 `miniprogram/` 目录
3. 修改 `utils/api.js` 中的 `API_BASE_URL` 为 `http://localhost:8000/api`
4. 编译运行

### 7.2 云服务器部署

**环境要求：**
- 云服务器：1 核 2G 起步（腾讯云/阿里云）
- 系统：Ubuntu 20.04 / CentOS 7
- Python：3.9+
- 域名：可选（用于 HTTPS）

**部署步骤：**

1. **安装依赖**
```bash
sudo apt update
sudo apt install python3.9 python3-pip nginx -y
```

2. **上传代码**
```bash
scp -r backend/ user@server:/opt/item-finder/
```

3. **安装 Python 依赖**
```bash
cd /opt/item-finder
pip3 install -r requirements.txt
```

4. **配置 Systemd 服务**
```bash
sudo vim /etc/systemd/system/item-finder.service
```

```ini
[Unit]
Description=Item Finder Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/item-finder
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **启动服务**
```bash
sudo systemctl daemon-reload
sudo systemctl enable item-finder
sudo systemctl start item-finder
```

6. **配置 Nginx**
```bash
sudo vim /etc/nginx/sites-available/item-finder
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        alias /opt/item-finder/uploads/;
        expires 30d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/item-finder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7.3 小程序上线

1. **配置合法域名**
   - 登录微信公众平台
   - 开发 → 开发管理 → 开发设置 → 服务器域名
   - 添加 `https://your-domain.com` 到 request 合法域名

2. **修改 API 地址**
   - 修改 `utils/api.js` 中的 `API_BASE_URL` 为线上地址

3. **上传代码**
   - 微信开发者工具 → 上传

4. **提交审核**
   - 登录微信公众平台 → 版本管理 → 提交审核

5. **发布**
   - 审核通过后发布

---

## 八、开发规范

### 8.1 代码规范

**Python：**
- 遵循 PEP 8
- 使用 Black 格式化
- 类型注解（Type Hints）
- 函数不超过 50 行

**JavaScript：**
- 使用 ESLint
- 使用 Prettier 格式化
- 避免全局变量

### 8.2 Git 规范

**分支管理：**
```
main          - 生产分支
develop       - 开发分支
feature/xxx   - 功能分支
bugfix/xxx    - 修复分支
```

**Commit 规范：**
```
feat: 新增功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

**示例：**
```bash
git commit -m "feat: 实现物品创建 API"
git commit -m "fix: 修复搜索接口分页问题"
```

### 8.3 数据库规范

- 所有表必须有主键
- 外键必须建立索引
- 时间字段统一使用 `TIMESTAMP`
- 软删除使用 `status` 字段，不物理删除

### 8.4 API 规范

- RESTful 风格
- 统一响应格式
- 错误码统一
- 必须写 API 文档（Swagger 自动生成）

---

## 附录

### A. 依赖清单

**backend/requirements.txt：**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
python-multipart==0.0.6
aiofiles==23.2.1
```

### B. 环境变量

**backend/.env.example：**
```bash
# 数据库
DATABASE_URL=sqlite:///./data/itemfinder.db

# 文件上传
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=5242880

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### C. 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [微信小程序文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)

---

**技术设计文档完成！** 🎉

下一步：开始编码实现
