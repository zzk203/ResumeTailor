---
name: resume-pipeline
description: 求职全流程助手。当用户说"帮我找工作"、"帮我写简历"、"我要投简历"、"准备求职"、或任何涉及岗位搜索+简历生成的完整求职流程时触发。整合 jd-hunter（岗位搜索评分）和 resume-matcher（简历生成），作为编排层统合两条子 Skill。
---

# 求职全流程管线 (Resume Pipeline)

## 设计原则

- **扁平执行**：agent 按顺序执行每个步骤，不跳过、不委托给 CLI 工具做 LLM 推理
- **生成即校验**：每个阶段结束时输出文件都要存在，否则不进入下一阶段
- **模板驱动**：所有 LLM prompt 从 `.jinja2` 模板读取，agent 预览模板后自行生成内容
- **最小交互**：只在关键决策节点询问用户（参看：精简交互原则表）

## 精简交互原则

| 节点 | 触发条件 | 默认策略 |
|------|----------|----------|
| 目标确认（A/B/C） | 入口 | 隐式推断，否则提问 |
| 目标岗位确认 | 推断后展示给用户，允许修改 | 默认用全部推荐 |
| 搜索参数（城市/经验） | 用户未提供 | 从个人信息取城市偏好，经验留空 |
| 评分阈值 | 阶段 2 开始前 | 默认 7 分，必须向用户确认一次 |
| JD 选择 | 评分筛选后 | 展示索引供选择，选全部高评分 |
| 模板文件 | 用户已有 | 必问路径 |
| 个人信息 | 用户已有 | 必问路径 |
| 编写逻辑文件 | 可选 | 默认不询问（AGENTS.md 中指定） |
| 扩展材料类型 | 默认全部 4 种 | 不询问 |

路径选择（A/B/C），用户未明确时默认 C（完整管线）。

## 阶段 0：环境初始化

1. 确保输出目录存在：`jd/`、`jd_raw/`、`resume/`
2. 确保已安装依赖：`pip install -r resume-matcher-skill/requirements.txt`
3. 确认 opencli 可用：`which opencli && opencli --version`

## 阶段 1：搜索 JD

目标：从选定的招聘渠道搜索 JD，获取详情页内容，保存原始 JD 到 `jd_raw/`。

### 1.1 收集输入

- 个人信息文件路径（用户提供或已知）
- 目标岗位（用户提供，或 agent 从个人信息推断后展示确认）
- 城市（个人信息的"城市偏好"字段，或用户直接指定）
- 招聘渠道（用户指定，默认 `["boss"]`）
- 经验年限（从工作经历推算，或用户指定）

### 1.2 推断目标岗位

读取 `jd-hunter-skill/src/prompt_templates/infer_jobs.jinja2`，用个人信息渲染出 prompt。

**agent 注意**：你是 LLM。直接读取模板 → 理解任务 → 生成对应的 JSON 数组输出（每个元素含 `job_title` 和 `reason`）。**不要调用任何 Python 脚本**，模板是你的 prompt。

展示给用户确认，允许修改。确认后进入搜索。

### 1.3 搜索 JD

对每个（岗位 × 渠道）组合，运行：

```bash
opencli boss search "<岗位名>" --city <城市> --experience <经验> -f json --limit 15
```

- 结果可能为空，跳过即可，继续下一个组合
- 收集所有结果列表

### 1.4 获取详情

对每个搜索结果，提取 `security_id` 字段，获取完整 JD 内容：

```bash
opencli boss detail <security_id> -f json
```

结果中的 `description` 字段即为 JD 正文。若失败（空输出），跳过该条。

### 1.5 保存原始 JD

对每条有详情的 JD，在 `jd_raw/boss/` 下保存为 `{公司}-{岗位}.md`。

**格式**（单文件包含完整岗位信息）：

```
岗位名称：{name}
公司：{company}
薪酬：{salary}
地点：{area}
经验：{experience}
学历：{degree}
技能要求：{skills}
BOSS：{boss}
URL：{url}

{description}
```

