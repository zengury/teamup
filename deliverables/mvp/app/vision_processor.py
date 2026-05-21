"""
SweetLoaf AI 组织转型系统 — 图像处理模块

支持:
1. 模拟模式（默认）：用随机+规则生成诊断结果
2. OpenCV模式：用颜色直方图分析面包成色
"""
import os
import json
import random
from config import MOCK_MODE, COLOR_THRESHOLDS


def diagnose_bread(image_path):
    """分析面包照片，诊断成色问题

    参数:
        image_path: 图片文件路径

    返回:
        dict: 诊断结果
    """
    if MOCK_MODE:
        return _mock_diagnose(image_path)

    try:
        return _opencv_diagnose(image_path)
    except ImportError:
        print("⚠️ 未安装 opencv-python，使用模拟模式")
        return _mock_diagnose(image_path)
    except Exception as e:
        print(f"⚠️ OpenCV 诊断失败: {e}，使用模拟模式")
        return _mock_diagnose(image_path)


def _opencv_diagnose(image_path):
    """使用 OpenCV 进行面包成色分析"""
    import cv2
    import numpy as np

    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        return _mock_diagnose(image_path)

    # 转换为 HSV 色彩空间
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 分析表面颜色
    height, width = img.shape[:2]
    # 取中间60%区域作为表面分析区域
    roi = hsv[
        int(height * 0.2):int(height * 0.8),
        int(width * 0.2):int(width * 0.8),
    ]

    # 计算各颜色占比
    total_pixels = roi.shape[0] * roi.shape[1]
    color_ratios = {}

    for color_name, thresholds in COLOR_THRESHOLDS.items():
        mask = cv2.inRange(
            roi,
            np.array([thresholds["h_low"], thresholds["s_low"], thresholds["v_low"]]),
            np.array([thresholds["h_high"], thresholds["s_high"], thresholds["v_high"]]),
        )
        color_pixels = cv2.countNonZero(mask)
        color_ratios[color_name] = color_pixels / total_pixels

    # 判断主要颜色
    dominant_color = max(color_ratios, key=color_ratios.get)
    dominant_ratio = color_ratios[dominant_color]

    # 底部区域（取图片底部20%区域）
    bottom_roi = hsv[int(height * 0.8):height, :]
    bottom_total = bottom_roi.shape[0] * bottom_roi.shape[1]
    bottom_ratios = {}
    for color_name, thresholds in COLOR_THRESHOLDS.items():
        mask = cv2.inRange(
            bottom_roi,
            np.array([thresholds["h_low"], thresholds["s_low"], thresholds["v_low"]]),
            np.array([thresholds["h_high"], thresholds["s_high"], thresholds["v_high"]]),
        )
        color_pixels = cv2.countNonZero(mask)
        bottom_ratios[color_name] = color_pixels / bottom_total if bottom_total > 0 else 0

    bottom_color = max(bottom_ratios, key=bottom_ratios.get)

    # 生成诊断结果
    return _generate_diagnosis_from_colors(dominant_color, dominant_ratio, bottom_color, color_ratios)


