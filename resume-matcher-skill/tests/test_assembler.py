import os
import tempfile
import pytest
from src.assembler import generate_resume_file, TemplateParseError


class TestGenerateResumeFile:
    def test_basic(self):
        template = """\
# <!-- fixed:姓名 -->张三<!-- /fixed:姓名 -->
## 项目经历
<!-- fill:项目经历 -->旧内容<!-- /fill:项目经历 -->
"""
        mapping = {"项目经历": "新项目经历内容"}
        result = generate_resume_file(template, mapping, "张三", "工程师", "腾讯", output_dir=tempfile.mkdtemp())
        assert result["success"] is True
        with open(result["file_path"], 'r', encoding='utf-8') as f:
            content = f.read()
        assert "<!-- fixed:姓名 -->" in content
        assert "新项目经历内容" in content
        assert "旧内容" not in content

    def test_missing_field(self):
        template = '<!-- fill:缺失字段 -->内容<!-- /fill:缺失字段 -->'
        result = generate_resume_file(template, {}, "张三", "工程师", "公司", output_dir=tempfile.mkdtemp())
        assert result["success"] is False
        assert "缺失" in result["errors"][0]

    def test_unclosed_tag(self):
        template = '<!-- fill:技能 -->内容'
        result = generate_resume_file(template, {"技能": "新技能"}, "张三", "工程师", "公司", output_dir=tempfile.mkdtemp())
        assert result["success"] is False

    def test_filename_collision(self):
        template = '<!-- fill:项目 -->内容<!-- /fill:项目 -->'
        mapping = {"项目": "项目内容"}
        output_dir = tempfile.mkdtemp()
        r1 = generate_resume_file(template, mapping, "张三", "工程师", "公司", output_dir=output_dir)
        r2 = generate_resume_file(template, mapping, "张三", "工程师", "公司", output_dir=output_dir)
        assert r1["file_path"] != r2["file_path"]
        assert os.path.exists(r1["file_path"])
        assert os.path.exists(r2["file_path"])

    def test_multiple_fills(self):
        template = """\
<!-- fill:A -->a<!-- /fill:A -->
<!-- fill:B -->b<!-- /fill:B -->
"""
        mapping = {"A": "AA", "B": "BB"}
        result = generate_resume_file(template, mapping, "张三", "工程师", "公司", output_dir=tempfile.mkdtemp())
        assert result["success"] is True
        with open(result["file_path"], 'r', encoding='utf-8') as f:
            content = f.read()
        assert "AA" in content
        assert "BB" in content
        assert "<!-- fill:" not in content
