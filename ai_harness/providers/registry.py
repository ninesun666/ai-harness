"""
AI Harness - Provider Registry Module

This module implements the plugin discovery and registration system
using setuptools entry_points.
"""

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import entry_points

from .base import BaseAIProvider, ProviderInfo, ProviderNotFoundError

logger = logging.getLogger(__name__)


# Entry point group name for AI Harness providers
ENTRY_POINT_GROUP = "ai_harness.providers"


class ProviderRegistry:
    """
    Registry for AI tool providers.

    This class manages provider discovery, registration, and instantiation.
    It uses setuptools entry_points for automatic plugin discovery.

    Example:
        registry = ProviderRegistry()
        registry.discover_providers()

        # List available providers
        providers = registry.list_providers()

        # Get a specific provider
        iflow = registry.get_provider("iflow")
    """

    def __init__(self):
        """Initialize the registry."""
        self._providers: Dict[str, Type[BaseAIProvider]] = {}
        self._instances: Dict[str, BaseAIProvider] = {}
        self._discovered: bool = False

    def discover_providers(self) -> List[str]:
        """
        Discover all registered providers via entry_points.

        Returns:
            List[str]: Names of discovered providers.
        """
        if self._discovered:
            return list(self._providers.keys())

        discovered_names = []

        # Get entry points for the provider group
        eps = entry_points()

        # Handle different entry_points API versions
        if hasattr(eps, "select"):
            # Python 3.10+ style
            provider_eps = eps.select(group=ENTRY_POINT_GROUP)
        else:
            # Python 3.8-3.9 style
            provider_eps = eps.get(ENTRY_POINT_GROUP, [])

        for ep in provider_eps:
            try:
                # Load the provider class
                provider_class = ep.load()

                # Validate it's a proper provider
                if not issubclass(provider_class, BaseAIProvider):
                    logger.warning(
                        f"Entry point {ep.name} is not a BaseAIProvider subclass"
                    )
                    continue

                # Register the provider
                provider_name = provider_class.__name__.replace("Provider", "").lower()
                self._providers[provider_name] = provider_class
                discovered_names.append(provider_name)

                logger.info(f"Discovered provider: {provider_name} ({ep.value})")

            except Exception as e:
                logger.error(f"Failed to load provider {ep.name}: {e}")

        self._discovered = True
        return discovered_names

    def register_provider(
        self, name: str, provider_class: Type[BaseAIProvider]
    ) -> None:
        """
        Manually register a provider class.

        Args:
            name: Provider name.
            provider_class: Provider class (must be BaseAIProvider subclass).

        Raises:
            TypeError: If provider_class is not a BaseAIProvider subclass.
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise TypeError(f"{provider_class} must be a subclass of BaseAIProvider")

        self._providers[name.lower()] = provider_class
        logger.info(f"Registered provider: {name}")

    def get_provider(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        auto_discover: bool = True,
    ) -> BaseAIProvider:
        """
        Get or create a provider instance.

        Args:
            name: Provider name.
            config: Optional configuration for initialization.
            auto_discover: Whether to auto-discover if not found.

        Returns:
            BaseAIProvider: Provider instance.

        Raises:
            ProviderNotFoundError: If provider is not found.
        """
        name = name.lower()

        # Auto discover if needed
        if auto_discover and not self._discovered:
            self.discover_providers()

        # Return existing instance if available
        if name in self._instances:
            return self._instances[name]

        # Create new instance
        if name not in self._providers:
            raise ProviderNotFoundError(
                f"Provider '{name}' not found. "
                f"Available: {list(self._providers.keys())}"
            )

        provider_class = self._providers[name]
        instance = provider_class()

        # Initialize the provider
        instance.initialize(config)

        # Cache the instance
        self._instances[name] = instance

        return instance

    def list_providers(self) -> List[ProviderInfo]:
        """
        List all registered provider information.

        Returns:
            List[ProviderInfo]: List of provider information.
        """
        if not self._discovered:
            self.discover_providers()

        infos = []
        for name, provider_class in self._providers.items():
            try:
                # Create temporary instance to get info
                temp_instance = provider_class()
                infos.append(temp_instance.info)
            except Exception as e:
                logger.warning(f"Failed to get info for {name}: {e}")

        return infos

    def has_provider(self, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Provider name.

        Returns:
            bool: True if registered, False otherwise.
        """
        if not self._discovered:
            self.discover_providers()

        return name.lower() in self._providers

    def clear_instances(self) -> None:
        """Clear all cached provider instances."""
        for instance in self._instances.values():
            try:
                instance.cleanup()
            except Exception as e:
                logger.warning(f"Failed to cleanup {instance.info.name}: {e}")

        self._instances.clear()

    def reload(self) -> None:
        """Force reload of all providers."""
        self._providers.clear()
        self._instances.clear()
        self._discovered = False
        self.discover_providers()


# Global registry instance
_global_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """
    Get the global provider registry.

    Returns:
        ProviderRegistry: The global registry instance.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ProviderRegistry()
    return _global_registry


def get_provider(name: str, config: Optional[Dict[str, Any]] = None) -> BaseAIProvider:
    """
    Convenience function to get a provider from the global registry.

    Args:
        name: Provider name.
        config: Optional configuration.

    Returns:
        BaseAIProvider: Provider instance.
    """
    return get_registry().get_provider(name, config)
