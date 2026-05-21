"""
SweetLoaf AI 组织转型系统 — LINE Bot 蓝图

当前为模拟模式，供未来对接 LINE Messaging API 使用。
部署时需配置 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET。
"""
import json
from flask import Blueprint, request, jsonify

line_bp = Blueprint("line", __name__, url_prefix="/line")

@line_bp.route("/webhook", methods=["POST"])
def webhook():
    """LINE Webhook 接收入口（模拟模式）"""
    body = request.get_json(silent=True) or {}
    if body.get("events"):
        for event in body["events"]:
            _handle_line_event(event)
    return jsonify({"status": "ok"})

@line_bp.route("/simulate", methods=["POST"])
def simulate_message():
    """模拟 LINE 消息（开发测试用）"""
    data = request.get_json(force=True) or {}
    message_type = data.get("type", "text")
    text = data.get("text", "")
    user_id = data.get("userId", "U-simulate")

    if message_type == "text":
        response = _process_text_message(text, user_id)
        return jsonify({"success": True, "reply": response})
    elif message_type == "image":
        response = _process_image_message(user_id)
        return jsonify({"success": True, "reply": response})
    elif message_type == "voice":
        response = _process_voice_message(user_id)
        return jsonify({"success": True, "reply": response})

    return jsonify({"success": False, "error": "不支持的消息类型"}), 400

def _handle_line_event(event):
    """处理 LINE 事件（预留）"""
    event_type = event.get("type", "")
    if event_type == "message":
        message = event.get("message", {})
        msg_type = message.get("type", "")
        user_id = event.get("source", {}).get("userId", "unknown")
        if msg_type == "text":
            _process_text_message(message.get("text", ""), user_id)
        elif msg_type == "image":
            _process_image_message(user_id)
        elif msg_type == "audio":
            _process_voice_message(user_id)

def _process_text_message(text, user_id):
    """处理文本消息"""
    text = text.strip()
    if text == "帮助":
        return (
            "🍞 SweetLoaf 烘焙助手\n\n"
            "📝 发送经验描述，自动生成 Skill\n"
            "   例如：「面团发酵到两倍大，手指沾面粉戳洞不回缩」\n\n"
            "📸 发送照片，自动诊断产品品质\n\n"
            "📊 发送「看板」查看团队技能统计\n\n"
            "👤 发送「我的技能」查看个人技能树"
        )
    if text == "看板":
        return "📊 团队看板请访问: http://sweetloaf.local/dashboard"
    if text == "我的技能":
        return "👤 个人技能地图请访问: http://sweetloaf.local/dashboard"

    from app.skill_engine import create_skill_from_voice
    try:
        skill_id, title = create_skill_from_voice(text, user_id=1)
        return (
            f"✅ 已创建 Skill：{title}\n\n"
            f"📎 查看详情: http://sweetloaf.local/skill/{skill_id}\n\n"
            "💡 继续分享经验，或发送「帮助」了解更多功能"
        )
    except Exception as e:
        return f"❌ 创建失败：{str(e)}，请重试或发送「帮助」"

def _process_image_message(user_id):
    """处理图片消息"""
    return (
        "📸 收到照片！正在诊断中...\n\n"
        "🔍 诊断结果会通过通知推送给您。\n"
        "请稍候片刻 ⏳"
    )

def _process_voice_message(user_id):
    """处理语音消息（预留）"""
    return (
        "🎤 收到语音消息！\n\n"
        "正在转写并分析内容...\n"
        "请稍候片刻 ⏳"
    )
