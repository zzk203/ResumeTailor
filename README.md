# ResumeTailor

简历自动定制工具 + JD 自动猎取。两个独立 skill 包构成完整管线。

## 项目结构

- `resume-matcher-skill/` — 简历匹配生成（模板 → 简历），含 extras 扩展材料管线
- `jd-hunter-skill/` — JD 自动猎取（搜索 → 评分 → 结构化）
- `openspec/` — OpenSpec spec-driven 工作区（实验性）
- `doc/` — 设计文档（gitignored）

## 命令

```bash
# 安装依赖（两包独立，依赖相同）
pip install -r resume-matcher-skill/requirements.txt
pip install -r jd-hunter-skill/requirements.txt

# 运行测试（从项目根执行）
python -m pytest resume-matcher-skill/tests/ -v
python -m pytest jd-hunter-skill/tests/ -v

# resume-matcher CLI
python -m resume-matcher-skill.src.tools --help
python -m resume-matcher-skill.src.tools parse-jd <jd_file>
python -m resume-matcher-skill.src.tools parse-template <template_file>
python -m resume-matcher-skill.src.tools assemble <template> <fill_json> <name> <job> <company>
python -m resume-matcher-skill.src.tools batch-assemble <template> <personal> <jd_dir> [--clean-json]
python -m resume-matcher-skill.src.tools generate-extras <jd> <personal> [--logic-file] [--extras first-msg,interview-intro,skill-gap,project-recommend]

# jd-hunter CLI
python -m jd-hunter-skill.src.main --help
python -m jd-hunter-skill.src.main hunt personal_info.md [--city] [--experience] [--jd-file] [--threshold/-t <分>]
python -m jd-hunter-skill.src.main search <channel> <job_title> [--city] [--experience]
python -m jd-hunter-skill.src.main score <jd_file...> <personal_info> [-t <分>]
python -m jd-hunter-skill.src.main extract <raw_jd> [--channel] [--url]
python -m jd-hunter-skill.src.main index [--jd-dir]
```

## 核心约定

- 模板标签: `<!-- fill:字段名 -->内容<!-- /fill:字段名 -->`，非 fill 内容自动保留（不再使用 `fixed` 标签）
- JD 文件必须有 `岗位名称：...` 和 `公司：...`
- 个人信息必须有 `姓名：...`
- 输出文件: `{姓名}-{岗位}-{公司}.md`，冲突加数字后缀
- 输出目录默认 `./resume`（若不存在自动创建）
- 无 lint/typecheck 配置，仅 pytest

## Prompts 与外部 LLM

- 两包均用 `jinja2` + `PackageLoader` 加载 prompt 模板
  - resume-matcher: `PackageLoader("resume-matcher-skill.src", "prompt_templates")`
  - jd-hunter: `PackageLoader("jd-hunter-skill.src", "prompt_templates")`
- LLM 调用通过 当前agent自己生成

## extras 扩展材料管线

resume-matcher 提供 4 种扩展材料生成（`generate-extras` 子命令）：
- `first-msg` — 投递第一句话（支持 `--channel im|email`）
- `interview-intro` — 面试自我介绍（支持 `--interview-duration 1min|3min`）
- `skill-gap` — 能力补充建议（支持 `--skill-focus gap|strength|balanced`）
- `project-recommend` — 练习项目推荐（支持 `--project-level beginner|intermediate|advanced`）

使用 `--extras` 逗号分隔可选子集，`--no-extras` 关闭。

## batch-assemble 工作流

`batch-assemble` 遍历 `jd_dir` 下所有 `.md` 文件，自动匹配同名 `.json` 填充映射文件。`--clean-json` 在组装完成后删除所有 `.json` 中间文件。

## 测试

- 仅 pytest，无其他框架
- 测试文件在各自 skill 包的 `tests/` 目录下
- 从项目根执行（`python -m pytest ...`）
