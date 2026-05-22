# ResumeTailor

简历自动定制工具 + JD 自动猎取。两个独立 skill 包构成完整管线。

## 项目结构

- `resume-matcher-skill/` — 简历匹配生成（模板 → 简历）
- `jd-hunter-skill/` — JD 自动猎取（搜索 → 评分 → 结构化）
- `openspec/` — openspec workspace（spec-driven 模式）
- `doc/` — 设计文档（gitignored）

## 命令

```
# 安装依赖（两个包独立）
pip install -r resume-matcher-skill/requirements.txt
pip install -r jd-hunter-skill/requirements.txt

# 测试
python -m pytest resume-matcher-skill/tests/ -v
python -m pytest jd-hunter-skill/tests/ -v

# CLI
python -m resume-matcher-skill.src.tools --help
python -m jd-hunter-skill.src.main --help
```

## 核心约定

- 模板标签: `<!-- fill:字段名 -->内容<!-- /fill:字段名 -->`，非 fill 内容自动保留
- JD 文件必须有 `岗位名称：...` 和 `公司：...`
- 个人信息必须有 `姓名：...`
- 输出文件命名: `{姓名}-{岗位}-{公司}.md`，冲突加数字后缀
- 无 lint/typecheck 配置，仅 pytest

## skill 结构

每个 skill 包采用 `src/` + `tests/` 布局，根目录有 `SKILL.md`（YAML frontmatter + Markdown，OpenCode 识别技能的依据）。依赖 `jinja2` 渲染 prompt 模板，用 `PackageLoader("src", "prompt_templates")` 加载。测试用 `python -m pytest`（从项目根运行）。LLM 调用通过 subprocess 外部工具完成，非 SDK 直连。
