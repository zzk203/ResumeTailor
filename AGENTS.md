# ResumeTailor

简历自动定制工具，根据模板 + 个人信息 + JD，通过 LLM 生成针对性简历。

## 项目结构

```
resume-matcher-skill/     # 核心代码
  src/
    parser.py             # 标签解析、元数据提取
    assembler.py          # 简历组装
    tools.py              # CLI 入口（argparse）
    prompt_templates/     # LLM prompt 模板
  tests/                  # pytest 单元测试
  SKILL.md                # Skill 说明书
my_resume/                # 个人简历素材 + 生成结果
doc/                      # 设计文档
```

## 命令

- 安装依赖: `pip install -r resume-matcher-skill/requirements.txt`
- 运行测试: `python -m pytest resume-matcher-skill/tests/ -v`
- CLI 使用: `python -m resume-matcher-skill.src.tools --help`

## 约定

- Python >= 3.8
- 模板中使用 `<!-- fill:字段名 -->` 标签标记需 LLM 生成的内容
- 非 fill 内容自动保留，无需 `<!-- fixed:... -->` 标记
- 编写规范遵循 STAR 法则，详见 `my_resume/编写逻辑.md`
