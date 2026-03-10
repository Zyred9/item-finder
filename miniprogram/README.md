# 寻物记 - 微信小程序

## 快速开始

1. 使用微信开发者工具导入 `miniprogram` 目录
2. 在 `project.config.json` 中填写你的 AppID
3. 修改 `utils/api.js` 中的 `API_BASE_URL` 为后端地址
4. 编译运行

## 项目结构

```
miniprogram/
├── app.js              # 小程序入口
├── app.json            # 小程序配置
├── project.config.json # 项目配置
│
├── pages/              # 页面
│   ├── index/          # 首页
│   ├── store/          # 存物页
│   ├── chat/           # 对话找物页
│   ├── detail/         # 物品详情页
│   ├── family/         # 家庭管理页
│   ├── reminders/      # 提醒列表页
│   ├── profile/        # 个人中心页
│   └── login/          # 登录页
│
├── components/         # 自定义组件
│   ├── item-card/      # 物品卡片
│   ├── reminder-card/  # 提醒卡片
│   └── category-picker/# 分类选择器
│
├── utils/              # 工具函数
│   ├── api.js          # API 封装
│   └── util.js         # 通用工具
│
└── images/             # 图片资源
    └── icons/          # TabBar 图标
```

## 页面说明

| 页面 | 路径 | 说明 |
|------|------|------|
| 首页 | `/pages/index/index` | 搜索、快捷入口、提醒、最近存放 |
| 存物 | `/pages/store/store` | 表单存物、语音输入、分类扩展 |
| 找物 | `/pages/chat/chat` | 对话式搜索、多轮对话 |
| 详情 | `/pages/detail/detail` | 物品详情 |
| 家庭 | `/pages/family/family` | 创建/加入家庭 |
| 提醒 | `/pages/reminders/reminders` | 提醒列表 |
| 我的 | `/pages/profile/profile` | 个人中心 |
| 登录 | `/pages/login/login` | 微信登录 |

## 配置后端地址

在 `utils/api.js` 中修改：

```javascript
const API_BASE_URL = 'http://localhost:8000/api'  // 本地开发
// const API_BASE_URL = 'https://your-domain.com/api'  // 生产环境
```

## TabBar 图标

需要准备以下图标文件（建议尺寸 81x81）：

- `images/icons/home.png`
- `images/icons/home-active.png`
- `images/icons/store.png`
- `images/icons/store-active.png`
- `images/icons/chat.png`
- `images/icons/chat-active.png`
- `images/icons/profile.png`
- `images/icons/profile-active.png`