def _generate_diagnosis_from_colors(surface_color, surface_score, bottom_color, color_ratios):
    """根据颜色分析结果生成诊断"""
    # 颜色名称映射
    color_names = {
        "golden_brown": "金棕色",
        "light_brown": "浅褐色",
        "dark_brown": "深褐色",
        "burnt": "焦黑色",
    }

    surface_name = color_names.get(surface_color, "未知")
    bottom_name = color_names.get(bottom_color, "未知")

    # 品质等级判断
    if surface_color == "golden_brown" and bottom_color in ("golden_brown", "light_brown"):
        grade = "A"
        verdict = "品质优良，烘烤到位"
        causes = []
        suggestions = ["继续保持当前烘烤参数"]
    elif surface_color == "burnt" or bottom_color == "burnt":
        grade = "C"
        verdict = "烤焦了"
        causes = ["烘烤时间过长", "烤箱温度偏高"]
        suggestions = ["缩短烘烤时间3-5分钟", "降低烤箱温度10℃"]
    elif surface_color == "dark_brown" or bottom_color == "dark_brown":
        grade = "B"
        verdict = "底部偏深"
        causes = ["烤盘位置偏低", "底火过高"]
        suggestions = ["将烤盘放在中下层", "底火设为195℃"]
    else:
        grade = "B"
        verdict = "表面颜色偏浅"
        causes = ["烘烤时间不足", "烤箱温度偏低"]
        suggestions = ["延长烘烤时间2-3分钟", "提高烤箱温度5℃"]

    surface_score_int = max(30, min(98, int(surface_score * 100)))
    bottom_score_int = max(20, min(95, int(color_ratios.get(bottom_color, 0.5) * 100)))

    return {
        "surface_color": surface_color,
        "surface_score": surface_score_int,
        "bottom_color": bottom_color,
        "bottom_score": bottom_score_int,
        "verdict": verdict,
        "possible_causes": causes,
        "suggestions": suggestions,
        "quality_grade": grade,
    }


def _mock_diagnose(image_path):
    """模拟诊断：根据文件名关键词返回预设结果"""
    filename = os.path.basename(image_path).lower()

    # 预设诊断结果
    mock_diagnoses = {
        "perfect": {
            "surface_color": "golden_brown",
            "surface_score": 92,
            "bottom_color": "light_brown",
            "bottom_score": 88,
            "verdict": "品质优良，烘烤到位",
            "possible_causes": [],
            "suggestions": ["继续保持当前烘烤参数"],
            "quality_grade": "A",
        },
        "burnt": {
            "surface_color": "dark_brown",
            "surface_score": 45,
            "bottom_color": "burnt",
            "bottom_score": 30,
            "verdict": "底部烤焦，表面颜色偏深",
            "possible_causes": ["烤盘位置偏低，离底火太近", "底火温度过高"],
            "suggestions": ["将烤盘放在中下层", "底火设为195℃", "缩短烘烤时间3分钟"],
            "quality_grade": "C",
        },
        "under": {
            "surface_color": "light_brown",
            "surface_score": 55,
            "bottom_color": "light_brown",
            "bottom_score": 60,
            "verdict": "烘烤不足，颜色偏浅",
            "possible_causes": ["烘烤时间不足", "烤箱温度偏低"],
            "suggestions": ["延长烘烤时间5分钟", "检查烤箱温度是否准确"],
            "quality_grade": "B",
        },
        "dark": {
            "surface_color": "dark_brown",
            "surface_score": 60,
            "bottom_color": "dark_brown",
            "bottom_score": 55,
            "verdict": "底部偏深",
            "possible_causes": ["烤盘位置偏低", "底火过高"],
            "suggestions": ["将烤盘放在中下层", "底火设为195℃"],
            "quality_grade": "B",
        },
        "default": {
            "surface_color": "golden_brown",
            "surface_score": 78,
            "bottom_color": "dark_brown",
            "bottom_score": 65,
            "verdict": "整体尚可，底部略深",
            "possible_causes": ["底火略微偏高"],
            "suggestions": ["底火降低5℃试试"],
            "quality_grade": "B",
        },
    }

    # 匹配关键词
    for key, diagnosis in mock_diagnoses.items():
        if key in filename:
            return diagnosis

    return mock_diagnoses["default"]


def compare_with_standard(image_path, skill_id):
    """对比标准品相（预留功能）

    参数:
        image_path: 待诊断图片路径
        skill_id: 技能包ID（从中获取标准参考图）

    返回:
        dict: 偏差分析
    """
    from app.models import get_skill

    skill = get_skill(skill_id)
    if not skill:
        return {"error": "Skill not found"}

    diagnosis = diagnose_bread(image_path)

    # 模拟偏差分析
    return {
        "current": diagnosis,
        "standard": {
            "description": skill.get("content", {}).get("expected_result", "标准品相"),
        },
        "deviation": diagnosis.get("verdict", ""),
        "improvement_suggestions": diagnosis.get("suggestions", []),
    }
