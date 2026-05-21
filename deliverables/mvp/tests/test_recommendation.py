"""
SweetLoaf AI 组织转型系统 — 推荐引擎测试

测试范围：recommendation.py 中的推送、指引、预警功能
"""
import sys
import os
from unittest.mock import patch
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DB_PATH"] = ":memory:"

from app import models
from app import recommendation


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建数据库"""
    models.DB_PATH = ":memory:"
    models.init_db()
    # 创建测试用户
    models.create_user("阿明", "烘焙师", "0912-345-003")
    models.create_user("小豪", "学徒", "0912-345-006")
    models.create_user("小玲", "销售", "0912-345-007")
    models.create_user("志伟", "店长", "0912-345-002")
    models.create_user("陈老板", "老板", "0912-345-001")
    models.create_user("美珍", "后勤", "0912-345-008")

    # 创建测试技能
    for i, (title, category) in enumerate([
        ("低温天气打面调整法", "烘焙工艺"),
        ("夏季高温打面法", "烘焙工艺"),
        ("可颂烘焙标准", "烘焙工艺"),
        ("客户推荐话术", "销售技巧"),
        ("节假日备货判断", "管理方法"),
        ("面粉验收技巧", "后勤采购"),
    ]):
        models.create_skill(
            title,
            {"trigger_condition": "测试条件", "steps": ["步骤1"], "expected_result": "好结果"},
            creator_id=(i % 5) + 1,
            category=category,
            tags="测试",
        )
        models.update_skill(i + 1, {"status": "已发布"})
    yield


# ============================================================
# F2.2 实时操作指引 — 推送测试
# ============================================================

class TestDailyTips:
    """测试每日提醒生成"""

    @patch('app.recommendation.generate_mock_weather')
    def test_baker_gets_weather_tips(self, mock_weather):
        """TC-F2.2-R001: 烘焙师收到天气相关提醒"""
        mock_weather.return_value = {
            "temp": 32, "humidity": 75, "condition": "晴", "description": "高温炎热"
        }
        tips = recommendation.get_daily_tips(user_id=1)  # 阿明（烘焙师）
        assert len(tips) > 0
        # 应有高温提醒
        titles = " ".join([t["title"] for t in tips])
        assert "高温" in titles or "烘焙" in titles

    @patch('app.recommendation.generate_mock_weather')
    def test_cold_weather_triggers_low_temp_tip(self, mock_weather):
        """TC-F2.2-R002: 低温天气触发低温提醒"""
        mock_weather.return_value = {
            "temp": 15, "humidity": 60, "condition": "晴", "description": "凉爽"
        }
        tips = recommendation.get_daily_tips(user_id=1)  # 阿明
        titles = " ".join([t["title"] for t in tips])
        assert "低温" in titles

    @patch('app.recommendation.generate_mock_weather')
    def test_sales_gets_sales_tips(self, mock_weather):
        """TC-F2.2-R003: 销售收到销售相关提醒"""
        mock_weather.return_value = {
            "temp": 25, "humidity": 60, "condition": "晴", "description": "舒适"
        }
        tips = recommendation.get_daily_tips(user_id=3)  # 小玲（销售）
        titles = " ".join([t["title"] for t in tips])
        assert "销售" in titles

    @patch('app.recommendation.generate_mock_weather')
    def test_manager_gets_management_tips(self, mock_weather):
        """TC-F2.2-R004: 店长收到管理相关提醒"""
        mock_weather.return_value = {
            "temp": 25, "humidity": 60, "condition": "晴", "description": "舒适"
        }
        tips = recommendation.get_daily_tips(user_id=4)  # 志伟（店长）
        titles = " ".join([t["title"] for t in tips])
        assert "管理" in titles

    @patch('app.recommendation.generate_mock_weather')
    def test_boss_gets_overview_tips(self, mock_weather):
        """TC-F2.2-R005: 老板收到全局概览提醒"""
        mock_weather.return_value = {
            "temp": 25, "humidity": 60, "condition": "晴", "description": "舒适"
        }
        tips = recommendation.get_daily_tips(user_id=5)  # 陈老板
        titles = " ".join([t["title"] for t in tips])
        assert "效率" in titles or "概览" in titles

    @patch('app.recommendation.generate_mock_weather')
    def test_logistics_gets_logistics_tips(self, mock_weather):
        """TC-F2.2-R006: 后勤收到后勤相关提醒"""
        mock_weather.return_value = {
            "temp": 25, "humidity": 60, "condition": "晴", "description": "舒适"
        }
        tips = recommendation.get_daily_tips(user_id=6)  # 美珍（后勤）
        titles = " ".join([t["title"] for t in tips])
        assert "后勤" in titles

    @patch('app.recommendation.generate_mock_weather')
    def test_nonexistent_user_returns_empty(self, mock_weather):
        """TC-F2.2-R007: 不存在的用户返回空列表"""
        mock_weather.return_value = {
            "temp": 25, "humidity": 60, "condition": "晴", "description": "舒适"
        }
        tips = recommendation.get_daily_tips(user_id=9999)
        assert tips == []

    @patch('app.recommendation.generate_mock_weather')
    def test_tips_contain_skill_recommendation(self, mock_weather):
        """TC-F2.2-R008: 提醒中包含技能推荐"""
        mock_weather.return_value = {
            "temp": 25, "humidity": 60, "condition": "晴", "description": "舒适"
        }
        tips = recommendation.get_daily_tips(user_id=1)  # 阿明
        skill_tips = [t for t in tips if t.get("type") == "skill_recommend"]
        assert len(skill_tips) >= 1

    @patch('app.recommendation.generate_mock_weather')
    def test_tips_content_not_too_long(self, mock_weather):
        """TC-F2.2-R009: 每条提醒内容不超过3句话"""
        mock_weather.return_value = {
            "temp": 32, "humidity": 75, "condition": "晴", "description": "高温炎热"
        }
        tips = recommendation.get_daily_tips(user_id=1)
        for tip in tips:
            sentences = tip["content"].count("。") + tip["content"].count("！")
            assert sentences <= 3, f"提醒内容超过3句话: {tip['title']}"


class TestOperationGuide:
    """测试实时操作指引"""

    def test_get_guide_for_existing_skill(self, setup_db):
        """TC-F2.2-R010: 获取已有 Skill 的操作指引"""
        guide = recommendation.get_operation_guide(skill_id=1)
        assert guide is not None
        assert len(guide) > 0
        # 不超过3句话
        sentences = guide.count("。") + 1
        assert sentences <= 3, f"操作指引超过3句话: {guide}"

    def test_get_guide_for_nonexistent_skill(self):
        """TC-F2.2-R011: 获取不存在的 Skill 指引"""
        guide = recommendation.get_operation_guide(skill_id=9999)
        assert "未找到" in guide

    def test_get_guide_with_context(self, setup_db):
        """TC-F2.2-R012: 带上下文的操作指引"""
        context = {"temp": 32, "humidity": 75}
        guide = recommendation.get_operation_guide(skill_id=1, context=context)
        assert guide is not None


class TestQualityAlert:
    """测试品质预警"""

    def test_grade_a_no_alert(self):
        """TC-F2.2-R013: A 级品质不触发预警"""
        alert = recommendation.get_quality_alert("可颂", {"quality_grade": "A"})
        assert alert is None

    def test_grade_b_triggers_warning(self):
        """TC-F2.2-R014: B 级品质触发警告"""
        alert = recommendation.get_quality_alert("可颂", {
            "quality_grade": "B",
            "verdict": "底部偏深",
            "suggestions": ["降低底火"],
        })
        assert alert is not None
        assert alert["level"] == "warning"

    def test_grade_c_triggers_critical(self):
        """TC-F2.2-R015: C 级品质触发严重警告"""
        alert = recommendation.get_quality_alert("可颂", {
            "quality_grade": "C",
            "verdict": "烤焦了",
            "suggestions": ["降低温度"],
        })
        assert alert is not None
        assert alert["level"] == "critical"

    def test_alert_has_suggestions(self):
        """TC-F2.2-R016: 预警包含改进建议"""
        alert = recommendation.get_quality_alert("可颂", {
            "quality_grade": "B",
            "verdict": "底部偏深",
            "suggestions": ["降低底火", "调整烤盘位置"],
        })
        assert len(alert["suggestions"]) >= 1
