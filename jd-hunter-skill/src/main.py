import argparse
import json
import os
import sys

from .hunter import CHANNELS, infer_job_titles, search_jd_on_channel, fetch_jd_detail
from .scorer import SCORE_THRESHOLD, score_jd_batch, filter_high_score, score_and_filter, save_raw_jd
from .extractor import extract_jd_fields, save_structured_jd
from .indexer import generate_jd_index, get_index_report


def cmd_hunt(args):
    with open(args.personal_info, "r", encoding="utf-8") as f:
        personal_info = f.read()

    threshold = args.threshold

    print("\n=== 步骤1: 推断目标岗位 ===")
    job_titles = infer_job_titles(personal_info)
    print(f"选定岗位: {[j['job_title'] for j in job_titles]}")

    all_raw_jds = []

    if args.jd_file:
        for jd_path in args.jd_file:
            with open(jd_path, "r", encoding="utf-8") as f:
                content = f.read()
            name = os.path.splitext(os.path.basename(jd_path))[0]
            all_raw_jds.append({
                "content": content,
                "channel": "manual",
                "url": "",
                "company": name.split("-")[0] if "-" in name else "",
                "job_title": name.split("-")[1] if "-" in name else name,
            })
    else:
        print("\n=== 步骤2: 搜索 JD ===")
        for job in job_titles:
            title = job["job_title"]
            for channel in CHANNELS:
                print(f"\n在 {channel['label']} 搜索「{title}」...", file=sys.stderr)
                listings = search_jd_on_channel(channel, title, args.city, args.experience)
                for item in listings:
                    detail = fetch_jd_detail(item.get("url", ""))
                    if detail:
                        item["content"] = detail
                        item["channel"] = channel["name"]
                        all_raw_jds.append(item)

    if not all_raw_jds:
        print("\n无 JD 数据。可使用 --jd-file 传入原始 JD 文件，或直接运行 score/extract/index 子命令。")
        return

    print(f"\n=== 步骤3: JD 评分（共 {len(all_raw_jds)} 条，阈值 ≥{threshold}）===")
    for channel in CHANNELS:
        channel_jds = [jd for jd in all_raw_jds if jd.get("channel") == channel["name"]]
        if not channel_jds:
            print(f"{channel['label']}: 0 条")
            continue

        high_score = score_and_filter(channel_jds, personal_info, threshold)

        for jd in high_score:
            save_raw_jd(jd, channel["name"])

        print(f"{channel['label']}: 匹配 {len(high_score)} 条")

    manual_jds = [jd for jd in all_raw_jds if jd.get("channel") == "manual"]
    if manual_jds:
        high_score = score_and_filter(manual_jds, personal_info, threshold)
        for jd in high_score:
            save_raw_jd(jd, "manual")
        print(f"手动输入: 匹配 {len(high_score)} 条")

    print("\n=== 步骤4: 提取结构化字段 ===")
    structured_files = []
    for jd in all_raw_jds:
        if jd.get("score", 0) >= threshold:
            fields = extract_jd_fields(
                jd.get("content", ""),
                channel_name=jd.get("channel", ""),
                url=jd.get("url", "")
            )
            filepath = save_structured_jd(fields, match_score=jd.get("score"))
            structured_files.append(filepath)
            print(f"  结构化: {filepath}")

    print(f"\n=== 步骤5: 生成索引 ===")
    index_path = generate_jd_index()
    report = get_index_report()

    result = {
        "success": True,
        "total_scored": len(all_raw_jds),
        "total_structured": len(structured_files),
        "index_path": index_path,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_search(args):
    channel = next((c for c in CHANNELS if c["name"] == args.channel), None)
    if not channel:
        print(json.dumps({"success": False, "message": f"未知渠道: {args.channel}"}, ensure_ascii=False))
        return

    listings = search_jd_on_channel(channel, args.job_title, args.city, args.experience)
    print(json.dumps(listings, ensure_ascii=False, indent=2))


def cmd_score(args):
    with open(args.personal_info, "r", encoding="utf-8") as f:
        personal_info = f.read()

    jd_list = []
    for jd_path in args.jd_file:
        with open(jd_path, "r", encoding="utf-8") as f:
            content = f.read()
        name = os.path.splitext(os.path.basename(jd_path))[0]
        jd_list.append({
            "content": content,
            "company": name.split("-")[0] if "-" in name else "",
            "job_title": name.split("-")[1] if "-" in name else name,
        })

    scored = score_jd_batch(jd_list, personal_info)
    threshold = args.threshold
    if threshold is not None:
        filtered = [jd for jd in scored if jd.get("score", 0) >= threshold]
        print(f"阈值 ≥{threshold}: {len(filtered)}/{len(scored)} 条匹配\n")
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(scored, ensure_ascii=False, indent=2))


def cmd_extract(args):
    with open(args.jd_file, "r", encoding="utf-8") as f:
        raw_content = f.read()

    fields = extract_jd_fields(raw_content, args.channel or "", args.url or "")
    filepath = save_structured_jd(fields)
    result = {"fields": fields, "output_path": filepath}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_index(args):
    index_path = generate_jd_index(args.jd_dir or "jd")
    report = get_index_report(args.jd_dir or "jd")
    report["index_path"] = index_path
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="JD Hunter - 自动搜集筛选结构化 JD")
    sub = parser.add_subparsers(dest="command")

    p_hunt = sub.add_parser("hunt", help="执行完整 JD 猎取流程（交互式）")
    p_hunt.add_argument("personal_info", help="个人信息文件路径")
    p_hunt.add_argument("--city", default="", help="目标城市")
    p_hunt.add_argument("--experience", default="", help="经验年限")
    p_hunt.add_argument("--jd-file", action="append", help="直接传入原始 JD 文件（可多次使用，跳过搜索步骤）")
    p_hunt.add_argument("-t", "--threshold", type=int, default=SCORE_THRESHOLD, help=f"评分阈值（默认 {SCORE_THRESHOLD} 分）")

    p_search = sub.add_parser("search", help="在指定渠道搜索 JD")
    p_search.add_argument("channel", choices=[c["name"] for c in CHANNELS], help="渠道名称")
    p_search.add_argument("job_title", help="岗位名称")
    p_search.add_argument("--city", default="", help="城市")
    p_search.add_argument("--experience", default="", help="经验年限")

    p_score = sub.add_parser("score", help="JD 匹配度评分（交互式）")
    p_score.add_argument("jd_file", nargs="+", help="JD 文件路径（可多个）")
    p_score.add_argument("personal_info", help="个人信息文件路径")
    p_score.add_argument("-t", "--threshold", type=int, help=f"评分阈值（可选，指定后只输出匹配结果）")

    p_extract = sub.add_parser("extract", help="提取 JD 结构化字段（交互式）")
    p_extract.add_argument("jd_file", help="原始 JD 文件路径")
    p_extract.add_argument("--channel", default="", help="来源渠道")
    p_extract.add_argument("--url", default="", help="JD 详情页 URL")

    p_index = sub.add_parser("index", help="生成 JD 索引文件")
    p_index.add_argument("--jd-dir", default="jd", help="JD 文件目录")

    args = parser.parse_args()
    if args.command == "hunt":
        cmd_hunt(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "score":
        cmd_score(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "index":
        cmd_index(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
