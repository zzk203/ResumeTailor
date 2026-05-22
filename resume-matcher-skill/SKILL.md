---
name: resume-matcher
description: 根据简历模板、个人经历和岗位描述自动生成定制简历。用户提供模板（含 fill 填充标签）、个人信息文件、JD 文件，Agent 自动匹配并生成个性化简历。
---

# 简历-岗位匹配生成器 (Resume Matcher)

根据 JD 和个人信息，按模板自动生成匹配的简历文件。

## 模板标签规范

模板使用 Markdown 注释作为标签，对渲染无影响。

**只需标记需要替换的部分**，其余内容自动保留。不再需要手动添加 `fixed` 标签。

### 填充标签（会被替换）
```
<!-- fill:字段名 --> 占位内容（可选） <!-- /fill:字段名 -->
```
Agent 会用匹配岗位后生成的内容**完全替换该标签块**（包括起止注释）。

### 字段名约定
推荐：`姓名`、`联系方式`、`教育经历`、`工作经历`、`项目经历`、`技能` 等。
字段名不能重复，如有重复则所有同名填充块用同一内容替换。

## 输入输出规格

### 输入
| 输入项 | 必须 | 格式 | 说明 |
|--------|------|------|------|
| 简历模板 | 是 | .md | 按上述标签规范编写 |
| 个人信息文件 | 是 | .md/.txt | 须在显眼处有 `姓名：XXX` |
| 岗位描述（JD） | 是 | .md | 须包含 `岗位名称：XXX` 和 `公司：XXX` |
| 编写逻辑文件 | 否 | .md/.txt | 描述如何组织填充内容 |

### 输出
- 简历 `.md` 文件，文件名：`{姓名}-{岗位名称}-{公司名}.md`
- 扩展材料 `.md` 文件（默认生成），文件名：`{姓名}-{岗位名称}-{公司名}-extras.md`
- 输出目录默认 `./resume`（若不存在自动创建）

## 交互流程

1. 触发 Skill，要求用户提供 **岗位描述文件 (JD)**
2. 提取 JD 中的 `岗位名称` 和 `公司`，若失败则询问用户
3. 接收 **简历模板**
4. 接收 **个人信息文件**，提取 `姓名`，若失败则询问
5. 询问是否有 **编写逻辑文件**，有则接收，无则跳过
6. **解析模板** 获取所有 `fill` 字段名列表（读取模板文件，用正则提取）
7. **循环生成填充文本**：对每个字段，结合 JD、个人信息、编写逻辑调用 LLM 生成专业化文本
8. 收集所有字段填充内容构成映射
9. **组装简历**：用 `fill_mapping` 替换模板中的 fill 标签块，生成简历文件
10. **生成扩展材料**：自动为每个 JD 生成 4 种扩展材料（投递第一句话、面试自我介绍、能力补充建议、练习项目推荐），使用 `generate-extras` 逻辑，写入 `*-extras.md`
11. **清理中间文件**：删除 jd 目录下所有 `.json` 中间文件（`rm jd_dir/*.json`），避免残留
12. **处理结果**：成功则发送所有文件，失败则提示错误并引导修正

### 生成填充内容的 Prompt 模板

对每个 fill 字段，使用以下 prompt（模板文件 `fill_section.jinja2`）调用 LLM：

```
你是一位专业简历优化师。请根据以下信息生成简历中"{{ field_name }}"模块的内容。

【目标岗位描述】
{{ jd_content }}

【个人全部经历与信息】
{{ personal_info }}

【编写逻辑要求】
{{ writing_logic }}

任务：只输出填充文本，不含注释、不增加模块标题，直接为简历部分准备文本。
```

其中 `writing_logic` 默认值为："使用 STAR 法则，突出与岗位最相关的经历，专业简洁，纯文本段落。"
若用户提供了`编写逻辑.md/writing_logic.md`，优先使用用户提供的

## extras 扩展材料管线

`batch-assemble` **默认自动生成** 4 种扩展材料。也可通过 `generate-extras` 子命令单独调用。

扩展材料类型：
- **`first-msg`** — 投递第一句话（支持 `--channel im|email`）
- **`interview-intro`** — 面试自我介绍（支持 `--interview-duration 1min|3min`）
- **`skill-gap`** — 能力补充建议（支持 `--skill-focus gap|strength|balanced`）
- **`project-recommend`** — 练习项目推荐（支持 `--project-level beginner|intermediate|advanced`）

使用 `--extras first-msg,interview-intro` 逗号分隔可选子集，`--no-extras` 关闭。

每个扩展材料有独立的 prompt 模板：
- `first_message.jinja2`
- `interview_intro.jinja2`
- `skill_gap.jinja2`
- `project_recommend.jinja2`

## CLI 使用

```bash
# 解析 JD 提取岗位/公司
python -m resume-matcher-skill.src.tools parse-jd <jd_file>

# 解析模板提取 fill 字段
python -m resume-matcher-skill.src.tools parse-template <template_file>

# 单份简历组装
python -m resume-matcher-skill.src.tools assemble <template> <fill_json> <name> <job> <company> [--output-dir]

# 批量组装 + 默认生成扩展材料（jd_dir 下 .md + .json 配对）
python -m resume-matcher-skill.src.tools batch-assemble <template> <personal> <jd_dir> [--logic-file] [--output-dir ./resume] [--clean-json] [--no-extras] [--extras first-msg,interview-intro] [--channel im] [--interview-duration 3min]

# 单独生成扩展材料
python -m resume-matcher-skill.src.tools generate-extras <jd> <personal> [--logic-file] [--extras first-msg,interview-intro,skill-gap,project-recommend] [--channel] [--interview-duration] [--skill-focus] [--project-level]
```

## 可用工具

Skill 目录提供了 Python 辅助脚本供调用：

### `src/parser.py`
- `extract_name(text)` — 从个人信息中提取姓名
- `extract_job_and_company(jd_text)` — 从 JD 文本提取岗位名称和公司
- `extract_fill_fields(template)` — 从模板提取所有 fill 字段名列表
- `extract_fixed_fields(template)` — 从模板提取所有 fixed 字段名列表（兼容旧语法）

### `src/assembler.py`
- `generate_resume_file(template_content, fill_mapping, user_name, job_title, company, output_dir)` — 将填充内容填入模板，生成最终简历文件
- `generate_extras_file(user_name, job_title, company, extras_map, output_dir)` — 组装扩展材料文件（投递信、面试介绍等）

### `src/tools.py`
CLI 入口，提供所有命令行子命令。

### `src/prompt_templates/`
Jinja2 prompt 模板目录，通过 `PackageLoader("resume-matcher-skill.src", "prompt_templates")` 加载：
- `fill_section.jinja2` — 简历字段填充 prompt
- `first_message.jinja2` — 投递第一句话 prompt
- `interview_intro.jinja2` — 面试自我介绍 prompt
- `skill_gap.jinja2` — 能力补充建议 prompt
- `project_recommend.jinja2` — 练习项目推荐 prompt

## 异常处理

| 场景 | 处理方式 |
|------|----------|
| 个人信息无姓名 | 提示用户手动提供 |
| JD 无岗位/公司 | 分别确认并补充 |
| 模板标签未闭合 | 返回错误，引导用户修正 |
| 填充映射缺少字段 | 提示内部错误并终止 |
| 输出文件重名 | 自动添加数字后缀 |
| 缺少输入文件 | 在交互步骤中直接提示，不进入生成 |

## 安全与隐私

- 用户上传文件仅在会话内存处理，不记录日志，不持久存储
- 提醒用户审阅生成的简历以确保准确性
