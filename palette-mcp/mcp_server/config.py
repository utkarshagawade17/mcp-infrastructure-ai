"""
Configuration management for Palette AI Ops Toolkit.

Handles:
- Environment variable configuration
- API credentials management
- Feature flags
- Logging configuration
"""

import os
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class PaletteConfig:
    """Configuration for Palette API connection."""

    # API Configuration
    api_endpoint: str = field(default_factory=lambda: os.getenv("PALETTE_API_ENDPOINT", "https://api.spectrocloud.com"))
    api_key: str = field(default_factory=lambda: os.getenv("PALETTE_API_KEY", ""))
    project_uid: Optional[str] = field(default_factory=lambda: os.getenv("PALETTE_PROJECT_UID"))

    # Timeout Configuration
    request_timeout: int = field(default_factory=lambda: int(os.getenv("PALETTE_REQUEST_TIMEOUT", "30")))

    # AI/LLM Configuration
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "local"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama3"))
    llm_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("LLM_ENDPOINT"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))

    # Feature Flags
    enable_guardrails: bool = field(default_factory=lambda: os.getenv("ENABLE_GUARDRAILS", "true").lower() == "true")
    enable_cost_analysis: bool = field(
        default_factory=lambda: os.getenv("ENABLE_COST_ANALYSIS", "true").lower() == "true"
    )
    enable_security_scan: bool = field(
        default_factory=lambda: os.getenv("ENABLE_SECURITY_SCAN", "true").lower() == "true"
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            logger.warning("PALETTE_API_KEY not set. Running in demo mode with mock data.")

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @property
    def auth_headers(self) -> dict:
        """Generate authentication headers for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["apiKey"] = self.api_key

        if self.project_uid:
            headers["ProjectUid"] = self.project_uid

        return headers

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode (no API key)."""
        return not bool(self.api_key)

    def get_llm_config(self) -> dict:
        """Get LLM configuration based on provider."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.llm_model or "gpt-4o-mini",
            }
        elif self.llm_provider == "local":
            return {
                "provider": "local",
                "endpoint": self.llm_endpoint or "http://localhost:11434/v1",
                "model": self.llm_model or "llama3",
            }
        else:
            return {
                "provider": self.llm_provider,
                "endpoint": self.llm_endpoint,
                "model": self.llm_model,
            }


@dataclass
class GuardrailsConfig:
    """Configuration for AI guardrails and governance."""

    # Policy Configuration
    policy_path: str = field(default_factory=lambda: os.getenv("GUARDRAILS_POLICY_PATH", "./guardrails/policies"))

    # Validation Settings
    strict_mode: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_STRICT", "false").lower() == "true")

    # Approval Requirements
    require_approval_for_delete: bool = field(
        default_factory=lambda: os.getenv("REQUIRE_APPROVAL_DELETE", "true").lower() == "true"
    )
    require_approval_for_scale: bool = field(
        default_factory=lambda: os.getenv("REQUIRE_APPROVAL_SCALE", "false").lower() == "true"
    )

    # Cost Guardrails
    max_cluster_cost_daily: Optional[float] = field(
        default_factory=lambda: float(os.getenv("MAX_CLUSTER_COST_DAILY", "0")) or None
    )

    # Security Guardrails
    block_public_endpoints: bool = field(
        default_factory=lambda: os.getenv("BLOCK_PUBLIC_ENDPOINTS", "true").lower() == "true"
    )
    require_resource_limits: bool = field(
        default_factory=lambda: os.getenv("REQUIRE_RESOURCE_LIMITS", "true").lower() == "true"
    )
