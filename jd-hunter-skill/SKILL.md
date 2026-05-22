---
name: jd-hunter
description: 根据个人信息自动搜集、筛选、结构化 JD，输出目录供简历匹配 Skill 使用。支持多招聘渠道搜索、LLM 匹配度评分、结构化字段提取和索引生成。
---

# JD 自动猎取 (JD Hunter)

根据个人信息自动搜索各招聘渠道的 JD，评分筛选后提取结构化字段，生成索引供简历匹配 Skill 使用。

## 交互流程

1. 用户提供**个人信息文件**（含 `姓名：...`、技能、经历等）
2. Agent 调用 LLM 推断 2-3 个目标岗位，用户确认或手动输入
3. 在多个招聘渠道搜索（Boss直聘、拉勾、猎聘），组合岗位名 + 城市 + 经验年限
4. 获取 JD 详情页内容
5. 对每条 JD 调用 LLM 评分（1-10），筛选 ≥阈值 分条目（默认 7，可通过 `-t` 自定义）
6. 原始 JD 落盘 `jd_raw/{渠道}/{公司}-{岗位}.md`
7. 调用 LLM 提取 7 个结构化字段（jd来源、投递渠道、URL、岗位名称、公司、岗位职责、任职要求）
8. 结构化结果存到 `jd/{公司}-{岗位}.md`
9. 生成 `jd/index.md` 索引汇总表
10. 向用户报告结果：各渠道数量、匹配度分布、索引路径

## CLI 使用

```bash
# 完整猎取流程（指定阈值 7，默认 7）
python -m jd-hunter-skill.src.main hunt personal_info.md --threshold 7
python -m jd-hunter-skill.src.main hunt personal_info.md -t 8        # 更严格筛选

# 单步操作
python -m jd-hunter-skill.src.main search boss "后端开发" --city 北京
python -m jd-hunter-skill.src.main score jd_file.md personal_info.md -t 6
python -m jd-hunter-skill.src.main extract raw_jd.md --channel boss --url https://...
python -m jd-hunter-skill.src.main index
```

## 异常处理

| 场景 | 处理方式 |
|------|----------|
| LLM 推断岗位失败 | 提示用户手动输入目标岗位 |
| 搜索无结果 | 跳过该渠道，继续其他渠道 |
| 详情页抓取失败 | 跳过该条 JD |
| LLM 调用失败 | 重试 1 次，跳过失败批次 |
| 文件名冲突 | 自动添加数字后缀 |
| 结构化字段缺失 | 填"未知" |

## 输出目录结构

```
jd_raw/              # 原始 JD（评分≥阈值的）
  boss/
    字节跳动-后端开发.md
  lagou/
jd/                  # 结构化 JD
  字节跳动-后端开发.md
  index.md           # JD 索引汇总表
```
