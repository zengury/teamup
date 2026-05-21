"""
SweetLoaf AI 组织转型系统 — 数据模型（SQLite）
"""
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH


# ============================================================
# 数据库连接管理
# ============================================================

@contextmanager
def get_db():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def dict_from_row(row):
    """将 sqlite3.Row 转为 dict"""
    if row is None:
        return None
    return dict(row)


def init_db():
    """初始化数据库，创建所有表（如果不存在）"""
    with get_db() as conn:
        conn.executescript("""
        -- 用户表
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '烘焙师'
                CHECK(role IN ('烘焙师','销售','店长','后勤','学徒','老板')),
            phone TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- 技能包表
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '未命名技能',
            content TEXT NOT NULL DEFAULT '{}',
            creator_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT '草稿'
                CHECK(status IN ('草稿','审核中','已发布','已归档')),
            category TEXT DEFAULT '通用'
                CHECK(category IN ('烘焙工艺','销售技巧','管理方法','后勤采购','通用')),
            tags TEXT DEFAULT '',
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            collect_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(creator_id) REFERENCES users(id)
        );

        -- 技能版本表
        CREATE TABLE IF NOT EXISTS skill_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT NOT NULL DEFAULT '{}',
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(skill_id) REFERENCES skills(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        );

        -- 操作日志表
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER,
            action TEXT NOT NULL
                CHECK(action IN ('创建','使用','收藏','点赞','查看','诊断')),
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );

        -- 产品照片表
        CREATE TABLE IF NOT EXISTS product_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER,
            image_path TEXT NOT NULL,
            diagnosis_result TEXT DEFAULT '{}',
            quality_grade TEXT DEFAULT 'N'
                CHECK(quality_grade IN ('A','B','C','N')),
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );

        -- 工作流表
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            config TEXT NOT NULL DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(created_by) REFERENCES users(id)
        );

        -- 员工技能进度表
        CREATE TABLE IF NOT EXISTS employee_skill_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT '未学习'
                CHECK(status IN ('未学习','学习中','已掌握','可教授')),
            progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(skill_id) REFERENCES skills(id),
            UNIQUE(user_id, skill_id)
        );

        -- 推送提醒表
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            skill_id INTEGER,
            is_read INTEGER DEFAULT 0,
            is_collected INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_skills_creator ON skills(creator_id);
        CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status);
        CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
        CREATE INDEX IF NOT EXISTS idx_operation_logs_user ON operation_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_operation_logs_skill ON operation_logs(skill_id);
        CREATE INDEX IF NOT EXISTS idx_progress_user ON employee_skill_progress(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
        """)


# ============================================================
# 用户操作
# ============================================================

def get_all_users():
    """获取所有用户"""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [dict_from_row(r) for r in rows]


def get_user(user_id):
    """根据ID获取用户"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict_from_row(row)


def get_user_by_role(role):
    """按角色获取用户列表"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE role=? ORDER BY id", (role,)
        ).fetchall()
        return [dict_from_row(r) for r in rows]


def create_user(name, role, phone=""):
    """创建新用户"""
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, role, phone) VALUES (?, ?, ?)",
            (name, role, phone),
        )
        return cur.lastrowid


# ============================================================
# 技能包操作
# ============================================================

def create_skill(title, content, creator_id, category="通用", tags=""):
    """创建新技能包"""
    with get_db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute(
            """INSERT INTO skills (title, content, creator_id, category, tags, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, json.dumps(content, ensure_ascii=False), creator_id, category, tags, now, now),
        )
        skill_id = cur.lastrowid
        # 同时记录操作日志
        conn.execute(
            "INSERT INTO operation_logs (user_id, skill_id, action) VALUES (?, ?, '创建')",
            (creator_id, skill_id),
        )
        # 自动创建技能进度记录
        _ensure_progress(conn, creator_id, skill_id)
        return skill_id


def get_skill(skill_id):
    """获取单个技能包详情"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM skills WHERE id=?", (skill_id,)).fetchone()
        skill = dict_from_row(row)
        if skill:
            skill["content"] = json.loads(skill["content"])
            # 增加浏览次数
            conn.execute(
                "UPDATE skills SET view_count = view_count + 1 WHERE id=?",
                (skill_id,),
            )
        return skill


