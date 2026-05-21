"""
SweetLoaf AI 组织转型系统 — 配置文件
"""
import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sweetloaf.db")

# 确保data目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# Flask 配置
SECRET_KEY = os.environ.get("SECRET_KEY", "sweetloaf-2026-mvp-secret")
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))

# 模拟模式（没有真实API时使用）
MOCK_MODE = os.environ.get("MOCK_MODE", "True").lower() == "true"

# 语音识别配置
# 真实Whisper模式: 需安装 openai-whisper
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")  # tiny/base/small/medium/large
# Google STT 配置（备用）
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

# 图像诊断配置
# 颜色阈值（HSV空间）
COLOR_THRESHOLDS = {
    "golden_brown": {
        "h_low": 10, "h_high": 30,
        "s_low": 40, "s_high": 255,
        "v_low": 100, "v_high": 220,
    },
    "light_brown": {
        "h_low": 15, "h_high": 35,
        "s_low": 20, "s_high": 100,
        "v_low": 180, "v_high": 255,
    },
    "dark_brown": {
        "h_low": 0, "h_high": 20,
        "s_low": 60, "s_high": 255,
        "v_low": 30, "v_high": 120,
    },
    "burnt": {
        "h_low": 0, "h_high": 10,
        "s_low": 80, "s_high": 255,
        "v_low": 10, "v_high": 60,
    },
}

# LINE Bot 配置（部署时填写）
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

# 推荐引擎配置
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
TAIPEI_LAT = 22.9997  # 台南纬度
TAIPEI_LON = 120.2270  # 台南经度
