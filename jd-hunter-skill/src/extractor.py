import json
import os
import re
import sys

from jinja2 import Environment, PackageLoader, select_autoescape

_jinja_env = None

DEFAULT_FIELDS = {
    "jd来源": "未知",
    "jd投递渠道": "未知",
    "jd投递url": "未知",
    "岗位名称": "未知",
    "公司": "未知",
    "岗位职责": "未知",
    "任职要求": "未知",
    "加分项": "",
}

CHANNEL_MAP = {
    "boss": "boss直聘",
    "lagou": "拉勾",
    "liepin": "猎聘",
}

CHANNEL_DELIVERY = {
    "boss": "im",
    "lagou": "im",
    "liepin": "email",
}


def _get_jinja_env():
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=PackageLoader("jd-hunter-skill.src", "prompt_templates"),
            autoescape=select_autoescape()
        )
    return _jinja_env


def infer_source_metadata(raw_content: str, channel_name: str = "", url: str = "") -> dict:
    source = CHANNEL_MAP.get(channel_name, channel_name or "未知")
    delivery = CHANNEL_DELIVERY.get(channel_name, "未知")

    if not url and raw_content:
        urls = re.findall(r'https?://[^\s"\'<>]+', raw_content)
        url = urls[0] if urls else "未知"

    return {
        "jd来源": source,
        "jd投递渠道": delivery,
        "jd投递url": url,
    }


def extract_jd_fields(raw_content: str, channel_name: str = "", url: str = "", fields_override: dict = None) -> dict:
    fields = dict(DEFAULT_FIELDS)

    if fields_override is not None:
        fields.update({k: v for k, v in fields_override.items() if v and v != "未知"})
        metadata = infer_source_metadata(raw_content, channel_name, url)
        for key, value in metadata.items():
            if fields.get(key) in ("未知", None, ""):
                fields[key] = value
        return fields

    env = _get_jinja_env()
    template = env.get_template("extract_fields.jinja2")
    prompt = template.render(raw_jd=raw_content)

    print(prompt, file=sys.stderr)
    print("---请在上方 prompt 的基础上，输出 JSON 结构化字段---", file=sys.stderr)

    try:
        response = input().strip()
        extracted = json.loads(response)
        fields.update({k: v for k, v in extracted.items() if v and v != "未知"})
    except (json.JSONDecodeError):
        pass

    metadata = infer_source_metadata(raw_content, channel_name, url)
    for key, value in metadata.items():
        if fields.get(key) in ("未知", None, ""):
            fields[key] = value

    return fields


def save_structured_jd(fields: dict, output_base: str = "jd", match_score: int = None) -> str:
    os.makedirs(output_base, exist_ok=True)

    company = fields.get("公司", "未知公司")
    position = fields.get("岗位名称", "未知岗位")
    safe_name = f"{company}-{position}".replace("/", "-").replace("\\", "-")

    filepath = os.path.join(output_base, f"{safe_name}.md")
    if os.path.exists(filepath):
        idx = 1
        while os.path.exists(os.path.join(output_base, f"{safe_name}-{idx}.md")):
            idx += 1
        filepath = os.path.join(output_base, f"{safe_name}-{idx}.md")

    score_line = ""
    if match_score is not None:
        score_line = "- 匹配度：" + str(match_score) + "\n"

    bonus_section = ""
    if fields.get("加分项"):
        bonus_section = "\n## 加分项\n\n" + fields["加分项"] + "\n"

    content = f"""# {fields['公司']} - {fields['岗位名称']}

- jd来源：{fields['jd来源']}
- jd投递渠道：{fields['jd投递渠道']}
- jd投递url：{fields['jd投递url']}
- 岗位名称：{fields['岗位名称']}
- 公司：{fields['公司']}
{score_line}## 岗位职责

{fields['岗位职责']}

## 任职要求

{fields['任职要求']}
{bonus_section}"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
