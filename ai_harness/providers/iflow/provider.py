"""
AI Harness - iFlow Provider Implementation

This module implements the iFlow CLI as a provider plugin.
"""

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from ..base import (
    BaseAIProvider,
    ExecutionResult,
    ExecutionStatus,
    ProviderInfo,
    ProviderCapabilities,
    ProviderStatus,
    ProviderInitializationError,
    ProviderExecutionError,
)

logger = logging.getLogger(__name__)


@dataclass
class IFlowConfig:
    """iFlow-specific configuration."""

    yolo_mode: bool = True
    max_turns_default: int = 50
    timeout_default: int = 600
    output_format: str = "json"
    discover_paths: List[str] = field(
        default_factory=lambda: [
            # Windows paths
            r"C:\nvm4w\nodejs\iflow.cmd",
            r"C:\nvm4w\nodejs\iflow",
            os.path.expandvars(r"%APPDATA%\npm\iflow.cmd"),
            os.path.expandvars(r"%APPDATA%\npm\iflow"),
            # Unix paths
            "/usr/local/bin/iflow",
            "/usr/bin/iflow",
        ]
    )


class IFlowProvider(BaseAIProvider):
    """
    iFlow CLI provider implementation.

    This provider wraps the iFlow CLI tool, enabling AI Harness
    to use iFlow for automated task execution.

    Features:
    - Auto-discovery of iFlow CLI installation
    - Support for --yolo mode (auto-accept)
    - Configurable timeout and max turns
    - Output file support for structured results

    Example:
        provider = IFlowProvider()
        provider.initialize()
        result = provider.execute("Implement user login feature")
    """

    def __init__(self):
        """Initialize the provider."""
        self._iflow_path: Optional[str] = None
        self._config: IFlowConfig = IFlowConfig()
        self._status: ProviderStatus = ProviderStatus.UNINITIALIZED
        self._node_paths_added: bool = False

    @property
    def info(self) -> ProviderInfo:
        """Return provider information."""
        return ProviderInfo(
            name="iflow",
            version="1.0.0",
            description="iFlow CLI integration for AI Harness",
            author="AI Harness Team",
            capabilities=ProviderCapabilities(
                supports_yolo_mode=True,
                supports_max_turns=True,
                supports_output_file=True,
                supports_interactive=False,
                max_turns_limit=500,
                default_timeout=600,
            ),
        )

    @property
    def status(self) -> ProviderStatus:
        """Return current status."""
        return self._status

    @status.setter
    def status(self, value: ProviderStatus) -> None:
        """Set status."""
        self._status = value

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the iFlow provider.

        Args:
            config: Optional configuration dictionary.

        Raises:
            ProviderInitializationError: If iFlow CLI cannot be found.
        """
        # Apply configuration
        if config:
            self._apply_config(config)

        # Find iFlow CLI
        self._iflow_path = self._discover_iflow()

        if not self._iflow_path:
            self._status = ProviderStatus.ERROR
            raise ProviderInitializationError(
                "iFlow CLI not found. Please ensure iFlow is installed and in PATH."
            )

        logger.info(f"Found iFlow at: {self._iflow_path}")
        self._status = ProviderStatus.READY

    def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply configuration settings."""
        settings = config.get("settings", {})

        if "yolo_mode" in settings:
            self._config.yolo_mode = settings["yolo_mode"]
        if "max_turns_default" in settings:
            self._config.max_turns_default = settings["max_turns_default"]
        if "timeout_default" in settings:
            self._config.timeout_default = settings["timeout_default"]
        if "output_format" in settings:
            self._config.output_format = settings["output_format"]
        if "discover_paths" in settings:
            self._config.discover_paths = settings["discover_paths"]

    def _discover_iflow(self) -> Optional[str]:
        """
        Discover iFlow CLI installation.

        Returns:
            Path to iFlow CLI or None if not found.
        """
        # 1. Try shutil.which
        iflow_path = shutil.which("iflow")
        if iflow_path:
            return iflow_path

        # 2. Try common paths
        for path in self._config.discover_paths:
            expanded = os.path.expandvars(path)
            if os.path.isfile(expanded):
                return expanded

        # 3. Search in PATH
        path_env = os.environ.get("PATH", "")
        for path_dir in path_env.split(os.pathsep):
            for name in ["iflow.cmd", "iflow.exe", "iflow"]:
                candidate = os.path.join(path_dir, name)
                if os.path.isfile(candidate):
                    return candidate

        return None

    def execute(
        self,
        prompt: str,
        timeout: int = 600,
        max_turns: int = 50,
        output_file: Optional[str] = None,
        working_dir: Optional[str] = None,
        **kwargs,
    ) -> ExecutionResult:
        """
        Execute a task using iFlow CLI.

        Args:
            prompt: The task prompt to execute.
            timeout: Maximum execution time in seconds.
            max_turns: Maximum number of turns/iterations.
            output_file: Path to save output data.
            working_dir: Working directory for execution.
            **kwargs: Additional options (ignored).

        Returns:
            ExecutionResult with status and output.

        Raises:
            ProviderExecutionError: If execution fails.
        """
        if self._status != ProviderStatus.READY:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                success=False,
                error=f"Provider not ready (status: {self._status.value})",
            )

        if not self._iflow_path:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                success=False,
                error="iFlow CLI path not configured",
            )

        # Validate prompt
        if not self.validate_prompt(prompt):
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                success=False,
                error="Invalid or empty prompt",
            )

        # Set working directory
        work_dir = Path(working_dir) if working_dir else Path.cwd()

        # Generate output file if not provided
        if not output_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = str(work_dir / f"iflow_output_{timestamp}.json")

        # Build command
        cmd = self._build_command(prompt, timeout, max_turns, output_file)

        logger.info(f"Executing: {self._iflow_path} -p ... --max-turns={max_turns}")
        logger.debug(f"Working directory: {work_dir}")

        # Update status
        self._status = ProviderStatus.BUSY

        try:
            start_time = time.time()

            # Prepare environment
            env = self._prepare_environment()

            # Execute
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # Extra buffer
                env=env,
            )

            elapsed = time.time() - start_time

            # Parse output
            output_data = self._parse_output(output_file)

            # Restore status
            self._status = ProviderStatus.READY

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS
                if result.returncode == 0
                else ExecutionStatus.FAILED,
                success=result.returncode == 0,
                message=f"Execution completed in {elapsed:.1f}s",
                elapsed_seconds=round(elapsed, 1),
                output_file=output_file if os.path.exists(output_file) else None,
                output_data=output_data,
                error=result.stderr[-1000:] if result.stderr else None,
            )

        except subprocess.TimeoutExpired:
            self._status = ProviderStatus.ERROR
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                success=False,
                error=f"Execution timed out after {timeout} seconds",
            )

        except FileNotFoundError as e:
            self._status = ProviderStatus.ERROR
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                success=False,
                error=f"iFlow CLI not found: {e}",
            )

        except Exception as e:
            self._status = ProviderStatus.ERROR
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                success=False,
                error=f"Unexpected error: {e}",
            )

    def _build_command(
        self,
        prompt: str,
        timeout: int,
        max_turns: int,
        output_file: str,
    ) -> List[str]:
        """Build the iFlow CLI command."""
        cmd = [
            self._iflow_path,
            "-p",
            prompt,
            f"--max-turns={max_turns}",
            "-o",
            output_file,
        ]

        if self._config.yolo_mode:
            cmd.append("--yolo")

        return cmd

    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for execution."""
        env = os.environ.copy()

        # Add Node.js paths if on Windows
        if os.name == "nt" and not self._node_paths_added:
            node_paths = [
                r"C:\nvm4w\nodejs",
                os.path.expandvars(r"%APPDATA%\npm"),
            ]
            for path in node_paths:
                if os.path.isdir(path) and path not in env.get("PATH", ""):
                    env["PATH"] = path + os.pathsep + env.get("PATH", "")
            self._node_paths_added = True

        return env

    def _parse_output(self, output_file: str) -> Optional[Dict[str, Any]]:
        """Parse iFlow output file."""
        if not os.path.exists(output_file):
            return None

        try:
            with open(output_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to parse output file: {e}")
            return None

    def cleanup(self) -> None:
        """Cleanup provider resources."""
        self._status = ProviderStatus.UNINITIALIZED
        self._iflow_path = None
        logger.info("iFlow provider cleaned up")

    def get_iflow_path(self) -> Optional[str]:
        """Get the path to iFlow CLI."""
        return self._iflow_path

    def get_config(self) -> IFlowConfig:
        """Get current configuration."""
        return self._config