**关键**：`岗位名称` 和 `公司` 必须出现在文件前三行之一，格式严格为 `岗位名称：XXX` 和 `公司：XXX`。这是后续解析的依据。

## 阶段 2：评分与筛选

目标：对每条原始 JD 打分（1-10），筛选出 ≥ 阈值的 JD。

### 2.1 评分

读取 `jd-hunter-skill/src/prompt_templates/score_jd.jinja2`，模板中有 `jd_content` 和 `personal_info` 两个变量。

**agent 注意**：你是 LLM。对每条 JD：
1. 读取模板
2. 用该 JD 内容 + 个人信息填入
3. 生成 JSON：`{"score": N, "reason": "..."}`
4. 记录分数

评分维度：
- 技能匹配度（C/C++、Linux、嵌入式等核心技能）
- 行业经验匹配（车载/嵌入式/后端经验）
- 年限匹配（3 年 vs 要求 3-5 年）
- 技术栈重叠度

### 2.2 筛选

- 默认阈值：7 分（`-t` 可自定义）
- **必须向用户确认阈值**：在评分开始前，向用户询问"评分阈值默认 7 分，要改吗？"
- 低于阈值的 JD 跳过，不进入下一阶段

### 2.3 落盘

将 ≥ 阈值的原始 JD **也保存一份到 `jd_raw/boss/`**（如果之前没保存过）。

## 阶段 3：结构化与索引

目标：将筛选后的 JD 按标准模板结构化，生成索引。

### 3.1 提取结构化字段

读取 `jd-hunter-skill/src/prompt_templates/extract_fields.jinja2`。

**agent 注意**：你是 LLM。对每条 ≥ 阈值的 JD，读取模板 → 生成结构化 JSON：

```json
{
  "jd来源": "boss直聘",
  "jd投递渠道": "im",
  "jd投递url": "原始 URL",
  "岗位名称": "提取值",
  "公司": "提取值",
  "岗位职责": "提取值",
  "任职要求": "提取值",
  "加分项": "如果有"
}
```

如果模板有额外要求，以模板中的字段说明为准。

### 3.2 保存结构化 JD

保存到 `jd/{公司}-{岗位}.md`，格式：

```markdown
# {公司名称} - {岗位名称}

- jd来源：boss直聘
- jd投递渠道：im
- jd投递url：{URL}
- 岗位名称：{岗位名称}
- 公司：{公司名称}
- 匹配度：{得分}

## 岗位职责

{岗位职责内容}

## 任职要求

{任职要求内容}
```

### 3.3 生成索引

运行：

```bash
python -m jd-hunter-skill.src.main index
```

这会读取 `jd/` 目录下的所有 `.md` 文件，生成 `jd/index.md`。

### 3.4 报告

向用户报告搜索结果：
- 各渠道数量
- 匹配度分布（最高分、最低分、平均分）
- `jd/index.md` 路径
- 询问是否需要对筛选结果进行调整（改变阈值、补充/删除）

## 阶段 4：生成定制简历

目标：对每个选中的 JD 生成定制简历和扩展材料。

### 4.1 收集输入

- 简历模板（用户提供路径，如 `personal/曾昭恺-简历-模板.md`）
- 编写逻辑（可选，如 `personal/编写逻辑.md`，其内容作为 writing_logic 传入 prompt）
- 确认个人信息文件路径

读取 `resume-matcher-skill/src/prompt_templates/fill_section.jinja2` 模板：
- 变量：`field_name`、`jd_content`、`personal_info`、`writing_logic`
- 如果用户提供了编写逻辑文件，reading_logic 用文件内容；否则用默认值："使用 STAR 法则，突出与岗位最相关的经历，专业简洁，纯文本段落。"

### 4.2 解析模板字段

读取模板 `.md`，提取所有 `<!-- fill:字段名 -->...<!-- /fill:字段名 -->` 标签的字段名。

### 4.3 生成填充内容

对 **每个 fill 字段**：

1. 读取 fill_section.jinja2 模板
2. 用字段名 + JD 全文 + 个人信息原文 + 编写逻辑 填入
3. **agent 注意**：你是 LLM，直接生成字段内容
4. 结果为纯文本段落，不含注释、不含模块标题

