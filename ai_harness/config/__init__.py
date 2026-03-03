"""
AI Harness - Configuration Package

This package provides configuration management with multi-level
configuration support and validation.
"""

from .manager import (
    ConfigManager,
    AIHarnessConfig,
    ProviderConfig,
    SchedulerConfig,
    ReportConfig,
    LoggingConfig,
    get_config_manager,
    get_config,
)
from .schema import (
    ConfigSchema,
    ConfigValidationError,
    validate_config,
    validate_and_raise,
)

__all__ = [
    # Manager
    "ConfigManager",
    "AIHarnessConfig",
    "ProviderConfig",
    "SchedulerConfig",
    "ReportConfig",
    "LoggingConfig",
    "get_config_manager",
    "get_config",
    # Schema
    "ConfigSchema",
    "ConfigValidationError",
    "validate_config",
    "validate_and_raise",
]
