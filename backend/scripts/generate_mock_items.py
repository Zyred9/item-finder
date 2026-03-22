"""
生成 300 条物品测试数据
- 覆盖 6 个分类
- 食品、药品类包含过期/临期数据
- 真实场景化的物品名称和存放位置
"""

import sys
import os
from datetime import datetime, timedelta
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db, Item, ItemExtension, Category
from services.item_service import ItemService
from sqlalchemy.orm import Session

# 配置
FAMILY_ID = 1
CREATOR_ID = 1  # 假设用户 ID 为 1
TOTAL_ITEMS = 300

# 分类配置 (category_id: 名称)
CATEGORIES = {
    1: {
        'name': '食品饮料',
        'count': 80,
        'locations': ['厨房 - 橱柜', '厨房 - 冰箱', '厨房 -  pantry', '餐厅 - 储物柜', '客厅 - 零食柜'],
        'items': [
            '蒙牛纯牛奶 250ml*12 盒', '伊利安慕希酸奶', '光明优倍鲜牛奶', '三元特品牛奶',
            '可口可乐 330ml*6 罐', '雪碧 500ml*4 瓶', '芬达橙味汽水', '农夫山泉矿泉水 5L',
            '康师傅红烧牛肉面', '统一老坛酸菜面', '日清合味道杯面', '出前一丁麻油味',
            '乐事薯片原味 104g', '品客薯片 sour cream', '好丽友派巧克力味', '达利园法式小面包',
            '三只松鼠每日坚果', '良品铺子混合坚果', '百草味夏威夷果', '来伊份核桃仁',
            '格力高百奇饼干', '奥利奥夹心饼干', '太平苏打饼干', '嘉顿动物饼干',
            '海天金标生抽 500ml', '李锦记旧庄蚝油', '恒顺香醋 500ml', '老干妈辣椒酱',
            '金龙鱼食用油 5L', '鲁花花生油 1.8L', '福临门大米 5kg', '香雪面粉 2.5kg',
            '双汇王中王火腿肠', '金锣玉米热狗肠', '美好火腿片', '荷美尔培根',
            '雀巢咖啡 1+2', '麦斯威尔速溶咖啡', '摩可纳冻干咖啡', '三顿半咖啡粉',
            '立顿红茶包', '大益普洱茶饼', '西湖龙井茶叶', '武夷山大红袍',
            '蜂蜜百花蜜 500g', '枣花蜂蜜', '冠生园蜂蜜', '百花牌蜂蜜',
            '老干妈豆豉酱', '饭扫光野香菌', '仲景香菇酱', '海天拌饭酱',
            '紫菜干品 50g', '干香菇 100g', '干木耳 80g', '干贝 50g',
            '海底捞牛油火锅底料', '好人家番茄底料', '桥头老灶火锅底料', '秋霞火锅底料',
            '面包切片 400g', '全麦吐司面包', '牛角包 6 个装', '法棍面包',
            '鸡蛋 30 枚装', '皮蛋 6 枚装', '咸鸭蛋 10 枚装', '鹌鹑蛋 20 枚装',
            '速冻水饺猪肉白菜', '思念汤圆黑芝麻', '湾仔码头云吞', '安井手抓饼',
            '午餐肉罐头 340g', '豆豉鲮鱼罐头', '玉米罐头 425g', '番茄酱罐头 400g',
            '薯片黄瓜味', '锅巴小米味', '米饼芝士味', '虾条 80g',
            '黑芝麻糊 600g', '燕麦片 1kg', '核桃粉 500g', '豆浆粉 800g',
            '牛肉干五香味', '猪肉脯蜜汁味', '鸭脖麻辣味', '鸡爪泡椒味'
        ],
        'shelf_life_ranges': {
            '鲜奶': (7, 21),
            '酸奶': (14, 30),
            '饮料': (90, 365),
            '方便面': (180, 365),
            '薯片': (180, 270),
            '饼干': (180, 365),
            '坚果': (180, 365),
            '调味品': (365, 730),
            '粮油': (180, 540),
            '火腿肠': (90, 180),
            '咖啡': (365, 730),
            '茶叶': (365, 1095),
            '蜂蜜': (540, 1095),
            '酱料': (180, 540),
            '干货': (180, 540),
            '火锅底料': (270, 540),
            '面包': (5, 15),
            '鸡蛋': (30, 60),
            '速冻食品': (270, 365),
            '罐头': (540, 1095),
            '零食': (180, 270),
            '冲饮': (180, 540),
            '肉干': (90, 180),
        }
    },
    2: {
        'name': '药品健康',
        'count': 40,
        'locations': ['卧室 - 药箱', '卫生间 - 药箱', '客厅 - 医药抽屉', '厨房 - 健康角'],
        'items': [
            '999 感冒灵颗粒 10 袋', '连花清瘟胶囊 24 粒', '板蓝根颗粒 20 袋', '小柴胡颗粒 10 袋',
            '布洛芬缓释胶囊 20 粒', '对乙酰氨基酚片 100 片', '阿司匹林肠溶片 30 片', '萘普生片 20 片',
            '阿莫西林胶囊 24 粒', '头孢克肟分散片 6 片', '罗红霉素胶囊 12 粒', '阿奇霉素片 6 片',
            '蒙脱石散 10 袋', '黄连素片 100 片', '整肠生胶囊 36 粒', '培菲康胶囊 24 粒',
            '开塞露 20ml*10 支', '乳果糖口服溶液 100ml', '莫沙必利片 24 片', '多潘立酮片 30 片',
            '氯雷他定片 12 片', '西替利嗪片 12 片', '扑尔敏片 100 片', '孟鲁司特钠片 14 片',
            '复方甘草片 100 片', '右美沙芬片 24 片', '氨溴索口服液 100ml', '乙酰半胱氨酸颗粒 10 袋',
            '人工牛黄甲硝唑胶囊 24 粒', '丁硼乳膏 120g', '复方氯己定含漱液 120ml', '西瓜霜喷剂 3g',
            '创可贴防水 100 片', '碘伏消毒液 100ml', '酒精棉球 100 粒', '无菌纱布 10 片',
            '云南白药气雾剂', '红花油 50ml', '正骨水 100ml', '麝香壮骨膏 10 贴',
            '连花清瘟颗粒', '维 C 银翘片 24 片', '感冒清热颗粒 12 袋', '荆防颗粒 10 袋',
            '六味地黄丸 200 丸', '杞菊地黄丸 200 丸', '归脾丸 200 丸', '补中益气丸 200 丸',
            '复合维生素 B 片 100 片', '维生素 C 片 100 片', '维生素 D3 胶囊 60 粒', '多维元素片 30 片',
            '鱼油软胶囊 100 粒', '卵磷脂软胶囊 100 粒', '辅酶 Q10 胶囊 60 粒', '葡萄籽胶囊 60 粒',
            '钙片碳酸钙 D3 60 片', '葡萄糖酸钙锌 12 支', '氨糖软骨素 60 片', '胶原蛋白粉 300g',
            '血糖试纸 50 片', '血压计袖带', '体温计电子', '口罩 N95 10 只装',
            '眼药水滴眼液 15ml', '人工泪液 10ml*30 支', '红霉素眼膏 2g', '氧氟沙星滴耳液 5ml',
            '皮炎平软膏 10g', '派瑞松乳膏 15g', '达克宁乳膏 20g', '红霉素软膏 10g'
        ],
        'shelf_life_ranges': {
            '感冒药': (24, 48),
            '止痛药': (24, 60),
            '抗生素': (24, 36),
            '肠胃药': (24, 48),
            '通便药': (24, 48),
            '抗过敏': (24, 48),
            '止咳药': (24, 48),
            '口腔科': (12, 36),
            '外伤护理': (24, 60),
            '跌打损伤': (24, 48),
            '中成药': (24, 60),
            '维生素': (24, 36),
            '保健品': (18, 36),
            '医疗器械': (36, 60),
            '滴眼液': (12, 36),
            '皮肤药': (24, 48),
        }
    },
    3: {
        'name': '服饰鞋包',
        'count': 50,
        'locations': ['卧室 - 衣柜', '卧室 - 鞋柜', '玄关 - 衣帽架', '储物间 - 换季区'],
        'items': [
            '白色 T 恤纯棉 L 码', '黑色 POLO 衫 XL 码', '灰色卫衣连帽 M 码', '蓝色牛仔外套 L 码',
            '卡其色休闲裤 32 码', '黑色西裤 31 码', '运动短裤速干 L 码', '睡衣套装纯棉 XL 码',
            '白色运动鞋 42 码', '黑色皮鞋 41 码', '帆布鞋经典款 40 码', '拖鞋居家防滑 42 码',
            '短袜纯棉 5 双装', '长袜运动 3 双装', '内裤纯棉 XL 码', '文胸无钢圈 75B',
            '围巾羊绒 灰色', '帽子棒球黑色', '手套冬季保暖', '腰带真皮黑色',
            '双肩包电脑 15 寸', '手提包通勤黑色', '钱包短款棕色', '卡包轻薄',
            '太阳镜偏光', '近视镜防蓝光', '老花镜 200 度', '泳镜高清',
            '泳衣连体 L 码', '瑜伽服套装 M 码', '跑步速干衣', '健身短裤',
            '羽绒服轻薄款', '棉服中长款', '毛呢大衣', '冲锋衣三合一',
            '毛衣圆领灰色', '针织开衫', '羊毛衫 V 领', '羊绒衫高领',
            '牛仔裤直筒 32 码', '休闲裤修身', '运动裤束脚', '卫裤加绒',
            '婚纱礼服 S 码', '西装套装定制', '旗袍改良款', '汉服全套',
            '高跟鞋 7cm 37 码', '平底鞋舒适', '凉鞋夏季', '靴子短筒',
            '凉鞋男士', '皮鞋商务', '登山鞋防水', '篮球鞋高帮',
            '运动鞋跑步', '板鞋休闲', '豆豆鞋驾车', '雪地靴保暖',
            '领带真丝', '领结商务', '袖扣精致', '皮带自动扣',
            '背包旅行', '拉杆箱 24 寸', '手提袋购物', '收纳袋衣物'
        ],
        'shelf_life_ranges': None  # 服饰鞋包一般无保质期
    },
    4: {
        'name': '数码家电',
        'count': 40,
        'locations': ['客厅 - 电视柜', '卧室 - 床头柜', '书房 - 电脑桌', '厨房 - 电器角'],
        'items': [
            'iPhone 15 Pro 256G', '华为 Mate60 Pro', '小米 14 Ultra', 'OPPO Find X7',
            'iPad Air 5 64G', '华为 MatePad', '小米平板 6', '联想平板',
            'MacBook Air M2', 'ThinkPad X1', '戴尔 XPS13', '华为 MateBook',
            ' AirPods Pro 2', '索尼 WF-1000XM5', 'Bose QC Earbuds', '小米 Buds 4',
            '索尼 WH-1000XM5', 'Bose QC45', 'Apple AirPods Max', '森海塞尔 MOMENTUM',
            'Apple Watch S9', '华为 Watch GT4', '小米 Watch S3', '佳明 Forerunner',
            'Kindle Paperwhite', '微信读书墨水屏', '掌阅 iReader', '文石 BOOX',
            ' Switch OLED', 'PS5 光驱版', 'Xbox Series X', 'Steam Deck',
            '大疆 Mini 4 Pro', '大疆 Pocket 3', 'GoPro Hero12', 'Insta360 X3',
            '小米手环 8', '华为手环 8', '荣耀手环 7', '乐心手环',
            '电动牙刷充电', '冲牙器便携式', '理发器家用', '美容仪导入',
            '吹风机负离子', '卷发棒恒温', '直发器陶瓷', '剃须刀电动',
            '电饭煲 5L', '电压力锅 6L', '电烤箱 32L', '空气炸锅 4L',
            '微波炉 23L', '破壁机静音', '豆浆机免滤', '咖啡机全自动',
            '净水器 RO 反渗透', '空气净化器除甲醛', '加湿器静音', '除湿机家用',
            '吸尘器无线', '扫地机器人', '擦窗机器人', '除螨仪家用',
            '电视机 65 寸 4K', '投影仪家用', '音响蓝牙', '路由器 WiFi6',
            '移动硬盘 2TB', '固态硬盘 1TB', 'U 盘 128G', '内存卡 256G',
            '充电器快充 65W', '数据线 Type-C', '无线充电器', '插排 USB',
            '键盘机械', '鼠标无线', '耳机游戏', '摄像头 1080P',
            '显示器 27 寸 2K', '支架笔记本', '散热垫电脑', '清洁套装数码'
        ],
        'shelf_life_ranges': None,  # 数码家电看保修期
        'warranty_years': (1, 3)
    },
    5: {
        'name': '证件文件',
        'count': 30,
        'locations': ['书房 - 文件柜', '卧室 - 保险箱', '客厅 - 抽屉', '玄关 - 收纳盒'],
        'items': [
            '身份证正本', '身份证副本', '户口本', '护照',
            '港澳通行证', '台湾通行证', '驾驶证正本', '驾驶证副本',
            '行驶证正本', '行驶证副本', '结婚证', '出生证明',
            '毕业证学士', '毕业证硕士', '学位证', '资格证',
            '房产证', '购房合同', '租房合同', '车辆登记证',
            '银行卡信用卡', '存折定期', '保单人寿险', '保单医疗险',
            '体检报告 2024', '病历本', '处方单', '发票电器',
            '发票家具', '发票珠宝', '发票数码', '发票培训',
            '劳动合同', '离职证明', '收入证明', '征信报告',
            '营业执照副本', '法人证', '公章财务章', '合同专用章',
            '专利证书', '商标注册证', '软件著作权证', '资质证书',
            '学生证', '工作证', '门禁卡', '会员卡'
        ],
        'shelf_life_ranges': None,
        'expiry_years': {
            '身份证': 20,  # 成人 20 年
            '护照': 10,
            '港澳通行证': 10,
            '台湾通行证': 5,
            '驾驶证': 6,
            '行驶证': None,  # 长期有效
            '结婚证': None,
            '出生证明': None,
            '毕业证': None,
            '房产证': None,
            '银行卡': 5,
            '保单': 1,  # 每年续费
            '体检报告': 1,
            '劳动合同': None,
            '营业执照': None,
        }
    },
    6: {
        'name': '生活用品',
        'count': 60,
        'locations': ['卫生间 - 洗漱台', '卫生间 - 储物柜', '阳台 - 洗衣区', '厨房 - 清洁角'],
        'items': [
            '洗发水 750ml', '护发素 750ml', '沐浴露 1L', '洗手液 500ml',
            '洗面奶氨基酸', '洗面奶泡沫', '洁面皂手工', '卸妆水 500ml',
            '牙膏 120g', '牙刷软毛', '牙线 200 支', '漱口水 500ml',
            '卫生纸卷纸 24 卷', '抽纸 3 层 20 包', '手帕纸 10 包装', '厨房用纸 6 卷',
            '卫生巾日用', '卫生巾夜用', '护垫 100 片', '棉条导管式',
            '洗衣液 3kg', '洗衣凝珠 52 颗', '柔顺剂 2L', '消毒液 1.8L',
            '洗洁精 1kg', '油污净 500ml', '洁厕灵 750ml', '管道疏通剂',
            '洗衣皂 5 块装', '香皂沐浴', '硫磺皂除螨', '内衣专用皂',
            '洗发水去屑', '洗发水控油', '洗发水滋润', '洗发水防脱',
            '沐浴露花香', '沐浴露果香', '沐浴露男士', '沐浴露儿童',
            '护手霜 50ml', '身体乳 400ml', '润唇膏', '护足霜',
            '洗发水男士', '沐浴露套装', '浴球搓澡', '浴帽防水',
            '洗发水儿童', '沐浴露婴儿', '润肤露婴儿', '护臀膏',
            '花露水 180ml', '蚊香液 3 瓶', '杀虫剂 600ml', '樟脑丸 20 粒',
            '空气清新剂', '香薰精油', '香薰蜡烛', '固体香膏',
            '垃圾袋 50*60', '保鲜膜 30cm', '保鲜袋大号', '密封袋 1L',
            '洗洁精柠檬', '洗洁精生姜', '洗洁精芦荟', '洗碗块 30 颗',
            '抹布 5 条装', '洗碗海绵', '钢丝球 10 个', '清洁刷',
            '手套橡胶', '手套一次性', '围裙防水', '袖套防污',
            '卫生纸大卷', '湿巾 80 片', '酒精湿巾', '婴儿湿巾',
            '牙膏美白', '牙膏抗敏', '牙膏儿童', '牙刷牙毛软',
            '毛巾纯棉', '浴巾加大', '方巾 5 条', '浴袍珊瑚绒',
            '洗发水套装', '沐浴旅行装', '洗漱杯', '牙刷架',
            '香皂盒沥水', '纸巾盒', '垃圾桶客厅', '垃圾桶厨房'
        ],
        'shelf_life_ranges': {
            '洗护': (365, 1095),
            '清洁': (730, 1095),
            '纸品': (730, 1095),
            '女性护理': (730, 1095),
            '洗涤': (730, 1095),
            '清洁工具': (365, 730),
            '香薰': (365, 730),
            '日用品': (730, 1095),
        }
    },
}

