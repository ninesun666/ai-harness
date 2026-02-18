# iFlow Runner - 自动化开发指南

本文档总结 iFlow CLI 自动化开发的完整方案和规则。

---

## 一、核心概念

### Agent Harness 模式

基于 Anthropic 的 Agent Harness 设计模式，实现长期运行的自动化开发 Agent：

```
┌─────────────────────────────────────────────────────────┐
│                   Agent Harness                          │
├─────────────────────────────────────────────────────────┤
│  feature_list.json  ←→  iflow_runner.py  ←→  iFlow CLI  │
│         ↓                      ↓                  ↓      │
│  任务状态管理           调度执行          AI 编码执行     │
│         ↓                      ↓                  ↓      │
│  claude-progress.txt ←─ 记录进度 ──────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 关键文件

| 文件 | 作用 |
|------|------|
| `feature_list.json` | 任务清单，包含所有待开发功能 |
| `claude-progress.txt` | 进度日志，记录每次会话的工作 |
| `agent_state.json` | Agent 状态，追踪初始化和会话数 |
| `iflow_runner.py` | 调度脚本，自动化调用 iFlow CLI |

---

## 二、使用方法

### 1. 检查项目状态

```bash
python scripts/iflow_runner.py --action status --project <项目名>
```

输出示例：
```json
{
  "project": "ai-legion",
  "total_tasks": 30,
  "completed": 3,
  "pending": 27,
  "next_task": {
    "id": "F005",
    "description": "地图交互 - 点击和悬停",
    "priority": "high"
  },
  "progress": "3/30 (10%)"
}
```

### 2. 单次执行

执行一个任务后停止：

```bash
python scripts/iflow_runner.py --action run --project <项目名>
```

### 3. 持续执行（永续模式）

自动循环执行所有任务：

```bash
python scripts/iflow_runner.py --action continuous --project <项目名> --interval 60
```

参数说明：
- `--project`: 项目名称（默认 ninesun-blog）
- `--interval`: 检查间隔秒数（默认 60）
- `--max-iterations`: 最大迭代次数（默认 100）

---

## 三、工作流程

### 单次执行流程

```
iFlow Runner 启动
       │
       ▼
读取 feature_list.json
       │
       ▼
找到下一个未完成任务 (passes: false)
       │
       ▼
生成执行 Prompt
       │
       ▼
调用: iflow -p "prompt" --yolo --max-turns=50
       │
       ▼
等待执行完成
       │
       ▼
检查任务状态更新
       │
       ▼
