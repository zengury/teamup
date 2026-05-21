"""
SweetLoaf AI 组织转型系统 — 工具函数
"""
import re
import json
import random
from datetime import datetime


def parse_temperature(text):
    """从文本中提取温度数字（摄氏度）
    例：'26度' → 26, '35℃' → 35
    """
    temps = re.findall(r'(\d+)\s*[度℃]', text)
    return [int(t) for t in temps]


def parse_time(text):
    """从文本中提取时间数字（分钟/小时）
    例：'40分钟' → (40, '分钟'), '2小时' → (2, '小时')
    """
    minutes = re.findall(r'(\d+)\s*分钟', text)
    hours = re.findall(r'(\d+)\s*小时', text)
    result = []
    for m in minutes:
        result.append((int(m), '分钟'))
    for h in hours:
        result.append((int(h), '小时'))
    return result


def parse_percentage(text):
    """从文本中提取百分比数字
    例：'80%' → 80
    """
    pcts = re.findall(r'(\d+)\s*%', text)
    return [int(p) for p in pcts]


def extract_keywords(text):
    """从文本中提取烘焙相关关键词"""
    keywords = []
    # 烘焙原料
    ingredients = [
        '面粉', '水', '盐', '糖', '黄油', '奶油', '牛奶', '鸡蛋',
        '酵母', '酸种', '酵种', '天然酵母', '老面', '汤种',
        '可可粉', '抹茶粉', '坚果', '果干', '芝士', '巧克力',
    ]
    # 烘焙动作
    actions = [
        '打面', '揉面', '发酵', '整形', '折叠', '翻面',
        '烘烤', '烤', '蒸', '煮', '炸', '冷冻', '冷藏',
        '松弛', '醒发', '分割', '滚圆', '排气',
    ]
    # 烘焙设备
    equipments = [
        '烤箱', '烤盘', '发酵箱', '搅拌机', '打面机',
        '温度计', '计时器', '电子秤', '筛网', '刮板',
    ]
    # 品质描述
    qualities = [
        '气孔', '颜色', '金黄', '焦', '塌陷', '开裂',
        '蓬松', '酥脆', '柔软', '湿润', '干燥',
    ]

    for word in ingredients + actions + equipments + qualities:
        if word in text:
            keywords.append(word)

    return list(set(keywords))


def extract_conditions(text):
    """从文本中提取触发条件"""
    conditions = []
    # 天气条件
    weather_patterns = [
        (r'(天气|气温|室温|温度).*?(\d+)\s*[度℃]', '温度'),
        (r'(下雨|雨天|潮湿|湿度高)', '潮湿'),
        (r'(干燥|湿度低)', '干燥'),
        (r'(台风|寒流|冷气团)', '极端天气'),
    ]
    for pattern, cond_type in weather_patterns:
        match = re.search(pattern, text)
        if match:
            temp = match.group(2) if match.lastindex and match.lastindex >= 2 else ''
            conditions.append(f"{cond_type}: {match.group(0)}")

    # 时间条件
    time_patterns = [
        (r'(早上|上午|清晨)', '早上'),
        (r'(下午|傍晚)', '下午'),
        (r'(晚上|夜间|半夜)', '晚上'),
        (r'(节假日|假日|周末|礼拜天)', '节假日'),
        (r'(工作日|平日|平常)', '工作日'),
    ]
    for pattern, cond_type in time_patterns:
        if re.search(pattern, text):
            conditions.append(f"时间: {cond_type}")

    return list(set(conditions))


def extract_steps(text):
    """从文本中提取操作步骤"""
    steps = []
    # 匹配带序号或动作词的句子
    lines = re.split(r'[，。！？\n]', text)
    action_verbs = ['调', '打', '加', '放', '烤', '蒸', '揉', '切', '卷', '包',
                    '擀', '折叠', '翻面', '松弛', '冷藏', '冷冻', '发酵', '分割']

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 检查是否包含动作词
        for verb in action_verbs:
            if verb in line:
                # 清理多余的空格和标点
                step = line.strip('，。！？、')
                if step and len(step) > 2:
                    steps.append(step)
                break

    return steps[:6]  # 最多取6个步骤


