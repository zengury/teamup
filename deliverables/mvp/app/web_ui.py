"""
SweetLoaf AI 组织转型系统 — Web UI 路由（蓝图）
"""
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

from app import models
from app.skill_engine import (
    parse_skill_from_text,
    create_skill_from_voice,
    get_skill_detail,
    search_skills,
    like_skill,
    collect_skill,
    get_employee_skill_map,
    get_team_skill_stats,
)
from app.utils import generate_mock_diagnosis, format_datetime

web_bp = Blueprint("web", __name__, url_prefix="")


# ============================================================
# 页面路由
# ============================================================

@web_bp.route("/")
def index():
    """首页 — 角色选择"""
    users = models.get_all_users()
    return render_template("index.html", users=users)


@web_bp.route("/login/<int:user_id>")
def login(user_id):
    """选择角色进入系统"""
    user = models.get_user(user_id)
    if not user:
        return redirect(url_for("web.index"))
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_role"] = user["role"]
    return redirect(url_for("web.dashboard"))


@web_bp.route("/dashboard")
def dashboard():
    """效率看板"""
    if "user_id" not in session:
        return redirect(url_for("web.index"))
    user = models.get_user(session["user_id"])
    stats = get_team_skill_stats()
    recent_logs = models.get_recent_logs(10)

    # 最近7天技能增长趋势（从日志中统计）
    trend_data = _get_skill_trend()

    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        recent_logs=recent_logs,
        trend_data=trend_data,
    )


@web_bp.route("/skills")
def skills():
    """技能库"""
    if "user_id" not in session:
        return redirect(url_for("web.index"))
    user = models.get_user(session["user_id"])
    keyword = request.args.get("keyword", "")
    category = request.args.get("category", "")
    skill_list = search_skills(keyword=keyword, category=category)
    return render_template(
        "skills.html",
        user=user,
        skills=skill_list,
        current_keyword=keyword,
        current_category=category,
    )


@web_bp.route("/skill/<int:skill_id>")
def skill_detail(skill_id):
    """Skill 详情页"""
    if "user_id" not in session:
        return redirect(url_for("web.index"))
    user = models.get_user(session["user_id"])
    detail = get_skill_detail(skill_id)
    if not detail:
        return redirect(url_for("web.skills"))
    # 相关推荐（同分类其他技能）
    related = models.search_skills(category=detail["skill"]["category"], status="已发布")
    related = [s for s in related if s["id"] != skill_id][:4]
    return render_template(
        "skill_detail.html",
        user=user,
        skill=detail["skill"],
        versions=detail["versions"],
        creator_name=detail["creator_name"],
        related=related,
    )


@web_bp.route("/skill/create", methods=["GET", "POST"])
def skill_create():
    """创建 Skill"""
    if "user_id" not in session:
        return redirect(url_for("web.index"))
    user = models.get_user(session["user_id"])

    if request.method == "POST":
        data = request.get_json(force=True) or {}
        text = data.get("text", "")
        template_type = data.get("template_type", "")
        answers = data.get("answers", {})

        if text:
            # 自由输入模式
            skill_id, title = create_skill_from_voice(text, session["user_id"])
            return jsonify({"success": True, "skill_id": skill_id, "title": title})
        elif template_type and answers:
            # 模板引导模式
            from app.skill_engine import create_skill_from_template
            skill_id, title = create_skill_from_template(
                answers, template_type, session["user_id"]
            )
            return jsonify({"success": True, "skill_id": skill_id, "title": title})
        else:
            return jsonify({"success": False, "error": "请输入经验描述或选择模板"}), 400

    return render_template("skill_create.html", user=user)


@web_bp.route("/skill/parse", methods=["POST"])
def skill_parse():
    """AI 解析文本（返回结构化结果供预览）"""
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"success": False, "error": "请输入文本"}), 400
    parsed = parse_skill_from_text(text)
    return jsonify({"success": True, "parsed": parsed})


@web_bp.route("/employee/<int:user_id>")
def employee_skill_map(user_id):
    """员工技能地图"""
    if "user_id" not in session:
        return redirect(url_for("web.index"))
    current_user = models.get_user(session["user_id"])
    skill_map = get_employee_skill_map(user_id)
    if not skill_map:
        return redirect(url_for("web.dashboard"))
    return render_template(
        "employee.html",
        user=current_user,
        target_user=skill_map["user"],
        skills=skill_map["skills"],
        stats=skill_map["stats"],
    )


