# AI Harness 配置说明

## 配置文件

AI Harness 使用 JSON 格式的配置文件，按以下优先级加载：

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 1 | `.ai-harness.config` | 项目根目录，最高优先级 |
| 2 | `.ai-harness/config.json` | 项目配置目录 |
| 3 | `~/.ai-harness/config.json` | 用户全局配置 |
| 4 | `templates/ai-harness.config.json` | 默认模板 |

## 配置示例

```json
{
  "scheduler": {
    "default_timeout": 600,
    "default_max_turns": 50,
    "interval": 60,
    "max_iterations": 100,
    "retry_attempts": 3,
    "retry_delay": 5.0
  },
  "runner": {
    "auto_select_project": true,
    "show_progress": true
  }
}
```

## 参数说明

### scheduler 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_timeout` | int | 600 | 单次执行超时时间（秒） |
| `default_max_turns` | int | 50 | 单次执行最大轮次/迭代次数 |
| `interval` | int | 60 | 持续模式下每次迭代的间隔时间（秒） |
| `max_iterations` | int | 100 | 持续模式最大迭代次数，0 表示无限制 |
| `retry_attempts` | int | 3 | 执行失败时的重试次数 |
| `retry_delay` | float | 5.0 | 重试间隔时间（秒） |

### runner 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `auto_select_project` | bool | true | 自动选择第一个可用项目 |
| `show_progress` | bool | true | 显示执行进度 |

## 使用方式

### 1. 修改项目配置

在项目根目录创建 `.ai-harness.config` 文件：

```json
{
  "scheduler": {
    "interval": 30,
    "max_iterations": 50,
    "default_timeout": 1800
  }
}
```

### 2. 命令行覆盖

命令行参数优先级最高，会覆盖配置文件：

```bash
# 使用配置文件的默认值
python iflow_runner.py --action continuous

# 覆盖配置文件的值
python iflow_runner.py --action continuous --interval 30 --max-iterations 20
```

### 3. 设置全局配置

在用户主目录创建配置文件，所有项目共享：

```bash
# Windows
mkdir %USERPROFILE%\.ai-harness
# 创建 %USERPROFILE%\.ai-harness\config.json

# Linux/macOS
mkdir -p ~/.ai-harness
# 创建 ~/.ai-harness/config.json
```

## 运行模式

### 单次运行

执行一个任务后退出：

```bash
python iflow_runner.py --action run --project my-project
```

### 持续运行

循环执行所有任务，直到完成或达到最大迭代次数：

```bash
python iflow_runner.py --action continuous --project my-project
```

运行时会显示当前配置：

```
📋 已加载配置: D:\项目\.ai-harness.config
检查间隔: 30 秒
单次超时: 1800 秒
最大轮次: 50
最大迭代: 50 次
```