def extract_expected_result(text):
    """从文本中提取预期效果描述"""
    # 查找效果相关的句子
    patterns = [
        r'(出来的|结果是|效果是|成品|做出[来]?的).*?(。|！)',
        r'(气孔|颜色|口感|味道|外形|形状).*?(。|！)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip('。！')

    return ''


def generate_skill_title(text):
    """根据文本自动生成技能标题"""
    # 尝试从文本中提取关键信息生成标题
    title_patterns = [
        (r'(低温|高温|下雨|台风|夏天|冬天|春季|秋季).*(打面|发酵|烘焙|烤)', r'\1\2调整法'),
        (r'(可颂|盐可颂|吐司|面包|酸种|佛卡夏).*(标准|做法|方法|配方)', r'\1\2'),
        (r'(打面|发酵|整形|烘烤).*(技巧|手法|方法|心得)', r'\1\2'),
    ]
    for pattern, title_template in title_patterns:
        match = re.search(pattern, text)
        if match:
            # 替换占位符
            title = title_template
            for i in range(1, match.lastindex + 1):
                title = title.replace(f'\\{i}', match.group(i))
            return title

    # 如果没有匹配到，使用默认标题
    temps = parse_temperature(text)
    if temps:
        return f"温度调整心得（{temps[0]}℃）"
    return "操作经验记录"


def generate_mock_diagnosis():
    """生成模拟的面包诊断结果"""
    grades = ['A', 'B', 'C']
    weights = [0.3, 0.5, 0.2]
    grade = random.choices(grades, weights=weights)[0]

    diagnoses = {
        'A': {
            'surface_color': 'golden_brown',
            'surface_score': random.randint(85, 98),
            'bottom_color': 'light_brown',
            'bottom_score': random.randint(80, 95),
            'verdict': '品质优良，烘烤到位',
            'possible_causes': [],
            'suggestions': ['继续保持当前烘烤参数'],
            'quality_grade': 'A',
        },
        'B': {
            'surface_color': random.choice(['golden_brown', 'light_brown']),
            'surface_score': random.randint(65, 80),
            'bottom_color': random.choice(['dark_brown', 'golden_brown']),
            'bottom_score': random.randint(55, 75),
            'verdict': random.choice(['底部偏深', '表面颜色偏浅', '烘烤均匀度有待提升']),
            'possible_causes': random.sample([
                '烤盘位置偏低', '底火过高', '烘烤时间偏长',
                '烤箱温度不均匀', '面团含水量偏高',
            ], 2),
            'suggestions': random.sample([
                '将烤盘放在中下层', '底火设为195℃',
                '缩短烘烤时间2-3分钟', '检查烤箱密封性',
                '调整面团含水量',
            ], 2),
            'quality_grade': 'B',
        },
        'C': {
            'surface_color': random.choice(['dark_brown', 'burnt', 'light_brown']),
            'surface_score': random.randint(30, 55),
            'bottom_color': random.choice(['burnt', 'dark_brown']),
            'bottom_score': random.randint(20, 50),
            'verdict': random.choice(['底部烤焦', '表面严重过火', '烘烤严重不足']),
            'possible_causes': random.sample([
                '烤箱温度严重偏差', '烤盘位置错误',
                '烘烤时间过长', '未预热烤箱',
                '面团重量不一致',
            ], 2),
            'suggestions': random.sample([
                '用烤箱温度计校准温度', '将烤盘放在中层',
                '缩短烘烤时间5分钟', '务必预热烤箱15分钟',
                '检查面团分割重量是否一致',
            ], 2),
            'quality_grade': 'C',
        },
    }

    return diagnoses[grade]


def generate_mock_weather():
    """生成模拟的天气数据（台南）"""
    weathers = [
        {'temp': 32, 'humidity': 75, 'condition': '晴', 'description': '高温炎热'},
        {'temp': 28, 'humidity': 80, 'condition': '多云', 'description': '闷热'},
        {'temp': 22, 'humidity': 65, 'condition': '阴', 'description': '舒适'},
        {'temp': 18, 'humidity': 70, 'condition': '小雨', 'description': '微凉'},
        {'temp': 15, 'humidity': 60, 'condition': '晴', 'description': '凉爽'},
    ]
    return random.choice(weathers)


def format_datetime(dt_str):
    """格式化日期时间字符串"""
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%m/%d %H:%M')
    except (ValueError, TypeError):
        return dt_str


def json_safe(obj):
    """确保对象可以安全JSON序列化"""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_safe(v) for v in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)
