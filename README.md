# 寻物记 - 快速开始指南

**最后更新：** 2026-03-03  
**当前状态：** 后端骨架已完成，小程序骨架已创建

---

## 一、项目结构

```
寻物记/
├── PRD.md              # 产品需求文档
├── ARCHITECTURE.md     # 技术架构文档
├── TODO.md             # 开发任务清单
├── README.md           # 本文件
├── backend/            # 后端 FastAPI ✅ 已完成
│   ├── main.py         # API 主文件
│   ├── requirements.txt
│   ├── start.bat       # Windows 启动脚本
│   └── README.md       # 后端开发文档
├── miniprogram/        # 微信小程序 ✅ 骨架已创建
│   ├── app.js
│   ├── app.json
│   ├── project.config.json
│   └── README.md       # 小程序开发文档
└── design-prototype/   # 高保真原型
    ├── index.html
    └── full-page-screenshot.png
```

---

## 二、快速开始

### 2.1 环境要求

- Python 3.9+
- 微信开发者工具
- 百度智能云账号（语音 API，后续使用）

### 2.2 后端启动（✅ 已完成）

**Windows:**
```bash
cd C:\Users\zyred\.copaw\workspaces\item-finder\backend
start.bat
```

**手动启动:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

服务启动后访问：
- API 地址：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 2.3 小程序启动（骨架已创建）

1. 打开微信开发者工具
2. 导入项目：`C:\Users\zyred\.copaw\workspaces\item-finder\miniprogram`
3. 填写 AppID（可用测试号）
4. 编译运行

> 注意：需先启动后端服务，小程序才能正常调用 API

---

## 三、开发流程

### 3.1 每日开发

```bash
# 启动后端（开发模式）
cd backend
uvicorn main:app --reload

# 小程序：用微信开发者工具打开，自动热重载
```

### 3.2 数据库迁移

```bash
# 首次启动时自动创建表
python init_db.py
```

### 3.3 API 测试

访问：http://127.0.0.1:8000/docs

---

## 四、配置说明

### 4.1 环境变量

创建 `backend/.env` 文件：

```bash
DATABASE_URL=sqlite:///./xunwuji.db
SECRET_KEY=your-random-secret-key-here
BAIDU_APP_ID=你的百度 APP_ID
BAIDU_API_KEY=你的百度 API_KEY
BAIDU_SECRET_KEY=你的百度 SECRET_KEY
```

### 4.2 百度语音 API 申请

1. 访问：https://ai.baidu.com/
2. 注册账号
3. 创建应用 → 选择"语音识别"和"语音合成"
4. 获取 AppID、API Key、Secret Key

---

## 五、常用命令

### 后端

```bash
# 启动开发服务器
uvicorn main:app --reload

# 启动生产服务器
uvicorn main:app --host 0.0.0.0 --port 8000

# 运行测试
pytest

# 查看 API 文档
# 浏览器访问：http://127.0.0.1:8000/docs
```

### 小程序

- 用微信开发者工具打开 `frontend/`
- 点击"编译"预览
- 点击"预览"手机扫码测试

---

## 六、部署上线

### 6.1 后端部署

```bash
# 服务器安装依赖
pip install -r requirements.txt

# 使用 Supervisor 管理进程
sudo supervisorctl start xunwuji

# 查看日志
sudo tail -f /var/log/xunwuji.log
```

### 6.2 小程序上线

1. 微信开发者工具 → 上传代码
2. 登录微信公众平台 → 版本管理
3. 提交审核
4. 审核通过后发布

---

## 七、问题排查

### 常见问题

**Q: 语音识别失败？**
- 检查百度 API 配额是否用完
- 检查网络连通性
- 查看后端日志

**Q: 图片上传失败？**
- 检查服务器磁盘空间
- 检查文件权限
- 检查文件大小限制

**Q: 小程序无法登录？**
- 检查微信 AppID 配置
- 检查服务器域名白名单
- 查看微信开发者工具控制台

---

## 八、开发资源

| 资源 | 链接 |
|------|------|
| FastAPI 文档 | https://fastapi.tiangolo.com/ |
| 微信小程序文档 | https://developers.weixin.qq.com/miniprogram/dev/framework/ |
| 百度语音 API | https://ai.baidu.com/tech/speech |
| SQLAlchemy 文档 | https://docs.sqlalchemy.org/ |

---

## 九、联系方式

- 项目仓库：[待创建]
- 问题反馈：[待创建]
- 产品建议：[待创建]

---

**开始开发吧！🚀**
