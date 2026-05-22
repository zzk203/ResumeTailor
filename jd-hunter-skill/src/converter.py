import os

from .extractor import extract_jd_fields, save_structured_jd


def convert_raw_jd(raw_content: str, channel_name: str = "", url: str = "") -> dict:
    return extract_jd_fields(raw_content, channel_name, url)


def convert_and_save(raw_content: str, channel_name: str = "", url: str = "",
                     raw_base: str = "jd_raw", structured_base: str = "jd") -> dict:
    fields = convert_raw_jd(raw_content, channel_name, url)
    output_path = save_structured_jd(fields, structured_base)
    return {
        "fields": fields,
        "output_path": output_path,
    }
