import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.extractor import infer_source_metadata, save_structured_jd


class TestInferSourceMetadata:
    def test_boss_channel(self):
        result = infer_source_metadata("", channel_name="boss", url="https://www.zhipin.com/job/123")
        assert result["jd来源"] == "boss直聘"
        assert result["jd投递渠道"] == "im"

    def test_lagou_channel(self):
        result = infer_source_metadata("", channel_name="lagou")
        assert result["jd来源"] == "拉勾"
        assert result["jd投递渠道"] == "im"

    def test_liepin_channel(self):
        result = infer_source_metadata("", channel_name="liepin")
        assert result["jd来源"] == "猎聘"
        assert result["jd投递渠道"] == "email"

    def test_url_from_content(self):
        raw = "详情请访问 https://www.zhipin.com/job/456 了解更多"
        result = infer_source_metadata(raw, channel_name="")
        assert result["jd投递url"] == "https://www.zhipin.com/job/456"

    def test_unknown_channel(self):
        result = infer_source_metadata("", channel_name="unknown")
        assert result["jd来源"] == "unknown"


class TestSaveStructuredJd:
    def test_save_creates_file(self):
        fields = {
            "jd来源": "boss直聘",
            "jd投递渠道": "im",
            "jd投递url": "https://example.com",
            "岗位名称": "后端开发",
            "公司": "腾讯",
            "岗位职责": "负责后端服务开发",
            "任职要求": "3年以上经验",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = save_structured_jd(fields, output_base=tmpdir)
            assert os.path.exists(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            assert "腾讯" in content
            assert "后端开发" in content

    def test_duplicate_filename_adds_suffix(self):
        fields = {
            "jd来源": "boss直聘",
            "jd投递渠道": "im",
            "jd投递url": "",
            "岗位名称": "后端开发",
            "公司": "腾讯",
            "岗位职责": "desc",
            "任职要求": "req",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            first = save_structured_jd(fields, output_base=tmpdir)
            second = save_structured_jd(fields, output_base=tmpdir)
            assert first != second
            assert os.path.exists(second)
