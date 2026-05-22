import re
from typing import List, Tuple


def extract_name(text: str) -> str:
    match = re.search(r'\*{0,2}姓名\*{0,2}[:：]\s*(.+)', text)
    if not match:
        return ""
    name = match.group(1).strip()
    name = name.strip('*')
    return name


def extract_job_and_company(jd_text: str) -> Tuple[str, str]:
    job = re.search(r'岗位名称[:：]\s*(.+)', jd_text)
    comp = re.search(r'公司[:：]\s*(.+)', jd_text)
    return (job.group(1).strip() if job else "", comp.group(1).strip() if comp else "")


def extract_fill_fields(template: str) -> List[str]:
    pattern = r'<!--\s*fill:([^\s>]+)\s*-->'
    matches = re.findall(pattern, template)
    fields = []
    seen = set()
    for m in matches:
        field = m.strip()
        if field not in seen:
            fields.append(field)
            seen.add(field)
    return fields


def extract_fixed_fields(template: str) -> List[str]:
    pattern = r'<!--\s*fixed:(.*?)\s*-->'
    matches = re.findall(pattern, template)
    fields = []
    seen = set()
    for m in matches:
        field = m.strip()
        if field not in seen:
            fields.append(field)
            seen.add(field)
    return fields