# 物品状态分布
STATUS_WEIGHTS = ['active'] * 95 + ['archived'] * 5

def get_shelf_life_days(category_config, item_name):
    """根据物品名称获取保质期天数"""
    if not category_config.get('shelf_life_ranges'):
        return None

    ranges = category_config['shelf_life_ranges']
    for key, (min_days, max_days) in ranges.items():
        if key in item_name:
            return random.randint(min_days, max_days)

    # 默认保质期
    default_ranges = list(ranges.values())
    min_days, max_days = random.choice(default_ranges)
    return random.randint(min_days, max_days)

def generate_exp_date(shelf_life_days, status='active'):
    """生成过期日期"""
    if shelf_life_days is None:
        return None, None, None

    today = datetime.now().date()

    # 根据保质期长短调整状态分布
    # 短保质期 (<60 天): 不能生成"正常"状态，因为 randint(61, shelf_life_days) 会失败
    if shelf_life_days < 61:
        rand = random.random()
        if rand < 0.3:  # 30% 已过期
            days_ago = random.randint(1, min(30, shelf_life_days))
            expire_date = today - timedelta(days=days_ago)
            production_date = expire_date - timedelta(days=shelf_life_days)
        else:  # 70% 临期
            days_until = random.randint(1, shelf_life_days)
            expire_date = today + timedelta(days=days_until)
            production_date = expire_date - timedelta(days=shelf_life_days)
    else:
        # 正常保质期 (>=60 天)
        rand = random.random()
        if rand < 0.15:  # 15% 已过期
            days_ago = random.randint(1, min(60, shelf_life_days // 2))
            expire_date = today - timedelta(days=days_ago)
            production_date = expire_date - timedelta(days=shelf_life_days)
        elif rand < 0.35:  # 20% 临期 (60 天内过期)
            days_until = random.randint(1, 60)
            expire_date = today + timedelta(days=days_until)
            production_date = expire_date - timedelta(days=shelf_life_days)
        else:  # 65% 正常
            days_until = random.randint(61, shelf_life_days)
            expire_date = today + timedelta(days=days_until)
            production_date = expire_date - timedelta(days=shelf_life_days)

    return expire_date, production_date, shelf_life_days

def generate_warranty_date(category_config, item_name):
    """生成保修日期（针对数码家电）"""
    if category_config.get('name') != '数码家电':
        return None

    today = datetime.now().date()
    warranty_years = category_config.get('warranty_years', (1, 3))
    years = random.randint(*warranty_years)

    # 购买日期在 0-3 年前
    purchase_days_ago = random.randint(0, 365 * 3)
    purchase_date = today - timedelta(days=purchase_days_ago)
    warranty_end = purchase_date + timedelta(days=years * 365)

    return warranty_end

def generate_items(db: Session):
    """生成物品数据"""
    print(f"开始生成 {TOTAL_ITEMS} 条物品数据...")
    print(f"目标家庭 ID: {FAMILY_ID}, 创建者 ID: {CREATOR_ID}")

    # 统计信息
    stats = {
        'expired': 0,
        'expiring_soon': 0,
        'normal': 0,
        'total': 0
    }

    items_to_insert = []
    extensions_to_insert = []

    today = datetime.now().date()

    # 为每个分类生成物品
    for cat_id, config in CATEGORIES.items():
        count = config['count']
        print(f"\n生成分类【{config['name']}】: {count} 条")

        for i in range(count):
            # 随机选择物品名称
            item_name = random.choice(config['items'])

            # 随机选择存放位置
            location = random.choice(config['locations'])

            # 随机描述
            descriptions = [
                f"新买的{item_name}",
                f"家里常备的{item_name}",
                f"刚囤货的{item_name}",
                f"常用的{item_name}",
                f"备用的{item_name}",
                None  # 有些没有描述
            ]
            description = random.choice(descriptions)

            # 随机状态
            status = random.choice(STATUS_WEIGHTS)

            # 随机创建时间（过去 365 天内）
            days_ago = random.randint(0, 365)
            created_at = datetime.now() - timedelta(days=days_ago)

            item = Item(
                family_id=FAMILY_ID,
                creator_id=CREATOR_ID,
                category_id=cat_id,
                name=item_name,
                location=location,
                description=description,
                photo_path=None,
                status=status,
                created_at=created_at,
                updated_at=datetime.now()
            )
            items_to_insert.append(item)

    # 批量插入物品
    print(f"\n正在插入 {len(items_to_insert)} 条物品记录...")
    for item in items_to_insert:
        db.add(item)
    db.flush()  # 获取 item.id

    print("正在生成扩展数据...")
    for item in items_to_insert:
        cat_config = CATEGORIES.get(item.category_id, {})

        # 食品、药品、生活用品可能有保质期
        if item.category_id in [1, 2, 6]:
            shelf_life_days = get_shelf_life_days(cat_config, item.name)
            if shelf_life_days:
                expire_date, production_date, shelf_life = generate_exp_date(shelf_life_days, item.status)

                if expire_date:
                    ext = ItemExtension(
                        item_id=item.id,
                        expire_date=expire_date,
                        production_date=production_date,
                        shelf_life_days=shelf_life
                    )
                    extensions_to_insert.append(ext)

                    # 统计
                    if expire_date < today:
                        stats['expired'] += 1
                    elif expire_date <= today + timedelta(days=60):
                        stats['expiring_soon'] += 1
                    else:
                        stats['normal'] += 1

        # 数码家电有保修期
        elif item.category_id == 4:
            warranty_date = generate_warranty_date(cat_config, item.name)
            if warranty_date:
                ext = ItemExtension(
                    item_id=item.id,
                    warranty_date=warranty_date
                )
                extensions_to_insert.append(ext)

        # 证件文件有过期日期
        elif item.category_id == 5:
            expiry_years_map = cat_config.get('expiry_years', {})
            for key, years in expiry_years_map.items():
                if key in item.name and years:
                    # 签发日期（过去 0-20 年）
                    issued_days_ago = random.randint(0, years * 365)
                    issued_date = today - timedelta(days=issued_days_ago)
                    expire_date = issued_date + timedelta(days=years * 365)

                    ext = ItemExtension(
                        item_id=item.id,
                        expire_date=expire_date
                    )
                    extensions_to_insert.append(ext)

                    if expire_date < today:
                        stats['expired'] += 1
                    elif expire_date <= today + timedelta(days=60):
                        stats['expiring_soon'] += 1
                    else:
                        stats['normal'] += 1
                    break

    # 批量插入扩展数据
    print(f"正在插入 {len(extensions_to_insert)} 条扩展记录...")
    for ext in extensions_to_insert:
        db.add(ext)

    db.commit()

    stats['total'] = len(items_to_insert)

    return stats

def main():
    """主函数"""
    db = next(get_db())

    try:
        stats = generate_items(db)
        print("\n" + "=" * 50)
        print("数据生成完成!")
        print("=" * 50)
        print(f"总物品数：{stats['total']}")
        print(f"已过期：{stats['expired']}")
        print(f"临期 (60 天内): {stats['expiring_soon']}")
        print(f"正常：{stats['normal']}")
        print("=" * 50)
    except Exception as e:
        db.rollback()
        print(f"生成数据时出错：{e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()
