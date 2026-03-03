"""
AI Harness - iFlow Executor Module

This module provides high-level execution utilities for iFlow CLI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import logging

from .provider import IFlowProvider, IFlowConfig
from ..base import ExecutionResult, ExecutionStatus, ProviderExecutionError

logger = logging.getLogger(__name__)


class IFlowExecutor:
    """
    High-level executor for iFlow CLI operations.

    This class provides convenient methods for common iFlow operations,
    including task execution, status checking, and result processing.

    Example:
        executor = IFlowExecutor()
        result = executor.run_task(
            project_path="/path/to/project",
            prompt="Implement user authentication",
            on_progress=lambda msg: print(msg)
        )
    """

    def __init__(self, provider: Optional[IFlowProvider] = None):
        """
        Initialize executor.

        Args:
            provider: Optional IFlowProvider instance. If not provided,
                     a new one will be created.
        """
        self.provider = provider or IFlowProvider()
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the executor and provider.

        Args:
            config: Optional provider configuration.
        """
        if not self._initialized:
            self.provider.initialize(config)
            self._initialized = True

    def ensure_initialized(self) -> None:
        """Ensure provider is initialized."""
        if not self._initialized:
            self.initialize()

    def run_task(
        self,
        prompt: str,
        project_path: Optional[str] = None,
        timeout: int = 600,
        max_turns: int = 50,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> ExecutionResult:
        """
        Execute a task using iFlow.

        Args:
            prompt: Task prompt to execute.
            project_path: Project directory (default: current directory).
            timeout: Execution timeout in seconds.
            max_turns: Maximum turns/iterations.
            on_progress: Optional progress callback.

        Returns:
            ExecutionResult with task outcome.
        """
        self.ensure_initialized()

        working_dir = project_path or str(Path.cwd())

        if on_progress:
            on_progress(f"Starting task execution...")
            on_progress(f"Working directory: {working_dir}")

        result = self.provider.execute(
            prompt=prompt,
            timeout=timeout,
            max_turns=max_turns,
            working_dir=working_dir,
        )

        if on_progress:
            status_emoji = "✅" if result.success else "❌"
            on_progress(f"{status_emoji} Task completed: {result.status.value}")
            on_progress(f"Elapsed: {result.elapsed_seconds:.1f}s")

        return result

    def run_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        **kwargs,
    ) -> ExecutionResult:
        """
        Execute a task with automatic retry on failure.

        Args:
            prompt: Task prompt to execute.
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries in seconds.
            **kwargs: Additional arguments for run_task().

        Returns:
            ExecutionResult from last attempt.
        """
        import time

        self.ensure_initialized()

        last_result: Optional[ExecutionResult] = None

        for attempt in range(max_retries + 1):
            logger.info(f"Execution attempt {attempt + 1}/{max_retries + 1}")

            result = self.run_task(prompt, **kwargs)
            last_result = result

            if result.success:
                return result

            if result.status == ExecutionStatus.TIMEOUT:
                logger.warning(f"Timeout on attempt {attempt + 1}")
            else:
                logger.warning(f"Failed on attempt {attempt + 1}: {result.error}")

            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        return (
            last_result
            if last_result
            else ExecutionResult(
                status=ExecutionStatus.FAILED,
                success=False,
                error="All retry attempts failed",
            )
        )

    def generate_task_prompt(
        self,
        task_id: str,
        task_description: str,
        project_name: str,
        steps: Optional[List[str]] = None,
        priority: str = "medium",
    ) -> str:
        """
        Generate a formatted task prompt for iFlow.

        Args:
            task_id: Task identifier.
            task_description: Task description.
            project_name: Project name.
            steps: Implementation steps.
            priority: Task priority.

        Returns:
            Formatted prompt string.
        """
        steps_text = ""
        if steps:
            steps_text = "\n## 执行步骤\n" + "\n".join(
                f"{i + 1}. {s}" for i, s in enumerate(steps)
            )

        prompt = f"""继续开发 **{project_name}** 项目的任务。

⚠️ 重要：这是 {project_name} 项目，请只操作 {project_name}/ 目录下的文件！

## 当前任务
- ID: {task_id}
- 描述: {task_description}
- 优先级: {priority}
{steps_text}

## 执行要求
1. 读取 {project_name}/.agent-harness/feature_list.json 确认任务状态
2. 按照任务描述完成开发
3. 完成后运行测试验证 (如适用)
4. 更新 {project_name}/.agent-harness/feature_list.json 中的 passes 状态为 true
5. 更新 {project_name}/.agent-harness/claude-progress.txt 记录进度

## 重要提醒
- 只处理这一个任务
- 只操作 {project_name}/ 目录
- 完成后必须标记 passes: true
- 如果遇到阻塞问题，记录到 progress 文件中并停止
"""
        return prompt

    def check_iflow_available(self) -> Dict[str, Any]:
        """
        Check if iFlow CLI is available.

        Returns:
            Dict with availability status and path.
        """
        self.ensure_initialized()

        path = self.provider.get_iflow_path()

        return {
            "available": path is not None,
            "path": path,
            "status": self.provider.status.value,
        }

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information.

        Returns:
            Dict with provider details.
        """
        self.ensure_initialized()

        info = self.provider.info

        return {
            "name": info.name,
            "version": info.version,
            "description": info.description,
            "capabilities": {
                "supports_yolo_mode": info.capabilities.supports_yolo_mode,
                "supports_max_turns": info.capabilities.supports_max_turns,
                "supports_output_file": info.capabilities.supports_output_file,
                "max_turns_limit": info.capabilities.max_turns_limit,
                "default_timeout": info.capabilities.default_timeout,
            },
        }

    def cleanup(self) -> None:
        """Cleanup executor resources."""
        self.provider.cleanup()
        self._initialized = False


def create_executor(config: Optional[Dict[str, Any]] = None) -> IFlowExecutor:
    """
    Factory function to create an initialized executor.

    Args:
        config: Optional provider configuration.

    Returns:
        Initialized IFlowExecutor instance.
    """
    executor = IFlowExecutor()
    executor.initialize(config)
    return executor
