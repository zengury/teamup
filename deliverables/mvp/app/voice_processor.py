"""
SweetLoaf AI 组织转型系统 — 语音处理模块

支持:
1. 模拟模式（默认）：用规则解析文本，无需真实语音API
2. Whisper模式：需安装 openai-whisper
3. Google STT模式：需配置 Google Cloud 凭证
"""
import os
import re
import json
import tempfile
from config import MOCK_MODE, WHISPER_MODEL


def transcribe_audio(audio_file_path):
    """语音识别：将音频文件转为文本

    支持中文（普通话+闽南语混合）

    参数:
        audio_file_path: 音频文件路径

    返回:
        str: 转写文本
    """
    if MOCK_MODE:
        return _mock_transcribe(audio_file_path)

    # 尝试使用 Whisper
    try:
        return _whisper_transcribe(audio_file_path)
    except ImportError:
        print("⚠️ 未安装 openai-whisper，使用模拟模式")
        return _mock_transcribe(audio_file_path)
    except Exception as e:
        print(f"⚠️ Whisper 识别失败: {e}，使用模拟模式")
        return _mock_transcribe(audio_file_path)


def _whisper_transcribe(audio_file_path):
    """使用 OpenAI Whisper 进行语音识别"""
    import whisper

    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(
        audio_file_path,
        language="zh",
        task="transcribe",
        # 支持多语言混合
        verbose=False,
    )
    return result["text"].strip()


def _mock_transcribe(audio_file_path):
    """模拟语音识别：从文件名或预设文本中返回模拟结果

    在实际演示中，这个函数根据文件名返回预设的烘焙经验文本
    """
    filename = os.path.basename(audio_file_path).lower()

    # 预设的模拟语音文本库
    mock_transcripts = {
        "cold": "今天台南降温，室温只有18度，我用了温水打面，水温调到35度，面温打到26度就停了，发酵时间比平时多了40分钟，出来的气孔特别漂亮。",
        "hot": "今天天气太热了，室温32度，面团温度上升很快，我用冰水打面，水温控制在12度，面温打到22度就停了，发酵时间缩短了30分钟，打好后马上放冰箱松弛。",
        "croissant": "可颂要烤到表面金黄油亮，层次分明，底部浅褐色，上火200度下火190度，烤18分钟。折叠的时候黄油不能太硬也不能太软。",
        "sourdough": "酸种面包的发酵要看状态不看时间，手指沾粉戳洞，洞口不回缩不塌陷就是发酵好了。夏天可能4小时，冬天可能12小时。",
        "salty": "盐可颂整形的时候，面团擀成倒三角形，顶部放3克有盐黄油，从上往下卷不要太紧，收口压在底部。最后发酵到1.5倍大。",
        "default": "今天做可颂，室温25度，湿度60%，面团温度控制在24度，发酵了2小时，烤出来效果不错，颜色金黄，层次分明。",
    }

    # 尝试匹配文件名关键词
    for key, transcript in mock_transcripts.items():
        if key in filename:
            return transcript

    return mock_transcripts["default"]


def parse_skill_from_text(text):
    """用NLP规则从文本中提取结构化信息

    参数:
        text: 原始文本

    返回:
        dict: 结构化信息
    """
    from app.skill_engine import parse_skill_from_text as _parse
    return _parse(text)


def transcribe_from_text(text):
    """直接处理文本（跳过语音识别，用于手动输入）"""
    return text


# ============================================================
# 闽南语常见烘焙词汇映射（用于辅助识别）
# ============================================================

# 闽南语→普通话 烘焙词汇对照
TAIWANESE_BAKING_GLOSSARY = {
    "面温": "面团温度",
    "打面": "搅拌面团",
    "发酵": "发酵",
    "烤": "烘烤",
    "气孔": "气孔",
    "有够水": "很漂亮",
    "今仔日": "今天",
    "天气": "天气",
    "较冷": "比较冷",
    "爱拍": "要打",
    "加": "增加",
    "延长": "延长",
    "齁": "语气词",
    "真水": "很漂亮",
    "有够": "非常",
    "客人": "顾客",
    "有够多": "非常多",
    "爱多准备": "要多准备",
    "两盘": "两盘",
}


def translate_taiwanese(text):
    """将闽南语烘焙词汇转换为普通话"""
    for tw_word, cn_word in TAIWANESE_BAKING_GLOSSARY.items():
        text = text.replace(tw_word, cn_word)
    return text
