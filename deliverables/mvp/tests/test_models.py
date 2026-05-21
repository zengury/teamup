"""
SweetLoaf AI 组织转型系统 — 数据模型测试

测试范围：models.py 中所有数据库操作函数
测试策略：使用内存 SQLite 数据库，每次测试独立
"""
import sys
import os
import json
import pytest
from datetime import datetime

# 确保能找到 mvp 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 测试前先设定测试数据库路径（内存数据库）
os.environ["DB_PATH"] = ":memory:"

# 重新导入时使用测试配置
import importlib
import config
import app.models as models


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建数据库"""
    # 使用内存数据库
    models.DB_PATH = ":memory:"
    models.init_db()
    yield
    # 测试结束后不需要清理，内存数据库自动销毁


@pytest.fixture
def sample_users(setup_db):
    """创建测试用户数据"""
    users = {}
    user_data = [
        ("阿明", "烘焙师", "0912-345-003"),
        ("小豪", "学徒", "0912-345-006"),
        ("小玲", "销售", "0912-345-007"),
        ("志伟", "店长", "0912-345-002"),
        ("陈老板", "老板", "0912-345-001"),
    ]
    for name, role, phone in user_data:
        uid = models.create_user(name, role, phone)
        users[name] = uid
    return users


@pytest.fixture
def sample_skills(sample_users):
    """创建测试技能数据"""
    users = sample_users
    skills = {}

    skill_data = [
        ("低温天气打面调整法", {
            "trigger_condition": "室温<20℃",
            "steps": ["水温调至35℃", "面温目标26℃", "发酵时间延长40分钟"],
            "expected_result": "气孔更漂亮，口感更蓬松",
        }, users["阿明"], "烘焙工艺", "低温,打面,发酵"),
        ("夏季高温打面法", {
            "trigger_condition": "室温>30℃",
            "steps": ["用冰水打面，水温12℃", "面温目标22℃", "发酵时间缩短30分钟"],
            "expected_result": "面团温度稳定，发酵正常",
        }, users["阿明"], "烘焙工艺", "高温,打面,冰水"),
        ("可颂烘焙标准", {
            "trigger_condition": "烘烤可颂",
            "steps": ["上火200℃下火190℃", "烤18分钟", "表面金黄油亮即可出炉"],
            "expected_result": "表面金黄油亮，层次分明",
        }, users["老王"], "烘焙工艺", "可颂,烘烤,标准"),
        ("客户推荐话术", {
            "trigger_condition": "客人犹豫时",
            "steps": ["先问口味偏好", "推荐店内招牌", "提供试吃"],
            "expected_result": "成交率提升",
        }, users["小玲"], "销售技巧", "销售,话术,客户"),
        ("节假日备货判断", {
            "trigger_condition": "节假日前一天",
            "steps": ["查看去年同期销量", "增加30%备货量", "提前准备礼盒包装"],
            "expected_result": "节假日不断货",
        }, users["志伟"], "管理方法", "备货,节假日,管理"),
    ]

    for title, content, creator_id, category, tags in skill_data:
        sid = models.create_skill(title, content, creator_id, category, tags)
        skills[title] = sid

    return skills


# ============================================================
# F1.1 语音记录经验 — 数据层测试
# ============================================================

class TestSkillCreation:
    """测试 Skill 创建功能（F1.1 数据层）"""

    def test_create_skill_basic(self, sample_users):
        """TC-F1.1-D001: 创建基本技能包"""
        uid = sample_users["阿明"]
        content = {
            "trigger_condition": "室温<20℃",
            "steps": ["水温调至35℃", "面温目标26℃"],
            "expected_result": "气孔漂亮",
        }
        sid = models.create_skill("低温打面法", content, uid, "烘焙工艺", "低温,打面")
        assert sid > 0, "Skill 创建应返回有效的 ID"

        skill = models.get_skill(sid)
        assert skill is not None
        assert skill["title"] == "低温打面法"
        assert skill["creator_id"] == uid
        assert skill["status"] == "草稿"
        assert skill["category"] == "烘焙工艺"
        assert json.loads(skill["content"])["trigger_condition"] == "室温<20℃"

    def test_create_skill_with_tags(self, sample_users):
        """TC-F1.1-D002: 创建带标签的技能包"""
        uid = sample_users["阿明"]
        sid = models.create_skill(
            "测试技能", {"steps": ["步骤1"]}, uid, "通用", "测试,标签,烘焙"
        )
        skill = models.get_skill(sid)
        assert skill["tags"] == "测试,标签,烘焙"

    def test_create_skill_empty_content(self, sample_users):
        """TC-F1.1-D003: 创建内容为空的技能包（边界条件）"""
        uid = sample_users["阿明"]
        sid = models.create_skill("空内容技能", {}, uid, "通用", "")
        assert sid > 0
        skill = models.get_skill(sid)
        assert skill["title"] == "空内容技能"

    def test_create_skill_logs_operation(self, sample_users):
        """TC-F1.1-D004: 创建技能时自动记录操作日志"""
        uid = sample_users["阿明"]
        sid = models.create_skill("日志测试", {"steps": ["测试"]}, uid, "通用", "")
        logs = models.get_recent_logs(10)
        matching = [log for log in logs if log["skill_id"] == sid and log["action"] == "创建"]
        assert len(matching) == 1, "创建 Skill 应自动生成一条操作日志"


class TestSkillStatusFlow:
    """测试 Skill 状态流转"""

    def test_skill_status_draft(self, sample_skills):
        """TC-F1.3-D001: 新建 Skill 默认为草稿状态"""
        sid = sample_skills["低温天气打面调整法"]
        skill = models.get_skill(sid)
        assert skill["status"] == "草稿"

    def test_skill_status_publish_creates_version(self, sample_skills):
        """TC-F1.3-D002: 发布 Skill 时自动创建版本记录"""
        sid = sample_skills["低温天气打面调整法"]
        models.update_skill(sid, {"status": "已发布"})
        versions = models.get_skill_versions(sid)
        assert len(versions) == 1, "发布时应创建一条版本记录"
        assert versions[0]["version_number"] == 1

    def test_skill_status_multiple_versions(self, sample_skills):
        """TC-F1.3-D003: 多次发布生成多个版本"""
        sid = sample_skills["低温天气打面调整法"]
        models.update_skill(sid, {"status": "已发布"})
        models.update_skill(sid, {"status": "已发布"})  # 第二次发布
        versions = models.get_skill_versions(sid)
        assert len(versions) == 2
        assert versions[0]["version_number"] == 2

    def test_skill_status_archive(self, sample_skills):
        """TC-F1.3-D004: Skill 归档操作"""
        sid = sample_skills["低温天气打面调整法"]
        models.update_skill(sid, {"status": "已归档"})
        skill = models.get_skill(sid)
        assert skill["status"] == "已归档"

    def test_skill_status_invalid(self, sample_skills):
        """TC-F1.3-D005: 尝试设置无效状态（数据库约束）"""
        sid = sample_skills["低温天气打面调整法"]
        with pytest.raises(Exception):
            models.update_skill(sid, {"status": "无效状态"})


class TestSkillSearch:
    """测试技能搜索功能（F1.3 数据层）"""

    def test_search_by_keyword(self, sample_skills):
        """TC-F1.3-D006: 按关键词搜索"""
        results = models.search_skills(keyword="打面", status="")
        assert len(results) >= 2  # 低温打面 + 夏季打面
        titles = [s["title"] for s in results]
        assert "低温天气打面调整法" in titles

    def test_search_by_category(self, sample_skills):
        """TC-F1.3-D007: 按分类搜索"""
        results = models.search_skills(category="销售技巧", status="")
        assert len(results) >= 1
        assert results[0]["category"] == "销售技巧"

    def test_search_by_status(self, sample_skills):
        """TC-F1.3-D008: 按状态搜索"""
        # 先发布一个 Skill
        models.update_skill(sample_skills["低温天气打面调整法"], {"status": "已发布"})
        results = models.search_skills(status="已发布")
        assert len(results) >= 1
        for s in results:
            assert s["status"] == "已发布"

    def test_search_no_results(self, sample_skills):
        """TC-F1.3-D009: 搜索不存在的关键词"""
        results = models.search_skills(keyword="不存在的关键词12345", status="")
        assert len(results) == 0

    def test_search_empty_keyword(self, sample_skills):
        """TC-F1.3-D010: 空关键词搜索（应返回全部）"""
        results = models.search_skills(keyword="", status="")
        assert len(results) >= 5  # 有5个种子技能


class TestSkillInteraction:
    """测试技能互动功能"""

    def test_like_skill(self, sample_skills, sample_users):
        """TC-F1.3-D011: 点赞技能"""
        sid = sample_skills["可颂烘焙标准"]
        models.like_skill(sample_users["小豪"], sid)
        skill = models.get_skill(sid)
        assert skill["like_count"] == 1

    def test_collect_skill(self, sample_skills, sample_users):
        """TC-F1.3-D012: 收藏技能"""
        sid = sample_skills["可颂烘焙标准"]
        models.collect_skill(sample_users["小豪"], sid)
        skill = models.get_skill(sid)
        assert skill["collect_count"] == 1

    def test_view_count_increment(self, sample_skills):
        """TC-F1.3-D013: 查看技能时浏览次数增加"""
        sid = sample_skills["可颂烘焙标准"]
        skill1 = models.get_skill(sid)
        view1 = skill1["view_count"]
        skill2 = models.get_skill(sid)
        assert skill2["view_count"] == view1 + 1


# ============================================================
# F2.1 员工技能地图 — 数据层测试
# ============================================================

class TestEmployeeSkillMap:
    """测试员工技能地图（F2.1 数据层）"""

    def test_get_skill_map_basic(self, sample_users, sample_skills):
        """TC-F2.1-D001: 获取员工技能地图"""
        uid = sample_users["小豪"]
        skill_map = models.get_employee_skill_map(uid)
        assert skill_map is not None
        assert skill_map["user"]["name"] == "小豪"
        assert "skills" in skill_map
        assert "stats" in skill_map

    def test_skill_map_stats(self, sample_users, sample_skills):
        """TC-F2.1-D002: 技能地图统计数据正确"""
        uid = sample_users["小豪"]
        skill_map = models.get_employee_skill_map(uid)
        stats = skill_map["stats"]
        assert stats["total"] >= 0
        assert stats["mastered"] + stats["learning"] + stats["not_started"] == stats["total"]

    def test_update_progress(self, sample_users, sample_skills):
        """TC-F2.1-D003: 更新技能学习进度"""
        uid = sample_users["小豪"]
        sid = sample_skills["可颂烘焙标准"]
        models.update_skill_progress(uid, sid, progress=50, status="学习中")
        skill_map = models.get_employee_skill_map(uid)
        target = [s for s in skill_map["skills"] if s["skill_id"] == sid]
        assert len(target) == 1
        assert target[0]["progress"] == 50
        assert target[0]["status"] == "学习中"

    def test_update_progress_to_mastered(self, sample_users, sample_skills):
        """TC-F2.1-D004: 技能进度更新为已掌握"""
        uid = sample_users["小豪"]
        sid = sample_skills["可颂烘焙标准"]
        models.update_skill_progress(uid, sid, progress=100, status="已掌握")
        skill_map = models.get_employee_skill_map(uid)
        target = [s for s in skill_map["skills"] if s["skill_id"] == sid]
        assert target[0]["status"] == "已掌握"

    def test_skill_map_nonexistent_user(self):
        """TC-F2.1-D005: 不存在的用户返回 None"""
        result = models.get_employee_skill_map(9999)
        assert result is None

    def test_team_skill_stats(self, sample_skills):
        """TC-F2.1-D006: 团队技能统计"""
        stats = models.get_team_skill_stats()
        assert "total_skills" in stats
        assert "category_stats" in stats
        assert "employee_stats" in stats


# ============================================================
# F2.2 实时操作指引 — 数据层测试
# ============================================================

class TestNotifications:
    """测试通知推送功能（F2.2 数据层）"""

    def test_create_notification(self, sample_users):
        """TC-F2.2-D001: 创建推送通知"""
        nid = models.create_notification(
            sample_users["阿明"],
            "高温提醒",
            "今日32℃，请注意打面温度",
            skill_id=1,
        )
        assert nid > 0

    def test_get_user_notifications(self, sample_users):
        """TC-F2.2-D002: 获取用户通知列表"""
        uid = sample_users["阿明"]
        models.create_notification(uid, "提醒1", "内容1")
        models.create_notification(uid, "提醒2", "内容2")
        notifications = models.get_user_notifications(uid)
        assert len(notifications) == 2

    def test_get_unread_notifications(self, sample_users):
        """TC-F2.2-D003: 获取未读通知"""
        uid = sample_users["阿明"]
        models.create_notification(uid, "提醒1", "内容1")
        models.create_notification(uid, "提醒2", "内容2")
        models.mark_notification_read(1)  # 标记第一个为已读
        unread = models.get_user_notifications(uid, unread_only=True)
        assert len(unread) == 1

    def test_mark_notification_read(self, sample_users):
        """TC-F2.2-D004: 标记通知已读"""
        uid = sample_users["阿明"]
        nid = models.create_notification(uid, "测试", "内容")
        models.mark_notification_read(nid)
        notifications = models.get_user_notifications(uid)
        assert notifications[0]["is_read"] == 1

    def test_collect_notification(self, sample_users):
        """TC-F2.2-D005: 收藏通知"""
        uid = sample_users["阿明"]
        nid = models.create_notification(uid, "测试", "内容")
        models.collect_notification(nid)
        notifications = models.get_user_notifications(uid)
        assert notifications[0]["is_collected"] == 1


# ============================================================
# 操作日志测试
# ============================================================

class TestOperationLogs:
    """测试操作日志功能"""

    def test_log_operation(self, sample_users, sample_skills):
        """TC-通用-D001: 记录操作日志"""
        models.log_operation(
            sample_users["小豪"],
            "使用",
            skill_id=sample_skills["可颂烘焙标准"],
            detail="查看了可颂烘焙标准",
        )
        logs = models.get_recent_logs(10)
        matching = [log for log in logs if log["action"] == "使用"]
        assert len(matching) >= 1

    def test_get_recent_logs_limit(self, sample_users):
        """TC-通用-D002: 获取最近日志（限制数量）"""
        for i in range(5):
            models.log_operation(sample_users["阿明"], "查看", detail=f"操作{i}")
        logs = models.get_recent_logs(limit=3)
        assert len(logs) == 3


# ============================================================
# 产品照片测试
# ============================================================

class TestProductPhotos:
    """测试产品照片功能（F2.3 数据层）"""

    def test_save_product_photo(self, sample_users, sample_skills):
        """TC-F2.3-D001: 保存产品照片和诊断结果"""
        uid = sample_users["小豪"]
        sid = sample_skills["可颂烘焙标准"]
        diagnosis = {
            "quality_grade": "B",
            "verdict": "底部偏深",
            "suggestions": ["降低底火"],
        }
        pid = models.save_product_photo(uid, "/images/test.jpg", diagnosis, sid)
        assert pid > 0

    def test_save_photo_without_skill(self, sample_users):
        """TC-F2.3-D002: 保存照片时不关联 Skill"""
        uid = sample_users["小豪"]
        diagnosis = {"quality_grade": "A", "verdict": "完美"}
        pid = models.save_product_photo(uid, "/images/test.jpg", diagnosis)
        assert pid > 0


# ============================================================
# 用户管理测试
# ============================================================

class TestUserManagement:
    """测试用户管理功能"""

    def test_create_user(self, setup_db):
        """TC-通用-D003: 创建用户"""
        uid = models.create_user("测试用户", "烘焙师", "0912-000-000")
        assert uid > 0
        user = models.get_user(uid)
        assert user["name"] == "测试用户"
        assert user["role"] == "烘焙师"

    def test_get_all_users(self, sample_users):
        """TC-通用-D004: 获取所有用户"""
        users = models.get_all_users()
        assert len(users) >= 5

    def test_get_user_by_role(self, sample_users):
        """TC-通用-D005: 按角色获取用户"""
        bakers = models.get_user_by_role("烘焙师")
        assert len(bakers) >= 2  # 阿明 + 老王
        for u in bakers:
            assert u["role"] == "烘焙师"

    def test_get_nonexistent_user(self):
        """TC-通用-D006: 获取不存在的用户"""
        user = models.get_user(9999)
        assert user is None


# ============================================================
# 边界条件测试
# ============================================================

class TestBoundaryConditions:
    """边界条件测试"""

    def test_concurrent_create_skills(self, sample_users):
        """TC-边界-D001: 模拟并发创建多个 Skill"""
        uid = sample_users["阿明"]
        ids = []
        for i in range(12):  # 模拟12人同时创建
            sid = models.create_skill(
                f"并发测试技能{i}", {"steps": [f"步骤{i}"]}, uid, "通用", ""
            )
            ids.append(sid)
        assert len(ids) == 12
        assert len(set(ids)) == 12  # 所有 ID 唯一

    def test_skill_title_very_long(self, sample_users):
        """TC-边界-D002: 超长技能标题"""
        uid = sample_users["阿明"]
        long_title = "超" * 500
        sid = models.create_skill(long_title, {"steps": ["测试"]}, uid, "通用", "")
        skill = models.get_skill(sid)
        assert skill is not None
        assert len(skill["title"]) == 500

    def test_skill_content_large(self, sample_users):
        """TC-边界-D003: 超大的技能内容"""
        uid = sample_users["阿明"]
        large_steps = [f"步骤{i}详细说明" for i in range(100)]
        content = {"steps": large_steps, "trigger_condition": "测试" * 1000}
        sid = models.create_skill("大内容技能", content, uid, "通用", "")
        skill = models.get_skill(sid)
        assert skill is not None

    def test_empty_skills_list_for_new_user(self, setup_db):
        """TC-边界-D004: 新用户技能地图为空"""
        uid = models.create_user("新员工", "学徒", "")
        skill_map = models.get_employee_skill_map(uid)
        assert skill_map is not None
        assert len(skill_map["skills"]) == 0
        assert skill_map["stats"]["total"] == 0
