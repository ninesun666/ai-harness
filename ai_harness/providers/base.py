"""
AI Harness - Provider Base Module

This module defines the base interface for AI tool providers.
All AI tool integrations must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path


class ProviderStatus(Enum):
    """Provider status enumeration"""

    UNINITIALIZED = "uninitialized"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


class ExecutionStatus(Enum):
    """Task execution status"""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ProviderCapabilities:
    """Provider capabilities descriptor"""

    supports_yolo_mode: bool = False
    supports_max_turns: bool = False
    supports_output_file: bool = False
    supports_interactive: bool = False
    max_turns_limit: Optional[int] = None
    default_timeout: int = 600


@dataclass
class ProviderInfo:
    """Provider information"""

    name: str
    version: str
    description: str = ""
    author: str = ""
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)


@dataclass
class ExecutionResult:
    """Task execution result"""

    status: ExecutionStatus
    success: bool
    message: str = ""
    elapsed_seconds: float = 0.0
    output_file: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAIProvider(ABC):
    """
    Abstract base class for AI tool providers.

    All AI tool integrations (iFlow, Claude Code, Cursor, etc.) must
    implement this interface to be compatible with AI Harness.

    Example:
        class IFlowProvider(BaseAIProvider):
            @property
            def info(self) -> ProviderInfo:
                return ProviderInfo(
                    name="iflow",
                    version="1.0.0",
                    description="iFlow CLI integration"
                )

            def initialize(self) -> None:
                # Setup iFlow environment
                pass

            def execute(self, prompt: str, **kwargs) -> ExecutionResult:
                # Execute task using iFlow
                pass
    """

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """
        Get provider information.

        Returns:
            ProviderInfo: Provider metadata including name, version, and capabilities.
        """
        pass

    @property
    def status(self) -> ProviderStatus:
        """
        Get current provider status.

        Returns:
            ProviderStatus: Current operational status.
        """
        return (
            self._status if hasattr(self, "_status") else ProviderStatus.UNINITIALIZED
        )

    @status.setter
    def status(self, value: ProviderStatus) -> None:
        """Set provider status."""
        self._status = value

    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the provider.

        This method is called once before any executions.
        Use it to setup the environment, validate dependencies, etc.

        Args:
            config: Optional provider-specific configuration.

        Raises:
            ProviderInitializationError: If initialization fails.
        """
        pass

    @abstractmethod
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
        Execute a task using the AI tool.

        Args:
            prompt: The task prompt to execute.
            timeout: Maximum execution time in seconds.
            max_turns: Maximum number of turns/iterations.
            output_file: Path to save output data (optional).
            working_dir: Working directory for execution (optional).
            **kwargs: Additional provider-specific options.

        Returns:
            ExecutionResult: The execution result with status and output.

        Raises:
            ProviderExecutionError: If execution fails.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup provider resources.

        This method is called when the provider is being shut down.
        Use it to release resources, close connections, etc.
        """
        pass

    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate the prompt before execution.

        Args:
            prompt: The prompt to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return bool(prompt and prompt.strip())

    def get_status_message(self) -> str:
        """
        Get a human-readable status message.

        Returns:
            str: Status message.
        """
        status_messages = {
            ProviderStatus.UNINITIALIZED: "Provider not initialized",
            ProviderStatus.READY: "Provider ready",
            ProviderStatus.BUSY: "Provider busy executing task",
            ProviderStatus.ERROR: "Provider in error state",
        }
        return status_messages.get(self.status, "Unknown status")


class ProviderInitializationError(Exception):
    """Raised when provider initialization fails."""

    pass


class ProviderExecutionError(Exception):
    """Raised when provider execution fails."""

    pass


class ProviderNotFoundError(Exception):
    """Raised when a requested provider is not found."""

    pass