def search_skills(keyword="", category="", role="", status="已发布"):
    """搜索技能包"""
    with get_db() as conn:
        query = "SELECT * FROM skills WHERE 1=1"
        params = []

        if status:
            query += " AND status=?"
            params.append(status)
        if category:
            query += " AND category=?"
            params.append(category)
        if keyword:
            query += " AND (title LIKE ? OR tags LIKE ? OR content LIKE ?)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        query += " ORDER BY updated_at DESC"
        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            s = dict_from_row(r)
            s["content"] = json.loads(s["content"])
            # 获取创建者姓名
            creator = conn.execute(
                "SELECT name FROM users WHERE id=?", (s["creator_id"],)
            ).fetchone()
            s["creator_name"] = creator["name"] if creator else "未知"
            results.append(s)
        return results


def update_skill(skill_id, updates):
    """更新技能包"""
    with get_db() as conn:
        allowed = ["title", "content", "status", "category", "tags"]
        set_parts = []
        params = []
        for key, value in updates.items():
            if key in allowed:
                if key == "content":
                    value = json.dumps(value, ensure_ascii=False)
                set_parts.append(f"{key}=?")
                params.append(value)
        if set_parts:
            set_parts.append("updated_at=datetime('now','localtime')")
            params.append(skill_id)
            conn.execute(
                f"UPDATE skills SET {', '.join(set_parts)} WHERE id=?",
                params,
            )
            # 如果是发布操作，创建版本记录
            if updates.get("status") == "已发布":
                skill = conn.execute(
                    "SELECT content, creator_id FROM skills WHERE id=?",
                    (skill_id,),
                ).fetchone()
                if skill:
                    version_num = conn.execute(
                        "SELECT COUNT(*) FROM skill_versions WHERE skill_id=?",
                        (skill_id,),
                    ).fetchone()[0] + 1
                    conn.execute(
                        """INSERT INTO skill_versions (skill_id, version_number, content, created_by)
                           VALUES (?, ?, ?, ?)""",
                        (skill_id, version_num, skill["content"], skill["creator_id"]),
                    )


def like_skill(user_id, skill_id):
    """点赞技能包"""
    with get_db() as conn:
        conn.execute("UPDATE skills SET like_count = like_count + 1 WHERE id=?", (skill_id,))
        conn.execute(
            "INSERT INTO operation_logs (user_id, skill_id, action) VALUES (?, ?, '点赞')",
            (user_id, skill_id),
        )


def collect_skill(user_id, skill_id):
    """收藏技能包"""
    with get_db() as conn:
        conn.execute(
            "UPDATE skills SET collect_count = collect_count + 1 WHERE id=?",
            (skill_id,),
        )
        conn.execute(
            "INSERT INTO operation_logs (user_id, skill_id, action) VALUES (?, ?, '收藏')",
            (user_id, skill_id),
        )


def get_skill_versions(skill_id):
    """获取技能包的版本历史"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT sv.*, u.name as creator_name
               FROM skill_versions sv
               LEFT JOIN users u ON sv.created_by = u.id
               WHERE sv.skill_id=?
               ORDER BY sv.version_number DESC""",
            (skill_id,),
        ).fetchall()
        results = []
        for r in rows:
            v = dict_from_row(r)
            v["content"] = json.loads(v["content"])
            results.append(v)
        return results


# ============================================================
# 员工技能进度
# ============================================================

def _ensure_progress(conn, user_id, skill_id):
    """确保技能进度记录存在"""
    existing = conn.execute(
        "SELECT id FROM employee_skill_progress WHERE user_id=? AND skill_id=?",
        (user_id, skill_id),
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO employee_skill_progress (user_id, skill_id, status, progress) VALUES (?, ?, '未学习', 0)",
            (user_id, skill_id),
        )


