"""
SweetLoaf AI 组织转型系统 — 语音处理模块测试

测试范围：voice_processor.py 中的语音识别和闽南语翻译功能
"""
import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DB_PATH"] = ":memory:"
os.environ["MOCK_MODE"] = "True"  # 确保使用模拟模式

from app import voice_processor


# ============================================================
# 语音识别测试（模拟模式）
# ============================================================

class TestTranscribeAudio:
    """测试语音识别功能"""

    def test_mock_transcribe_cold(self):
        """TC-F1.1-V001: 模拟识别'低温'关键词"""
        with tempfile.NamedTemporaryFile(suffix="cold.wav", delete=False) as f:
            path = f.name
        try:
            result = voice_processor.transcribe_audio(path)
            assert "台南降温" in result
            assert "室温只有18度" in result
        finally:
            os.unlink(path)

    def test_mock_transcribe_hot(self):
        """TC-F1.1-V002: 模拟识别'高温'关键词"""
        with tempfile.NamedTemporaryFile(suffix="hot.wav", delete=False) as f:
            path = f.name
        try:
            result = voice_processor.transcribe_audio(path)
            assert "室温32度" in result
        finally:
            os.unlink(path)

    def test_mock_transcribe_croissant(self):
        """TC-F1.1-V003: 模拟识别'可颂'关键词"""
        with tempfile.NamedTemporaryFile(suffix="croissant.wav", delete=False) as f:
            path = f.name
        try:
            result = voice_processor.transcribe_audio(path)
            assert "可颂" in result
        finally:
            os.unlink(path)

    def test_mock_transcribe_sourdough(self):
        """TC-F1.1-V004: 模拟识别'酸种'关键词"""
        with tempfile.NamedTemporaryFile(suffix="sourdough.wav", delete=False) as f:
            path = f.name
        try:
            result = voice_processor.transcribe_audio(path)
            assert "酸种" in result
        finally:
            os.unlink(path)

    def test_mock_transcribe_salty(self):
        """TC-F1.1-V005: 模拟识别'盐可颂'关键词"""
        with tempfile.NamedTemporaryFile(suffix="salty.wav", delete=False) as f:
            path = f.name
        try:
            result = voice_processor.transcribe_audio(path)
            assert "盐可颂" in result
        finally:
            os.unlink(path)

    def test_mock_transcribe_default(self):
        """TC-F1.1-V006: 模拟识别未知关键词（返回默认）"""
        with tempfile.NamedTemporaryFile(suffix="unknown_audio.wav", delete=False) as f:
            path = f.name
        try:
            result = voice_processor.transcribe_audio(path)
            assert result  # 返回默认文本，不为空
        finally:
            os.unlink(path)

    def test_transcribe_from_text(self):
        """TC-F1.1-V007: 直接文本输入（跳过语音识别）"""
        text = "今天天气冷，面温打到26度"
        result = voice_processor.transcribe_from_text(text)
        assert result == text


class TestTaiwaneseTranslation:
    """测试闽南语翻译功能"""

    def test_translate_taiwanese_basic(self):
        """TC-F1.1-V008: 闽南语基本词汇翻译"""
        text = "今仔日天气较冷"
        result = voice_processor.translate_taiwanese(text)
        assert "今天" in result

    def test_translate_taiwanese_mixed(self):
        """TC-F1.1-V009: 闽南语+普通话混合翻译"""
        text = "今仔日天气较冷，面温爱拍到26度"
        result = voice_processor.translate_taiwanese(text)
        assert "今天" in result
        assert "面温" in result  # 普通话部分保留

    def test_translate_taiwanese_with_exclamation(self):
        """TC-F1.1-V010: 闽南语感叹词翻译"""
        text = "齁！这个可颂烤得真水，气孔有够水"
        result = voice_processor.translate_taiwanese(text)
        assert "真水" not in result or "很漂亮" in result

    def test_translate_taiwanese_empty(self):
        """TC-F1.1-V011: 空文本翻译"""
        result = voice_processor.translate_taiwanese("")
        assert result == ""

    def test_translate_taiwanese_no_match(self):
        """TC-F1.1-V012: 无闽南语词汇的文本"""
        text = "今天天气不错"
        result = voice_processor.translate_taiwanese(text)
        assert result == text  # 不变

    def test_translate_taiwanese_full_sentence(self):
        """TC-F1.1-V013: 完整闽南语句子翻译"""
        text = "今仔日天气较冷，面温爱拍到26度，比平常加2度，发酵时间爱延长40分钟"
        result = voice_processor.translate_taiwanese(text)
        assert "今天" in result
        assert "比" in result  # "比平常"中的"比"保留
