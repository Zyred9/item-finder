"""
生成 200 条家庭日常物品 mock 数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from random import choice, randint
from datetime import datetime, timedelta
from models.base import SessionLocal
from models import Item, ItemExtension, Category

# 物品分类
CATEGORIES = [
    "食品", "饮料", "调味品", "粮油副食", "零食", "保健品", "药品",
    "衣物", "鞋子", "箱包", "床上用品", "毛巾浴巾",
    "洗漱用品", "护肤品", "化妆品", "清洁用品", "纸品",
    "文具", "书籍", "电子产品", "数码配件", "小家电", "厨房用具",
    "工具", "玩具", "体育用品", "宠物用品"
]

# 物品名称（按分类）
ITEM_NAMES = {
    "食品": [
        "五常大米", "金龙鱼食用油", "海天生抽", "李锦记蚝油", "白砂糖",
        "食用盐", "陈醋", "料酒", "淀粉", "面粉",
        "挂面", "方便面", "燕麦片", "玉米片", "八宝粥",
        "饼干", "薯片", "坚果礼盒", "牛肉干", "猪肉脯",
        "巧克力", "糖果", "果冻", "话梅", "瓜子",
        "花生", "核桃", "红枣", "桂圆干", "葡萄干"
    ],
    "饮料": [
        "可口可乐", "雪碧", "芬达", "冰红茶", "绿茶",
        "乌龙茶", "普洱茶", "铁观音", "龙井茶", "茉莉花茶",
        "纯牛奶", "酸奶", "乳酸菌饮料", "豆浆粉", "麦片",
        "橙汁", "苹果汁", "葡萄汁", "椰汁", "露露杏仁露",
        "啤酒", "红酒", "白酒", "黄酒", "米酒"
    ],
    "调味品": [
        "老干妈辣椒酱", "豆瓣酱", "甜面酱", "芝麻酱", "花生酱",
        "番茄酱", "沙拉酱", "蜂蜜", "果酱", "腐乳",
        "榨菜", "泡菜", "咸菜", "海苔", "紫菜",
        "虾皮", "干贝", "香菇", "木耳", "银耳"
    ],
    "药品": [
        "感冒灵颗粒", "板蓝根", "VC 银翘片", "布洛芬", "阿司匹林",
        "创可贴", "碘伏", "酒精棉片", "棉签", "纱布",
        "体温计", "血压计", "血糖仪", "口罩", "消毒湿巾",
        "眼药水", "滴耳液", "鼻炎喷雾", "咽喉含片", "止咳糖浆",
        "胃药", "止泻药", "便秘药", "晕车药", "止痛膏药"
    ],
    "保健品": [
        "复合维生素", "维生素 C", "维生素 D", "钙片", "铁剂",
        "鱼油", "卵磷脂", "蛋白粉", "胶原蛋白", "葡萄籽",
        "褪黑素", "益生菌", "酵素", "蜂蜜胶囊", "灵芝孢子粉",
        "西洋参", "人参", "枸杞", "黄芪", "三七"
    ],
    "衣物": [
        "T 恤", "衬衫", "毛衣", "卫衣", "外套",
        "牛仔裤", "休闲裤", "运动裤", "短裤", "裙子",
        "内衣", "内裤", "袜子", "睡衣", "家居服",
        "羽绒服", "棉衣", "风衣", "西装", "大衣"
    ],
    "鞋子": [
        "运动鞋", "跑步鞋", "篮球鞋", "足球鞋", "休闲鞋",
        "皮鞋", "凉鞋", "拖鞋", "雨鞋", "雪地靴",
        "高跟鞋", "平底鞋", "单鞋", "靴子", "帆布鞋"
    ],
    "床上用品": [
        "四件套", "被套", "床单", "枕套", "枕头",
        "被子", "褥子", "床垫", "凉席", "蚊帐",
        "毛毯", "毛巾被", "电热毯", "暖宝宝", "热水袋"
    ],
    "洗漱用品": [
        "牙刷", "牙膏", "漱口水", "牙线", "洗牙粉",
        "洗面奶", "洁面仪", "洗脸巾", "沐浴露", "香皂",
        "洗发水", "护发素", "发膜", "精油", "染发剂",
        "沐浴球", "搓澡巾", "浴帽", "拖鞋", "浴巾"
    ],
    "护肤品": [
        "爽肤水", "乳液", "面霜", "精华液", "眼霜",
        "面膜", "防晒霜", "隔离霜", "卸妆水", "卸妆油",
        "护手霜", "身体乳", "润唇膏", "香水", "精油",
        "化妆水", "喷雾", "去角质", "黑头贴", "收缩水"
    ],
    "化妆品": [
        "粉底液", "气垫", "散粉", "蜜粉", "腮红",
        "口红", "唇釉", "唇彩", "眼影", "眼线笔",
        "睫毛膏", "眉笔", "眉粉", "修容", "高光",
        "化妆刷", "美妆蛋", "粉扑", "镜子", "化妆包"
    ],
    "清洁用品": [
        "洗衣液", "洗衣粉", "柔顺剂", "消毒液", "漂白剂",
        "洗洁精", "油污净", "洁厕灵", "管道疏通剂", "杀虫剂",
        "空气清新剂", "除湿盒", "樟脑丸", "干燥剂", "除味剂",
        "玻璃水", "地板清洁剂", "家具护理剂", "皮革护理剂", "不锈钢清洁剂"
    ],
    "纸品": [
        "卫生纸", "抽纸", "手帕纸", "湿巾", "厨房用纸",
        "洗脸巾", "化妆棉", "棉柔巾", "婴儿湿巾", "消毒湿巾"
    ],
    "文具": [
        "中性笔", "圆珠笔", "铅笔", "钢笔", "荧光笔",
        "记号笔", "白板笔", "修正带", "修正液", "橡皮",
        "尺子", "剪刀", "胶水", "胶带", "订书机",
        "回形针", "长尾夹", "文件夹", "笔记本", "便签纸"
    ],
    "电子产品": [
        "手机", "平板", "笔记本电脑", "台式电脑", "显示器",
        "键盘", "鼠标", "耳机", "音箱", "麦克风",
        "摄像头", "路由器", "机顶盒", "智能手表", "手环",
        "充电宝", "数据线", "充电器", "转换插头", "排插"
    ],
    "小家电": [
        "电饭煲", "电压力锅", "电磁炉", "电热水壶", "饮水机",
        "微波炉", "烤箱", "空气炸锅", "破壁机", "榨汁机",
        "豆浆机", "面包机", "电饼铛", "电炖锅", "电蒸锅",
        "电风扇", "空调扇", "取暖器", "电热毯", "电暖器",
        "吸尘器", "扫地机器人", "拖把", "除螨仪", "挂烫机"
    ],
    "厨房用具": [
        "菜刀", "水果刀", "剪刀", "砧板", "锅铲",
        "汤勺", "漏勺", "筷子", "勺子", "叉子",
        "碗", "盘子", "碟子", "杯子", "玻璃杯",
        "保温杯", "饭盒", "保鲜盒", "保鲜膜", "保鲜袋",
        "炒锅", "汤锅", "蒸锅", "砂锅", "高压锅"
    ],
    "工具": [
        "螺丝刀", "扳手", "钳子", "锤子", "卷尺",
        "电钻", "锯子", "锉刀", "美工刀", "胶带",
        "电线", "开关", "插座", "灯泡", "电池",
        "工具箱", "梯子", "绳索", "挂钩", "收纳箱"
    ],
    "宠物用品": [
        "猫粮", "狗粮", "猫砂", "尿垫", "宠物零食",
        "宠物玩具", "宠物窝", "宠物衣服", "牵引绳", "项圈",
        "宠物沐浴露", "宠物梳子", "宠物指甲剪", "宠物碗", "宠物水壶"
    ]
}

# 存放位置
LOCATIONS = [
    # 厨房
    "厨房第一个抽屉", "厨房第二个抽屉", "厨房第三个抽屉",
    "厨房左边柜子", "厨房右边柜子", "厨房下面柜子",
    "厨房台面上", "厨房置物架第一层", "厨房置物架第二层", "厨房置物架第三层",
    "冰箱冷藏室", "冰箱冷冻室", "冰箱门上",
    "微波炉上面", "烤箱旁边",
    
    # 客厅
    "客厅电视柜第一个抽屉", "客厅电视柜第二个抽屉", "客厅电视柜第三个抽屉",
    "客厅沙发左边抽屉", "客厅沙发右边抽屉",
    "客厅茶几下面", "客厅书架第一层", "客厅书架第二层", "客厅书架第三层",
    "客厅角落柜子上面", "客厅玄关柜",
    
    # 卧室
    "主卧床头柜第一个抽屉", "主卧床头柜第二个抽屉",
    "主卧衣柜第一层", "主卧衣柜第二层", "主卧衣柜第三层",
    "主卧梳妆台第一个抽屉", "主卧梳妆台第二个抽屉", "主卧梳妆台第三个抽屉",
    "主卧书桌抽屉", "主卧书架上",
    "次卧衣柜", "次卧书桌",
    
    # 卫生间
    "卫生间洗手台第一个抽屉", "卫生间洗手台第二个抽屉",
    "卫生间镜柜第一层", "卫生间镜柜第二层",
    "卫生间置物架", "卫生间马桶旁边柜子",
    "卫生间洗衣机上面", "卫生间墙上挂钩",
    
    # 阳台
    "阳台洗衣柜", "阳台储物柜第一层", "阳台储物柜第二层",
    "阳台晾衣架旁边", "阳台角落",
    
    # 玄关
    "玄关鞋柜第一层", "玄关鞋柜第二层", "玄关鞋柜第三层",
    "玄关挂衣钩", "玄关换鞋凳下面",
    "玄关储物柜",
    
    # 书房
    "书房书桌第一个抽屉", "书房书桌第二个抽屉",
    "书房书柜第一层", "书房书柜第二层", "书房书柜第三层",
    "书房电脑桌下面", "书房角落",
    
    # 其他
    "储物间第一排架子", "储物间第二排架子", "储物间第三排架子",
    "走廊柜子里", "楼梯下面储物间",
]

# 描述模板
DESCRIPTION_TEMPLATES = [
    "日常使用",
    "经常用",
    "备用",
    "新买的",
    "快用完了",
    "囤货",
    "打折时买的",
    "网购的",
    "超市买的",
    "朋友送的",
    "公司发的",
    "生日礼物",
    "节日礼物",
    "旅行买的纪念品",
    "进口商品",
    "国货",
    "老牌子",
    "网红产品",
    "推荐购买的",
    "用了很多年",
]

# 品牌
BRANDS = [
    "华为", "小米", "苹果", "三星", "OPPO", "vivo",
    "海尔", "美的", "格力", "松下", "索尼", "西门子",
    "耐克", "阿迪达斯", "安踏", "李宁",
    "欧莱雅", "雅诗兰黛", "兰蔻", "SK-II", "资生堂",
    "海天", "李锦记", "金龙鱼", "福临门",
    "强生", "宝洁", "联合利华", "花王",
]


def get_random_date(start_year=2023, end_year=2026):
    """生成随机日期"""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = randint(0, delta.days)
    return start + timedelta(days=random_days)


def generate_item_name():
    """生成物品名称"""
    category = choice(CATEGORIES)
    if category in ITEM_NAMES:
        return choice(ITEM_NAMES[category]), category
    else:
        return choice(ITEM_NAMES["食品"]), "食品"


def generate_description():
    """生成描述"""
    return choice(DESCRIPTION_TEMPLATES)


def generate_mock_items(count=200):
    """生成 mock 数据"""
    items = []
    for i in range(count):
        name, category = generate_item_name()
        location = choice(LOCATIONS)
        description = generate_description()
        
        item = {
            "name": name,
            "category": category,
            "location": location,
            "description": description,
            "creator_nickname": choice(["张三", "李四", "王五", "赵六"]),
        }
        items.append(item)
    
    return items


def insert_items_to_db(items, family_id=2, creator_id=1):
    """插入数据到数据库"""
    session = SessionLocal()
    
    try:
        # 先获取或创建分类
        categories = {}
        for item_data in items:
            cat_name = item_data["category"]
            if cat_name not in categories:
                category = session.query(Category).filter(Category.name == cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    session.add(category)
                    session.flush()
                categories[cat_name] = category
        
        session.commit()
        
        # 插入物品
        inserted_count = 0
        for item_data in items:
            try:
                category = categories.get(item_data["category"])
                
                # 检查是否已存在同名物品
                existing = session.query(Item).filter(
                    Item.name == item_data["name"],
                    Item.location == item_data["location"],
                    Item.family_id == family_id
                ).first()
                
                if existing:
                    print(f"Skip existing: {item_data['name']} @ {item_data['location']}")
                    continue
                
                item = Item(
                    family_id=family_id,
                    creator_id=creator_id,
                    name=item_data["name"],
                    location=item_data["location"],
                    description=item_data["description"],
                    category_id=category.id if category else None,
                    status="active"
                )
                session.add(item)
                session.flush()
                
                # 随机生成扩展信息（60% 的概率，提高过期物品的比例）
                if randint(1, 10) <= 6:
                    ext_data = {}
                    
                    # 食品类 - 模拟真实过期场景
                    if item_data["category"] in ["食品", "饮料", "调味品", "零食"]:
                        # 30% 已过期，40% 快过期（30 天内），30% 正常
                        expire_scenario = randint(1, 10)
                        if expire_scenario <= 3:
                            # 已过期：生产日期 + 保质期 < 今天
                            days_ago = randint(30, 365)
                            prod_date = datetime.now() - timedelta(days=days_ago)
                            shelf_life = randint(30, min(180, days_ago))  # 确保已过期
                        elif expire_scenario <= 7:
                            # 快过期：过期日期在未来 30 天内
                            days_until_expire = randint(1, 30)
                            expire_date = datetime.now() + timedelta(days=days_until_expire)
                            shelf_life = randint(30, 180)
                            prod_date = expire_date - timedelta(days=shelf_life)
                        else:
                            # 正常：还有较长时间
                            days_until_expire = randint(60, 365)
                            expire_date = datetime.now() + timedelta(days=days_until_expire)
                            shelf_life = randint(90, 365)
                            prod_date = expire_date - timedelta(days=shelf_life)
                        
                        ext_data["production_date"] = prod_date.strftime("%Y-%m-%d")
                        ext_data["shelf_life_days"] = shelf_life
                        ext_data["brand"] = choice(BRANDS) if randint(1, 10) <= 5 else None
                    
                    # 药品保健品 - 模拟真实过期场景
                    elif item_data["category"] in ["药品", "保健品"]:
                        # 20% 已过期，30% 快过期，50% 正常
                        expire_scenario = randint(1, 10)
                        if expire_scenario <= 2:
                            # 已过期
                            days_expired = randint(10, 180)
                            exp_date = datetime.now() - timedelta(days=days_expired)
                        elif expire_scenario <= 5:
                            # 快过期（30 天内）
                            days_until_expire = randint(1, 30)
                            exp_date = datetime.now() + timedelta(days=days_until_expire)
                        else:
                            # 正常
                            months_until_expire = randint(6, 24)
                            exp_date = datetime.now() + timedelta(days=months_until_expire * 30)
                        
                        ext_data["expire_date"] = exp_date.strftime("%Y-%m-%d")
                        ext_data["brand"] = choice(BRANDS) if randint(1, 10) <= 5 else None
                    
                    # 衣物鞋帽
                    elif item_data["category"] in ["衣物", "鞋子", "箱包"]:
                        ext_data["size"] = choice(["S", "M", "L", "XL", "XXL", "38", "39", "40", "41", "42"])
                        ext_data["color"] = choice(["黑色", "白色", "红色", "蓝色", "灰色", "卡其色"])
                        ext_data["material"] = choice(["棉质", "涤纶", "羊毛", "真皮", "人造革"])
                    
                    # 电子产品
                    elif item_data["category"] in ["电子产品", "小家电"]:
                        ext_data["brand"] = choice(BRANDS)
                        ext_data["model"] = f"X{randint(100, 999)}"
                        purchase_date = get_random_date(2023, 2026)
                        ext_data["purchase_date"] = purchase_date.strftime("%Y-%m-%d")
                        ext_data["warranty_date"] = (purchase_date + timedelta(days=365)).strftime("%Y-%m-%d")
                    
                    # 宠物用品
                    elif item_data["category"] == "宠物用品":
                        ext_data["brand"] = choice(BRANDS) if randint(1, 10) <= 5 else None
                    
                    if ext_data:
                        # 过滤掉 None 值
                        clean_ext = {k: v for k, v in ext_data.items() if v is not None}
                        if clean_ext:
                            extension = ItemExtension(
                                item_id=item.id,
                                **clean_ext
                            )
                            session.add(extension)
                
                inserted_count += 1
                if inserted_count % 20 == 0:
                    print(f"Inserted {inserted_count} items...")
                    
            except Exception as e:
                print(f"Insert failed {item_data['name']}: {e}")
                session.rollback()
                continue
        
        session.commit()
        print(f"\nSuccessfully inserted {inserted_count} items")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    print("Start generating 200 mock items...")
    
    # 生成数据
    items = generate_mock_items(200)
    print(f"Generated {len(items)} items")
    
    # 显示前 10 条预览
    print("\nPreview (first 10):")
    for i, item in enumerate(items[:10], 1):
        print(f"{i}. {item['name']} - {item['category']} @ {item['location']}")
    
    # 插入数据库
    print("\nInserting to database...")
    insert_items_to_db(items)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