def get_employee_skill_map(user_id):
    """获取员工的技能地图"""
    with get_db() as conn:
        # 获取员工信息
        user = dict_from_row(
            conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        )
        if not user:
            return None

        # 获取该员工所有技能进度
        rows = conn.execute(
            """SELECT esp.*, s.title, s.category, s.tags, s.status as skill_status
               FROM employee_skill_progress esp
               JOIN skills s ON esp.skill_id = s.id
               WHERE esp.user_id=?
               ORDER BY esp.status, s.category""",
            (user_id,),
        ).fetchall()

        skills = []
        for r in rows:
            skill = dict_from_row(r)
            skills.append(skill)

        # 统计
        total = len(skills)
        mastered = sum(1 for s in skills if s["status"] in ("已掌握", "可教授"))
        learning = sum(1 for s in skills if s["status"] == "学习中")
        not_started = sum(1 for s in skills if s["status"] == "未学习")

        return {
            "user": user,
            "skills": skills,
            "stats": {
                "total": total,
                "mastered": mastered,
                "learning": learning,
                "not_started": not_started,
                "completion_percent": round(mastered / total * 100, 1) if total > 0 else 0,
            },
        }


def update_skill_progress(user_id, skill_id, progress=None, status=None):
    """更新员工技能进度"""
    with get_db() as conn:
        _ensure_progress(conn, user_id, skill_id)
        set_parts = ["updated_at=datetime('now','localtime')"]
        params = []
        if progress is not None:
            set_parts.append("progress=?")
            params.append(progress)
        if status is not None:
            set_parts.append("status=?")
            params.append(status)
        params.extend([user_id, skill_id])
        conn.execute(
            f"UPDATE employee_skill_progress SET {', '.join(set_parts)} WHERE user_id=? AND skill_id=?",
            params,
        )


def get_team_skill_stats():
    """获取团队技能统计"""
    with get_db() as conn:
        # 总技能数
        total_skills = conn.execute(
            "SELECT COUNT(*) FROM skills WHERE status='已发布'"
        ).fetchone()[0]

        # 各分类统计
        category_stats = conn.execute(
            """SELECT category, COUNT(*) as count
               FROM skills WHERE status='已发布'
               GROUP BY category ORDER BY count DESC"""
        ).fetchall()

        # 使用最多的技能
        top_skills = conn.execute(
            """SELECT s.id, s.title, s.view_count, s.like_count, s.collect_count,
                      u.name as creator_name
               FROM skills s
               LEFT JOIN users u ON s.creator_id = u.id
               WHERE s.status='已发布'
               ORDER BY s.view_count DESC LIMIT 10"""
        ).fetchall()

        # 员工掌握情况
        employee_stats = conn.execute(
            """SELECT u.id, u.name, u.role,
                      COUNT(CASE WHEN esp.status IN ('已掌握','可教授') THEN 1 END) as mastered,
                      COUNT(CASE WHEN esp.status = '学习中' THEN 1 END) as learning,
                      COUNT(CASE WHEN esp.status = '未学习' THEN 1 END) as not_started
               FROM users u
               LEFT JOIN employee_skill_progress esp ON u.id = esp.user_id
               GROUP BY u.id
               ORDER BY mastered DESC"""
        ).fetchall()

        return {
            "total_skills": total_skills,
            "category_stats": [dict_from_row(r) for r in category_stats],
            "top_skills": [dict_from_row(r) for r in top_skills],
            "employee_stats": [dict_from_row(r) for r in employee_stats],
        }


# ============================================================
# 操作日志
# ============================================================

def log_operation(user_id, action, skill_id=None, detail=""):
    """记录操作日志"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO operation_logs (user_id, skill_id, action, detail) VALUES (?, ?, ?, ?)",
            (user_id, skill_id, action, detail),
        )


def get_recent_logs(limit=20):
    """获取最近的操作日志"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT ol.*, u.name as user_name, s.title as skill_title
               FROM operation_logs ol
               LEFT JOIN users u ON ol.user_id = u.id
               LEFT JOIN skills s ON ol.skill_id = s.id
               ORDER BY ol.created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict_from_row(r) for r in rows]


# ============================================================
# 产品照片
# ============================================================

