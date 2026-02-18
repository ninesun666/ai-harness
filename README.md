# AI Harness - iFlow CLI 自动化开发框架

一套完整的 AI 辅助开发自动化方案，让 iFlow CLI 能够持续、自主地完成软件开发任务。

---

## 核心特性

- **自动化执行** - 无需人工干预，AI 自动完成开发任务
- **任务管理** - 基于 feature_list.json 的任务清单系统
- **进度追踪** - 详细的会话日志和进度记录
- **永续运行** - 支持持续运行直到所有任务完成
- **多项目支持** - 可同时管理多个项目的开发

---

## 快速开始

### 1. 安装依赖

```bash
# 需要 Python 3.8+
python --version

# 需要 iFlow CLI
iflow --version
```

### 2. 配置项目

在项目根目录创建 `.agent-harness/` 目录：

```
your-project/
└── .agent-harness/
    ├── feature_list.json      # 任务清单
    ├── claude-progress.txt    # 进度日志
    └── AGENT_INSTRUCTIONS.md  # 工作流程规范（可选）
```

### 3. 创建任务清单

```json
{
  "project_spec": "项目描述",
  "total_features": 10,
  "completed": 0,
  "pending": 10,
  "features": [
    {
      "id": "F001",
      "description": "功能描述",
      "priority": "high",
      "steps": ["步骤1", "步骤2"],
      "passes": false,
      "dependencies": []
    }
  ]
}
```

### 4. 运行

```bash
# 检查状态
python iflow_runner.py --action status --project your-project

# 单次执行
python iflow_runner.py --action run --project your-project

# 持续运行
python iflow_runner.py --action continuous --project your-project
```

---

## 目录结构

```
ai-harness/
├── iflow_runner.py              # 主调度脚本
├── README.md                    # 本文件
└── iflow_runner/
    └── AGENT_HARNESS_GUIDE.md   # 详细使用指南
```

---

## 核心文件说明

### iflow_runner.py

主调度脚本，负责：
- 读取任务清单
- 调用 iFlow CLI 执行任务
- 追踪执行结果
- 循环执行直到完成

### feature_list.json

任务清单格式：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 功能ID (F001, F002...) |
| description | string | 功能描述 |
| priority | string | 优先级 (high/medium/low) |
| steps | array | 实现步骤 |
| passes | boolean | 是否通过测试 |
| dependencies | array | 依赖的功能ID |

### claude-progress.txt

进度日志格式：

```
[Session N - Coding Agent] YYYY-MM-DD HH:MM
Feature: F001 - 功能名称
Status: COMPLETED
Summary:
  - 完成的工作
Files Modified:
  - file1.ts
Build: ✅ 成功
```

---

## 使用示例

### 示例 1: 单项目开发

```bash
# 初始化项目
mkdir my-project/.agent-harness

# 创建 feature_list.json（参考 templates/feature_list_template.json）

# 运行
python iflow_runner.py --action continuous --project my-project
```

### 示例 2: 多项目管理

```bash
# 项目 A
python iflow_runner.py --action run --project project-a

# 项目 B
python iflow_runner.py --action run --project project-b
```

---

## 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --action | run/continuous/status | status |
| --project | 项目名称 | ninesun-blog |
| --interval | 持续模式间隔(秒) | 60 |
| --max-iterations | 最大迭代次数 | 100 |

---

## 工作原理

```
┌─────────────────────────────────────────────────────────┐
│                   AI Harness                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  feature_list.json  →  iflow_runner.py  →  iFlow CLI   │
│         ↓                      ↓                  ↓     │
│    任务状态管理          调度执行          AI编码执行    │
│         ↓                      ↓                  ↓     │
│  claude-progress.txt ←── 记录进度 ←─────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 注意事项

1. **并发限制** - 不要同时在多个会话运行
2. **任务粒度** - 每个任务应该是独立可测试的功能点
3. **依赖管理** - 明确标注任务依赖关系
4. **安全考虑** - --yolo 模式会自动接受所有操作

---

## 模板文件

### feature_list_template.json

```json
{
  "project_spec": "你的项目描述",
  "created_at": "2026-02-16T00:00:00",
  "total_features": 0,
  "completed": 0,
  "pending": 0,
  "features": []
}
```

### AGENT_INSTRUCTIONS_template.md

```markdown
# Agent Instructions

## 会话开始流程
1. 读取进度文件
2. 检查任务状态
3. 开始工作

## 会话结束流程
1. 测试验证
2. 更新状态
3. 记录进度
```

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

*Created by iFlow CLI Automation*
