import os
import json
import tempfile
import pytest
from argparse import Namespace
from src.tools import (
    generate_extras_prompt, EXTRAS_TEMPLATES, EXTRAS_CHOICES,
    CHANNEL_CHOICES, DURATION_CHOICES, SKILL_FOCUS_CHOICES, PROJECT_LEVEL_CHOICES,
    cmd_generate_extras
)
from src.assembler import generate_extras_file


JD_SAMPLE = "岗位名称：前端工程师\n公司：字节跳动\n"
PERSONAL_SAMPLE = "姓名：张三\n技能：JavaScript, Vue\n"
LOGIC_SAMPLE = "使用STAR法则"


class TestGenerateExtrasPrompt:
    def test_all_templates_render(self):
        for field in EXTRAS_TEMPLATES:
            result = generate_extras_prompt(
                field_name=field,
                jd_content=JD_SAMPLE,
                personal_info=PERSONAL_SAMPLE,
                writing_logic=LOGIC_SAMPLE,
            )
            assert result is not None
            assert len(result) > 50

    def test_unknown_field(self):
        with pytest.raises(ValueError, match="未知的扩展子项"):
            generate_extras_prompt(
                field_name="invalid-field",
                jd_content=JD_SAMPLE,
                personal_info=PERSONAL_SAMPLE,
            )

    def test_first_msg_channel_param(self):
        result_im = generate_extras_prompt(
            field_name="first-msg", jd_content=JD_SAMPLE,
            personal_info=PERSONAL_SAMPLE, channel="im"
        )
        result_email = generate_extras_prompt(
            field_name="first-msg", jd_content=JD_SAMPLE,
            personal_info=PERSONAL_SAMPLE, channel="email"
        )
        assert result_im is not None
        assert result_email is not None

    def test_interview_duration_param(self):
        result_1min = generate_extras_prompt(
            field_name="interview-intro", jd_content=JD_SAMPLE,
            personal_info=PERSONAL_SAMPLE, interview_duration="1min"
        )
        result_3min = generate_extras_prompt(
            field_name="interview-intro", jd_content=JD_SAMPLE,
            personal_info=PERSONAL_SAMPLE, interview_duration="3min"
        )
        assert result_1min is not None
        assert result_3min is not None

    def test_skill_focus_param(self):
        for focus in SKILL_FOCUS_CHOICES:
            result = generate_extras_prompt(
                field_name="skill-gap", jd_content=JD_SAMPLE,
                personal_info=PERSONAL_SAMPLE, skill_focus=focus
            )
            assert result is not None

    def test_project_level_param(self):
        for level in PROJECT_LEVEL_CHOICES:
            result = generate_extras_prompt(
                field_name="project-recommend", jd_content=JD_SAMPLE,
                personal_info=PERSONAL_SAMPLE, project_level=level
            )
            assert result is not None


class TestGenerateExtrasFile:
    def test_basic_generation(self):
        extras_map = {
            "first-msg": "您好，我对贵公司前端岗位很感兴趣。",
            "interview-intro": "我叫张三，有3年前端开发经验。",
        }
        result = generate_extras_file(
            user_name="张三", job_title="前端工程师", company="字节跳动",
            extras_map=extras_map, output_dir=tempfile.mkdtemp()
        )
        assert result["success"] is True
        assert "extras" in result["file_path"]
        with open(result["file_path"], 'r', encoding='utf-8') as f:
            content = f.read()
        assert "# 投递第一句话" in content
        assert "# 面试个人介绍" in content
        assert "能力补充建议" not in content

    def test_filename_collision(self):
        extras_map = {"first-msg": "测试内容"}
        output_dir = tempfile.mkdtemp()
        r1 = generate_extras_file(
            "张三", "前端工程师", "字节跳动", extras_map, output_dir
        )
        r2 = generate_extras_file(
            "张三", "前端工程师", "字节跳动", extras_map, output_dir
        )
        assert r1["file_path"] != r2["file_path"]
        assert os.path.exists(r1["file_path"])
        assert os.path.exists(r2["file_path"])

    def test_all_four_items(self):
        extras_map = {
            "first-msg": "内容1",
            "interview-intro": "内容2",
            "skill-gap": "内容3",
            "project-recommend": "内容4",
        }
        result = generate_extras_file(
            "张三", "前端工程师", "字节跳动",
            extras_map, output_dir=tempfile.mkdtemp()
        )
        with open(result["file_path"], 'r', encoding='utf-8') as f:
            content = f.read()
        assert "# 投递第一句话" in content
        assert "# 面试个人介绍" in content
        assert "# 能力补充建议" in content
        assert "# 练习项目推荐" in content

    def test_sanitize_filename(self):
        extras_map = {"first-msg": "test"}
        result = generate_extras_file(
            "张/三", "前端/工程师", "字节/跳动",
            extras_map, output_dir=tempfile.mkdtemp()
        )
        assert result["success"] is True
        filename = os.path.basename(result["file_path"])
        assert "/" not in filename


class TestCliGenerateExtras:
    def test_cmd_generate_extras(self, capsys):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', encoding='utf-8', delete=False) as jd_f:
            jd_f.write(JD_SAMPLE)
            jd_path = jd_f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', encoding='utf-8', delete=False) as pi_f:
            pi_f.write(PERSONAL_SAMPLE)
            pi_path = pi_f.name

        args = Namespace(
            jd_file=jd_path, personal_info_file=pi_path,
            logic_file=None, output_dir=tempfile.mkdtemp(),
            extras="first-msg,interview-intro",
            no_extras=False, channel=None, interview_duration=None,
            skill_focus=None, project_level=None,
        )
        cmd_generate_extras(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert os.path.exists(data["file_path"])
        with open(data["file_path"], 'r', encoding='utf-8') as f:
            content = f.read()
        assert "# 投递第一句话" in content
        assert "# 面试个人介绍" in content

    def test_no_extras_skip(self):
        pass
