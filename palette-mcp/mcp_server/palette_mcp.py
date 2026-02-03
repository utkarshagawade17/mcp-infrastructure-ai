"""
Palette MCP Server - Model Context Protocol Server for Spectro Cloud Palette

MCP server implementation providing programmatic access to Palette operations:
- Cluster lifecycle management and monitoring
- Cluster profile configuration and application
- Infrastructure diagnostics and health analysis
- Policy enforcement and compliance validation
- AI guardrails for safe operation

License: MIT
"""

import logging
import sys
from pathlib import Path
from typing import Any
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .config import PaletteConfig
from .tools.cluster_tools import ClusterTools
from .tools.profile_tools import ProfileTools
from .tools.diagnostic_tools import DiagnosticTools

# Add guardrails to path for local imports
guardrails_path = Path(__file__).parent.parent / "guardrails"
sys.path.insert(0, str(guardrails_path.parent))

from guardrails.policy_engine import (  # noqa: E402
    PolicyEngine,
    ActionValidator,
    PromptValidator,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("palette")

# Initialize configuration
config = PaletteConfig()

# Initialize tool handlers
cluster_tools = ClusterTools(config)
profile_tools = ProfileTools(config)
diagnostic_tools = DiagnosticTools(config)

# Initialize guardrails
policy_engine = PolicyEngine(str(guardrails_path / "policies"))
action_validator = ActionValidator(policy_engine)


# =============================================================================
# CLUSTER MANAGEMENT TOOLS
# =============================================================================


@mcp.tool()
async def list_clusters(project_uid: str | None = None, status_filter: str | None = None) -> dict[str, Any]:
    """
    List all Kubernetes clusters managed by Palette.

    Args:
        project_uid: Optional project UID to filter clusters
        status_filter: Optional status filter (Running, Provisioning, Error, etc.)

    Returns:
        Dictionary containing list of clusters with their status and basic info
    """
    logger.info(f"Listing clusters (project={project_uid}, status={status_filter})")
    return await cluster_tools.list_clusters(project_uid, status_filter)


@mcp.tool()
async def get_cluster_details(cluster_uid: str) -> dict[str, Any]:
    """
    Get detailed information about a specific cluster.

    Args:
        cluster_uid: The unique identifier of the cluster

    Returns:
        Comprehensive cluster details including:
        - Cluster metadata and configuration
        - Node status and health
        - Applied cluster profile
        - Recent events
        - Resource utilization
    """
    logger.info(f"Getting cluster details for {cluster_uid}")
    return await cluster_tools.get_cluster_details(cluster_uid)


@mcp.tool()
async def get_cluster_events(cluster_uid: str, severity: str | None = None, limit: int = 50) -> dict[str, Any]:
    """
    Retrieve recent events for a cluster.

    Args:
        cluster_uid: The unique identifier of the cluster
        severity: Optional filter by severity (Info, Warning, Error, Critical)
        limit: Maximum number of events to return (default 50)

    Returns:
        List of recent cluster events with timestamps and details
    """
    logger.info(f"Getting events for cluster {cluster_uid}")
    return await cluster_tools.get_cluster_events(cluster_uid, severity, limit)


@mcp.tool()
async def get_cluster_cost(cluster_uid: str, time_range: str = "7d") -> dict[str, Any]:
    """
    Get cost analysis for a cluster.

    Args:
        cluster_uid: The unique identifier of the cluster
        time_range: Time range for cost analysis (1d, 7d, 30d)

    Returns:
        Cost breakdown by resource type and recommendations for optimization
    """
    logger.info(f"Getting cost analysis for cluster {cluster_uid}")
    return await cluster_tools.get_cluster_cost(cluster_uid, time_range)


# =============================================================================
# CLUSTER PROFILE TOOLS
# =============================================================================


@mcp.tool()
async def list_cluster_profiles(profile_type: str | None = None, cloud_type: str | None = None) -> dict[str, Any]:
    """
    List available cluster profiles.

    Args:
        profile_type: Filter by type (cluster, infra, add-on, system)
        cloud_type: Filter by cloud provider (aws, azure, gcp, vsphere, edge)

    Returns:
        List of cluster profiles with their versions and configurations
    """
    logger.info(f"Listing profiles (type={profile_type}, cloud={cloud_type})")
    return await profile_tools.list_profiles(profile_type, cloud_type)


@mcp.tool()
async def get_profile_details(profile_uid: str) -> dict[str, Any]:
    """
    Get detailed information about a cluster profile.

    Args:
        profile_uid: The unique identifier of the profile

    Returns:
        Profile details including:
        - All pack layers (OS, K8s, CNI, CSI, add-ons)
        - Configuration values
        - Version history
        - Associated clusters
    """
    logger.info(f"Getting profile details for {profile_uid}")
    return await profile_tools.get_profile_details(profile_uid)


@mcp.tool()
async def list_available_packs(layer: str | None = None, registry: str | None = None) -> dict[str, Any]:
    """
    List available packs from registries.

    Args:
        layer: Filter by layer (os, k8s, cni, csi, addon)
        registry: Filter by registry name

    Returns:
        List of available packs with versions and compatibility info
    """
    logger.info(f"Listing packs (layer={layer}, registry={registry})")
    return await profile_tools.list_packs(layer, registry)


# =============================================================================
# AI-POWERED DIAGNOSTIC TOOLS
# =============================================================================


@mcp.tool()
async def diagnose_cluster(cluster_uid: str, include_recommendations: bool = True) -> dict[str, Any]:
    """
    Perform automated diagnosis of cluster health and compliance.

    This tool analyzes:
    - Cluster events and alerts
    - Node health and resource utilization
    - Pod status and restart patterns
    - Configuration drift from profile
    - Security vulnerabilities (if Trivy integrated)

    Args:
        cluster_uid: The unique identifier of the cluster
        include_recommendations: Whether to include AI-generated recommendations

    Returns:
        Comprehensive health report with:
        - Overall health score (0-100)
        - Identified issues by severity
        - Root cause analysis
        - Actionable recommendations
    """
    logger.info(f"Diagnosing cluster {cluster_uid}")
    return await diagnostic_tools.diagnose_cluster(cluster_uid, include_recommendations)


@mcp.tool()
async def recommend_profile(
    workload_description: str,
    cloud_provider: str,
    requirements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Get cluster profile recommendations based on workload requirements.

    Args:
        workload_description: Natural language description of the workload
            (e.g., "ML training pipeline with GPU requirements")
        cloud_provider: Target cloud provider (aws, azure, gcp, vsphere, edge)
        requirements: Optional specific requirements:
            - min_nodes: Minimum number of nodes
            - gpu_required: Whether GPUs are needed
            - high_availability: HA requirements
            - compliance: Compliance frameworks (HIPAA, PCI-DSS, etc.)
            - budget: Cost constraints

    Returns:
        Ranked list of profile recommendations with:
        - Recommended packs and versions
        - Configuration suggestions
        - Cost estimates
        - Trade-off analysis
    """
    logger.info(f"Generating profile recommendation for: {workload_description}")
    return await diagnostic_tools.recommend_profile(workload_description, cloud_provider, requirements)


@mcp.tool()
async def validate_configuration(config: dict[str, Any], policy_set: str = "default") -> dict[str, Any]:
    """
    Validate a cluster or profile configuration against governance policies.

    Uses the AI guardrails policy engine to enforce:
    - Security policies (privileged containers, host network, etc.)
    - Cost policies (node limits, GPU approval, instance sizes)
    - Compliance policies (encryption, audit logging, approved regions)

    Args:
        config: The configuration to validate (cluster or profile spec)
        policy_set: Name of the policy set to validate against

    Returns:
        Validation results including:
        - Pass/fail status
        - Policy violations with severity
        - Remediation suggestions
        - Compliance score
    """
    logger.info(f"Validating configuration against {policy_set} policies")

    # First, run through guardrails policy engine
    guardrails_result = policy_engine.validate_action(
        config, policy_sets=[policy_set] if policy_set != "default" else None
    )

    # Get diagnostic tool validation
    diagnostic_result = await diagnostic_tools.validate_configuration(config, policy_set)

    # Merge results
    diagnostic_result["guardrails"] = {
        "is_valid": guardrails_result.is_valid,
        "requires_approval": guardrails_result.requires_approval,
        "approval_reason": guardrails_result.approval_reason,
        "action_required": guardrails_result.action_required.value,
        "violations": [
            {
                "policy": v.policy_name,
                "severity": v.severity.value,
                "message": v.message,
                "remediation": v.remediation,
            }
            for v in guardrails_result.violations
        ],
        "warnings": [
            {
                "policy": w.policy_name,
                "severity": w.severity.value,
                "message": w.message,
            }
            for w in guardrails_result.warnings
        ],
    }

    return diagnostic_result


@mcp.tool()
async def compare_clusters(cluster_uid_1: str, cluster_uid_2: str) -> dict[str, Any]:
    """
    Compare two clusters for configuration differences.

    Useful for:
    - Debugging why one cluster works and another doesn't
    - Ensuring consistency across environments
    - Identifying configuration drift

    Args:
        cluster_uid_1: First cluster UID
        cluster_uid_2: Second cluster UID

    Returns:
        Detailed comparison including:
        - Profile differences
        - Configuration differences
        - Resource allocation differences
        - Status comparison
    """
    logger.info(f"Comparing clusters {cluster_uid_1} and {cluster_uid_2}")
    return await diagnostic_tools.compare_clusters(cluster_uid_1, cluster_uid_2)


# =============================================================================
# AI GUARDRAILS TOOLS
# =============================================================================


@mcp.tool()
async def validate_prompt(prompt: str) -> dict[str, Any]:
    """
    Validate a user prompt for safety before processing.

    Checks for:
    - Prompt injection attempts
    - Requests for harmful actions
    - Out-of-scope requests
    - Blocked patterns

    Args:
        prompt: The user prompt to validate

    Returns:
        Validation result including:
        - is_safe: Whether the prompt is safe to process
        - violations: Any detected policy violations
        - warnings: Potential concerns that don't block processing
    """
    logger.info("Validating prompt through guardrails")

    result = PromptValidator.validate(prompt)

    return {
        "is_safe": result.is_valid,
        "action_required": result.action_required.value,
        "violations": [
            {
                "policy": v.policy_name,
                "severity": v.severity.value,
                "message": v.message,
            }
            for v in result.violations
        ],
        "warnings": [
            {
                "policy": w.policy_name,
                "severity": w.severity.value,
                "message": w.message,
            }
            for w in result.warnings
        ],
    }


@mcp.tool()
async def validate_action(
    action_type: str, action_params: dict[str, Any], auto_approve: bool = False
) -> dict[str, Any]:
    """
    Validate a proposed infrastructure action before execution.

    Ensures:
    - Actions are within allowed scope
    - Destructive actions require confirmation
    - Resource limits are respected
    - Governance policies are followed

    Args:
        action_type: Type of action (create_cluster, delete_cluster, etc.)
        action_params: Parameters for the action
        auto_approve: Skip approval checks (for automation pipelines)

    Returns:
        Validation result including:
        - is_allowed: Whether the action can proceed
        - requires_approval: Whether human approval is needed
        - approval_reason: Why approval is required
        - violations: Policy violations that block the action
    """
    logger.info(f"Validating action '{action_type}' through guardrails")

    action = {"type": action_type, **action_params}
    result = action_validator.validate(action, auto_approve=auto_approve)

    return {
        "is_allowed": result.is_valid,
        "requires_approval": result.requires_approval,
        "approval_reason": result.approval_reason,
        "action_required": result.action_required.value,
        "violations": [
            {
                "policy": v.policy_name,
                "severity": v.severity.value,
                "message": v.message,
                "remediation": v.remediation,
            }
            for v in result.violations
        ],
        "warnings": [
            {
                "policy": w.policy_name,
                "severity": w.severity.value,
                "message": w.message,
            }
            for w in result.warnings
        ],
    }


@mcp.tool()
async def get_audit_log(action_type: str | None = None, limit: int = 50) -> dict[str, Any]:
    """
    Retrieve the guardrails audit log for compliance tracking.

    Args:
        action_type: Optional filter by action type
        limit: Maximum number of entries to return

    Returns:
        List of audit log entries with timestamps and validation results
    """
    logger.info(f"Retrieving audit log (action_type={action_type}, limit={limit})")

    entries = policy_engine.get_audit_log(action_type=action_type)

    return {"total": len(entries), "entries": entries[:limit]}


# =============================================================================
# RESOURCE MANAGEMENT TOOLS
# =============================================================================


@mcp.resource("palette://clusters")
async def clusters_resource() -> str:
    """
    Resource endpoint providing real-time cluster status summary.

    Returns formatted overview of all clusters for AI context.
    """
    clusters = await cluster_tools.list_clusters()

    summary_lines = ["# Palette Clusters Overview\n"]
    summary_lines.append(f"Total clusters: {clusters.get('total', 0)}\n")

    for cluster in clusters.get("items", []):
        status_indicator = "[OK]" if cluster["status"] == "Running" else "[WARN]"
        summary_lines.append(
            f"- {status_indicator} **{cluster['name']}** ({cluster['cloud_type']}): "
            f"{cluster['status']} - {cluster['node_count']} nodes"
        )

    return "\n".join(summary_lines)


@mcp.resource("palette://profiles")
async def profiles_resource() -> str:
    """
    Resource endpoint providing cluster profile catalog.

    Returns formatted list of available profiles for AI context.
    """
    profiles = await profile_tools.list_profiles()

    summary_lines = ["# Available Cluster Profiles\n"]

    for profile in profiles.get("items", []):
        summary_lines.append(f"- **{profile['name']}** (v{profile['version']}): " f"{profile['description']}")

    return "\n".join(summary_lines)


# =============================================================================
# SERVER LIFECYCLE
# =============================================================================


def main():
    """Run the MCP server."""
    logger.info("Starting Palette MCP Server...")
    logger.info(f"Palette API Endpoint: {config.api_endpoint}")
    logger.info(f"Server started at {datetime.now().isoformat()}")

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