返回执行结果
```

### 持续执行流程

```
┌──────────────────────────────────────┐
│                                      │
│  1. 读取 feature_list.json           │
│           ↓                          │
│  2. 找到未完成任务                    │
│           ↓                          │
│  3. 调用 iFlow 执行                   │
│           ↓                          │
│  4. 等待完成                          │
│           ↓                          │
│  5. 检查是否全部完成                  │
│           ↓                          │
│  [否] → 等待 interval 秒 → 回到步骤1  │
│           ↓                          │
│  [是] → 退出                         │
│                                      │
└──────────────────────────────────────┘
```

---

## 四、Feature List 规范

### 结构定义

```json
{
  "project_spec": "项目描述",
  "created_at": "2026-02-15T00:00:00",
  "last_updated": "2026-02-16T00:00:00",
  
  "modules": {
    "list": [
      { "id": "M001", "name": "模块名", "status": "completed|in_progress|pending" }
    ]
  },
  
  "total_features": 40,
  "completed": 26,
  "in_progress": 0,
  "pending": 14,
  
  "features": [
    {
      "id": "F001",
      "category": "ui|api|ai|visual|setup",
      "module": "M001",
      "description": "功能描述",
      "priority": "high|medium|low",
      "author": "human|ai",
      "steps": ["步骤1", "步骤2"],
      "passes": false,
      "dependencies": ["F000"],
      "notes": "备注信息"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 功能ID，格式 F001, F002... |
| `category` | string | 分类：ui/api/ai/visual/setup |
| `module` | string | 所属模块ID |
| `description` | string | 功能描述 |
| `priority` | string | 优先级：high/medium/low |
| `author` | string | 作者：human/ai |
| `steps` | array | 实现步骤 |
| `passes` | boolean | 是否通过测试 |
| `dependencies` | array | 依赖的功能ID |
| `completed_at` | string | 完成时间（可选） |
| `notes` | string | 备注信息（可选） |

---

## 五、Progress Log 规范

### 格式

```markdown
# Claude Progress Log

================================================================================
PROJECT: 项目名称 - 项目描述
================================================================================

[Session N - Coding Agent] YYYY-MM-DD HH:MM
Feature: F001 - 功能名称
Status: COMPLETED | FAILED | IN_PROGRESS
Author: AI | Human
Summary:
  - 完成的工作1
  - 完成的工作2
  
Files Modified:
  - path/to/file1.ts
  - path/to/file2.ts

Build: ✅ 成功 (1.90s) | ❌ 失败 (错误信息)

================================================================================
FEATURE STATUS
================================================================================
COMPLETED: 26 (F001-F026)
PENDING:   14 (F027-F040)

NEXT FEATURES:
  - F027: 功能描述
  - F028: 功能描述
================================================================================
```

---

## 六、iFlow CLI 参数

### 非交互模式

```bash
iflow -p "prompt" [options]
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `-p, --prompt` | 非交互模式，传入 prompt |
| `--yolo` | 自动接受所有操作（危险但自动化必需） |
| `--max-turns=N` | 最大轮次，防止无限循环 |
| `-o, --output-file` | 输出文件路径 |
| `-i, --prompt-interactive` | 执行后继续交互模式 |

### 示例

```bash
# 基础执行
iflow -p "实现用户登录功能" --yolo --max-turns=30

# 带输出文件
iflow -p "修复bug" --yolo --max-turns=20 -o result.json
```

---

## 七、最佳实践

### 1. 任务粒度

- ✅ 每个任务应该是一个独立可测试的功能点
- ✅ 任务描述要具体，包含明确的完成条件
- ❌ 避免过于宽泛的任务（如"完成整个模块"）

### 2. 依赖管理

- 明确标注 `dependencies`
- Runner 会按优先级和依赖顺序执行
- 依赖未满足的任务会被跳过

### 3. 错误处理

- 任务失败时不会标记 `passes: true`
- 查看日志了解失败原因
- 修复问题后重新运行

### 4. 并发限制

- 不要同时在多个会话中运行 Runner
- 会触发 API 并发限制
- 建议：关闭当前会话后在新终端运行

### 5. 定期检查

```bash
# 检查状态
python scripts/iflow_runner.py --action status --project ai-legion

# 查看进度日志
cat ai-legion/.agent-harness/claude-progress.txt
```

---

## 八、故障排查

### iflow 命令未找到

```
错误: iflow 命令未找到，请确保已安装 iFlow CLI
```

解决方案：
1. 确认 iflow 已安装：`where.exe iflow`
2. 脚本会自动搜索常见路径
3. 如果仍找不到，检查 PATH 环境变量

### 任务未标记完成

可能原因：
1. 构建失败
2. 测试未通过
3. Agent 没有更新 feature_list.json

解决方案：
- 查看 `claude-progress.txt` 了解详情
- 手动检查并标记完成

### API 并发限制

```
错误: 您当前的账号已达到平台并发限制
```

解决方案：
- 关闭其他 iFlow 会话
- 等待几分钟后重试

---

## 九、扩展开发

### 添加新项目

1. 创建项目目录结构
2. 添加 `.agent-harness/feature_list.json`
3. 运行：`python scripts/iflow_runner.py --action run --project 新项目名`

### 自定义 Prompt 模板

编辑 `iflow_runner.py` 中的 `generate_prompt()` 函数。

### 添加日志输出

Runner 支持输出到文件，查看执行结果。

---

## 十、相关文件

```
clawd/
├── scripts/
│   └── iflow_runner.py          # 主调度脚本
│
├── ninesun-blog/
│   └── .agent-harness/
│       ├── AGENT_INSTRUCTIONS.md # Agent 工作流程
│       ├── feature_list.json     # 任务清单
│       ├── claude-progress.txt   # 进度日志
│       └── agent_state.json      # Agent 状态
│
└── ai-legion/
    └── .agent-harness/
        ├── feature_list.json
        └── claude-progress.txt
```

---

*最后更新: 2026-02-16*
