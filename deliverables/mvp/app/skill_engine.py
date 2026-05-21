"""
SweetLoaf AI 组织转型系统 — Skill 创建与管理核心逻辑
"""
import re
import json
from app import models
from app.utils import (
    parse_temperature, parse_time, extract_keywords,
    extract_conditions, extract_steps, extract_expected_result,
    generate_skill_title,
)


def create_skill_from_voice(transcript, creator_id):
    """将语音转写文本解析为结构化 Skill

    参数:
        transcript: 语音转写文本
        creator_id: 创建者用户ID

    返回:
        创建的 skill_id
    """
    # 1. 解析文本
    structured = parse_skill_from_text(transcript)

    # 2. 生成标题
    title = structured.get("title") or generate_skill_title(transcript)

    # 3. 提取关键词和分类
    keywords = extract_keywords(transcript)
    tags = ",".join(keywords[:5]) if keywords else "经验记录"

    # 4. 自动判断分类
    category = _guess_category(transcript, keywords)

    # 5. 保存到数据库
    content = {
        "trigger_condition": structured.get("trigger_condition", ""),
        "steps": structured.get("steps", []),
        "expected_result": structured.get("expected_result", ""),
        "tips": structured.get("tips", ""),
        "raw_transcript": transcript,
    }

    skill_id = models.create_skill(
        title=title,
        content=content,
        creator_id=creator_id,
        category=category,
        tags=tags,
    )

    return skill_id, title


def create_skill_from_template(answers, template_type, creator_id):
    """根据模板引导创建 Skill

    参数:
        answers: dict，模板问题的回答
        template_type: 模板类型（'baking', 'sales', 'management', 'purchase'）
        creator_id: 创建者用户ID

    返回:
        创建的 skill_id
    """
    templates = {
        "baking": {
            "title_prefix": "烘焙",
            "fields": ["product", "condition", "steps", "effect", "tips"],
        },
        "sales": {
            "title_prefix": "销售",
            "fields": ["scenario", "approach", "keywords", "effect", "tips"],
        },
        "management": {
            "title_prefix": "管理",
            "fields": ["scenario", "decision", "steps", "expected", "tips"],
        },
        "purchase": {
            "title_prefix": "采购",
            "fields": ["item", "standard", "check_method", "special_handling", "tips"],
        },
    }

    tmpl = templates.get(template_type, templates["baking"])
    title = f"{tmpl['title_prefix']}经验：{answers.get('product', answers.get('scenario', answers.get('item', '未命名')))}"

    content = {
        "trigger_condition": answers.get("condition", answers.get("scenario", "")),
        "steps": _split_steps(answers.get("steps", answers.get("approach", answers.get("decision", "")))),
        "expected_result": answers.get("effect", answers.get("expected", "")),
        "tips": answers.get("tips", ""),
        "template_type": template_type,
    }

    # 提取关键词
    all_text = " ".join(str(v) for v in answers.values())
    keywords = extract_keywords(all_text)
    tags = ",".join(keywords[:5]) if keywords else template_type

    category_map = {
        "baking": "烘焙工艺",
        "sales": "销售技巧",
        "management": "管理方法",
        "purchase": "后勤采购",
    }

    skill_id = models.create_skill(
        title=title,
        content=content,
        creator_id=creator_id,
        category=category_map.get(template_type, "通用"),
        tags=tags,
    )

    return skill_id, title


def parse_skill_from_text(text):
    """用规则从文本中提取结构化信息

    参数:
        text: 原始文本

    返回:
        dict: 结构化信息
    """
    result = {
        "title": "",
        "trigger_condition": "",
        "steps": [],
        "expected_result": "",
        "tips": "",
    }

    if not text or not text.strip():
        return result

    # 1. 提取标题
    result["title"] = generate_skill_title(text)

    # 2. 提取触发条件
    conditions = extract_conditions(text)
    if conditions:
        result["trigger_condition"] = "；".join(conditions)

    # 3. 提取温度条件（最常见）
    temps = parse_temperature(text)
    if temps and not result["trigger_condition"]:
        # 尝试判断是室温还是水温
        if "室温" in text or "天气" in text or "气温" in text:
            result["trigger_condition"] = f"室温{temps[0]}℃"
        elif "水温" in text:
            result["trigger_condition"] = f"水温{temps[0]}℃"

    # 4. 提取操作步骤
    steps = extract_steps(text)
    if steps:
        result["steps"] = steps

    # 5. 提取预期效果
    expected = extract_expected_result(text)
    if expected:
        result["expected_result"] = expected

    # 6. 提取注意事项（"注意"、"提醒"后面的内容）
    tip_match = re.search(r'(注意|提醒|小提示)[：:]\s*(.*?)(。|！|$)', text)
    if tip_match:
        result["tips"] = tip_match.group(2)

    return result


def _guess_category(text, keywords):
    """根据文本内容猜测技能分类"""
    category_scores = {
        "烘焙工艺": 0,
        "销售技巧": 0,
        "管理方法": 0,
        "后勤采购": 0,
    }

    # 烘焙工艺关键词
    baking_words = ['打面', '发酵', '烘烤', '烤', '面团', '面温', '烤箱',
                    '整形', '折叠', '气孔', '出炉', '温度', '时间']
    for w in baking_words:
        if w in text:
            category_scores["烘焙工艺"] += 2

    # 销售技巧关键词
    sales_words = ['客人', '客户', '推荐', '销售', '话术', '服务',
                   '介绍', '结账', '会员', '优惠', '复购']
    for w in sales_words:
        if w in text:
            category_scores["销售技巧"] += 2

    # 管理方法关键词
    mgmt_words = ['管理', '排班', '备货', '库存', '流程', '安排',
                  '检查', '监控', '计划', '数据']
    for w in mgmt_words:
        if w in text:
            category_scores["管理方法"] += 2

    # 后勤采购关键词
    purchase_words = ['采购', '验收', '供应商', '进货', '库存',
                      '面粉', '原料', '食材', '到货']
    for w in purchase_words:
        if w in text:
            category_scores["后勤采购"] += 2

    # 取分数最高的分类
    best = max(category_scores, key=category_scores.get)
    if category_scores[best] > 0:
        return best
    return "通用"


def _split_steps(text):
    """将文本按标点分割为步骤列表"""
    if not text:
        return []
    steps = re.split(r'[。！\n]', text)
    return [s.strip() for s in steps if s.strip() and len(s.strip()) > 2]


def get_skill_detail(skill_id):
    """获取 Skill 详情含版本历史"""
    skill = models.get_skill(skill_id)
    if not skill:
        return None

    versions = models.get_skill_versions(skill_id)
    creator = models.get_user(skill["creator_id"])

    return {
        "skill": skill,
        "versions": versions,
        "creator_name": creator["name"] if creator else "未知",
    }


def search_skills(keyword="", category="", role=""):
    """搜索技能库，支持关键词、分类、角色筛选"""
    return models.search_skills(keyword=keyword, category=category, status="已发布")


def like_skill(user_id, skill_id):
    """点赞技能"""
    models.like_skill(user_id, skill_id)


def collect_skill(user_id, skill_id):
    """收藏技能"""
    models.collect_skill(user_id, skill_id)


def get_employee_skill_map(user_id):
    """获取员工技能树"""
    return models.get_employee_skill_map(user_id)


def get_team_skill_stats():
    """获取团队技能统计"""
    return models.get_team_skill_stats()
