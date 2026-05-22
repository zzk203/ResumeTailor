import os
import re


def _parse_jd_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    fields = {}
    fields["文件名"] = os.path.basename(filepath)

    meta_match = re.search(r'^- jd来源：(.+)$', content, re.MULTILINE)
    fields["渠道"] = meta_match.group(1).strip() if meta_match else "未知"

    channel_match = re.search(r'^- jd投递渠道：(.+)$', content, re.MULTILINE)
    fields["投递渠道"] = channel_match.group(1).strip() if channel_match else "未知"

    company_match = re.search(r'^# (.+) - (.+)$', content, re.MULTILINE)
    fields["公司"] = company_match.group(1).strip() if company_match else "未知"
    fields["岗位"] = company_match.group(2).strip() if company_match else "未知"

    score_match = re.search(r'^- 匹配度：(.+)$', content, re.MULTILINE)
    fields["匹配度"] = score_match.group(1).strip() if score_match else "N/A"

    return fields


def generate_jd_index(jd_dir: str = "jd", output_path: str = "jd/index.md") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(jd_dir):
        content = """# JD 索引

暂无 JD 数据
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    md_files = sorted([
        f for f in os.listdir(jd_dir)
        if f.endswith(".md") and f != "index.md"
    ])

    if not md_files:
        content = """# JD 索引

暂无 JD 数据
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    entries = []
    for fname in md_files:
        filepath = os.path.join(jd_dir, fname)
        entry = _parse_jd_file(filepath)
        entries.append(entry)

    lines = ["# JD 索引", "", "| 文件名 | 公司 | 岗位 | 渠道 | 匹配度 | 投递渠道 |",
             "|--------|------|------|------|--------|----------|"]
    for e in entries:
        lines.append(f"| {e['文件名']} | {e['公司']} | {e['岗位']} | {e['渠道']} | {e['匹配度']} | {e['投递渠道']} |")

    content = "\n".join(lines) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def get_index_report(jd_dir: str = "jd", raw_base: str = "jd_raw") -> dict:
    channel_counts = {}
    if os.path.exists(raw_base):
        for channel in os.listdir(raw_base):
            channel_dir = os.path.join(raw_base, channel)
            if os.path.isdir(channel_dir):
                count = len([f for f in os.listdir(channel_dir) if f.endswith(".md")])
                channel_counts[channel] = count

    structured_count = 0
    if os.path.exists(jd_dir):
        structured_count = len([
            f for f in os.listdir(jd_dir)
            if f.endswith(".md") and f != "index.md"
        ])

    return {
        "channel_counts": channel_counts,
        "total_raw": sum(channel_counts.values()),
        "total_structured": structured_count,
        "index_path": os.path.join(jd_dir, "index.md") if structured_count > 0 else "",
    }
