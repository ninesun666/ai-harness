"""
AI Harness - Configuration Schema Module

This module provides schema validation for configuration files.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, errors: List[Tuple[str, str]]):
        """
        Initialize with validation errors.

        Args:
            errors: List of (field, message) tuples.
        """
        self.errors = errors
        error_messages = [f"{field}: {msg}" for field, msg in errors]
        super().__init__("\n".join(error_messages))


@dataclass
class FieldSpec:
    """Field specification for validation."""

    name: str
    type: type
    required: bool = False
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[List[Any]] = None
    pattern: Optional[str] = None


# Configuration schema definitions
PROVIDER_SCHEMA: Dict[str, FieldSpec] = {
    "name": FieldSpec("name", str, required=True),
    "enabled": FieldSpec("enabled", bool, default=True),
    "auto_discover": FieldSpec("auto_discover", bool, default=True),
    "settings": FieldSpec("settings", dict, default={}),
}

SCHEDULER_SCHEMA: Dict[str, FieldSpec] = {
    "default_timeout": FieldSpec(
        "default_timeout", int, default=600, min_value=60, max_value=3600
    ),
    "default_max_turns": FieldSpec(
        "default_max_turns", int, default=50, min_value=1, max_value=500
    ),
    "retry_attempts": FieldSpec(
        "retry_attempts", int, default=3, min_value=0, max_value=10
    ),
    "retry_delay": FieldSpec(
        "retry_delay", float, default=5.0, min_value=0.1, max_value=60.0
    ),
    "parallel_execution": FieldSpec("parallel_execution", bool, default=False),
    "max_parallel_tasks": FieldSpec(
        "max_parallel_tasks", int, default=1, min_value=1, max_value=10
    ),
}

REPORT_SCHEMA: Dict[str, FieldSpec] = {
    "default_format": FieldSpec(
        "default_format", str, default="json", choices=["json", "text", "html"]
    ),
    "output_directory": FieldSpec(
        "output_directory", str, default=".ai-harness/reports"
    ),
    "include_timestamp": FieldSpec("include_timestamp", bool, default=True),
    "templates_directory": FieldSpec("templates_directory", str, default=None),
}

LOGGING_SCHEMA: Dict[str, FieldSpec] = {
    "level": FieldSpec(
        "level", str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    ),
    "format": FieldSpec(
        "format", str, default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ),
    "file": FieldSpec("file", str, default=None),
    "console": FieldSpec("console", bool, default=True),
}

MAIN_SCHEMA: Dict[str, FieldSpec] = {
    "default_provider": FieldSpec("default_provider", str, default="iflow"),
    "project_name": FieldSpec("project_name", str, default=None),
    "project_root": FieldSpec("project_root", str, default=None),
    "feature_list_path": FieldSpec(
        "feature_list_path", str, default="feature_list.json"
    ),
    "progress_file": FieldSpec("progress_file", str, default="claude-progress.txt"),
    "debug_mode": FieldSpec("debug_mode", bool, default=False),
    "dry_run": FieldSpec("dry_run", bool, default=False),
}


class ConfigSchema:
    """
    Configuration schema validator.

    Validates configuration dictionaries against defined schemas.

    Example:
        schema = ConfigSchema()
        errors = schema.validate(config_dict)
        if errors:
            raise ConfigValidationError(errors)
    """

    def __init__(self):
        """Initialize schema validator."""
        self.schemas = {
            "main": MAIN_SCHEMA,
            "scheduler": SCHEDULER_SCHEMA,
            "report": REPORT_SCHEMA,
            "logging": LOGGING_SCHEMA,
            "provider": PROVIDER_SCHEMA,
        }

    def validate_field(
        self,
        value: Any,
        spec: FieldSpec,
        path: str = "",
    ) -> Optional[str]:
        """
        Validate a single field.

        Args:
            value: Field value to validate.
            spec: Field specification.
            path: Field path for error messages.

        Returns:
            Error message if validation fails, None otherwise.
        """
        field_path = f"{path}.{spec.name}" if path else spec.name

        # Check required
        if value is None:
            if spec.required:
                return f"Required field '{field_path}' is missing"
            return None

        # Check type
        if not isinstance(value, spec.type):
            # Special case: int is acceptable for float fields
            if spec.type == float and isinstance(value, int):
                value = float(value)
            else:
                return f"Field '{field_path}' must be {spec.type.__name__}, got {type(value).__name__}"

        # Check choices
        if spec.choices and value not in spec.choices:
            return f"Field '{field_path}' must be one of {spec.choices}, got '{value}'"

        # Check numeric ranges
        if isinstance(value, (int, float)):
            if spec.min_value is not None and value < spec.min_value:
                return f"Field '{field_path}' must be >= {spec.min_value}, got {value}"
            if spec.max_value is not None and value > spec.max_value:
                return f"Field '{field_path}' must be <= {spec.max_value}, got {value}"

        # Check pattern
        if spec.pattern and isinstance(value, str):
            if not re.match(spec.pattern, value):
                return f"Field '{field_path}' does not match pattern {spec.pattern}"

        return None

    def validate_section(
        self,
        data: Dict[str, Any],
        schema_name: str,
        path: str = "",
    ) -> List[Tuple[str, str]]:
        """
        Validate a configuration section.

        Args:
            data: Configuration dictionary.
            schema_name: Name of schema to use.
            path: Base path for error messages.

        Returns:
            List of (field, message) errors.
        """
        errors: List[Tuple[str, str]] = []

        if schema_name not in self.schemas:
            errors.append((path, f"Unknown schema: {schema_name}"))
            return errors

        schema = self.schemas[schema_name]

        for field_name, spec in schema.items():
            value = data.get(field_name, spec.default)
            error = self.validate_field(value, spec, path)
            if error:
                errors.append((f"{path}.{field_name}" if path else field_name, error))

        return errors

    def validate_config(self, config: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Validate full configuration.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            List of (field, message) errors.
        """
        errors: List[Tuple[str, str]] = []

        # Validate main section
        errors.extend(self.validate_section(config, "main"))

        # Validate scheduler section
        if "scheduler" in config:
            errors.extend(
                self.validate_section(config["scheduler"], "scheduler", "scheduler")
            )

        # Validate report section
        if "report" in config:
            errors.extend(self.validate_section(config["report"], "report", "report"))

        # Validate logging section
        if "logging" in config:
            errors.extend(
                self.validate_section(config["logging"], "logging", "logging")
            )

        # Validate providers
        if "providers" in config:
            for provider_name, provider_config in config["providers"].items():
                provider_errors = self.validate_section(
                    provider_config, "provider", f"providers.{provider_name}"
                )
                errors.extend(provider_errors)

        return errors

    def validate_and_raise(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration and raise exception if invalid.

        Args:
            config: Configuration dictionary to validate.

        Raises:
            ConfigValidationError: If validation fails.
        """
        errors = self.validate_config(config)
        if errors:
            raise ConfigValidationError(errors)


def validate_config(config: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Convenience function to validate configuration.

    Args:
        config: Configuration dictionary.

    Returns:
        List of validation errors.
    """
    schema = ConfigSchema()
    return schema.validate_config(config)


def validate_and_raise(config: Dict[str, Any]) -> None:
    """
    Validate configuration and raise on errors.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigValidationError: If validation fails.
    """
    schema = ConfigSchema()
    schema.validate_and_raise(config)
