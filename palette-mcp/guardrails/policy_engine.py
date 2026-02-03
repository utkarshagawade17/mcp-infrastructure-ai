"""
AI Guardrails Policy Engine for Palette AI Ops Toolkit.

This module provides governance and safety controls for AI-driven operations:
- Input validation (prevent harmful prompts)
- Action validation (ensure AI recommendations are safe)
- Policy enforcement (organizational rules)
- Audit logging (compliance tracking)

Critical for enterprise AI rollout as mentioned in the JD:
"engaging with risk compliance and legal to define the guardrails"
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PolicySeverity(Enum):
    """Severity levels for policy violations."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKING = "blocking"


class PolicyAction(Enum):
    """Actions to take when policy is violated."""

    LOG = "log"
    WARN = "warn"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class PolicyViolation:
    """Represents a policy violation."""

    policy_name: str
    severity: PolicySeverity
    message: str
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    remediation: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of policy validation."""

    is_valid: bool
    violations: list[PolicyViolation] = field(default_factory=list)
    warnings: list[PolicyViolation] = field(default_factory=list)
    action_required: PolicyAction = PolicyAction.LOG
    requires_approval: bool = False
    approval_reason: Optional[str] = None


class PolicyEngine:
    """
    Central policy engine for AI guardrails.

    Implements:
    - Policy loading from YAML files
    - Rule evaluation against actions/configurations
    - Approval workflow triggers
    - Audit trail generation
    """

    def __init__(self, policy_path: str = "./guardrails/policies"):
        self.policy_path = Path(policy_path)
        self.policies: dict[str, dict] = {}
        self.audit_log: list[dict] = []
        self._load_policies()

    def _load_policies(self):
        """Load all policy files from the policy directory."""
        if not self.policy_path.exists():
            logger.warning(f"Policy path {self.policy_path} does not exist, using defaults")
            self._load_default_policies()
            return

        for policy_file in self.policy_path.glob("*.yaml"):
            try:
                with open(policy_file) as f:
                    policy_data = yaml.safe_load(f)
                    policy_name = policy_file.stem
                    self.policies[policy_name] = policy_data
                    logger.info(f"Loaded policy: {policy_name}")
            except Exception as e:
                logger.error(f"Failed to load policy {policy_file}: {e}")

    def _load_default_policies(self):
        """Load default built-in policies."""
        self.policies = {
            "security": {
                "name": "security",
                "description": "Security-related policies",
                "rules": [
                    {
                        "name": "no_privileged_containers",
                        "description": "Prevent creation of privileged containers",
                        "severity": "critical",
                        "action": "block",
                        "condition": "action.creates_privileged_container == true",
                    },
                    {
                        "name": "no_host_network",
                        "description": "Prevent use of host network",
                        "severity": "critical",
                        "action": "block",
                        "condition": "action.uses_host_network == true",
                    },
                    {
                        "name": "require_resource_limits",
                        "description": "All containers must have resource limits",
                        "severity": "warning",
                        "action": "warn",
                        "condition": "action.has_resource_limits == false",
                    },
                    {
                        "name": "no_public_load_balancer",
                        "description": "Require approval for public load balancers",
                        "severity": "warning",
                        "action": "require_approval",
                        "condition": "action.creates_public_lb == true",
                    },
                ],
            },
            "cost": {
                "name": "cost",
                "description": "Cost governance policies",
                "rules": [
                    {
                        "name": "max_node_count",
                        "description": "Limit maximum nodes per cluster",
                        "severity": "warning",
                        "action": "require_approval",
                        "condition": "action.node_count > 10",
                        "threshold": 10,
                    },
                    {
                        "name": "no_gpu_without_approval",
                        "description": "GPU instances require approval",
                        "severity": "warning",
                        "action": "require_approval",
                        "condition": "action.uses_gpu == true",
                    },
                    {
                        "name": "max_instance_size",
                        "description": "Limit instance sizes",
                        "severity": "info",
                        "action": "warn",
                        "condition": "action.instance_size in ['xlarge', '2xlarge', '4xlarge']",
                    },
                ],
            },
            "compliance": {
                "name": "compliance",
                "description": "Compliance framework policies",
                "rules": [
                    {
                        "name": "encryption_at_rest",
                        "description": "Storage must be encrypted",
                        "severity": "critical",
                        "action": "block",
                        "condition": "action.storage_encrypted == false",
                    },
                    {
                        "name": "audit_logging",
                        "description": "Audit logging must be enabled",
                        "severity": "warning",
                        "action": "warn",
                        "condition": "action.audit_logging == false",
                    },
                    {
                        "name": "approved_regions_only",
                        "description": "Deploy only to approved regions",
                        "severity": "critical",
                        "action": "block",
                        "condition": "action.region not in approved_regions",
                    },
                ],
            },
        }

    def validate_action(
        self,
        action: dict[str, Any],
        policy_sets: list[str] = None,
        context: dict[str, Any] = None,
    ) -> ValidationResult:
        """
        Validate a proposed action against policies.

        Args:
            action: The action to validate (e.g., create cluster, deploy app)
            policy_sets: List of policy sets to check (default: all)
            context: Additional context for evaluation

        Returns:
            ValidationResult with violations and recommended action
        """
        violations = []
        warnings = []
        requires_approval = False
        approval_reasons = []

        # Determine which policies to check
        policy_sets = policy_sets or list(self.policies.keys())

        for policy_set_name in policy_sets:
            if policy_set_name not in self.policies:
                continue

            policy_set = self.policies[policy_set_name]

            for rule in policy_set.get("rules", []):
                result = self._evaluate_rule(rule, action, context)

                if result["violated"]:
                    violation = PolicyViolation(
                        policy_name=rule["name"],
                        severity=PolicySeverity(rule.get("severity", "warning")),
                        message=rule["description"],
                        details={"rule": rule, "action": action},
                        remediation=rule.get("remediation"),
                    )

                    if rule.get("action") == "block":
                        violations.append(violation)
                    elif rule.get("action") == "require_approval":
                        requires_approval = True
                        approval_reasons.append(rule["description"])
                        warnings.append(violation)
                    else:
                        warnings.append(violation)

        # Determine overall action
        if violations:
            action_required = PolicyAction.BLOCK
            is_valid = False
        elif requires_approval:
            action_required = PolicyAction.REQUIRE_APPROVAL
            is_valid = True  # Valid but needs approval
        elif warnings:
            action_required = PolicyAction.WARN
            is_valid = True
        else:
            action_required = PolicyAction.LOG
            is_valid = True

        result = ValidationResult(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            action_required=action_required,
            requires_approval=requires_approval,
            approval_reason="; ".join(approval_reasons) if approval_reasons else None,
        )

        # Log to audit trail
        self._log_audit(action, result)

        return result

    def _evaluate_rule(self, rule: dict, action: dict, context: dict = None) -> dict:
        """
        Evaluate a single rule against an action.

        This is a simplified rule evaluation. In production, you might use
        a proper rule engine like OPA (Open Policy Agent) or CEL.
        """
        context = context or {}

        # Simple condition evaluation
        condition = rule.get("condition", "")

        # Check common conditions
        violated = False

        # Privileged container check
        if "creates_privileged_container" in condition:
            violated = action.get("security_context", {}).get("privileged", False)

        # Host network check
        elif "uses_host_network" in condition:
            violated = action.get("host_network", False)

        # Resource limits check
        elif "has_resource_limits" in condition:
            violated = not action.get("resources", {}).get("limits")

        # Public LB check
        elif "creates_public_lb" in condition:
            violated = action.get("service_type") == "LoadBalancer" and action.get("load_balancer_type") == "public"

        # Node count check
        elif "node_count" in condition:
            threshold = rule.get("threshold", 10)
            violated = action.get("node_count", 0) > threshold

        # GPU check
        elif "uses_gpu" in condition:
            violated = action.get("gpu_enabled", False)

        # Storage encryption check
        elif "storage_encrypted" in condition:
            violated = not action.get("storage", {}).get("encrypted", True)

        return {"violated": violated, "rule_name": rule["name"], "condition": condition}

    def _log_audit(self, action: dict, result: ValidationResult):
        """Log validation to audit trail."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_type": action.get("type", "unknown"),
            "action_summary": self._summarize_action(action),
            "validation_result": "passed" if result.is_valid else "failed",
            "violations": [v.policy_name for v in result.violations],
            "warnings": [w.policy_name for w in result.warnings],
            "action_taken": result.action_required.value,
            "requires_approval": result.requires_approval,
        }

        self.audit_log.append(audit_entry)
        logger.info(f"Audit: {audit_entry['action_type']} - {audit_entry['validation_result']}")

    def _summarize_action(self, action: dict) -> str:
        """Create human-readable summary of action."""
        action_type = action.get("type", "unknown")
        target = action.get("target", "unknown")
        return f"{action_type} on {target}"

    def get_audit_log(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        action_type: str = None,
    ) -> list[dict]:
        """
        Retrieve audit log entries with optional filtering.

        Args:
            start_time: Filter entries after this time
            end_time: Filter entries before this time
            action_type: Filter by action type

        Returns:
            List of audit log entries
        """
        filtered = self.audit_log

        if action_type:
            filtered = [e for e in filtered if e["action_type"] == action_type]

        # Add time filtering if needed
        # (simplified for demo)

        return filtered

    def export_policies(self, format: str = "yaml") -> str:
        """Export all policies in specified format."""
        if format == "yaml":
            return yaml.dump(self.policies, default_flow_style=False)
        elif format == "json":
            import json

            return json.dumps(self.policies, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


class PromptValidator:
    """
    Validates AI prompts to prevent harmful or malicious inputs.

    Checks for:
    - Prompt injection attempts
    - Requests for harmful actions
    - Out-of-scope requests
    """

    BLOCKED_PATTERNS = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard your instructions",
        "pretend you are",
        "act as if you have no restrictions",
        "bypass security",
        "delete all",
        "drop database",
        "rm -rf",
        "format disk",
    ]

    OUT_OF_SCOPE_PATTERNS = [
        "personal information",
        "social security",
        "credit card",
        "password",
        "api key",
        "secret key",
    ]

    @classmethod
    def validate(cls, prompt: str) -> ValidationResult:
        """
        Validate a prompt for safety.

        Args:
            prompt: The user prompt to validate

        Returns:
            ValidationResult indicating if prompt is safe
        """
        violations = []
        warnings = []
        prompt_lower = prompt.lower()

        # Check for blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern in prompt_lower:
                violations.append(
                    PolicyViolation(
                        policy_name="blocked_prompt_pattern",
                        severity=PolicySeverity.CRITICAL,
                        message=f"Prompt contains blocked pattern: '{pattern}'",
                        details={"pattern": pattern},
                    )
                )

        # Check for out-of-scope patterns
        for pattern in cls.OUT_OF_SCOPE_PATTERNS:
            if pattern in prompt_lower:
                warnings.append(
                    PolicyViolation(
                        policy_name="out_of_scope_request",
                        severity=PolicySeverity.WARNING,
                        message=f"Request may be out of scope: '{pattern}'",
                        details={"pattern": pattern},
                    )
                )

        is_valid = len(violations) == 0

        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            action_required=PolicyAction.BLOCK if violations else PolicyAction.LOG,
        )