对所有字段执行完毕，组装成 JSON 映射：

```json
{
  "工作经历": "生成的文本...",
  "工作项目": "生成的文本...",
  ...
}
```

### 4.4 组装简历

对每个 JD，用 batch-assemble 命令生成简历文件：

```bash
python -m resume-matcher-skill.src.tools batch-assemble \
  <模板文件> \
  <个人信息> \
  <jd_dir> \
  --logic-file <编写逻辑> \
  --output-dir resume \
  --no-extras \
  --clean-json
```

### 4.5 生成扩展材料

对每个 JD，agent 读取 4 个 jinja2 模板（位于 `resume-matcher-skill/src/prompt_templates/`），依次生成实际内容：

| 类型 | 模板文件 | 说明 |
|------|----------|------|
| first-msg | `first_message.jinja2` | 投递第一句话（channel: im） |
| interview-intro | `interview_intro.jinja2` | 面试自我介绍（duration: 3min） |
| skill-gap | `skill_gap.jinja2` | 能力补充建议（focus: balanced） |
| project-recommend | `project_recommend.jinja2` | 练习项目推荐（level: intermediate） |

**执行步骤**：

1. agent 读取模板 → 作为 LLM 直接生成内容（**不要**只输出 prompt，必须是最终给用户看的文本）
2. 将 4 项生成结果写入 JSON 文件（如 `/tmp/extras.json`）：

```json
{
  "first-msg": "您好，我有 3 年华为...",
  "interview-intro": "我叫XXX，毕业于...",
  "skill-gap": "岗位匹配优势：...",
  "project-recommend": "推荐项目：..."
}
```

3. 调用 CLI 组装文件：

```bash
python -m resume-matcher-skill.src.tools generate-extras \
  <结构化JD路径> \
  <个人信息路径> \
  --extras-content /tmp/extras.json \
  --output-dir resume
```

4. 确认输出 `resume/{姓名}-{岗位}-{公司}-extras.md` 存在且内容非空

**关键**：模板是你的 LLM prompt，你读完后直接输出最终内容，不要再套一层 prompt 文字。

## 阶段 5：校验与报告

### 5.1 输出校验清单

| 检查项 | 验证方式 |
|--------|----------|
| `jd_raw/` 有原始 JD | `ls jd_raw/boss/*.md` |
| `jd/` 有结构化 JD | `ls jd/*.md`（不含 index.md） |
| `jd/index.md` 存在 | `test -f jd/index.md` |
| `resume/` 有简历 | `ls resume/*.md`（不含 extras） |
| 索引中有匹配度列 | `grep "匹配度" jd/index.md` |
| 简历文件名含姓名-岗位-公司 | 格式 `{姓名}-{岗位}-{公司}.md` |

如果任何校验项缺失，**打印警告**并重新执行对应的阶段。

### 5.2 报告

向用户汇总：
```
✅ 搜索渠道：Boss直聘
   - 搜索岗位数：{N} 个
   - 获取 JD 总数：{N} 条
   - 匹配 ≥{阈值} 分：{N} 条

📂 原始 JD：  jd_raw/（{N} 条）
📂 结构化 JD：jd/（{N} 条）
📂 简历：     resume/（{N} 份）
📂 扩展材料： resume/（{N} 份）

📊 索引路径：jd/index.md
```

## 异常处理

| 场景 | 处理方式 |
|------|----------|
| 用户无个人信息文件 | 提示创建，示例：含 `姓名：XXX`、技能、经历 |
| 用户无简历模板 | 提示创建，说明 fill 标签格式 |
| opencli 搜索失败（无结果） | 提示用户并建议放宽搜索条件 |
| JD 详情获取失败 | 跳过该条，继续后续 |
| 生成简历失败 | 跳过该 JD，继续下一个，最终汇总失败列表 |
| 文件名冲突 | 添加数字后缀（已有文件 `-2`、`-3`） |
| 用户中途修改需求 | 记录当前位置，告知用户可回退到上一阶段 |
