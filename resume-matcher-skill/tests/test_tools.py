import json
import os
import tempfile
from src.tools import cmd_parse_jd, cmd_parse_template
from argparse import Namespace


class TestTools:
    def test_cmd_parse_jd(self, capsys):
        fname = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', encoding='utf-8', delete=False) as f:
                f.write("岗位名称：前端工程师\n公司：阿里\n")
                fname = f.name
            args = Namespace(jd_file=fname)
            cmd_parse_jd(args)
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["job_title"] == "前端工程师"
            assert data["company"] == "阿里"
        finally:
            if fname and os.path.exists(fname):
                os.unlink(fname)

    def test_cmd_parse_template(self, capsys):
        fname = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', encoding='utf-8', delete=False) as f:
                f.write('<!-- fill:技能 -->内容<!-- /fill:技能 -->')
                fname = f.name
            args = Namespace(template_file=fname)
            cmd_parse_template(args)
            captured = capsys.readouterr()
            fields = json.loads(captured.out)
            assert fields == ["技能"]
        finally:
            if fname and os.path.exists(fname):
                os.unlink(fname)
