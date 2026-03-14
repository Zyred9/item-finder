"""
生成会过期的物品数据（食品、药品、保健品等）
包括：已过期、快过期（30 天内）、正常
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from random import choice, randint
from datetime import datetime, timedelta
from models.base import SessionLocal
from models import Item, ItemExtension, Category


# 过期物品数据
EXPIRY_ITEMS = [
    # 已过期食品（生产日期 + 保质期 < 今天）
    {"name": "达利园法式小面包", "category": "食品", "location": "厨房置物架第二层", "status": "expired", "days_ago": 120},
    {"name": "康师傅红烧牛肉面", "category": "食品", "location": "厨房第二个抽屉", "status": "expired", "days_ago": 60},
    {"name": "乐事薯片原味", "category": "食品", "location": "客厅茶几下面", "status": "expired", "days_ago": 30},
    {"name": "蒙牛纯牛奶 250ml", "category": "饮料", "location": "冰箱冷藏室", "status": "expired", "days_ago": 15},
    {"name": "伊利酸奶", "category": "饮料", "location": "冰箱冷藏室", "status": "expired", "days_ago": 7},
    {"name": "海天黄豆酱", "category": "调味品", "location": "厨房左边柜子", "status": "expired", "days_ago": 90},
    {"name": "老干妈辣椒酱", "category": "调味品", "location": "厨房左边柜子", "status": "expired", "days_ago": 45},
    {"name": "徐福记酥心糖", "category": "零食", "location": "客厅电视柜第一个抽屉", "status": "expired", "days_ago": 180},
    {"name": "洽洽香瓜子", "category": "零食", "location": "客厅电视柜第二个抽屉", "status": "expired", "days_ago": 25},
    
    # 快过期食品（30 天内过期）
    {"name": "金龙鱼食用油 1.8L", "category": "食品", "location": "厨房下面柜子", "status": "expiring_soon", "days_until": 25},
    {"name": "五常大米 5kg", "category": "食品", "location": "厨房右边柜子", "status": "expiring_soon", "days_until": 15},
    {"name": "伊利纯牛奶 250ml*16", "category": "饮料", "location": "冰箱冷藏室", "status": "expiring_soon", "days_until": 8},
    {"name": "光明酸奶", "category": "饮料", "location": "冰箱冷藏室", "status": "expiring_soon", "days_until": 5},
    {"name": "李锦记生抽", "category": "调味品", "location": "厨房左边柜子", "status": "expiring_soon", "days_until": 20},
    {"name": "福临门食用油", "category": "食品", "location": "厨房下面柜子", "status": "expiring_soon", "days_until": 12},
    {"name": "奥利奥夹心饼干", "category": "零食", "location": "客厅电视柜第三个抽屉", "status": "expiring_soon", "days_until": 18},
    {"name": "德芙巧克力", "category": "零食", "location": "客厅茶几下面", "status": "expiring_soon", "days_until": 10},
    
    # 已过期药品
    {"name": "感冒灵颗粒 999", "category": "药品", "location": "卫生间洗手台第一个抽屉", "status": "expired", "days_ago": 60},
    {"name": "板蓝根颗粒", "category": "药品", "location": "卫生间洗手台第一个抽屉", "status": "expired", "days_ago": 120},
    {"name": "布洛芬缓释胶囊", "category": "药品", "location": "主卧床头柜第一个抽屉", "status": "expired", "days_ago": 30},
    {"name": "创可贴", "category": "药品", "location": "卫生间洗手台第二个抽屉", "status": "expired", "days_ago": 180},
    {"name": "酒精棉片", "category": "药品", "location": "卫生间洗手台第二个抽屉", "status": "expired", "days_ago": 90},
    {"name": "VC 银翘片", "category": "药品", "location": "主卧床头柜第二个抽屉", "status": "expired", "days_ago": 45},
    
    # 快过期药品
    {"name": "阿莫西林胶囊", "category": "药品", "location": "卫生间洗手台第一个抽屉", "status": "expiring_soon", "days_until": 20},
    {"name": "黄连素片", "category": "药品", "location": "卫生间洗手台第一个抽屉", "status": "expiring_soon", "days_until": 15},
    {"name": "眼药水", "category": "药品", "location": "主卧梳妆台第一个抽屉", "status": "expiring_soon", "days_until": 10},
    {"name": "止咳糖浆", "category": "药品", "location": "卫生间洗手台第一个抽屉", "status": "expiring_soon", "days_until": 25},
    
    # 已过期保健品
    {"name": "汤臣倍健蛋白粉", "category": "保健品", "location": "厨房置物架第三层", "status": "expired", "days_ago": 90},
    {"name": "善存复合维生素", "category": "保健品", "location": "主卧梳妆台第二个抽屉", "status": "expired", "days_ago": 60},
    {"name": "钙尔奇钙片", "category": "保健品", "location": "主卧床头柜第一个抽屉", "status": "expired", "days_ago": 30},
    {"name": "深海鱼油胶囊", "category": "保健品", "location": "厨房置物架第三层", "status": "expired", "days_ago": 45},
    
    # 快过期保健品
    {"name": "安利纽崔莱维生素 C", "category": "保健品", "location": "厨房置物架第三层", "status": "expiring_soon", "days_until": 28},
    {"name": "褪黑素片", "category": "保健品", "location": "主卧床头柜第二个抽屉", "status": "expiring_soon", "days_until": 22},
    {"name": "益生菌粉", "category": "保健品", "location": "冰箱冷藏室", "status": "expiring_soon", "days_until": 15},
    {"name": "胶原蛋白口服液", "category": "保健品", "location": "主卧梳妆台第三个抽屉", "status": "expiring_soon", "days_until": 12},
    
    # 正常物品（还有 6 个月以上）
    {"name": "旺旺仙贝", "category": "零食", "location": "客厅电视柜第一个抽屉", "status": "normal", "months_left": 12},
    {"name": "统一老坛酸菜面", "category": "食品", "location": "厨房置物架第一层", "status": "normal", "months_left": 8},
    {"name": "云南白药牙膏", "category": "洗漱用品", "location": "卫生间洗手台第一个抽屉", "status": "normal", "months_left": 18},
    {"name": "海飞丝洗发水", "category": "洗漱用品", "location": "卫生间镜柜第二层", "status": "normal", "months_left": 24},
    {"name": "飘柔护发素", "category": "洗漱用品", "location": "卫生间镜柜第二层", "status": "normal", "months_left": 20},
    {"name": "舒肤佳香皂", "category": "洗漱用品", "location": "卫生间洗手台第二个抽屉", "status": "normal", "months_left": 36},
]


def insert_expiry_items(family_id=2, creator_id=1):
    """插入过期物品数据"""
    session = SessionLocal()
    
    try:
        # 获取或创建分类
        categories = {}
        for item_data in EXPIRY_ITEMS:
            cat_name = item_data["category"]
            if cat_name not in categories:
                category = session.query(Category).filter(Category.name == cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    session.add(category)
                    session.flush()
                categories[cat_name] = category
        
        session.commit()
        
        inserted_count = 0
        expired_count = 0
        expiring_soon_count = 0
        normal_count = 0
        
        for item_data in EXPIRY_ITEMS:
            try:
                # 检查是否已存在
                existing = session.query(Item).filter(
                    Item.name == item_data["name"],
                    Item.location == item_data["location"],
                    Item.family_id == family_id
                ).first()
                
                if existing:
                    print(f"Skip existing: {item_data['name']} @ {item_data['location']}")
                    continue
                
                # 创建物品
                item = Item(
                    family_id=family_id,
                    creator_id=creator_id,
                    name=item_data["name"],
                    location=item_data["location"],
                    description=f"{item_data['status']} 物品模拟数据",
                    category_id=categories[item_data["category"]].id,
                    status="active"
                )
                session.add(item)
                session.flush()
                
                # 创建扩展信息（过期日期）
                ext_data = {}
                
                if item_data["category"] in ["食品", "饮料", "调味品", "零食"]:
                    if item_data["status"] == "expired":
                        # 已过期：生产日期 + 保质期 < 今天
                        days_ago = item_data.get("days_ago", 30)
                        shelf_life = randint(30, 180)
                        prod_date = datetime.now() - timedelta(days=days_ago + shelf_life)
                        ext_data["production_date"] = prod_date.strftime("%Y-%m-%d")
                        ext_data["shelf_life_days"] = shelf_life
                        expired_count += 1
                    elif item_data["status"] == "expiring_soon":
                        # 快过期：过期日期在未来 30 天内
                        days_until = item_data.get("days_until", 15)
                        shelf_life = randint(90, 365)
                        expire_date = datetime.now() + timedelta(days=days_until)
                        prod_date = expire_date - timedelta(days=shelf_life)
                        ext_data["production_date"] = prod_date.strftime("%Y-%m-%d")
                        ext_data["shelf_life_days"] = shelf_life
                        expiring_soon_count += 1
                    else:
                        # 正常：还有较长时间
                        months_left = item_data.get("months_left", 12)
                        shelf_life = randint(180, 365)
                        expire_date = datetime.now() + timedelta(days=months_left * 30)
                        prod_date = expire_date - timedelta(days=shelf_life)
                        ext_data["production_date"] = prod_date.strftime("%Y-%m-%d")
                        ext_data["shelf_life_days"] = shelf_life
                        normal_count += 1
                    
                    ext_data["brand"] = choice(["达利园", "康师傅", "蒙牛", "伊利", "海天", "金龙鱼", "统一", "旺旺"])
                
                elif item_data["category"] in ["药品", "保健品"]:
                    if item_data["status"] == "expired":
                        # 已过期
                        days_expired = item_data.get("days_ago", 30)
                        exp_date = datetime.now() - timedelta(days=days_expired)
                        ext_data["expire_date"] = exp_date.strftime("%Y-%m-%d")
                        expired_count += 1
                    elif item_data["status"] == "expiring_soon":
                        # 快过期
                        days_until = item_data.get("days_until", 15)
                        exp_date = datetime.now() + timedelta(days=days_until)
                        ext_data["expire_date"] = exp_date.strftime("%Y-%m-%d")
                        expiring_soon_count += 1
                    else:
                        # 正常
                        months_left = item_data.get("months_left", 12)
                        exp_date = datetime.now() + timedelta(days=months_left * 30)
                        ext_data["expire_date"] = exp_date.strftime("%Y-%m-%d")
                        normal_count += 1
                    
                    ext_data["brand"] = choice(["999", "同仁堂", "汤臣倍健", "善存", "钙尔奇", "安利", "白云山"])
                
                if ext_data:
                    extension = ItemExtension(item_id=item.id, **ext_data)
                    session.add(extension)
                
                inserted_count += 1
                print(f"Inserted: {item.name} @ {item.location} ({item_data['status']})")
                
            except Exception as e:
                print(f"Insert failed {item_data['name']}: {e}")
                session.rollback()
                continue
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"Successfully inserted {inserted_count} expiry-related items")
        print(f"  - Expired items: {expired_count}")
        print(f"  - Expiring soon (30 days): {expiring_soon_count}")
        print(f"  - Normal items: {normal_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    print("="*60)
    print("Generating expiry items mock data...")
    print("="*60)
    insert_expiry_items()
    print("\nDone! Remember to rebuild search index:")
    print("  python -m tasks.rebuild_search_index")


if __name__ == "__main__":
    main()
