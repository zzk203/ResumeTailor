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
- 单个 `.md` 文件，文件名：`{姓名}-{岗位名称}-{公司名}.md`
- 放在当前会话的可访问目录，发送给用户

## 交互流程

1. 触发 Skill，要求用户提供 **岗位描述文件 (JD)**
2. 提取 JD 中的 `岗位名称` 和 `公司`，若失败则询问用户
3. 接收 **简历模板**
4. 接收 **个人信息文件**，提取 `姓名`，若失败则询问
5. 询问是否有 **编写逻辑文件**，有则接收，无则跳过
6. **解析模板** 获取所有 `fill` 字段名列表（读取模板文件，用正则提取）
7. **循环生成填充文本**：对每个字段，结合 JD、个人信息、编写逻辑调用 LLM 生成专业化文本
8. 收集所有字段填充内容构成映射
9. **组装简历**：用 `fill_mapping` 替换模板中的 fill 标签块，生成文件
10. **清理中间文件**：删除 jd 目录下所有 `.json` 中间文件（`rm jd_dir/*.json`），避免残留
11. 处理结果：成功则发送文件，失败则提示错误并引导修正

### 生成填充内容的 Prompt 模板

对每个 fill 字段，使用以下 prompt 调用 LLM：

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

## 可用工具

Skill 目录提供了 Python 辅助脚本供调用：

### `src/parser.py`
- `extract_name(text)` — 从个人信息中提取姓名
- `extract_job_and_company(jd_text)` — 从 JD 文本提取岗位名称和公司
- `extract_fill_fields(template)` — 从模板提取所有 fill 字段名列表

### `src/assembler.py`
- `generate_resume_file(template_content, fill_mapping, user_name, job_title, company, output_dir)` — 将填充内容填入模板，生成最终简历文件

### `src/tools.py`
CLI 入口，提供：
- `python src/tools.py parse-jd <jd_file>` — 提取岗位名称和公司
- `python src/tools.py parse-template <template_file>` — 提取 fill 字段列表
- `python src/tools.py assemble <template_file> <fill_mapping_json> <user_name> <job_title> <company> [--output-dir]` — 组装单份简历
- `python src/tools.py batch-assemble <template_file> <personal_info_file> <jd_dir> [--fill-ext .json] [--output-dir ./output] [--clean-json]` — **批量组装**：jd_dir 下每个 `.md` JD 文件自动匹配同名 `.json` 填充映射，批量生成所有简历；加 `--clean-json` 在组装完成后自动删除所有 `.json` 中间文件

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
