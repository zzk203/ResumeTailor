import pytest
from src.parser import extract_name, extract_job_and_company, extract_fill_fields


class TestExtractName:
    def test_normal(self):
        assert extract_name("姓名：张三") == "张三"
        assert extract_name("姓名: 李四") == "李四"

    def test_missing(self):
        assert extract_name("没有名字") == ""

    def test_empty(self):
        assert extract_name("") == ""

    def test_with_bold_markers(self):
        assert extract_name("**姓名**：**张三**") == "张三"
        assert extract_name("**姓名：**张三**") == "张三"


class TestExtractJobAndCompany:
    def test_normal(self):
        text = "岗位名称：后端开发工程师\n公司：字节跳动"
        job, comp = extract_job_and_company(text)
        assert job == "后端开发工程师"
        assert comp == "字节跳动"

    def test_missing_job(self):
        text = "公司：字节跳动"
        job, comp = extract_job_and_company(text)
        assert job == ""
        assert comp == "字节跳动"

    def test_missing_company(self):
        text = "岗位名称：后端开发工程师"
        job, comp = extract_job_and_company(text)
        assert job == "后端开发工程师"
        assert comp == ""

    def test_empty(self):
        assert extract_job_and_company("") == ("", "")


class TestExtractFillFields:
    TEMPLATE_NORMAL = """\
# 简历
<!-- fill:教育经历 -->内容<!-- /fill:教育经历 -->
<!-- fill:工作经历 -->内容<!-- /fill:工作经历 -->
"""

    def test_normal(self):
        fields = extract_fill_fields(self.TEMPLATE_NORMAL)
        assert fields == ["教育经历", "工作经历"]

    def test_duplicate(self):
        t = """\
<!-- fill:技能 -->A<!-- /fill:技能 -->
<!-- fill:技能 -->B<!-- /fill:技能 -->
"""
        fields = extract_fill_fields(t)
        assert fields == ["技能"]

    def test_no_fill(self):
        assert extract_fill_fields("纯文本") == []

    def test_empty(self):
        assert extract_fill_fields("") == []
