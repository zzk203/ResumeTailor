import json
import os
import subprocess
import sys

from jinja2 import Environment, PackageLoader, select_autoescape

CHANNELS = [
    {"name": "boss", "label": "Boss直聘", "search_cmd": "boss search"},
    {"name": "lagou", "label": "拉勾", "search_cmd": "lagou search"},
    {"name": "liepin", "label": "猎聘", "search_cmd": "liepin search"},
]

_jinja_env = None


def _get_jinja_env():
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=PackageLoader("jd-hunter-skill.src", "prompt_templates"),
            autoescape=select_autoescape()
        )
    return _jinja_env


def infer_job_titles(personal_info: str, suggested_titles: list = None) -> list:
    if suggested_titles is not None:
        return suggested_titles if suggested_titles else [{"job_title": "软件工程师", "reason": "默认"}]

    env = _get_jinja_env()
    template = env.get_template("infer_jobs.jinja2")
    prompt = template.render(personal_info=personal_info)

    print(prompt, file=sys.stderr)
    print("---请在上面 prompt 的基础上，输出 JSON 数组（每个元素含 job_title 和 reason 字段）---", file=sys.stderr)

    try:
        response = input().strip()
        suggestions = json.loads(response)
        if not suggestions:
            raise ValueError("Empty suggestions")
    except (json.JSONDecodeError, ValueError):
        print("无法从个人信息推断岗位，请手动输入目标岗位名：", file=sys.stderr)
        manual = input().strip()
        return [{"job_title": manual, "reason": "用户手动输入"}]

    print("\n根据您的个人信息，推荐以下目标岗位：")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s['job_title']} - {s.get('reason', '')}")

    print("\n请确认（输入编号选择，或输入新岗位名，直接回车使用全部）：")
    choice = input().strip()
    if not choice:
        return suggestions
    if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
        return [suggestions[int(choice) - 1]]
    return [{"job_title": choice, "reason": "用户自定义"}]


def search_jd_on_channel(channel: dict, job_title: str, city: str = "", experience: str = "") -> list:
    query_parts = [job_title]
    if city:
        query_parts.append(city)
    if experience:
        query_parts.append(experience)
    query = " ".join(query_parts)

    try:
        result = subprocess.run(
            ["opencli"] + channel["search_cmd"].split() + [query],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"{channel['label']} 搜索失败: {result.stderr.strip()}", file=sys.stderr)
            return []

        listings = json.loads(result.stdout)
        if not listings:
            print(f"{channel['label']} 未找到匹配 JD")
            return []
        return listings
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError):
        print(f"{channel['label']} 搜索异常，已跳过", file=sys.stderr)
        return []


def fetch_jd_detail(url: str) -> str:
    try:
        result = subprocess.run(
            ["opencli", "browser", "fetch", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ""