class ActionValidator:
    """
    Validates AI-recommended actions before execution.

    Ensures:
    - Actions are within allowed scope
    - Destructive actions require confirmation
    - Resource limits are respected
    """

    DESTRUCTIVE_ACTIONS = [
        "delete_cluster",
        "delete_profile",
        "scale_down",
        "terminate_node",
        "remove_pack",
    ]

    REQUIRES_APPROVAL = [
        "create_cluster",
        "upgrade_cluster",
        "modify_production",
        "change_network",
    ]

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def validate(self, action: dict[str, Any], auto_approve: bool = False) -> ValidationResult:
        """
        Validate an action before execution.

        Args:
            action: The action to validate
            auto_approve: Skip approval checks (for automation)

        Returns:
            ValidationResult with validation status
        """
        # First, check against policy engine
        policy_result = self.policy_engine.validate_action(action)

        # Additional action-specific checks
        action_type = action.get("type", "")

        if action_type in self.DESTRUCTIVE_ACTIONS:
            if not auto_approve:
                policy_result.requires_approval = True
                policy_result.approval_reason = f"Destructive action '{action_type}' requires explicit approval"
                policy_result.action_required = PolicyAction.REQUIRE_APPROVAL

        elif action_type in self.REQUIRES_APPROVAL:
            if not auto_approve:
                policy_result.requires_approval = True
                policy_result.approval_reason = f"Action '{action_type}' requires approval per policy"

        return policy_result
