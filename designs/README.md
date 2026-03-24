# 寻物记 - UI 设计文件

## 设计系统概述

本设计文件包含"寻物记"微信小程序的完整 UI 设计，使用 Pencil MCP 工具创建。

## 设计文件

- **文件位置**: `designs/item-finder.pen`
- **画布尺寸**: 402x874 像素（微信小程序标准）
- **主题色**: #FF6B5B（珊瑚红）

## 页面列表

所有页面垂直排列，每个页面无重叠：

| 页面名称 | 节点 ID | 坐标 | 说明 |
|---------|--------|------|------|
| 01_Login | mDgYh | x:0, y:0 | 登录页 |
| 02_Index | p68a3 | x:0, y:900 | 首页 |
| 03_Store | Szn8A | x:0, y:1800 | 存物页 |
| 04_Chat | YDCs0 | x:0, y:2700 | 找物页（对话） |
| 05_Detail | V4ZzE | x:0, y:3600 | 详情页 |
| 06_Profile | GsBw8 | x:0, y:4500 | 个人中心页 |
| 07_Reminders | LIMAe | x:0, y:5400 | 提醒列表页 |

## 主题变量

### 颜色
- `$primary`: #FF6B5B（主色调 - 珊瑚红）
- `$primary-gradient`: #FF8E53
- `$secondary`: #667EEA
- `$secondary-gradient`: #764BA2
- `$success`: #2ED573
- `$warning`: #FFA502
- `$danger`: #FF4757
- `$text-primary`: #333333
- `$text-secondary`: #666666
- `$text-tertiary`: #999999
- `$background`: #F8F9FA
- `$white`: #FFFFFF
- `$border`: #EEEEEE

### 圆角
- `$radius-sm`: 6px
- `$radius-md`: 8px
- `$radius-lg`: 12px
- `$radius-xl`: 16px

### 间距
- `$spacing-xs`: 8px
- `$spacing-sm`: 12px
- `$spacing-md`: 16px
- `$spacing-lg`: 24px
- `$spacing-xl`: 32px

## 页面功能说明

### 01_Login（登录页）
- Logo 和品牌名称展示
- Slogan 标语
- 微信一键登录按钮

### 02_Index（首页）
- 头部问候语和家庭名称
- 统计卡片（总物品/临期/已过期）
- 快捷操作（快速存物/对话找物）
- 智能提醒卡片
- 最近存放列表
- 底部 TabBar 导航

### 03_Store（存物页）
- 拍照/语音分段选择器
- 拍照面板
- 物品信息表单（名称/位置/分类）
- 提交按钮

### 04_Chat（找物页）
- 对话消息列表
- 用户消息气泡
- AI 回复（含物品结果卡片）
- 输入框

### 05_Detail（详情页）
- 物品照片展示
- 名称和位置信息
- 快速信息卡片
- 基本信息区域
- 编辑/删除操作栏

### 06_Profile（个人中心页）
- 用户头像和昵称
- 家庭信息卡片
- 菜单列表（家庭管理/智能提醒/物品统计/帮助反馈/关于我们）
- 退出登录按钮

### 07_Reminders（提醒列表页）
- 页面头部和筛选标签（全部/紧急/临期）
- 提醒卡片列表（三级颜色区分：红色紧急/橙色临期/绿色正常）
- 空状态提示

## 导出预览

设计预览图位于 `designs/exports/` 目录：
- `mDgYh.png` - 登录页
- `p68a3.png` - 首页
- `Szn8A.png` - 存物页
- `YDCs0.png` - 找物页
- `V4ZzE.png` - 详情页
- `GsBw8.png` - 个人中心页
- `LIMAe.png` - 提醒列表页

## 使用方式

使用 Pencil MCP 工具打开设计文件：

```bash
# 在 claude-code 中打开设计文件
/open designs/item-finder.pen
```

## 设计规范

1. **布局**: 采用绝对定位布局（layout: "none"），每个页面独立放置在画布上
2. **间距**: 统一使用主题变量定义的间距系统
3. **颜色**: 严格遵循主题色板，确保视觉一致性
4. **圆角**: 统一使用主题变量定义的圆角系统
5. **TabBar**: 所有页面底部统一 62px 高度圆角导航栏
6. **页面间距**: 每个页面垂直间距 900px，确保不重叠