def save_product_photo(user_id, image_path, diagnosis_result, skill_id=None):
    """保存产品照片和诊断结果"""
    with get_db() as conn:
        grade = diagnosis_result.get("quality_grade", "N") if diagnosis_result else "N"
        cur = conn.execute(
            """INSERT INTO product_photos (user_id, skill_id, image_path, diagnosis_result, quality_grade)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, skill_id, image_path, json.dumps(diagnosis_result, ensure_ascii=False), grade),
        )
        return cur.lastrowid


# ============================================================
# 通知/推送
# ============================================================

def create_notification(user_id, title, content, skill_id=None):
    """创建推送通知"""
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO notifications (user_id, title, content, skill_id) VALUES (?, ?, ?, ?)",
            (user_id, title, content, skill_id),
        )
        return cur.lastrowid


def get_user_notifications(user_id, unread_only=False):
    """获取用户的通知列表"""
    with get_db() as conn:
        query = "SELECT * FROM notifications WHERE user_id=?"
        params = [user_id]
        if unread_only:
            query += " AND is_read=0"
        query += " ORDER BY created_at DESC LIMIT 50"
        rows = conn.execute(query, params).fetchall()
        return [dict_from_row(r) for r in rows]


def mark_notification_read(notification_id):
    """标记通知为已读"""
    with get_db() as conn:
        conn.execute(
            "UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,)
        )


def collect_notification(notification_id):
    """收藏通知"""
    with get_db() as conn:
        conn.execute(
            "UPDATE notifications SET is_collected=1 WHERE id=?", (notification_id,)
        )


# ============================================================
# 种子数据
# ============================================================

def seed_data():
    """初始化种子数据（如果数据库为空）"""
    with get_db() as conn:
        # 检查是否已有数据
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return  # 已有数据，跳过

        print("🌱 正在初始化种子数据...")

        # ---- 员工数据 ----
        employees = [
            ("陈老板", "老板", "0912-345-001"),
            ("志伟", "店长", "0912-345-002"),
            ("阿明", "烘焙师", "0912-345-003"),
            ("老王", "烘焙师", "0912-345-004"),
            ("阿杰", "烘焙师", "0912-345-005"),
            ("小豪", "学徒", "0912-345-006"),
            ("小玲", "销售", "0912-345-007"),
            ("小美", "销售", "0912-345-008"),
            ("阿华", "销售", "0912-345-009"),
            ("淑芬", "销售", "0912-345-010"),
            ("美珍", "后勤", "0912-345-011"),
            ("阿强", "后勤", "0912-345-012"),
        ]
        user_ids = {}
        for name, role, phone in employees:
            cur = conn.execute(
                "INSERT INTO users (name, role, phone) VALUES (?, ?, ?)",
                (name, role, phone),
            )
            user_ids[name] = cur.lastrowid

        # ---- 技能数据 ----
        skills_data = [
            {
                "title": "低温天气打面调整法",
                "content": {
                    "trigger_condition": "室温低于20℃",
                    "steps": [
                        "水温调至35℃（常温+8℃）",
                        "面温目标26℃（比常温+2℃）",
                        "发酵时间延长40分钟",
                    ],
                    "expected_result": "气孔更漂亮，口感更蓬松",
                    "tips": "如果室温低于15℃，建议使用温水和面，同时将发酵箱温度调高2℃",
                },
                "creator": "阿明",
                "category": "烘焙工艺",
                "tags": "打面,低温,发酵",
                "status": "已发布",
            },
            {
                "title": "夏季高温打面法",
                "content": {
                    "trigger_condition": "室温高于30℃",
                    "steps": [
                        "使用冰水打面，水温控制在12℃",
                        "面温目标22℃（比平时低2℃）",
                        "发酵时间缩短30分钟",
                        "面团打好后立即入冰箱松弛15分钟",
                    ],
                    "expected_result": "面团温度可控，发酵不过度",
                    "tips": "夏天面粉温度也高，建议面粉提前冷藏2小时",
                },
                "creator": "阿明",
                "category": "烘焙工艺",
                "tags": "打面,高温,夏季,发酵",
                "status": "已发布",
            },
            {
                "title": "可颂标准烘焙法",
                "content": {
                    "trigger_condition": "制作可颂面团",
                    "steps": [
                        "面团温度控制在24℃",
                        "折叠3次，每次冷藏30分钟",
                        "最后发酵温度28℃，湿度75%，时间2小时",
                        "烘烤温度：上火200℃/下火190℃，时间18分钟",
                    ],
                    "expected_result": "表面金黄油亮，层次分明，内部蜂窝状",
                    "tips": "折叠时黄油不能太硬也不能太软，手指按下去有印但不会黏手",
                },
                "creator": "老王",
                "category": "烘焙工艺",
                "tags": "可颂,折叠,烘烤,标准",
                "status": "已发布",
            },
            {
                "title": "酸种面包发酵判断法",
                "content": {
                    "trigger_condition": "制作酸种面包",
                    "steps": [
                        "酵种活性测试：取一勺酵种放入水中，浮起表示活性好",
                        "面团发酵至体积增加80%",
                        "手指沾粉戳洞，洞口不回缩不塌陷",
                        "轻拍面团表面，听到空洞声",
                    ],
                    "expected_result": "发酵到位，气孔分布均匀，酸味适中",
                    "tips": "酸种发酵看状态不看时间，夏天可能4小时，冬天可能12小时",
                },
                "creator": "老王",
                "category": "烘焙工艺",
                "tags": "酸种,发酵,判断,天然酵母",
                "status": "已发布",
            },
            {
                "title": "盐可颂整形手法",
                "content": {
                    "trigger_condition": "制作盐可颂整形时",
                    "steps": [
                        "面团擀成倒三角形，长20cm",
                        "顶部放3g有盐黄油",
                        "从上往下卷，不要太紧",
                        "收口压在底部",
                        "最后发酵至1.5倍大",
                    ],
                    "expected_result": "层次分明，底部平整，侧面能看到螺旋纹",
                    "tips": "卷的时候两边稍微往外拉，成品会更好看",
                },
                "creator": "阿杰",
                "category": "烘焙工艺",
                "tags": "盐可颂,整形,手法",
                "status": "已发布",
            },
            {
                "title": "烤箱温度偏差修正法",
                "content": {
                    "trigger_condition": "发现成品颜色不均或烤焦/不熟",
                    "steps": [
                        "用烤箱温度计实测温度，与设定值对比",
                        "如果实测偏高：降低设定值（偏高多少降多少）",
                        "如果实测偏低：升高设定值",
                        "注意：商用烤箱开门后温度会骤降30-50℃",
                    ],
                    "expected_result": "烤出来的成品颜色均匀，达到标准色卡",
                    "tips": "建议每周用温度计校准一次烤箱",
                },
                "creator": "志伟",
                "category": "烘焙工艺",
                "tags": "烤箱,温度,校准,偏差",
                "status": "已发布",
            },
            {
                "title": "常客喜好记忆法",
                "content": {
                    "trigger_condition": "接待常客时",
                    "steps": [
                        "先打招呼+问近况（建立亲切感）",
                        "主动推荐上次买过的产品",
                        "推荐新品时关联到上次的口味偏好",
                        "结账时提醒会员积分和优惠",
                    ],
                    "expected_result": "客人感到被重视，复购率提升",
                    "tips": "如果记不住，可以说'我查一下您的记录'，用系统查",
                },
                "creator": "小玲",
                "category": "销售技巧",
                "tags": "常客,销售,服务,复购",
                "status": "已发布",
            },
            {
                "title": "面包推荐话术（糖尿病客人）",
                "content": {
                    "trigger_condition": "客人询问适合糖尿病人的面包",
                    "steps": [
                        "推荐酸种面包（升糖指数低）",
                        "推荐全麦面包",
                        "避免推荐含糖量高的台式软包",
                        "提醒：我们的酸种面包是低糖配方",
                    ],
                    "expected_result": "客人感到专业和贴心，信任度提升",
                    "tips": "不要直接说'这个糖分高'，可以说'这款比较适合您'",
                },
                "creator": "小玲",
                "category": "销售技巧",
                "tags": "话术,糖尿病,推荐,健康",
                "status": "已发布",
            },
            {
                "title": "面粉采购验收标准",
                "content": {
                    "trigger_condition": "面粉到货验收时",
                    "steps": [
                        "看颜色：呈米黄色为佳，太白可能漂白过",
                        "闻气味：有麦香味，不能有霉味或酸味",
                        "摸手感：细腻顺滑，不能结块",
                        "夏天到货的面粉需冷冻48小时杀虫卵",
                    ],
                    "expected_result": "确保面粉品质达标，避免虫害",
                    "tips": "不同品牌的面粉吸水性不同，换品牌时要重新测试",
                },
                "creator": "美珍",
                "category": "后勤采购",
                "tags": "面粉,采购,验收,品质",
                "status": "已发布",
            },
            {
                "title": "节假日备货量估算",
                "content": {
                    "trigger_condition": "节假日前一天",
                    "steps": [
                        "查看去年同期销量数据",
                        "查看今日订单量（LINE/电话预订）",
                        "主力产品（可颂、吐司）备货量×1.5",
                        "节日限定款备货量×2",
                        "通知烘焙师提前2小时到岗",
                    ],
                    "expected_result": "节假日不断货、不过量浪费",
                    "tips": "宁可多做10%也不要少做，面包可以捐给慈善机构",
                },
                "creator": "志伟",
                "category": "管理方法",
                "tags": "节假日,备货,管理,计划",
                "status": "已发布",
            },
        ]

        for sd in skills_data:
            creator_name = sd["creator"]
            creator_id = user_ids.get(creator_name, 1)
            content_json = json.dumps(sd["content"], ensure_ascii=False)
            now = "2026-05-15 08:00:00"
            cur = conn.execute(
                """INSERT INTO skills (title, content, creator_id, category, tags, status, created_at, updated_at, view_count, like_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sd["title"],
                    content_json,
                    creator_id,
                    sd["category"],
                    sd["tags"],
                    sd["status"],
                    now,
                    now,
                    0,
                    0,
                ),
            )
            skill_id = cur.lastrowid

            # 创建版本记录
            conn.execute(
                """INSERT INTO skill_versions (skill_id, version_number, content, created_by, created_at)
                   VALUES (?, 1, ?, ?, ?)""",
                (skill_id, content_json, creator_id, now),
            )

            # 为所有员工创建技能进度
            for uid in user_ids.values():
                conn.execute(
                    """INSERT OR IGNORE INTO employee_skill_progress (user_id, skill_id, status, progress)
                       VALUES (?, ?, '未学习', 0)""",
                    (uid, skill_id),
                )

        # ---- 设置一些员工的技能进度 ----
        # 阿明（资深烘焙师）已掌握大部分烘焙技能
        for skill_id in range(1, 7):
            conn.execute(
                """UPDATE employee_skill_progress SET status='已掌握', progress=100
                   WHERE user_id=? AND skill_id=?""",
                (user_ids["阿明"], skill_id),
            )
        # 小豪（学徒）还在学习中
        conn.execute(
            """UPDATE employee_skill_progress SET status='已掌握', progress=100
               WHERE user_id=? AND skill_id IN (1,2)""",
            (user_ids["小豪"],),
        )
        conn.execute(
            """UPDATE employee_skill_progress SET status='学习中', progress=60
               WHERE user_id=? AND skill_id IN (3,5)""",
            (user_ids["小豪"],),
        )
        # 小玲（销售）已掌握销售技能
        conn.execute(
            """UPDATE employee_skill_progress SET status='已掌握', progress=100
               WHERE user_id=? AND skill_id IN (7,8)""",
            (user_ids["小玲"],),
        )
        # 志伟（店长）掌握管理和部分烘焙
        conn.execute(
            """UPDATE employee_skill_progress SET status='已掌握', progress=100
               WHERE user_id=? AND skill_id IN (6,10)""",
            (user_ids["志伟"],),
        )

        # ---- 一些操作日志 ----
        actions = [
            (user_ids["阿明"], 1, "使用"),
            (user_ids["小豪"], 1, "使用"),
            (user_ids["小豪"], 3, "查看"),
            (user_ids["小玲"], 7, "使用"),
            (user_ids["小玲"], 8, "使用"),
            (user_ids["志伟"], 6, "使用"),
            (user_ids["志伟"], 10, "使用"),
            (user_ids["老王"], 3, "创建"),
            (user_ids["老王"], 4, "创建"),
        ]
        for uid, sid, act in actions:
            conn.execute(
                "INSERT INTO operation_logs (user_id, skill_id, action) VALUES (?, ?, ?)",
                (uid, sid, act),
            )

        print(f"✅ 种子数据初始化完成！共 {len(employees)} 名员工，{len(skills_data)} 个技能包。")
