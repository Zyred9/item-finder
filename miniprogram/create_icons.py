from PIL import Image, ImageDraw
import os

# 图标尺寸 (微信小程序推荐 81x81)
size = 81

# 颜色定义
colors = {
    'normal': '#999999',      # 灰色 - 未选中
    'active': '#07C160',      # 微信绿 - 选中
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_home(draw, color, offset=(0, 0)):
    """房子图标"""
    ox, oy = offset
    # 屋顶 (三角形)
    draw.polygon([(ox+40, oy+15), (ox+15, oy+40), (ox+65, oy+40)], fill=color)
    # 房身
    draw.rectangle([ox+22, oy+40, ox+58, oy+65], fill=color)

def draw_store(draw, color, offset=(0, 0)):
    """商店图标"""
    ox, oy = offset
    # 主体
    draw.rectangle([ox+15, oy+30, ox+65, oy+65], fill=color)
    # 招牌
    draw.rectangle([ox+15, oy+15, ox+65, oy+28], fill=color)

def draw_chat(draw, color, offset=(0, 0)):
    """聊天图标"""
    ox, oy = offset
    # 气泡
    draw.ellipse([ox+12, oy+12, ox+62, oy+55], fill=color)
    # 小尾巴
    draw.polygon([(ox+25, oy+52), (ox+20, oy+68), (ox+38, oy+52)], fill=color)

def draw_profile(draw, color, offset=(0, 0)):
    """用户图标"""
    ox, oy = offset
    # 头部
    draw.ellipse([ox+28, oy+12, ox+52, oy+36], fill=color)
    # 身体
    draw.ellipse([ox+12, oy+40, ox+68, oy+80], fill=color)

# 创建图标
icons = {
    'home': draw_home,
    'store': draw_store,
    'chat': draw_chat,
    'profile': draw_profile
}

icons_dir = os.path.join(os.path.dirname(__file__), 'images', 'icons')
os.makedirs(icons_dir, exist_ok=True)

for name, draw_func in icons.items():
    # 普通状态
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, hex_to_rgb(colors['normal']))
    img.save(os.path.join(icons_dir, f'{name}.png'))
    
    # 选中状态
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, hex_to_rgb(colors['active']))
    img.save(os.path.join(icons_dir, f'{name}-active.png'))

print('图标创建完成!')
print('已创建:', os.listdir(icons_dir))