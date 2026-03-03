"""
AI Harness - Configuration Manager Module

This module implements the configuration management system with
support for global and project-level configurations.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


# Default configuration file names
GLOBAL_CONFIG_NAME = "config.yaml"
PROJECT_CONFIG_DIR = ".ai-harness"
PROJECT_CONFIG_NAME = "config.yaml"


@dataclass
class ProviderConfig:
    """Provider-specific configuration"""

    name: str
    enabled: bool = True
    auto_discover: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    """Scheduler configuration"""

    default_timeout: int = 600
    default_max_turns: int = 50
    retry_attempts: int = 3
    retry_delay: float = 5.0
    parallel_execution: bool = False
    max_parallel_tasks: int = 1


@dataclass
class ReportConfig:
    """Report configuration"""

    default_format: str = "json"
    output_directory: str = ".ai-harness/reports"
    include_timestamp: bool = True
    templates_directory: Optional[str] = None


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True


@dataclass
class AIHarnessConfig:
    """
    Main configuration class for AI Harness.

    This class holds all configuration settings and supports
    merging from multiple sources with proper precedence.
    """

    # Provider settings
    default_provider: str = "iflow"
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    # Scheduler settings
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)

    # Report settings
    report: ReportConfig = field(default_factory=ReportConfig)

    # Logging settings
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Project settings
    project_name: Optional[str] = None
    project_root: Optional[str] = None

    # Feature list settings
    feature_list_path: str = "feature_list.json"
    progress_file: str = "claude-progress.txt"

    # Advanced settings
    debug_mode: bool = False
    dry_run: bool = False


class ConfigManager:
    """
    Configuration manager with multi-level configuration support.

    Configuration precedence (highest to lowest):
    1. Environment variables (AI_HARNESS_*)
    2. Project-level config (.ai-harness/config.yaml)
    3. Global config (~/.ai-harness/config.yaml)
    4. Default values

    Example:
        manager = ConfigManager()
        manager.load()
        config = manager.get_config()
    """

    def __init__(
        self,
        global_config_dir: Optional[Path] = None,
        project_config_dir: Optional[Path] = None,
    ):
        """
        Initialize configuration manager.

        Args:
            global_config_dir: Directory for global config (default: ~/.ai-harness)
            project_config_dir: Directory for project config (default: ./.ai-harness)
        """
        self.global_config_dir = global_config_dir or Path.home() / ".ai-harness"
        self.project_config_dir = project_config_dir

        self._config: Optional[AIHarnessConfig] = None
        self._loaded: bool = False

    def find_project_config_dir(
        self, start_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Find the project configuration directory by searching upward.

        Args:
            start_dir: Starting directory (default: current directory)

        Returns:
            Path to .ai-harness directory or None if not found.
        """
        if start_dir is None:
            start_dir = Path.cwd()

        current = start_dir.resolve()

        while current != current.parent:
            config_dir = current / PROJECT_CONFIG_DIR
            if config_dir.exists():
                return config_dir
            current = current.parent

        return None

    def get_global_config_path(self) -> Path:
        """Get the global configuration file path."""
        return self.global_config_dir / GLOBAL_CONFIG_NAME

    def get_project_config_path(self) -> Optional[Path]:
        """Get the project configuration file path."""
        if self.project_config_dir:
            return self.project_config_dir / PROJECT_CONFIG_NAME
        return None

    def load_yaml(self, path: Path) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML file.

        Returns:
            Dict: Configuration dictionary.
        """
        if not path.exists():
            return {}

        if yaml is None:
            logger.warning("PyYAML not installed, cannot load YAML config")
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            return {}

    def load_env_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Environment variables use the prefix AI_HARNESS_ and
        nested keys use double underscore.

        Examples:
            AI_HARNESS_DEFAULT_PROVIDER=claude
            AI_HARNESS_SCHEDULER__DEFAULT_TIMEOUT=1200
            AI_HARNESS_REPORT__DEFAULT_FORMAT=html

        Returns:
            Dict: Configuration dictionary.
        """
        config: Dict[str, Any] = {}
        prefix = "AI_HARNESS_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Remove prefix and convert to lowercase
            config_key = key[len(prefix) :].lower()

            # Handle nested keys (double underscore)
            parts = config_key.split("__")

            # Build nested dict
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the value
            current[parts[-1]] = self._parse_env_value(value)

        return config

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    def merge_configs(self, *configs: Dict[str, Any]) -> AIHarnessConfig:
        """
        Merge multiple configuration dictionaries.

        Later configs override earlier ones.

        Args:
            *configs: Configuration dictionaries to merge.

        Returns:
            AIHarnessConfig: Merged configuration.
        """
        merged: Dict[str, Any] = {}

        for config in configs:
            self._deep_merge(merged, config)

        return self._dict_to_config(merged)

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _dict_to_config(self, data: Dict[str, Any]) -> AIHarnessConfig:
        """Convert dictionary to AIHarnessConfig object."""
        config = AIHarnessConfig()

        # Simple fields
        if "default_provider" in data:
            config.default_provider = data["default_provider"]
        if "project_name" in data:
            config.project_name = data["project_name"]
        if "project_root" in data:
            config.project_root = data["project_root"]
        if "feature_list_path" in data:
            config.feature_list_path = data["feature_list_path"]
        if "progress_file" in data:
            config.progress_file = data["progress_file"]
        if "debug_mode" in data:
            config.debug_mode = data["debug_mode"]
        if "dry_run" in data:
            config.dry_run = data["dry_run"]

        # Scheduler config
        if "scheduler" in data:
            sched = data["scheduler"]
            config.scheduler = SchedulerConfig(
                default_timeout=sched.get("default_timeout", 600),
                default_max_turns=sched.get("default_max_turns", 50),
                retry_attempts=sched.get("retry_attempts", 3),
                retry_delay=sched.get("retry_delay", 5.0),
                parallel_execution=sched.get("parallel_execution", False),
                max_parallel_tasks=sched.get("max_parallel_tasks", 1),
            )

        # Report config
        if "report" in data:
            rep = data["report"]
            config.report = ReportConfig(
                default_format=rep.get("default_format", "json"),
                output_directory=rep.get("output_directory", ".ai-harness/reports"),
                include_timestamp=rep.get("include_timestamp", True),
                templates_directory=rep.get("templates_directory"),
            )

        # Logging config
        if "logging" in data:
            log = data["logging"]
            config.logging = LoggingConfig(
                level=log.get("level", "INFO"),
                format=log.get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                file=log.get("file"),
                console=log.get("console", True),
            )

        # Provider configs
        if "providers" in data:
            for name, prov in data["providers"].items():
                config.providers[name] = ProviderConfig(
                    name=name,
                    enabled=prov.get("enabled", True),
                    auto_discover=prov.get("auto_discover", True),
                    settings=prov.get("settings", {}),
                )

        return config

    def load(
        self,
        project_dir: Optional[Path] = None,
        reload: bool = False,
    ) -> AIHarnessConfig:
        """
        Load configuration from all sources.

        Args:
            project_dir: Project directory (optional, auto-detected if not provided).
            reload: Force reload even if already loaded.

        Returns:
            AIHarnessConfig: Loaded configuration.
        """
        if self._loaded and not reload:
            return self._config if self._config else AIHarnessConfig()

        # Find project config directory if not provided
        if project_dir and not self.project_config_dir:
            self.project_config_dir = project_dir / PROJECT_CONFIG_DIR
        elif not self.project_config_dir:
            self.project_config_dir = self.find_project_config_dir()

        # Load from sources (in precedence order: lowest to highest)
        configs: List[Dict[str, Any]] = []

        # 1. Defaults (built-in)
        configs.append({})

        # 2. Global config
        global_path = self.get_global_config_path()
        if global_path.exists():
            configs.append(self.load_yaml(global_path))

        # 3. Project config
        project_path = self.get_project_config_path()
        if project_path and project_path.exists():
            configs.append(self.load_yaml(project_path))

        # 4. Environment variables
        env_config = self.load_env_config()
        if env_config:
            configs.append(env_config)

        # Merge all
        self._config = self.merge_configs(*configs)
        self._loaded = True

        return self._config

    def get_config(self) -> AIHarnessConfig:
        """
        Get current configuration.

        Returns:
            AIHarnessConfig: Current configuration.
        """
        if not self._loaded:
            return self.load()
        return self._config if self._config else AIHarnessConfig()

    def save_config(
        self,
        config: AIHarnessConfig,
        path: Path,
        create_parents: bool = True,
    ) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration to save.
            path: Destination file path.
            create_parents: Create parent directories if needed.
        """
        if yaml is None:
            raise RuntimeError("PyYAML required for saving configuration")

        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        data = self._config_to_dict(config)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _config_to_dict(self, config: AIHarnessConfig) -> Dict[str, Any]:
        """Convert AIHarnessConfig to dictionary."""
        data: Dict[str, Any] = {
            "default_provider": config.default_provider,
            "feature_list_path": config.feature_list_path,
            "progress_file": config.progress_file,
            "debug_mode": config.debug_mode,
            "dry_run": config.dry_run,
        }

        if config.project_name:
            data["project_name"] = config.project_name
        if config.project_root:
            data["project_root"] = config.project_root

        # Scheduler
        data["scheduler"] = {
            "default_timeout": config.scheduler.default_timeout,
            "default_max_turns": config.scheduler.default_max_turns,
            "retry_attempts": config.scheduler.retry_attempts,
            "retry_delay": config.scheduler.retry_delay,
            "parallel_execution": config.scheduler.parallel_execution,
            "max_parallel_tasks": config.scheduler.max_parallel_tasks,
        }

        # Report
        data["report"] = {
            "default_format": config.report.default_format,
            "output_directory": config.report.output_directory,
            "include_timestamp": config.report.include_timestamp,
        }
        if config.report.templates_directory:
            data["report"]["templates_directory"] = config.report.templates_directory

        # Logging
        data["logging"] = {
            "level": config.logging.level,
            "format": config.logging.format,
            "console": config.logging.console,
        }
        if config.logging.file:
            data["logging"]["file"] = config.logging.file

        # Providers
        if config.providers:
            data["providers"] = {}
            for name, prov in config.providers.items():
                data["providers"][name] = {
                    "enabled": prov.enabled,
                    "auto_discover": prov.auto_discover,
                    "settings": prov.settings,
                }

        return data


# Global config manager instance
_global_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ConfigManager()
    return _global_manager


def get_config() -> AIHarnessConfig:
    """Convenience function to get current configuration."""
    return get_config_manager().get_config()