@web_bp.route("/workflows")
def workflows():
    """流程管理"""
    if "user_id" not in session:
        return redirect(url_for("web.index"))
    user = models.get_user(session["user_id"])
    with models.get_db() as conn:
        rows = conn.execute(
            """SELECT w.*, u.name as creator_name
               FROM workflows w
               LEFT JOIN users u ON w.created_by = u.id
               ORDER BY w.created_at DESC"""
        ).fetchall()
        workflow_list = [models.dict_from_row(r) for r in rows]
    return render_template("workflows.html", user=user, workflows=workflow_list)


# ============================================================
# API 路由
# ============================================================

@web_bp.route("/api/skills/search")
def api_search_skills():
    """搜索技能 API"""
    keyword = request.args.get("keyword", "")
    category = request.args.get("category", "")
    results = search_skills(keyword=keyword, category=category)
    return jsonify({"success": True, "skills": results})


@web_bp.route("/api/skill/<int:skill_id>/like", methods=["POST"])
def api_like_skill(skill_id):
    """点赞技能"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"}), 401
    like_skill(session["user_id"], skill_id)
    skill = models.get_skill(skill_id)
    return jsonify({"success": True, "like_count": skill["like_count"]})


@web_bp.route("/api/skill/<int:skill_id>/collect", methods=["POST"])
def api_collect_skill(skill_id):
    """收藏技能"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"}), 401
    collect_skill(session["user_id"], skill_id)
    skill = models.get_skill(skill_id)
    return jsonify({"success": True, "collect_count": skill["collect_count"]})


@web_bp.route("/api/skill/<int:skill_id>/comment", methods=["POST"])
def api_comment_skill(skill_id):
    """提交评论（记录到操作日志）"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"}), 401
    data = request.get_json(force=True) or {}
    comment = data.get("comment", "")
    if comment:
        models.log_operation(
            session["user_id"],
            "评论",
            skill_id=skill_id,
            detail=comment[:200],
        )
    return jsonify({"success": True})


@web_bp.route("/api/skill/<int:skill_id>/progress", methods=["POST"])
def api_update_progress(skill_id):
    """更新技能学习进度"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"}), 401
    data = request.get_json(force=True) or {}
    progress = data.get("progress")
    status = data.get("status")
    models.update_skill_progress(
        session["user_id"], skill_id, progress=progress, status=status
    )
    return jsonify({"success": True})


@web_bp.route("/api/notifications")
def api_notifications():
    """获取当前用户的通知"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"}), 401
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    notifications = models.get_user_notifications(
        session["user_id"], unread_only=unread_only
    )
    return jsonify({"success": True, "notifications": notifications})


@web_bp.route("/api/notification/<int:nid>/read", methods=["POST"])
def api_mark_read(nid):
    """标记通知已读"""
    models.mark_notification_read(nid)
    return jsonify({"success": True})


@web_bp.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    """拍照诊断"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "未登录"}), 401
    # 模拟诊断
    result = generate_mock_diagnosis()
    return jsonify({"success": True, "diagnosis": result})


@web_bp.route("/api/dashboard/stats")
def api_dashboard_stats():
    """看板统计数据 API"""
    stats = get_team_skill_stats()
    trend = _get_skill_trend()
    return jsonify({"success": True, "stats": stats, "trend": trend})


@web_bp.route("/api/employees/skill-map")
def api_all_employee_skill_maps():
    """所有员工技能地图（用于看板）"""
    users = models.get_all_users()
    result = []
    for u in users:
        sm = get_employee_skill_map(u["id"])
        if sm:
            result.append({
                "user": sm["user"],
                "stats": sm["stats"],
            })
    return jsonify({"success": True, "employees": result})


@web_bp.route("/logout")
def logout():
    """登出"""
    session.clear()
    return redirect(url_for("web.index"))


# ============================================================
# 辅助函数
# ============================================================

def _get_skill_trend():
    """获取最近7天技能增长趋势"""
    from datetime import timedelta
    trend = []
    today = datetime.now()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        label = day.strftime("%m/%d")
        with models.get_db() as conn:
            count = conn.execute(
                """SELECT COUNT(*) FROM skills
                   WHERE DATE(created_at) <= ? AND status='已发布'""",
                (day_str,),
            ).fetchone()[0]
        trend.append({"label": label, "count": count})
    return trend
