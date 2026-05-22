import os
import re
from typing import Dict


class TemplateParseError(Exception):
    pass


def generate_resume_file(
    template_content: str,
    fill_mapping: Dict[str, str],
    user_name: str,
    job_title: str,
    company: str,
    output_dir: str = "./resume"
) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    def replace_fill(match):
        field = match.group(1).strip()
        if field not in fill_mapping:
            raise TemplateParseError(f"缺少字段 '{field}' 的填充内容")
        return fill_mapping[field]

    fill_pattern = r'<!--\s*fill:([^\s>]+)\s*-->.*?<!--\s*/fill:\1\s*-->'
    try:
        filled = re.sub(fill_pattern, replace_fill, template_content, flags=re.DOTALL)
    except (TemplateParseError, re.error) as e:
        return {"success": False, "message": "填充替换失败", "errors": [str(e)], "file_path": None}

    unmatched = re.findall(r'(<!--\s*(fill|/fill):[^>]*-->)', filled)
    if unmatched:
        tags = [m[0] for m in unmatched]
        return {"success": False, "message": f"模板中存在未匹配的填充标签: {tags}", "errors": ["标签闭合错误"], "file_path": None}

    def sanitize(s: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', '-', s).strip()

    base = f"{sanitize(user_name)}-{sanitize(job_title)}-{sanitize(company)}"
    filename = f"{base}.md"
    counter = 1
    while os.path.exists(os.path.join(output_dir, filename)):
        filename = f"{base}_{counter}.md"
        counter += 1

    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(filled)

    return {"success": True, "message": "简历生成成功", "file_path": filepath, "errors": []}


def generate_extras_file(
    user_name: str,
    job_title: str,
    company: str,
    extras_map: Dict[str, str],
    output_dir: str = "./resume"
) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    def sanitize(s: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', '-', s).strip()

    base = f"{sanitize(user_name)}-{sanitize(job_title)}-{sanitize(company)}-extras"
    filename = f"{base}.md"
    counter = 1
    while os.path.exists(os.path.join(output_dir, filename)):
        filename = f"{base}_{counter}.md"
        counter += 1

    title_map = {
        "first-msg": "投递第一句话",
        "interview-intro": "面试个人介绍",
        "skill-gap": "能力补充建议",
        "project-recommend": "练习项目推荐",
    }

    sections = []
    for key in ["first-msg", "interview-intro", "skill-gap", "project-recommend"]:
        if key in extras_map:
            sections.append(f"# {title_map[key]}\n\n{extras_map[key].strip()}\n")

    content = "\n".join(sections)

    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return {"success": True, "message": "扩展文件生成成功", "file_path": filepath, "errors": []}
