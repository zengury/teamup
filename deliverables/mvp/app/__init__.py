"""
SweetLoaf AI 组织转型系统 — Flask 应用初始化
"""
from flask import Flask
from flask_cors import CORS


def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object("config")
    CORS(app)

    # 注册蓝图
    from app.web_ui import web_bp
    from app.line_bot import line_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(line_bp)

    # 初始化数据库
    from app.models import init_db
    init_db()

    return app
