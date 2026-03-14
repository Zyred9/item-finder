# 智能提醒修复说明

## 问题

清理数据库后发现：
- 物品表中有 29 个物品
- 提醒表中有 28 个过期提醒
- **但这 28 个提醒对应的物品都已经不存在了**

## 根本原因

虽然 `Reminder` 模型定义了外键级联删除：
```python
item_id = Column(BigInteger, ForeignKey("items.id", ondelete="CASCADE"))
```

但在实际删除 `locations` 表时，可能触发了意外的级联删除，导致：
1. items 表的数据被删除
2. reminders 表的数据**没有**被级联删除（成为孤儿数据）

## 解决方案

### 1. 清理孤儿提醒 ✅

执行脚本清理所有物品已删除的提醒：
```bash
python scripts/cleanup_orphan_reminders.py
```

**结果：**
- 删除了 28 条孤儿提醒
- 为当前 29 个物品重新生成提醒
- 创建了 6 条新的过期提醒

### 2. 确保级联删除生效

修改数据库外键约束，确保级联删除真正生效：

```sql
-- 检查外键约束
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME,
    DELETE_RULE
FROM information_schema.KEY_COLUMN_USAGE
WHERE REFERENCED_TABLE_NAME = 'items';
```

### 3. 添加物品删除时的提醒清理

在 `ItemService.delete()` 中确保提醒被清理：

```python
@staticmethod
def delete(db: Session, item_id: int) -> bool:
    """删除物品"""
    item = ItemService.get_by_id(db, item_id)
    if not item:
        return False
    
    # 先删除相关提醒（双重保险）
    from models import Reminder
    db.query(Reminder).filter(Reminder.item_id == item.id).delete()
    
    deleted_item_id = int(item.id)
    db.delete(item)
    db.commit()
    
    # 同步删除搜索索引
    ItemService._schedule_search_index_sync(db, deleted_item_id, "delete")
    
    return True
```

## 智能提醒的设计原则

### ✅ 正确的设计
1. **提醒与物品绑定** - 每个提醒必须对应一个物品
2. **物品删除，提醒删除** - 级联删除或通过代码确保
3. **提醒是物品的属性** - 不是独立存在的数据

### ❌ 错误的设计
- 提醒独立于物品存在
- 物品删除了提醒还在
- 提醒不指向任何物品

## 提醒类型

目前支持的提醒类型：

| 类型 | 说明 | 触发条件 |
|------|------|----------|
| `expire` | 过期提醒 | 物品有过期日期 |
| `open` | 开封提醒 | 物品有开封日期 + 开封保质期 |
| `warranty` | 保修提醒 | 物品有保修到期日期 |

## 提醒级别

| 级别 | 说明 | 条件 |
|------|------|------|
| `urgent` | 紧急 | 已过期或 7 天内过期 |
| `warning` | 警告 | 7-30 天内过期 |
| `normal` | 普通 | 30 天以上过期 |

## 自动创建提醒的时机

1. **创建物品时** - `ItemService.create()` 调用 `sync_reminders_for_item()`
2. **更新物品时** - `ItemService.update()` 调用 `sync_reminders_for_item()`
3. **手动触发** - 运行 `sync_all_reminders.py` 脚本

## 验证方法

### 检查提醒是否与物品绑定
```python
from models import Reminder, Item

reminders = db.query(Reminder).all()
for r in reminders:
    item = db.query(Item).filter(Item.id == r.item_id).first()
    assert item is not None, f"Reminder {r.id} has no item!"
```

### 检查级联删除
```python
# 删除一个物品
item = db.query(Item).filter(Item.id == 1).first()
db.delete(item)
db.commit()

# 验证提醒也被删除
reminder = db.query(Reminder).filter(Reminder.item_id == 1).first()
assert reminder is None, "Reminder should be deleted!"
```

## 维护脚本

### 清理孤儿提醒
```bash
python scripts/cleanup_orphan_reminders.py
```

### 为所有物品重新生成提醒
```bash
python scripts/sync_all_reminders.py
```

### 检查提醒健康状态
```bash
python scripts/check_reminder_health.py
```

## 后续改进

1. **定期清理** - 每周运行一次孤儿提醒清理脚本
2. **数据库约束** - 确保外键级联删除真正生效
3. **单元测试** - 添加测试确保删除物品时提醒被清理
4. **监控告警** - 发现孤儿提醒时发送告警
