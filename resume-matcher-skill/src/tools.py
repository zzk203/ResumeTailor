import argparse
import glob
import json
import os
import sys


from jinja2 import Environment, PackageLoader, select_autoescape

from .parser import extract_job_and_company, extract_name, extract_fill_fields
from .assembler import generate_resume_file, generate_extras_file

EXTRAS_TEMPLATES = {
    "first-msg": "first_message.jinja2",
    "interview-intro": "interview_intro.jinja2",
    "skill-gap": "skill_gap.jinja2",
    "project-recommend": "project_recommend.jinja2",
}

EXTRAS_TITLE_MAP = {
    "first-msg": "投递第一句话",
    "interview-intro": "面试个人介绍",
    "skill-gap": "能力补充建议",
    "project-recommend": "练习项目推荐",
}

_jinja_env = None


def _get_jinja_env():
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=PackageLoader("resume-matcher-skill.src", "prompt_templates"),
            autoescape=select_autoescape()
        )
    return _jinja_env


def generate_extras_prompt(field_name: str, jd_content: str, personal_info: str, writing_logic: str = "", **kwargs) -> str:
    template_name = EXTRAS_TEMPLATES.get(field_name)
    if not template_name:
        raise ValueError(f"未知的扩展子项: {field_name}，有效选项: {', '.join(EXTRAS_TEMPLATES.keys())}")

    env = _get_jinja_env()
    template = env.get_template(template_name)

    params = {
        "jd_content": jd_content,
        "personal_info": personal_info,
        "writing_logic": writing_logic,
    }

    if field_name == "first-msg":
        params["channel"] = kwargs.get("channel", "im")
    elif field_name == "interview-intro":
        params["interview_duration"] = kwargs.get("interview_duration", "3min")
    elif field_name == "skill-gap":
        params["skill_focus"] = kwargs.get("skill_focus", "balanced")
    elif field_name == "project-recommend":
        params["project_level"] = kwargs.get("project_level", "intermediate")

    return template.render(**params)


def cmd_parse_jd(args):
    with open(args.jd_file, 'r', encoding='utf-8') as f:
        text = f.read()
    job_title, company = extract_job_and_company(text)
    result = {"job_title": job_title, "company": company}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_parse_template(args):
    with open(args.template_file, 'r', encoding='utf-8') as f:
        text = f.read()
    fields = extract_fill_fields(text)
    print(json.dumps(fields, ensure_ascii=False, indent=2))


