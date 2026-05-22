# ResumeTailor

简历自动定制工具 + JD 自动猎取。三个 skill 包构成完整管线。

## 项目结构

- `resume-matcher-skill/` — 简历匹配生成（模板 → 简历），含 extras 扩展材料管线
- `jd-hunter-skill/` — JD 自动猎取（搜索 → 评分 → 结构化），通过 opencli 搜 Boss/拉勾/猎聘
- `resume-pipeline-skill/` — 编排层，统合 jd-hunter 和 resume-matcher，根据意图选择路径

## 命令

```bash
pip install -r resume-matcher-skill/requirements.txt   # jinja2 + pytest
pip install -r jd-hunter-skill/requirements.txt          # 同上（依赖相同）

# 测试（从项目根执行）
python -m pytest resume-matcher-skill/tests/ -v
python -m pytest jd-hunter-skill/tests/ -v

# resume-matcher CLI
python -m resume-matcher-skill.src.tools parse-jd <jd_file>
python -m resume-matcher-skill.src.tools parse-template <template_file>
python -m resume-matcher-skill.src.tools assemble <template> <fill_json> <name> <job> <company>
python -m resume-matcher-skill.src.tools batch-assemble <template> <personal> <jd_dir> [--logic-file] [--clean-json] [--no-extras]
python -m resume-matcher-skill.src.tools generate-extras <jd> <personal> [--logic-file] [--extras first-msg,...]

# jd-hunter CLI
python -m jd-hunter-skill.src.main hunt personal_info.md [--city] [--experience] [--jd-file] [-t <分>]
python -m jd-hunter-skill.src.main search <channel> <job_title> [--city] [--experience]
python -m jd-hunter-skill.src.main score <jd_file...> <personal_info> [-t <分>]
python -m jd-hunter-skill.src.main extract <raw_jd> [--channel] [--url]
python -m jd-hunter-skill.src.main index [--jd-dir]
```

## 核心约定

- 模板标签: `<!-- fill:字段名 -->内容<!-- /fill:字段名 -->`，非 fill 内容自动保留
- JD 文件必须有 `岗位名称：...` 和 `公司：...`
- 个人信息必须有 `姓名：...`
- 输出文件: `{姓名}-{岗位}-{公司}.md`，冲突加数字后缀
- 输出目录默认 `./resume`（自动创建）；jd-hunter 输出到 `./jd/`
- 无 lint/typecheck 配置，仅 pytest

## 编程注意事项

- jd-hunter 的 `infer_job_titles()` 通过 `print(prompt, file=sys.stderr) + input()` 与 LLM 交互 — 在 agent 上下文中需要直接生成 prompt 而非读 stdin
- jd-hunter 用 opencli 子进程搜 JD：`boss search`、`lagou search`、`liepin search`
- 两包的 prompt 模板通过 `jinja2.PackageLoader` 加载，包名对应各自 src 目录
- `resume-pipeline` skill 无 Python 代码，纯 SKILL.md 编排；通过 `skill("jd-hunter")` / `skill("resume-matcher")` 委托子 skill

