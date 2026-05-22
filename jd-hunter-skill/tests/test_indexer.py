import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.indexer import generate_jd_index, get_index_report


class TestGenerateJdIndex:
    def test_no_jd_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            jd_dir = os.path.join(tmpdir, "jd")
            index_path = generate_jd_index(jd_dir=jd_dir, output_path=os.path.join(jd_dir, "index.md"))
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "暂无 JD 数据" in content

    def test_empty_jd_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "jd"), exist_ok=True)
            index_path = generate_jd_index(jd_dir=os.path.join(tmpdir, "jd"),
                                           output_path=os.path.join(tmpdir, "jd", "index.md"))
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "暂无 JD 数据" in content

    def test_generates_table_with_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            jd_dir = os.path.join(tmpdir, "jd")
            os.makedirs(jd_dir, exist_ok=True)

            jd_content = """# 腾讯 - 后端开发

- jd来源：boss直聘
- jd投递渠道：im
- jd投递url：https://example.com
- 岗位名称：后端开发
- 公司：腾讯

## 岗位职责

desc

## 任职要求

req
"""
            with open(os.path.join(jd_dir, "腾讯-后端开发.md"), "w", encoding="utf-8") as f:
                f.write(jd_content)

            index_path = generate_jd_index(jd_dir=jd_dir,
                                           output_path=os.path.join(jd_dir, "index.md"))
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "腾讯" in content
            assert "后端开发" in content
            assert "boss直聘" in content
            assert "|" in content


class TestGetIndexReport:
    def test_report_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = get_index_report(jd_dir=os.path.join(tmpdir, "jd"),
                                      raw_base=os.path.join(tmpdir, "jd_raw"))
            assert report["total_structured"] == 0
            assert report["total_raw"] == 0
