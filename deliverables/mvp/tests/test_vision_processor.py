"""
SweetLoaf AI 组织转型系统 — 图像处理模块测试

测试范围：vision_processor.py 中的面包诊断功能
"""
import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DB_PATH"] = ":memory:"
os.environ["MOCK_MODE"] = "True"

from app import vision_processor
from app import models


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建数据库"""
    models.DB_PATH = ":memory:"
    models.init_db()
    models.create_user("阿明", "烘焙师", "0912-345-003")
    yield


# ============================================================
# 拍照诊断测试（模拟模式）
# ============================================================

class TestDiagnoseBread:
    """测试面包诊断功能"""

    def test_diagnose_perfect(self):
        """TC-F2.3-V001: 诊断完美成品"""
        with tempfile.NamedTemporaryFile(suffix="perfect_croissant.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            assert result["quality_grade"] == "A"
            assert "优良" in result["verdict"] or "到位" in result["verdict"]
        finally:
            os.unlink(path)

    def test_diagnose_burnt(self):
        """TC-F2.3-V002: 诊断烤焦成品"""
        with tempfile.NamedTemporaryFile(suffix="burnt_bread.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            assert result["quality_grade"] == "C"
            assert "焦" in result["verdict"]
        finally:
            os.unlink(path)

    def test_diagnose_under(self):
        """TC-F2.3-V003: 诊断烘烤不足"""
        with tempfile.NamedTemporaryFile(suffix="under_baked.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            assert result["quality_grade"] == "B"
            assert "不足" in result["verdict"] or "偏浅" in result["verdict"]
        finally:
            os.unlink(path)

    def test_diagnose_dark_bottom(self):
        """TC-F2.3-V004: 诊断底部偏深"""
        with tempfile.NamedTemporaryFile(suffix="dark_bottom.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            assert result["quality_grade"] == "B"
            assert "偏深" in result["verdict"]
        finally:
            os.unlink(path)

    def test_diagnose_default(self):
        """TC-F2.3-V005: 诊断未知文件（返回默认结果）"""
        with tempfile.NamedTemporaryFile(suffix="random_photo.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            assert result is not None
            assert "quality_grade" in result
        finally:
            os.unlink(path)

    def test_diagnose_nonexistent_file(self):
        """TC-F2.3-V006: 诊断不存在的文件"""
        result = vision_processor.diagnose_bread("/nonexistent/path.jpg")
        assert result is not None  # 模拟模式应返回默认结果

    def test_diagnose_result_has_all_fields(self):
        """TC-F2.3-V007: 诊断结果包含所有必要字段"""
        with tempfile.NamedTemporaryFile(suffix="perfect_croissant.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            required_fields = [
                "surface_color", "surface_score", "bottom_color",
                "bottom_score", "verdict", "possible_causes",
                "suggestions", "quality_grade",
            ]
            for field in required_fields:
                assert field in result, f"缺少必要字段: {field}"
        finally:
            os.unlink(path)

    def test_diagnose_grade_a_has_no_causes(self):
        """TC-F2.3-V008: A 级产品没有原因和建议"""
        with tempfile.NamedTemporaryFile(suffix="perfect_croissant.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            if result["quality_grade"] == "A":
                assert len(result["possible_causes"]) == 0
                assert "继续保持" in result["suggestions"][0]
        finally:
            os.unlink(path)

    def test_diagnose_grade_c_has_suggestions(self):
        """TC-F2.3-V009: C 级产品有改进建议"""
        with tempfile.NamedTemporaryFile(suffix="burnt_bread.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.diagnose_bread(path)
            if result["quality_grade"] == "C":
                assert len(result["suggestions"]) >= 2
                assert len(result["possible_causes"]) >= 1
        finally:
            os.unlink(path)

    def test_diagnose_consistency(self):
        """TC-F2.3-V010: 同一文件多次诊断结果一致（模拟模式）"""
        with tempfile.NamedTemporaryFile(suffix="perfect_croissant.jpg", delete=False) as f:
            path = f.name
        try:
            result1 = vision_processor.diagnose_bread(path)
            result2 = vision_processor.diagnose_bread(path)
            # 模拟模式下，同一文件名应返回相同结果
            assert result1["quality_grade"] == result2["quality_grade"]
            assert result1["verdict"] == result2["verdict"]
        finally:
            os.unlink(path)


class TestCompareWithStandard:
    """测试与标准品相对比功能"""

    def test_compare_with_standard(self, setup_db):
        """TC-F2.3-V011: 与标准 Skill 对比"""
        # 先创建一个 Skill
        content = {
            "trigger_condition": "烘烤可颂",
            "steps": ["上火200℃下火190℃", "烤18分钟"],
            "expected_result": "表面金黄油亮，层次分明",
        }
        sid = models.create_skill("可颂标准", content, creator_id=1, category="烘焙工艺")

        with tempfile.NamedTemporaryFile(suffix="burnt_bread.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.compare_with_standard(path, sid)
            assert "current" in result
            assert "standard" in result
            assert "deviation" in result
            assert "improvement_suggestions" in result
        finally:
            os.unlink(path)

    def test_compare_with_nonexistent_skill(self):
        """TC-F2.3-V012: 对比不存在的 Skill"""
        with tempfile.NamedTemporaryFile(suffix="perfect_croissant.jpg", delete=False) as f:
            path = f.name
        try:
            result = vision_processor.compare_with_standard(path, 9999)
            assert "error" in result
        finally:
            os.unlink(path)
