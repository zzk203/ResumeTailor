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

_jinja_env = None


def _get_jinja_env():
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=PackageLoader("resume-matcher-skill.src", "prompt_templates"),
            autoescape=select_autoescape()
        )
    return _jinja_env


DEFAULT_WRITING_LOGIC = "使用 STAR 法则，突出与岗位最相关的经历，专业简洁，纯文本段落。"

def generate_extras_prompt(field_name: str, jd_content: str, personal_info: str, writing_logic: str = "", **kwargs) -> str:
    template_name = EXTRAS_TEMPLATES.get(field_name)
    if not template_name:
        raise ValueError(f"未知的扩展子项: {field_name}，有效选项: {', '.join(EXTRAS_TEMPLATES.keys())}")

    env = _get_jinja_env()
    template = env.get_template(template_name)

    if not writing_logic:
        writing_logic = DEFAULT_WRITING_LOGIC

    params = {
        "jd_content": jd_content,
        "personal_info": personal_info,
        "writing_logic": writing_logic,
    }

    if field_name == "first-msg":
        params["channel"] = kwargs.get("channel") or "im"
    elif field_name == "interview-intro":
        params["interview_duration"] = kwargs.get("interview_duration") or "3min"
    elif field_name == "skill-gap":
        params["skill_focus"] = kwargs.get("skill_focus") or "balanced"
    elif field_name == "project-recommend":
        params["project_level"] = kwargs.get("project_level") or "intermediate"

    return template.render(**params)


def _read_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(json.dumps({"success": False, "message": f"文件未找到: {path}"}, ensure_ascii=False))
        sys.exit(1)
    except IOError as e:
        print(json.dumps({"success": False, "message": f"文件读取失败: {path}", "errors": [str(e)]}, ensure_ascii=False))
        sys.exit(1)


def cmd_parse_jd(args):
    text = _read_file(args.jd_file)
    job_title, company = extract_job_and_company(text)
    result = {"job_title": job_title, "company": company}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_parse_template(args):
    text = _read_file(args.template_file)
    fields = extract_fill_fields(text)
    print(json.dumps(fields, ensure_ascii=False, indent=2))