def cmd_assemble(args):
    with open(args.template_file, 'r', encoding='utf-8') as f:
        template = f.read()
    fill_mapping = json.loads(args.fill_mapping_json)
    result = generate_resume_file(
        template_content=template,
        fill_mapping=fill_mapping,
        user_name=args.user_name,
        job_title=args.job_title,
        company=args.company,
        output_dir=args.output_dir or "./output"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_batch_assemble(args):
    with open(args.template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()
    with open(args.personal_info_file, 'r', encoding='utf-8') as f:
        personal_info = f.read()

    user_name = extract_name(personal_info)
    if not user_name:
        print(json.dumps({"success": False, "message": "个人信息文件中未找到姓名"}, ensure_ascii=False))
        return

    jd_dir = args.jd_dir
    fill_ext = args.fill_ext or ".json"
    output_dir = args.output_dir or "./output"
    os.makedirs(output_dir, exist_ok=True)

    jd_files = sorted(glob.glob(os.path.join(jd_dir, '*.md')))
    results = []

    for jd_path in jd_files:
        with open(jd_path, 'r', encoding='utf-8') as f:
            jd_content = f.read()
        job_title, company = extract_job_and_company(jd_content)
        base = os.path.splitext(os.path.basename(jd_path))[0]
        fill_path = os.path.join(jd_dir, base + fill_ext)

        if not os.path.exists(fill_path):
            results.append({"jd": base, "success": False, "message": f"未找到填充映射文件 {fill_path}"})
            continue

        with open(fill_path, 'r', encoding='utf-8') as f:
            fill_mapping = json.load(f)

        result = generate_resume_file(
            template_content=template_content,
            fill_mapping=fill_mapping,
            user_name=user_name,
            job_title=job_title,
            company=company,
            output_dir=output_dir
        )
        result["jd"] = base
        if result["success"]:
            result["file_path"] = os.path.relpath(result["file_path"])
        results.append(result)

    if args.clean_json:
        for jd_path in jd_files:
            base = os.path.splitext(os.path.basename(jd_path))[0]
            fill_path = os.path.join(jd_dir, base + fill_ext)
            if os.path.exists(fill_path):
                os.remove(fill_path)

    summary = {"success": True, "total": len(results), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_generate_extras(args):
    with open(args.jd_file, 'r', encoding='utf-8') as f:
        jd_content = f.read()
    with open(args.personal_info_file, 'r', encoding='utf-8') as f:
        personal_info = f.read()

    writing_logic = ""
    if args.logic_file:
        with open(args.logic_file, 'r', encoding='utf-8') as f:
            writing_logic = f.read()

    extras_list = args.extras.split(",") if args.extras else list(EXTRAS_TEMPLATES.keys())

    extras_params = {
        "channel": args.channel,
        "interview_duration": args.interview_duration,
        "skill_focus": args.skill_focus,
        "project_level": args.project_level,
    }

    user_name = extract_name(personal_info)
    job_title, company = extract_job_and_company(jd_content)

    extras_map = {}
    for field in extras_list:
        prompt = generate_extras_prompt(
            field_name=field,
            jd_content=jd_content,
            personal_info=personal_info,
            writing_logic=writing_logic,
            **extras_params
        )
        extras_map[field] = prompt

    result = generate_extras_file(
        user_name=user_name or "未知",
        job_title=job_title or "未知",
        company=company or "未知",
        extras_map=extras_map,
        output_dir=args.output_dir or "./output"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


EXTRAS_CHOICES = list(EXTRAS_TEMPLATES.keys())
CHANNEL_CHOICES = ["im", "email"]
DURATION_CHOICES = ["1min", "3min"]
SKILL_FOCUS_CHOICES = ["gap", "strength", "balanced"]
PROJECT_LEVEL_CHOICES = ["beginner", "intermediate", "advanced"]


def _add_extras_arguments(parser):
    parser.add_argument("--extras", default=",".join(EXTRAS_CHOICES),
                        help=f"需生成的扩展子项，逗号分隔。选项: {','.join(EXTRAS_CHOICES)}，默认全部")
    parser.add_argument("--no-extras", action="store_true", help="关闭扩展文件生成")
    parser.add_argument("--channel", choices=CHANNEL_CHOICES, default=None,
                        help="投递渠道（im/email），用于生成投递第一句话")
    parser.add_argument("--interview-duration", choices=DURATION_CHOICES, default=None,
                        help="面试自我介绍时长（1min/3min）")
    parser.add_argument("--skill-focus", choices=SKILL_FOCUS_CHOICES, default=None,
                        help="能力补充建议聚焦方向（gap/strength/balanced）")
    parser.add_argument("--project-level", choices=PROJECT_LEVEL_CHOICES, default=None,
                        help="练习项目推荐难度（beginner/intermediate/advanced）")



def main():
    parser = argparse.ArgumentParser(description="简历-岗位匹配生成器工具集")
    sub = parser.add_subparsers(dest="command")

    p_jd = sub.add_parser("parse-jd", help="从 JD 文件提取岗位名称和公司")
    p_jd.add_argument("jd_file", help="岗位描述文件路径")

    p_tmpl = sub.add_parser("parse-template", help="从模板提取 fill 字段列表")
    p_tmpl.add_argument("template_file", help="模板文件路径")

    p_assemble = sub.add_parser("assemble", help="组装单份简历")
    p_assemble.add_argument("template_file", help="模板文件路径")
    p_assemble.add_argument("fill_mapping_json", help="填充映射 JSON 字符串")
    p_assemble.add_argument("user_name", help="用户姓名")
    p_assemble.add_argument("job_title", help="岗位名称")
    p_assemble.add_argument("company", help="公司名称")
    p_assemble.add_argument("--output-dir", default="./resume", help="输出目录")

    p_batch = sub.add_parser("batch-assemble", help="批量组装简历")
    p_batch.add_argument("template_file", help="模板文件路径")
    p_batch.add_argument("personal_info_file", help="个人信息文件路径")
    p_batch.add_argument("jd_dir", help="JD 文件目录（内含 .md + .json 配对）")
    p_batch.add_argument("--fill-ext", default=".json", help="填充映射文件扩展名，默认 .json")
    p_batch.add_argument("--output-dir", default="./resume", help="输出目录")
    p_batch.add_argument("--clean-json", action="store_true", help="组装完成后删除所有 .json 中间文件")

    p_extras = sub.add_parser("generate-extras", help="生成扩展求职材料（投递第一句话、面试介绍等）")
    p_extras.add_argument("jd_file", help="岗位描述文件路径")
    p_extras.add_argument("personal_info_file", help="个人信息文件路径")
    p_extras.add_argument("--logic-file", help="编写逻辑文件路径（可选）")
    p_extras.add_argument("--output-dir", default="./resume", help="输出目录")
    _add_extras_arguments(p_extras)

    args = parser.parse_args()
    if args.command == "parse-jd":
        cmd_parse_jd(args)
    elif args.command == "parse-template":
        cmd_parse_template(args)
    elif args.command == "assemble":
        cmd_assemble(args)
    elif args.command == "batch-assemble":
        cmd_batch_assemble(args)
    elif args.command == "generate-extras":
        cmd_generate_extras(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
