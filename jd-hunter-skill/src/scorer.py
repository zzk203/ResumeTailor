import json
import os
import sys

from jinja2 import Environment, PackageLoader, select_autoescape

_jinja_env = None

SCORE_THRESHOLD = 7


def _get_jinja_env():
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=PackageLoader("jd-hunter-skill.src", "prompt_templates"),
            autoescape=select_autoescape()
        )
    return _jinja_env


def score_jd_batch(jd_list: list, personal_info: str) -> list:
    env = _get_jinja_env()
    template = env.get_template("score_jd.jinja2")
    scored = []

    for i, jd in enumerate(jd_list):
        prompt = template.render(jd_content=jd.get("content", ""), personal_info=personal_info)
        print(f"\n========== JD {i+1}/{len(jd_list)} 评分 prompt ==========", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print(f"========== 请输出 JSON 评分结果 ==========", file=sys.stderr)

        try:
            response = input().strip()
            result = json.loads(response)
            score = int(result.get("score", 0))
        except (json.JSONDecodeError, ValueError):
            score = 0

        jd["score"] = score
        scored.append(jd)

    return scored


def filter_high_score(scored_list: list, threshold: int = SCORE_THRESHOLD) -> list:
    return [jd for jd in scored_list if jd.get("score", 0) >= threshold]


def save_raw_jd(jd: dict, channel_name: str, output_base: str = "jd_raw") -> str:
    company = jd.get("company", "未知公司")
    position = jd.get("job_title", "未知岗位")
    safe_name = f"{company}-{position}".replace("/", "-").replace("\\", "-")
    channel_dir = os.path.join(output_base, channel_name)
    os.makedirs(channel_dir, exist_ok=True)

    filepath = os.path.join(channel_dir, f"{safe_name}.md")
    if os.path.exists(filepath):
        idx = 1
        while os.path.exists(os.path.join(channel_dir, f"{safe_name}-{idx}.md")):
            idx += 1
        filepath = os.path.join(channel_dir, f"{safe_name}-{idx}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(jd.get("content", ""))

    return filepath
