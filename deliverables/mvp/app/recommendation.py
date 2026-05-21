"""
SweetLoaf AI 组织转型系统 — 推荐引擎

根据时间、天气、用户角色、操作历史等生成个性化推送
"""
import random
from datetime import datetime, time
from app import models
from app.utils import generate_mock_weather


def get_daily_tips(user_id):
    """根据时间+天气+用户角色生成今日提醒

    参数:
        user_id: 用户ID

    返回:
        list: 提醒列表
    """
    user = models.get_user(user_id)
    if not user:
        return []

    # 获取天气（模拟或真实）
    weather = generate_mock_weather()
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()  # 0=周一, 6=周日

    tips = []

    # ---- 通用提醒 ----
    # 早上开工提醒
    if 5 <= hour < 8:
        tips.append({
            "title": "🌅 早安！今日开工提醒",
            "content": f"今日台南{weather['description']}，气温{weather['temp']}℃，湿度{weather['humidity']}%。"
                       f"{'高温注意打面温度控制！' if weather['temp'] > 30 else ''}"
                       f"{'湿度高注意发酵时间调整！' if weather['humidity'] > 75 else ''}",
            "type": "weather",
        })

    # 营业高峰提醒
    if 10 <= hour < 13 or 16 <= hour < 19:
        tips.append({
            "title": "⏰ 高峰时段提醒",
            "content": "现在是营业高峰，请注意出餐节奏，保持品质稳定。",
            "type": "peak",
        })

    # 收工提醒
    if 20 <= hour:
        tips.append({
            "title": "🌙 收工检查清单",
            "content": "打烊前请检查：烤箱关闭、原料归位、明日备料确认、卫生打扫。",
            "type": "closing",
        })

    # ---- 根据角色生成提醒 ----
    role = user.get("role", "")

    if role == "烘焙师" or role == "学徒":
        # 烘焙师相关提醒
        if weather["temp"] > 30:
            tips.append({
                "title": "🔥 高温烘焙提醒",
                "content": f"今日{weather['temp']}℃，建议使用冰水打面（水温12℃），面温目标22℃，发酵时间缩短30分钟。",
                "type": "baking",
                "skill_id": 2,  # 夏季高温打面法
            })
        elif weather["temp"] < 20:
            tips.append({
                "title": "❄️ 低温烘焙提醒",
                "content": f"今日{weather['temp']}℃，建议使用温水打面（水温35℃），面温目标26℃，发酵时间延长40分钟。",
                "type": "baking",
                "skill_id": 1,  # 低温天气打面调整法
            })

        # 随机推荐一个烘焙技能
        baking_skills = models.search_skills(category="烘焙工艺", status="已发布")
        if baking_skills:
            skill = random.choice(baking_skills)
            tips.append({
                "title": f"📖 推荐技能：{skill['title']}",
                "content": f"来自 {skill['creator_name']} 的经验分享，已有 {skill['view_count']} 人看过。",
                "type": "skill_recommend",
                "skill_id": skill["id"],
            })

    elif role == "销售":
        # 销售相关提醒
        if weekday >= 5:  # 周末
            tips.append({
                "title": "📢 周末销售提醒",
                "content": "周末客流较大，建议主推节日限定款和礼盒装，推荐话术已更新。",
                "type": "sales",
            })
        else:
            tips.append({
                "title": "💬 今日销售小技巧",
                "content": "主动询问客人'要不要试试我们的新品？'，成交率可提升30%！",
                "type": "sales",
            })

        # 推荐销售技能
        sales_skills = models.search_skills(category="销售技巧", status="已发布")
        if sales_skills:
            skill = random.choice(sales_skills)
            tips.append({
                "title": f"📖 推荐技能：{skill['title']}",
                "content": f"来自 {skill['creator_name']} 的经验分享，已有 {skill['view_count']} 人看过。",
                "type": "skill_recommend",
                "skill_id": skill["id"],
            })

    elif role == "店长":
        # 店长相关提醒
        tips.append({
            "title": "📊 今日管理重点",
            "content": f"今日{'周末' if weekday >= 5 else '工作日'}，请关注：出餐准时率、品质合格率、员工在岗情况。",
            "type": "management",
        })

        # 查看是否有品质预警
        tips.append({
            "title": "📋 团队技能概览",
            "content": "查看团队技能掌握情况，安排今日培训重点。",
            "type": "management",
        })

    elif role == "后勤":
        # 后勤相关提醒
        tips.append({
            "title": "📦 今日后勤重点",
            "content": "检查原料库存，确认明日到货计划。夏季注意面粉冷冻储存。",
            "type": "logistics",
        })

    elif role == "老板":
        # 老板看全局
        stats = models.get_team_skill_stats()
        tips.append({
            "title": "📈 团队效率概览",
            "content": f"技能库共 {stats['total_skills']} 个已发布技能，"
                       f"今日查看详情了解团队技能掌握情况。",
            "type": "boss",
        })

    # ---- 检查未读推送 ----
    unread_count = len(models.get_user_notifications(user_id, unread_only=True))
    if unread_count > 0:
        tips.append({
            "title": f"🔔 您有 {unread_count} 条未读消息",
            "content": "点击查看最新的操作提醒和技能推荐。",
            "type": "unread",
        })

    return tips


def get_operation_guide(skill_id, context=None):
    """生成实时操作指引（3句话以内）

    参数:
        skill_id: 技能包ID
        context: 上下文信息（如天气、时间等）

    返回:
        str: 简洁的操作指引
    """
    skill = models.get_skill(skill_id)
    if not skill:
        return "未找到相关操作指引。"

    content = skill.get("content", {})
    steps = content.get("steps", [])
    tips = content.get("tips", "")

    guide_parts = []

    # 第1句：触发条件
    trigger = content.get("trigger_condition", "")
    if trigger:
        guide_parts.append(f"适用场景：{trigger}")

    # 第2句：核心步骤（取前2个）
    if steps:
        core_steps = steps[:2]
        guide_parts.append(f"要点：{'，'.join(core_steps)}")

    # 第3句：小提示
    if tips:
        guide_parts.append(f"提示：{tips}")

    return "。".join(guide_parts[:3])


def get_quality_alert(product_type, quality_data):
    """品质异常预警

    参数:
        product_type: 产品类型
        quality_data: 品质数据

    返回:
        dict: 预警信息
    """
    grade = quality_data.get("quality_grade", "A")

    if grade == "A":
        return None  # 品质正常，无需预警

    alerts = {
        "B": {
            "level": "warning",
            "title": f"⚠️ {product_type} 品质预警",
            "content": f"检测到{product_type}品质为B级（{quality_data.get('verdict', '轻微偏差')}），建议关注。",
            "suggestions": quality_data.get("suggestions", []),
        },
        "C": {
            "level": "critical",
            "title": f"🚨 {product_type} 品质异常！",
            "content": f"检测到{product_type}品质为C级（{quality_data.get('verdict', '严重偏差')}），需要立即处理！",
            "suggestions": quality_data.get("suggestions", []),
        },
    }

    return alerts.get(grade)
