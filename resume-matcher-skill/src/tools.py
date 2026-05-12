import argparse
import json
import sys

from .parser import extract_job_and_company, extract_name, extract_fill_fields
from .assembler import generate_resume_file


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


def main():
    parser = argparse.ArgumentParser(description="简历-岗位匹配生成器工具集")
    sub = parser.add_subparsers(dest="command")

    p_jd = sub.add_parser("parse-jd", help="从 JD 文件提取岗位名称和公司")
    p_jd.add_argument("jd_file", help="岗位描述文件路径")

    p_tmpl = sub.add_parser("parse-template", help="从模板提取 fill 字段列表")
    p_tmpl.add_argument("template_file", help="模板文件路径")

    p_assemble = sub.add_parser("assemble", help="组装简历")
    p_assemble.add_argument("template_file", help="模板文件路径")
    p_assemble.add_argument("fill_mapping_json", help="填充映射 JSON 字符串")
    p_assemble.add_argument("user_name", help="用户姓名")
    p_assemble.add_argument("job_title", help="岗位名称")
    p_assemble.add_argument("company", help="公司名称")
    p_assemble.add_argument("--output-dir", default="./output", help="输出目录")

    args = parser.parse_args()
    if args.command == "parse-jd":
        cmd_parse_jd(args)
    elif args.command == "parse-template":
        cmd_parse_template(args)
    elif args.command == "assemble":
        cmd_assemble(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
