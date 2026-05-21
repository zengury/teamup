"""
SweetLoaf AI 组织转型系统 — 工具函数测试

测试范围：utils.py 中的文本解析、关键词提取等功能
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import utils


class TestParseTemperature:
    """测试温度解析"""

    def test_parse_simple_temperature(self):
        assert utils.parse_temperature("26度") == [26]

    def test_parse_celsius_symbol(self):
        assert utils.parse_temperature("35℃") == [35]

    def test_parse_multiple_temperatures(self):
        result = utils.parse_temperature("水温35度，面温26度，室温18度")
        assert result == [35, 26, 18]

    def test_parse_no_temperature(self):
        assert utils.parse_temperature("今天天气不错") == []

    def test_parse_empty_string(self):
        assert utils.parse_temperature("") == []


class TestParseTime:
    """测试时间解析"""

    def test_parse_minutes(self):
        result = utils.parse_time("发酵40分钟")
        assert (40, "分钟") in result

    def test_parse_hours(self):
        result = utils.parse_time("发酵2小时")
        assert (2, "小时") in result

    def test_parse_multiple_times(self):
        result = utils.parse_time("发酵40分钟，松弛30分钟，冷藏2小时")
        assert (40, "分钟") in result
        assert (30, "分钟") in result
        assert (2, "小时") in result

    def test_parse_no_time(self):
        assert utils.parse_time("今天天气不错") == []


class TestExtractKeywords:
    """测试关键词提取"""

    def test_extract_ingredients(self):
        keywords = utils.extract_keywords("今天用了面粉和水")
        assert "面粉" in keywords
        assert "水" in keywords

    def test_extract_actions(self):
        keywords = utils.extract_keywords("打面之后发酵，然后整形")
        assert "打面" in keywords
        assert "发酵" in keywords
        assert "整形" in keywords

    def test_extract_equipment(self):
        keywords = utils.extract_keywords("烤箱温度200度")
        assert "烤箱" in keywords

    def test_extract_qualities(self):
        keywords = utils.extract_keywords("气孔很漂亮，颜色金黄")
        assert "气孔" in keywords
        assert "金黄" in keywords

    def test_extract_empty(self):
        assert utils.extract_keywords("") == []

    def test_extract_no_match(self):
        assert utils.extract_keywords("今天天气不错") == []

    def test_extract_duplicates_removed(self):
        keywords = utils.extract_keywords("打面，打面，打面")
        assert len(keywords) == 1  # 去重


class TestExtractConditions:
    """测试条件提取"""

    def test_extract_temperature_condition(self):
        conditions = utils.extract_conditions("天气32度，室温较高")
        assert len(conditions) >= 1
        assert any("32" in c for c in conditions)

    def test_extract_weather_condition(self):
        conditions = utils.extract_conditions("今天下雨，湿度高")
        assert any("潮湿" in c for c in conditions)

    def test_extract_time_condition(self):
        conditions = utils.extract_conditions("早上来的时候发现面团发过了")
        assert any("早上" in c for c in conditions)

    def test_extract_holiday_condition(self):
        conditions = utils.extract_conditions("今天是礼拜天，客人很多")
        assert any("节假日" in c or "周末" in c for c in conditions)

    def test_extract_no_conditions(self):
        assert utils.extract_conditions("把面团擀开") == []


class TestExtractSteps:
    """测试步骤提取"""

    def test_extract_basic_steps(self):
        steps = utils.extract_steps("把面团擀开，卷起来，放烤盘里。")
        assert len(steps) >= 2

    def test_extract_no_action(self):
        steps = utils.extract_steps("今天天气不错")
        assert steps == []

    def test_extract_max_six_steps(self):
        text = "。".join([f"调温度{i}度" for i in range(10)])
        steps = utils.extract_steps(text)
        assert len(steps) <= 6


class TestGenerateSkillTitle:
    """测试技能标题生成"""

    def test_generate_low_temp_title(self):
        title = utils.generate_skill_title("低温天气打面方法")
        assert "低温" in title or "打面" in title or "调整" in title

    def test_generate_high_temp_title(self):
        title = utils.generate_skill_title("高温天气发酵调整")
        assert "高温" in title or "发酵" in title or "调整" in title

    def test_generate_by_product(self):
        title = utils.generate_skill_title("可颂的标准做法")
        assert "可颂" in title

    def test_generate_with_temperature(self):
        title = utils.generate_skill_title("今天25度打面心得")
        assert "25" in title or "温度" in title or "心得" in title

    def test_generate_default_title(self):
        title = utils.generate_skill_title("今天做了面包")
        assert title  # 应返回默认标题


class TestGenerateMockWeather:
    """测试模拟天气生成"""

    def test_weather_has_required_fields(self):
        weather = utils.generate_mock_weather()
        assert "temp" in weather
        assert "humidity" in weather
        assert "condition" in weather
        assert "description" in weather

    def test_weather_temp_range(self):
        for _ in range(100):
            weather = utils.generate_mock_weather()
            assert 15 <= weather["temp"] <= 32

    def test_weather_humidity_range(self):
        for _ in range(100):
            weather = utils.generate_mock_weather()
            assert 60 <= weather["humidity"] <= 80


class TestGenerateMockDiagnosis:
    """测试模拟诊断生成"""

    def test_diagnosis_has_required_fields(self):
        diagnosis = utils.generate_mock_diagnosis()
        required = [
            "surface_color", "surface_score", "bottom_color",
            "bottom_score", "verdict", "possible_causes",
            "suggestions", "quality_grade",
        ]
        for field in required:
            assert field in diagnosis

    def test_diagnosis_grade_in_valid_range(self):
        for _ in range(100):
            diagnosis = utils.generate_mock_diagnosis()
            assert diagnosis["quality_grade"] in ("A", "B", "C")

    def test_diagnosis_scores_in_range(self):
        for _ in range(100):
            diagnosis = utils.generate_mock_diagnosis()
            assert 0 <= diagnosis["surface_score"] <= 100
            assert 0 <= diagnosis["bottom_score"] <= 100


class TestFormatDatetime:
    """测试日期格式化"""

    def test_format_valid_datetime(self):
        result = utils.format_datetime("2026-05-21 12:30:00")
        assert result == "05/21 12:30"

    def test_format_invalid_datetime(self):
        result = utils.format_datetime("invalid")
        assert result == "invalid"

    def test_format_none(self):
        result = utils.format_datetime(None)
        assert result == "None"
