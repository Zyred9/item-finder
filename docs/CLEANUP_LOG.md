# 数据库清理日志

## 清理时间
2026-03-12

## 清理内容

### 1. 清理二级分类 ✅

**操作：**
- 删除 `categories` 表中所有 `parent_id IS NOT NULL` 的记录
- 移除 `Category` 模型中的 `parent_id` 字段和自引用关系
- 只保留 7 个一级分类

**结果：**
```
categories 表：7 条记录
- food (食品饮料)
- medicine (药品健康)
- clothing (服饰鞋包)
- electronics (数码家电)
- document (证件文件)
- daily (生活用品)
- other (其他物品)
```

### 2. 清理 Qdrant 数据 ✅

**操作：**
- 重新索引所有 active 物品到 Qdrant
- 自动清理旧的二级分类数据

**结果：**
- Qdrant 集合中的数据已更新
- 所有物品使用新的 7 个分类

### 3. 删除未使用的表 ✅

**删除的表：**
- `locations` 表 - 位置管理功能已废弃
- 同时删除了 `Location` 模型文件

**保留的表（9 个）：**
1. `users` - 用户表
2. `families` - 家庭表
3. `categories` - 分类表（7 个分类）
4. `items` - 物品表
5. `item_extensions` - 物品扩展信息表
6. `reminders` - 提醒表
7. `chat_messages` - 聊天消息表
8. `search_sync_tasks` - 搜索同步任务表
9. `feedbacks` - 反馈表（保留但暂未使用）

### 4. 模型文件清理 ✅

**删除的文件：**
- `backend/models/location.py`

**修改的文件：**
- `backend/models/category.py` - 移除 parent_id 字段
- `backend/models/family.py` - 移除 locations 关系
- `backend/models/__init__.py` - 移除 Location 导入
- `backend/models/base.py` - 移除 Location 导入

## 分类体系

### 最终分类（7 个）

| 序号 | Code | 名称 | 图标 |
|------|------|------|------|
| 1 | food | 食品饮料 | 🍔 |
| 2 | medicine | 药品健康 | 💊 |
| 3 | clothing | 服饰鞋包 | 👕 |
| 4 | electronics | 数码家电 | 📱 |
| 5 | document | 证件文件 | 📄 |
| 6 | daily | 生活用品 | 🏠 |
| 7 | other | 其他物品 | 📦 |

## 影响范围

### 前端影响
- 分类选择器只需要显示 7 个选项
- 图标映射逻辑已更新支持 code 和名称匹配
- 移除了二级分类相关的 UI 逻辑

### 后端影响
- 分类 API 只返回 7 个一级分类
- 物品创建/更新时使用 7 个分类之一
- 移除了所有 parent_id 相关的查询逻辑

### 数据迁移
- 原有物品的分类映射：
  - 所有二级分类物品 → 对应的一级分类
  - 无法映射的 → other（其他物品）

## 验证结果

### 数据库验证
```sql
-- 分类表
SELECT * FROM categories ORDER BY sort_order;
-- 结果：7 条记录

-- 表列表
SHOW TABLES;
-- 结果：9 个表（无 locations）
```

### 代码验证
- ✅ Category 模型无 parent_id 字段
- ✅ Family 模型无 locations 关系
- ✅ 所有导入已更新
- ✅ 数据库表已删除

## 后续工作

1. **前端测试** - 验证分类选择器正常显示 7 个选项
2. **存物测试** - 验证新建物品能正确选择分类
3. **搜索测试** - 验证搜索功能正常
4. **提醒测试** - 验证过期提醒功能正常

## 备注

- 清理脚本位置：`backend/scripts/cleanup_database.py`
- 分类文档位置：`docs/CATEGORIES.md`
- 如有问题可回滚到清理前的数据库备份
