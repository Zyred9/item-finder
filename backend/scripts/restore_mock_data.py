"""
恢复模拟数据（简化版）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from random import choice, randint
from datetime import datetime, timedelta
from models.base import SessionLocal
from models import Item, ItemExtension, Category


# 简化的物品数据
MOCK_ITEMS = [
    # 食品饮料
    {"name": "蒙牛纯牛奶", "category": "food", "location": "冰箱冷藏室"},
    {"name": "康师傅红烧牛肉面", "category": "food", "location": "厨房第二个抽屉"},
    {"name": "乐事薯片原味", "category": "food", "location": "客厅茶几下面"},
    {"name": "五常大米 5kg", "category": "food", "location": "厨房右边柜子"},
    {"name": "海天黄豆酱", "category": "food", "location": "厨房左边柜子"},
    
    # 药品健康
    {"name": "感冒灵颗粒 999", "category": "medicine", "location": "卫生间洗手台第一个抽屉"},
    {"name": "板蓝根颗粒", "category": "medicine", "location": "卫生间洗手台第一个抽屉"},
    {"name": "布洛芬缓释胶囊", "category": "medicine", "location": "主卧床头柜第一个抽屉"},
    {"name": "创可贴", "category": "medicine", "location": "卫生间洗手台第二个抽屉"},
    {"name": "善存复合维生素", "category": "medicine", "location": "主卧梳妆台第二个抽屉"},
    
    # 服饰鞋包
    {"name": "白色 T 恤", "category": "clothing", "location": "主卧衣柜第一层"},
    {"name": "牛仔裤", "category": "clothing", "location": "主卧衣柜第二层"},
    {"name": "运动鞋", "category": "clothing", "location": "玄关鞋柜第二层"},
    {"name": "双肩包", "category": "clothing", "location": "次卧衣柜"},
    
    # 数码家电
    {"name": "iPhone 15", "category": "electronics", "location": "主卧床头柜"},
    {"name": "MacBook Pro", "category": "electronics", "location": "书房书桌"},
    {"name": "电饭煲", "category": "electronics", "location": "厨房台面上"},
    {"name": "充电宝", "category": "electronics", "location": "客厅电视柜第一个抽屉"},
    
    # 证件文件
    {"name": "身份证", "category": "document", "location": "主卧床头柜第二个抽屉"},
    {"name": "护照", "category": "document", "location": "主卧床头柜第二个抽屉"},
    {"name": "银行卡", "category": "document", "location": "主卧床头柜第二个抽屉"},
    {"name": "房产证", "category": "document", "location": "主卧床头柜第二个抽屉"},
    
    # 生活用品
    {"name": "洗衣液", "category": "daily", "location": "阳台洗衣柜"},
    {"name": "卫生纸", "category": "daily", "location": "卫生间洗手台第二个抽屉"},
    {"name": "洗发水", "category": "daily", "location": "卫生间镜柜第二层"},
    {"name": "牙膏", "category": "daily", "location": "卫生间洗手台第一个抽屉"},
    {"name": "四件套", "category": "daily", "location": "主卧衣柜第三层"},
    
    # 其他
    {"name": "指甲刀", "category": "other", "location": "卫生间洗手台第一个抽屉"},
    {"name": "剪刀", "category": "other", "location": "书房书桌第一个抽屉"},
]


def restore_mock_data(family_id=2, creator_id=1):
    """恢复模拟数据"""
    session = SessionLocal()
    
    try:
        # 获取分类
        categories = {}
        for cat in session.query(Category).all():
            categories[cat.code] = cat
        
        inserted_count = 0
        for item_data in MOCK_ITEMS:
            try:
                category = categories.get(item_data["category"])
                
                # 检查是否已存在
                existing = session.query(Item).filter(
                    Item.name == item_data["name"],
                    Item.location == item_data["location"],
                    Item.family_id == family_id
                ).first()
                
                if existing:
                    continue
                
                item = Item(
                    family_id=family_id,
                    creator_id=creator_id,
                    name=item_data["name"],
                    location=item_data["location"],
                    category_id=category.id if category else None,
                    status="active"
                )
                session.add(item)
                session.flush()
                
                # 30% 的概率添加扩展信息
                if randint(1, 10) <= 3:
                    ext_data = {}
                    if item_data["category"] in ["food", "medicine"]:
                        days = randint(10, 180)
                        if randint(1, 3) == 1:
                            # 已过期
                            expire_date = datetime.now() - timedelta(days=days)
                        else:
                            # 未来过期
                            expire_date = datetime.now() + timedelta(days=days)
                        ext_data["expire_date"] = expire_date.strftime("%Y-%m-%d")
                    
                    if ext_data:
                        extension = ItemExtension(item_id=item.id, **ext_data)
                        session.add(extension)
                
                inserted_count += 1
                    
            except Exception as e:
                print(f"Error inserting {item_data['name']}: {e}")
                continue
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"Successfully restored {inserted_count} items")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    print("="*60)
    print("Restoring mock data...")
    print("="*60)
    restore_mock_data()
    print("\n[OK] Done!")


if __name__ == "__main__":
    main()
