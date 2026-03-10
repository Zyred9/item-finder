# 寻物记 - 技术架构文档

**版本：** v1.0  
**创建时间：** 2025-01-XX

---

## 一、技术栈

### 前端（微信小程序）
```
框架：原生微信小程序
UI 库：Vant Weapp
语音：微信小程序语音识别 API + 百度 TTS
图片：微信小程序拍照 API
```

### 后端
```
语言：Python 3.11+
框架：FastAPI
数据库：SQLite（初期）→ PostgreSQL（后期）
ORM：SQLAlchemy
API 文档：Swagger UI（自动生成）
```

### 部署
```
服务器：腾讯云/阿里云（2 核 4G）
进程管理：PM2 / Supervisor
域名：xunwuji.com（示例）
HTTPS：Let's Encrypt 免费证书
```

---

## 二、项目结构

```
寻物记/
├── frontend/                 # 微信小程序
│   ├── pages/
│   │   ├── index/           # 首页
│   │   ├── search/          # 搜索页
│   │   ├── add-item/        # 存物页
│   │   └── family/          # 家庭管理
│   ├── components/          # 组件
│   ├── utils/               # 工具函数
│   └── app.js
│
├── backend/                 # 后端 API
│   ├── main.py             # FastAPI 入口
│   ├── models/             # 数据模型
│   │   ├── family.py
│   │   ├── user.py
│   │   └── item.py
│   ├── routers/            # API 路由
│   │   ├── items.py
│   │   ├── users.py
│   │   └── families.py
│   ├── services/           # 业务逻辑
│   │   ├── speech.py       # 语音服务
│   │   └── storage.py      # 存储服务
│   ├── database.py         # 数据库配置
│   └── config.py           # 配置文件
│
└── docs/                   # 文档
    ├── PRD.md
    └── ARCHITECTURE.md
```

---

## 三、API 设计

### 3.1 物品相关

```
POST   /api/items           # 创建物品
GET    /api/items           # 搜索物品
GET    /api/items/{id}      # 获取物品详情
DELETE /api/items/{id}      # 删除物品
```

### 3.2 家庭相关

```
POST   /api/families        # 创建家庭
GET    /api/families/{id}   # 获取家庭信息
POST   /api/families/join   # 加入家庭
GET    /api/families/{id}/members  # 获取家庭成员
```

### 3.3 用户相关

```
POST   /api/users/login     # 微信登录
GET    /api/users/me        # 获取当前用户信息
```

---

## 四、数据表详细设计

### 4.1 families 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 主键（UUID） |
| name | TEXT | 家庭名称 |
| invite_code | TEXT | 邀请码（6 位随机码） |
| created_at | TIMESTAMP | 创建时间 |

### 4.2 users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 主键（UUID） |
| family_id | TEXT | 外键（families.id） |
| name | TEXT | 用户昵称 |
| avatar_url | TEXT | 头像 URL |
| wechat_openid | TEXT | 微信 OpenID |
| created_at | TIMESTAMP | 创建时间 |

### 4.3 items 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 主键（UUID） |
| family_id | TEXT | 外键（families.id） |
| creator_id | TEXT | 外键（users.id） |
| name | TEXT | 物品名称 |
| location | TEXT | 位置描述 |
| photo_url | TEXT | 照片 URL |
| voice_note_url | TEXT | 语音备注 URL |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

## 五、核心流程

### 5.1 存物流程

```
小程序端                          后端                          数据库
   |                               |                               |
   |--1.拍照 + 语音 --------------->|                               |
   |                               |--2.语音识别------------------>|
   |                               |<--3.返回文本------------------|
   |                               |--4.解析（物品名，位置）------->|
   |                               |--5.保存图片------------------>|
   |                               |--6.保存记录------------------>|
   |<--7.返回成功------------------|                               |
```

### 5.2 搜索流程

```
小程序端                          后端                          数据库
   |                               |                               |
   |--1.语音/文字搜索------------->|                               |
   |                               |--2.数据库搜索---------------->|
   |                               |<--3.返回结果------------------|
   |                               |--3.TTS 转语音---------------->|
   |                               |<--4.返回音频------------------|
   |<--5.返回结果 + 音频-----------|                               |
```

---

## 六、安全设计

### 6.1 认证
- 微信小程序登录（获取 OpenID）
- JWT Token 认证

### 6.2 授权
- 用户只能访问自己家庭的数据
- 家庭邀请码验证

### 6.3 数据安全
- 图片 URL 签名（防直接访问）
- 敏感信息加密存储

---

## 七、性能优化

### 7.1 数据库
- 常用字段建立索引（family_id, name, created_at）
- 分页查询（避免一次性加载过多数据）

### 7.2 缓存
- 热门物品信息缓存（Redis）
- 用户信息缓存

### 7.3 图片
- 缩略图 + 原图分离
- CDN 加速

---

## 八、监控与日志

### 8.1 日志
- 访问日志（Nginx）
- 应用日志（Python logging）
- 错误日志（Sentry）

### 8.2 监控
- 服务器监控（CPU、内存、磁盘）
- API 响应时间监控
- 错误率监控

---

## 九、部署方案

### 9.1 开发环境
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
用微信开发者工具打开 frontend/
```

### 9.2 生产环境
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（Supervisor 配置）
[program:xunwuji]
command=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=/path/to/backend
autostart=true
autorestart=true

# Nginx 反向代理
server {
    listen 443 ssl;
    server_name xunwuji.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 十、开发工具

| 用途 | 工具 |
|------|------|
| 代码编辑 | VS Code |
| 小程序开发 | 微信开发者工具 |
| API 测试 | Postman / Insomnia |
| 数据库管理 | DBeaver / Navicat |
| 版本控制 | Git + GitHub |

---

## 附录

### A. 依赖包清单

```txt
# backend/requirements.txt
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
python-jose==3.3.0
python-multipart==0.0.6
baidu-aip==4.16.12  # 百度语音 API
pillow==10.2.0
```

### B. 环境变量

```bash
# .env
DATABASE_URL=sqlite:///./xunwuji.db
SECRET_KEY=your-secret-key-here
BAIDU_APP_ID=your-app-id
BAIDU_API_KEY=your-api-key
BAIDU_SECRET_KEY=your-secret-key
```