def cmd_assemble(args):
    template = _read_file(args.template_file)
    fill_mapping = json.loads(args.fill_mapping_json)
    result = generate_resume_file(
        template_content=template,
        fill_mapping=fill_mapping,
        user_name=args.user_name,
        job_title=args.job_title,
        company=args.company,
        output_dir=args.output_dir or "./resume"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_batch_assemble(args):
    template_content = _read_file(args.template_file)
    personal_info = _read_file(args.personal_info_file)

    user_name = extract_name(personal_info)
    if not user_name:
        print(json.dumps({"success": False, "message": "个人信息文件中未找到姓名"}, ensure_ascii=False))
        return

    writing_logic = ""
    if args.logic_file:
        writing_logic = _read_file(args.logic_file)

    jd_dir = args.jd_dir
    fill_ext = args.fill_ext or ".json"
    output_dir = args.output_dir or "./resume"
    os.makedirs(output_dir, exist_ok=True)

    jd_files = sorted(glob.glob(os.path.join(jd_dir, '*.md')))
    if not jd_files:
        print(json.dumps({"success": False, "message": f"未在目录 '{jd_dir}' 中找到任何 .md 文件"}, ensure_ascii=False))
        return
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

        jd_result = generate_resume_file(
            template_content=template_content,
            fill_mapping=fill_mapping,
            user_name=user_name,
            job_title=job_title,
            company=company,
            output_dir=output_dir
        )
        jd_result["jd"] = base
        if jd_result["success"]:
            jd_result["file_path"] = os.path.relpath(jd_result["file_path"])
        results.append(jd_result)

        if not getattr(args, 'no_extras', False):
            extras_map = {}
            extras_content_file = getattr(args, 'extras_content', None)
            if extras_content_file:
                with open(extras_content_file, 'r', encoding='utf-8') as f:
                    extras_map = json.load(f)
            else:
                extras_list = args.extras.split(",") if args.extras else list(EXTRAS_TEMPLATES.keys())
                extras_params = {
                    "channel": args.channel,
                    "interview_duration": args.interview_duration,
                    "skill_focus": args.skill_focus,
                    "project_level": args.project_level,
                }
                for field in extras_list:
                    prompt = generate_extras_prompt(
                        field_name=field,
                        jd_content=jd_content,
                        personal_info=personal_info,
                        writing_logic=writing_logic,
                        **extras_params
                    )
                    extras_map[field] = prompt

            extras_result = generate_extras_file(
                user_name=user_name or "未知",
                job_title=job_title or "未知",
                company=company or "未知",
                extras_map=extras_map,
                output_dir=output_dir
            )
            extras_result["jd"] = base
            if extras_result["success"]:
                extras_result["file_path"] = os.path.relpath(extras_result["file_path"])
            results.append(extras_result)

    if args.clean_json:
        for jd_path in jd_files:
            base = os.path.splitext(os.path.basename(jd_path))[0]
            fill_path = os.path.join(jd_dir, base + fill_ext)
            if os.path.exists(fill_path):
                os.remove(fill_path)

    summary = {"success": True, "total": len(results), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_generate_extras(args):
    jd_content = _read_file(args.jd_file)
    personal_info = _read_file(args.personal_info_file)

    writing_logic = ""
    if args.logic_file:
        writing_logic = _read_file(args.logic_file)

    extras_map = {}
    extras_content_file = getattr(args, 'extras_content', None)
    if extras_content_file:
        with open(extras_content_file, 'r', encoding='utf-8') as f:
            extras_map = json.load(f)
    else:
        extras_list = args.extras.split(",") if args.extras else list(EXTRAS_TEMPLATES.keys())
        extras_params = {
            "channel": args.channel,
            "interview_duration": args.interview_duration,
            "skill_focus": args.skill_focus,
            "project_level": args.project_level,
        }
        for field in extras_list:
            prompt = generate_extras_prompt(
                field_name=field,
                jd_content=jd_content,
                personal_info=personal_info,
                writing_logic=writing_logic,
                **extras_params
            )
            extras_map[field] = prompt

    user_name = extract_name(personal_info)
    job_title, company = extract_job_and_company(jd_content)

    result = generate_extras_file(
        user_name=user_name or "未知",
        job_title=job_title or "未知",
        company=company or "未知",
        extras_map=extras_map,
        output_dir=args.output_dir or "./resume"
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
    parser.add_argument("--channel", choices=CHANNEL_CHOICES, default="im",
                        help="投递渠道（im/email），用于生成投递第一句话，默认 im")
    parser.add_argument("--interview-duration", choices=DURATION_CHOICES, default="3min",
                        help="面试自我介绍时长（1min/3min），默认 3min")
    parser.add_argument("--skill-focus", choices=SKILL_FOCUS_CHOICES, default="balanced",
                        help="能力补充建议聚焦方向（gap/strength/balanced），默认 balanced")
    parser.add_argument("--project-level", choices=PROJECT_LEVEL_CHOICES, default="intermediate",
                        help="练习项目推荐难度（beginner/intermediate/advanced），默认 intermediate")



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

    p_batch = sub.add_parser("batch-assemble", help="批量组装简历（含扩展材料）")
    p_batch.add_argument("template_file", help="模板文件路径")
    p_batch.add_argument("personal_info_file", help="个人信息文件路径")
    p_batch.add_argument("jd_dir", help="JD 文件目录（内含 .md + .json 配对）")
    p_batch.add_argument("--fill-ext", default=".json", help="填充映射文件扩展名，默认 .json")
    p_batch.add_argument("--output-dir", default="./resume", help="输出目录")
    p_batch.add_argument("--clean-json", action="store_true", help="组装完成后删除所有 .json 中间文件")
    p_batch.add_argument("--logic-file", help="编写逻辑文件路径（可选）")
    p_batch.add_argument("--extras-content", help="预生成的扩展内容 JSON 文件路径，跳过 prompt 生成")
    _add_extras_arguments(p_batch)

    p_extras = sub.add_parser("generate-extras", help="生成扩展求职材料（投递第一句话、面试介绍等）")
    p_extras.add_argument("jd_file", help="岗位描述文件路径")
    p_extras.add_argument("personal_info_file", help="个人信息文件路径")
    p_extras.add_argument("--logic-file", help="编写逻辑文件路径（可选）")
    p_extras.add_argument("--output-dir", default="./resume", help="输出目录")
    p_extras.add_argument("--extras-content", help="预生成的扩展内容 JSON 文件路径，跳过 prompt 生成")
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
