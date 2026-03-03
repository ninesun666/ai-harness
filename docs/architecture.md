# AI Harness Architecture

**Version**: 1.0.0  
**Last Updated**: 2026-03-04

---

## Overview

AI Harness is a modular automation framework that enables AI coding tools to autonomously complete software development tasks. The architecture is designed around a **plugin system** that allows seamless integration of multiple AI tools (iFlow CLI, Claude Code, Cursor, etc.).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI Harness Core                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │     CLI      │    │    Config    │    │    Report    │                 │
│  │   (Click)    │───▶│   Manager    │◀───│   Generator  │                 │
│  └──────────────┘    └──────────────┘    └──────────────┘                 │
│         │                   │                   │                          │
│         └───────────────────┼───────────────────┘                          │
│                             │                                                │
│                    ┌────────▼────────┐                                      │
│                    │   Task Manager  │                                      │
│                    │    (Scheduler)  │                                      │
│                    └────────┬────────┘                                      │
│                             │                                                │
├─────────────────────────────┼───────────────────────────────────────────────┤
│                     PROVIDER REGISTRY                                        │
│                             │                                                │
│         ┌───────────────────┼───────────────────┐                          │
│         │                   │                   │                          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                   │
│  │    iFlow    │    │Claude Code  │    │   Cursor    │    ...            │
│  │   Provider  │    │  Provider   │    │  Provider   │                   │
│  └─────────────┘    └─────────────┘    └─────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Provider System

The provider system is the heart of AI Harness, enabling pluggable AI tool integration.

#### BaseAIProvider Interface

All providers must implement the `BaseAIProvider` abstract class:

```python
class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Return provider metadata."""
        pass
    
    @abstractmethod
    def initialize(self, config: Optional[Dict] = None) -> None:
        """Setup the provider."""
        pass
    
    @abstractmethod
    def execute(self, prompt: str, **kwargs) -> ExecutionResult:
        """Execute a task using the AI tool."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass
```

#### Provider Registry

Providers are discovered and loaded via **setuptools entry_points**:

```python
# setup.py
entry_points={
    "ai_harness.providers": [
        "iflow = ai_harness.providers.iflow:IFlowProvider",
        "claude = ai_harness.providers.claude:ClaudeProvider",
    ]
}
```

The registry provides:
- Automatic provider discovery
- Lazy initialization
- Provider validation
- Instance caching

### 2. Task Manager

The task manager orchestrates task execution:

- Reads `feature_list.json` for pending tasks
- Resolves task dependencies
- Selects appropriate provider
- Tracks execution progress
- Handles retries and error recovery

### 3. Configuration System

Two-level configuration hierarchy:

```
~/.ai-harness/config.yaml     # Global configuration
  └── project/.ai-harness/    # Project-level configuration
        ├── config.yaml
        └── feature_list.json
```

Configuration precedence: Project > Global > Defaults

### 4. Report Generator

Generates progress reports in multiple formats:
- **JSON** (default): Structured, machine-readable
- **Text**: Human-readable, similar to existing format
- **HTML**: Visual reports for web viewing

---

## Data Flow

```
1. User Action
   │
   ▼
2. CLI parses command (start, status, run)
   │
   ▼
3. Config Manager loads settings
   │
   ▼
4. Task Manager reads feature_list.json
   │
   ▼
5. Provider Registry selects provider
   │
   ▼
6. Provider executes task
   │
   ▼
7. Results logged and reported
   │
   ▼
8. State updated (feature_list.json, progress)
```

---

## Plugin Development Guide

### Creating a New Provider

1. **Create the provider module**:

```python
# ai_harness/providers/my_provider/provider.py

from ai_harness.providers.base import BaseAIProvider, ProviderInfo, ExecutionResult

class MyProvider(BaseAIProvider):
    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="my_provider",
            version="1.0.0",
            description="My AI tool integration",
            capabilities=ProviderCapabilities(
                supports_yolo_mode=True,
                supports_max_turns=True,
            )
        )
    
    def initialize(self, config=None):
        # Setup your AI tool
        pass
    
    def execute(self, prompt, timeout=600, **kwargs):
        # Implement execution logic
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            success=True,
            message="Task completed"
        )
    
    def cleanup(self):
        # Cleanup resources
        pass
```

2. **Register via entry_points**:

```python
# setup.py
entry_points={
    "ai_harness.providers": [
        "my_provider = ai_harness.providers.my_provider:MyProvider",
    ]
}
```

### Provider Best Practices

1. **Error Handling**: Catch all exceptions and return proper `ExecutionResult`
2. **Timeout Support**: Respect the timeout parameter
3. **Resource Cleanup**: Always implement `cleanup()`
4. **Capability Declaration**: Accurately declare what your provider supports
5. **Version Management**: Use semantic versioning for provider versions

---

## Directory Structure

```
ai_harness/
├── __init__.py           # Package entry point
├── cli/                  # CLI commands
│   ├── __init__.py
│   └── commands/         # Command implementations
├── core/                 # Core functionality
│   ├── __init__.py
│   ├── scheduler.py      # Task scheduling
│   ├── task_manager.py   # Task management
│   ├── errors.py         # Error definitions
│   └── retry.py          # Retry logic
├── providers/            # AI tool plugins
│   ├── __init__.py
│   ├── base.py           # Base interface
│   ├── registry.py       # Plugin registry
│   └── iflow/            # iFlow implementation
│       ├── __init__.py
│       ├── provider.py
│       └── executor.py
├── config/               # Configuration
│   ├── __init__.py
│   ├── manager.py        # Config loading
│   └── schema.py         # Validation schema
├── report/               # Reporting
│   ├── __init__.py
│   ├── tracker.py        # Progress tracking
│   └── generator.py      # Report generation
└── utils/                # Utilities
    ├── __init__.py
    └── platform.py       # Cross-platform helpers
```

---

## Backward Compatibility

The architecture maintains backward compatibility through:

1. **Legacy Entry Points**: `iflow_runner.py` and `init_project.py` remain functional
2. **Feature List Format**: Existing `feature_list.json` format is supported
3. **Configuration Migration**: Automatic migration from old config format
4. **CLI Compatibility**: Existing command-line arguments work unchanged

---

## Security Considerations

1. **Yolo Mode**: Auto-accept all operations (use with caution)
2. **Working Directory Isolation**: Each provider execution is sandboxed
3. **Timeout Enforcement**: Prevents runaway executions
4. **Provider Validation**: Only trusted providers are loaded

---

## Performance

- **Lazy Loading**: Providers loaded only when needed
- **Instance Caching**: Provider instances reused across tasks
- **Parallel Execution**: Independent tasks can run concurrently (optional)
- **Lightweight Dependencies**: Minimal external dependencies

---

## Future Extensions

1. **Web Dashboard**: Real-time progress visualization
2. **Remote Execution**: Distributed task execution
3. **Plugin Hot-Loading**: Runtime plugin updates
4. **Advanced Scheduling**: Priority queues, resource limits

---

*Document Version: 1.0.0*  
*Generated: 2026-03-04*
