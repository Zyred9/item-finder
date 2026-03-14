# 字段清理总结

## 已删除的数据库字段

### Item 表
- ✅ `is_favorite` - 未使用
- ✅ `find_count` - 已删除
- ✅ `last_found_at` - 已删除

### ItemExtension 表
- ✅ `open_date` - 未使用
- ✅ `open_shelf_life` - 未使用
- ✅ `dosage` - 未使用
- ✅ `document_number` - 未使用
- ✅ `issuer` - 未使用
- ✅ `accessories` - 未使用
- ✅ `size` - 低使用率 (5%)
- ✅ `color` - 低使用率 (5%)
- ✅ `season` - 未使用
- ✅ `material` - 低使用率 (5%)
- ✅ `storage_condition` - 低使用率 (1%)
- ✅ `brand` - 低使用率 (已删除)
- ✅ `model` - 低使用率 (已删除)
- ✅ `purchase_date` - 低使用率 (已删除)

## 保留的核心字段

### ItemExtension
- ✅ `expire_date` - 过期日期（34% 使用率）
- ✅ `production_date` - 生产日期（56% 使用率）
- ✅ `shelf_life_days` - 保质期天数（55% 使用率）
- ✅ `warranty_date` - 保修到期日（6% 使用率）

## 已更新的代码

### 后端
1. ✅ `models/item.py` - 更新模型定义
2. ✅ `schemas/item.py` - 更新 Schema
3. ✅ `services/expiry_reminder_agent.py` - 只使用核心字段
4. ✅ `services/search_index_service.py` - 更新 EXTENSION_LABELS
5. ✅ `api/categories.py` - 移除 parent_id 引用

### 前端
1. ✅ `miniprogram/pages/detail/detail.js` - 只展示核心字段
2. ✅ `miniprogram/pages/store/store.js` - 只处理核心字段

## 分类使用说明

当前系统只有 **7 个一级分类**，没有二级分类：
- 食品饮料
- 药品健康
- 服饰鞋包
- 数码家电
- 证件文件
- 生活用品
- 其他物品

分类不再包含复杂的扩展字段配置，所有物品统一使用 4 个核心扩展字段。

## 影响范围

### 正面影响
- ✅ 数据库表结构更简洁
- ✅ 减少存储空间
- ✅ 提高查询性能
- ✅ 降低代码维护成本
- ✅ 用户体验更清晰（只展示有用信息）

### 需要注意
- ⚠️ 如果未来需要衣物尺码、颜色等信息，需要重新添加字段
- ⚠️ 如果未来需要证件号码等信息，需要重新添加字段
- ⚠️ 建议采用灵活的 JSON 字段存储扩展信息

## 建议

如果未来需要支持更多字段，建议：
1. 使用 `extra_fields` JSON 列存储不常用的扩展信息
2. 或者按分类创建不同的扩展表
3. 保持核心表简洁，扩展信息可单独存储
