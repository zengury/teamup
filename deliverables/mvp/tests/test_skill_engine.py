"""
SweetLoaf AI 组织转型系统 — 技能引擎测试

测试范围：skill_engine.py 中的解析、分类、生成逻辑
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DB_PATH"] = ":memory:"

from app import skill_engine
from app import models


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
    yield


# ============================================================
# F1.1 语音记录经验 — 解析逻辑测试
# ============================================================

class TestParseSkillFromText:
    """测试从文本解析结构化 Skill"""

    def test_parse_normal_text(self):
        """TC-F1.1-E001: 解析正常经验文本"""
        text = "今天天气比较冷，室温只有18度，我用了温水打面，水温调到35度，面温打到26度就停了，发酵时间比平时多了40分钟，出来的气孔特别漂亮。"
        result = skill_engine.parse_skill_from_text(text)

        assert result["title"] != ""
        assert "18" in result["trigger_condition"] or "室温" in result["trigger_condition"]
        assert len(result["steps"]) >= 2  # 至少提取出几个步骤
        assert "气孔" in result["expected_result"]

    def test_parse_taiwanese_mixed(self):
        """TC-F1.1-E002: 解析闽南语+普通话混合文本"""
        text = "今仔日天气较冷，面温爱拍到26度，比平常加2度，发酵时间爱延长40分钟"
        result = skill_engine.parse_skill_from_text(text)

        assert result["title"] != ""
        # 检查是否提取到温度信息
        assert "26" in str(result)

    def test_parse_with_temperature(self):
        """TC-F1.1-E003: 解析含温度参数的文本"""
        text = "今天32度，用冰水打面，水温12度，面温22度"
        result = skill_engine.parse_skill_from_text(text)

        assert "32" in str(result) or "12" in str(result) or "22" in str(result)

    def test_parse_empty_text(self):
        """TC-F1.1-E004: 解析空文本"""
        result = skill_engine.parse_skill_from_text("")
        assert result["title"] == ""
        assert result["steps"] == []
        assert result["trigger_condition"] == ""

    def test_parse_whitespace_text(self):
        """TC-F1.1-E005: 解析纯空白文本"""
        result = skill_engine.parse_skill_from_text("   ")
        assert result["title"] == ""

    def test_parse_very_long_text(self):
        """TC-F1.1-E006: 解析超长文本"""
        text = "今天做可颂。" * 100  # 重复100次
        result = skill_engine.parse_skill_from_text(text)
        assert result["title"] != ""
        assert len(result["steps"]) <= 6  # 最多取6个步骤

    def test_parse_short_text(self):
        """TC-F1.1-E007: 解析极短文本"""
        text = "发酵"
        result = skill_engine.parse_skill_from_text(text)
        # 短文本也能解析，只是内容较少
        assert isinstance(result, dict)

    def test_parse_with_tips(self):
        """TC-F1.1-E008: 解析含注意事项的文本"""
        text = "打面时注意水温不能太高，提醒：超过40度酵母会死掉"
        result = skill_engine.parse_skill_from_text(text)
        assert "酵母" in result.get("tips", "") or "40" in result.get("tips", "")

    def test_parse_baking_terminology(self):
        """TC-F1.1-E009: 解析含烘焙专业术语的文本"""
        text = "酸种的酵种活性今天不错，pH值4.0，喂养比例1:1:1，发酵12小时后使用，折叠手法用了三次翻面"
        result = skill_engine.parse_skill_from_text(text)
        assert "折叠" in str(result) or "翻面" in str(result)

    def test_parse_without_conditions(self):
        """TC-F1.1-E010: 解析不含条件的纯步骤文本"""
        text = "把面团擀开，卷起来，放烤盘，发酵到两倍大"
        result = skill_engine.parse_skill_from_text(text)
        assert len(result["steps"]) >= 3


class TestCreateSkillFromVoice:
    """测试从语音创建完整 Skill"""

    def test_create_skill_from_voice_basic(self, setup_db):
        """TC-F1.1-E011: 从语音文本创建 Skill（完整流程）"""
        text = "今天天气比较冷，室温只有18度，我用了温水打面，水温调到35度，面温打到26度就停了，发酵时间比平时多了40分钟，出来的气孔特别漂亮。"
        skill_id, title = skill_engine.create_skill_from_voice(text, creator_id=1)

        assert skill_id > 0
        assert title != ""

        # 验证数据库中的内容
        skill = models.get_skill(skill_id)
        assert skill is not None
        assert skill["status"] == "草稿"
        content = skill.get("content", {})
        if isinstance(content, str):
            content = __import__('json').loads(content)
        assert "trigger_condition" in content
        assert "steps" in content
        assert "raw_transcript" in content

    def test_create_skill_from_voice_category_baking(self, setup_db):
        """TC-F1.1-E012: 烘焙类语音自动分类为烘焙工艺"""
        text = "今天打面温度控制得很好，面团打到光滑，发酵了2小时"
        skill_id, title = skill_engine.create_skill_from_voice(text, creator_id=1)
        skill = models.get_skill(skill_id)
        assert skill["category"] == "烘焙工艺"

    def test_create_skill_from_voice_category_sales(self, setup_db):
        """TC-F1.1-E013: 销售类语音自动分类为销售技巧"""
        text = "今天有个客人问有没有适合糖尿病人的面包，我推荐了酸种面包"
        skill_id, title = skill_engine.create_skill_from_voice(text, creator_id=3)
        skill = models.get_skill(skill_id)
        assert skill["category"] == "销售技巧"

    def test_create_skill_from_voice_category_management(self, setup_db):
        """TC-F1.1-E014: 管理类语音自动分类为管理方法"""
        text = "今天检查了库存，发现面粉库存不够，安排了紧急采购"
        skill_id, title = skill_engine.create_skill_from_voice(text, creator_id=4)
        skill = models.get_skill(skill_id)
        assert skill["category"] == "管理方法"

    def test_create_skill_from_voice_empty_text(self, setup_db):
        """TC-F1.1-E015: 空文本创建 Skill"""
        with pytest.raises(Exception):
            skill_engine.create_skill_from_voice("", creator_id=1)

    def test_create_skill_from_voice_generates_tags(self, setup_db):
        """TC-F1.1-E016: 从语音创建时自动生成标签"""
        text = "今天打面用了冰水，面团温度控制得很好，发酵也很顺利"
        skill_id, title = skill_engine.create_skill_from_voice(text, creator_id=1)
        skill = models.get_skill(skill_id)
        assert skill["tags"] != ""


class TestCategoryGuessing:
    """测试自动分类功能"""

    def test_guess_category_baking(self):
        """TC-F1.1-E017: 烘焙文本分类正确"""
        text = "今天打面温度控制得很好，发酵了2小时，烤箱温度200度"
        cat = skill_engine._guess_category(text, [])
        assert cat == "烘焙工艺"

    def test_guess_category_sales(self):
        """TC-F1.1-E018: 销售文本分类正确"""
        text = "今天有客人来问推荐，我介绍了新品，成交了3单"
        cat = skill_engine._guess_category(text, [])
        assert cat == "销售技巧"

    def test_guess_category_management(self):
        """TC-F1.1-E019: 管理文本分类正确"""
        text = "今天排班检查了库存，安排了明天的备货计划"
        cat = skill_engine._guess_category(text, [])
        assert cat == "管理方法"

    def test_guess_category_purchase(self):
        """TC-F1.1-E020: 采购文本分类正确"""
        text = "今天验收了一批面粉，检查了供应商的到货质量"
        cat = skill_engine._guess_category(text, [])
        assert cat == "后勤采购"

    def test_guess_category_default(self):
        """TC-F1.1-E021: 无法判断时返回通用"""
        text = "今天天气不错"
        cat = skill_engine._guess_category(text, [])
        assert cat == "通用"


class TestCreateSkillFromTemplate:
    """测试模板引导创建 Skill"""

    def test_create_from_baking_template(self, setup_db):
        """TC-F1.4-E001: 从烘焙模板创建 Skill"""
        answers = {
            "product": "可颂",
            "condition": "室温25度",
            "steps": "面团擀开，折叠三次，冷藏30分钟",
            "effect": "层次分明",
            "tips": "黄油不能太软",
        }
        skill_id, title = skill_engine.create_skill_from_template(answers, "baking", creator_id=1)
        assert skill_id > 0
        assert "可颂" in title

    def test_create_from_purchase_template(self, setup_db):
        """TC-F1.4-E002: 从采购模板创建 Skill"""
        answers = {
            "item": "面粉",
            "standard": "米黄色为佳",
            "check_method": "看颜色，闻味道",
            "special_handling": "夏季冷冻48小时",
            "tips": "注意生产日期",
        }
        skill_id, title = skill_engine.create_skill_from_template(answers, "purchase", creator_id=5)
        assert skill_id > 0
        assert "面粉" in title

    def test_create_from_template_empty_answers(self, setup_db):
        """TC-F1.4-E003: 空答案创建模板 Skill"""
        skill_id, title = skill_engine.create_skill_from_template({}, "baking", creator_id=1)
        assert skill_id > 0  # 即使空答案也能创建


class TestSkillDetailAndSearch:
    """测试 Skill 详情和搜索功能"""

    def test_get_skill_detail(self, setup_db):
        """TC-F1.3-E001: 获取 Skill 详情包含版本历史"""
        # 先创建一个 Skill 并发布
        text = "今天天气冷，面温打到26度"
        skill_id, title = skill_engine.create_skill_from_voice(text, creator_id=1)
        models.update_skill(skill_id, {"status": "已发布"})

        detail = skill_engine.get_skill_detail(skill_id)
        assert detail is not None
        assert detail["skill"]["id"] == skill_id
        assert detail["creator_name"] == "阿明"
        assert len(detail["versions"]) >= 1

    def test_get_skill_detail_not_found(self):
        """TC-F1.3-E002: 不存在的 Skill 详情"""
        detail = skill_engine.get_skill_detail(9999)
        assert detail is None

    def test_search_skills_by_keyword(self, setup_db):
        """TC-F1.3-E003: 搜索技能"""
        # 创建并发布几个技能
        skill_engine.create_skill_from_voice("今天打面用了冰水", creator_id=1)
        skill_engine.create_skill_from_voice("可颂烤了18分钟", creator_id=1)
        models.update_skill(1, {"status": "已发布"})
        models.update_skill(2, {"status": "已发布"})

        results = skill_engine.search_skills(keyword="打面")
        assert len(results) >= 1

    def test_search_skills_by_category(self, setup_db):
        """TC-F1.3-E004: 按分类搜索技能"""
        skill_engine.create_skill_from_voice("今天打面用了冰水", creator_id=1)
        models.update_skill(1, {"status": "已发布"})

        results = skill_engine.search_skills(category="烘焙工艺")
        assert len(results) >= 1
