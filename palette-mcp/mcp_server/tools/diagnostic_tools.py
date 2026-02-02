"""
Diagnostic and analysis tools for Palette MCP Server.

Provides infrastructure analysis capabilities:
- Cluster health diagnosis with root cause analysis
- Profile recommendations based on workload requirements
- Configuration validation against defined policies
- Cluster state comparison for drift detection

Implements systematic health scoring and issue detection patterns.
"""

import logging
from typing import Any, Optional
from datetime import datetime
import json

from ..config import PaletteConfig

logger = logging.getLogger(__name__)


class DiagnosticTools:
    """Diagnostic and recommendation tool implementation."""

    def __init__(self, config: PaletteConfig):
        self.config = config
        self.llm_config = config.get_llm_config()

    async def diagnose_cluster(
        self,
        cluster_uid: str,
        include_recommendations: bool = True
    ) -> dict[str, Any]:
        """
        Perform comprehensive cluster health diagnosis.

        Analysis workflow:
        1. Gather cluster state (events, metrics, node conditions)
        2. Run analyzer rules to detect known issue patterns
        3. Generate recommendations based on findings
        """
        
        logger.info(f"Starting diagnosis for cluster {cluster_uid}")
        
        # Step 1: Gather cluster data (in production, this calls Palette APIs)
        cluster_state = await self._gather_cluster_state(cluster_uid)
        
        # Step 2: Run built-in analyzers
        analyzer_results = await self._run_analyzers(cluster_state)
        
        # Step 3: Calculate health score
        health_score = self._calculate_health_score(analyzer_results)
        
        # Step 4: Enrich with AI analysis if recommendations requested
        enriched_analysis = {}
        if include_recommendations and analyzer_results["issues"]:
            enriched_analysis = await self._get_enriched_analysis(
                cluster_state, 
                analyzer_results
            )
        
        return {
            "cluster_uid": cluster_uid,
            "cluster_name": cluster_state.get("name", "Unknown"),
            "diagnosis_timestamp": datetime.utcnow().isoformat(),
            "health_summary": {
                "score": health_score,
                "status": self._score_to_status(health_score),
                "total_issues": len(analyzer_results["issues"]),
                "critical_issues": len([i for i in analyzer_results["issues"] if i["severity"] == "critical"]),
                "warning_issues": len([i for i in analyzer_results["issues"] if i["severity"] == "warning"])
            },
            "issues": analyzer_results["issues"],
            "enriched_analysis": enriched_analysis,
            "recommendations": enriched_analysis.get("recommendations", []),
            "next_steps": enriched_analysis.get("next_steps", [])
        }
    
    async def recommend_profile(
        self,
        workload_description: str,
        cloud_provider: str,
        requirements: Optional[dict] = None
    ) -> dict[str, Any]:
        """
        Generate cluster profile recommendations based on workload requirements.

        Analysis process:
        1. Parse workload characteristics and requirements
        2. Match against available pack catalog
        3. Generate optimized profile configuration
        """
        
        requirements = requirements or {}
        
        # Get available packs and profiles
        available_packs = await self._get_available_packs(cloud_provider)
        
        # Build recommendation context
        context = {
            "workload": workload_description,
            "cloud_provider": cloud_provider,
            "requirements": requirements,
            "available_packs": available_packs
        }
        
        # Generate recommendations using AI
        recommendations = await self._generate_profile_recommendations(context)
        
        return {
            "workload_description": workload_description,
            "cloud_provider": cloud_provider,
            "requirements": requirements,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def validate_configuration(
        self,
        config: dict,
        policy_set: str = "default"
    ) -> dict[str, Any]:
        """
        Validate configuration against governance policies.
        
        Checks:
        - Security policies (no public endpoints, resource limits, etc.)
        - Cost policies (resource quotas, instance types)
        - Compliance policies (specific framework requirements)
        """
        
        # Load policies
        policies = await self._load_policies(policy_set)
        
        # Run validation
        violations = []
        warnings = []
        passed = []
        
        for policy in policies:
            result = await self._evaluate_policy(policy, config)
            
            if result["status"] == "violation":
                violations.append(result)
            elif result["status"] == "warning":
                warnings.append(result)
            else:
                passed.append(result)
        
        # Calculate compliance score
        total_policies = len(policies)
        compliance_score = (len(passed) / total_policies * 100) if total_policies > 0 else 100
        
        return {
            "config_type": self._detect_config_type(config),
            "policy_set": policy_set,
            "validation_result": "pass" if not violations else "fail",
            "compliance_score": round(compliance_score, 1),
            "summary": {
                "total_policies": total_policies,
                "passed": len(passed),
                "warnings": len(warnings),
                "violations": len(violations)
            },
            "violations": violations,
            "warnings": warnings,
            "passed_policies": [p["policy_name"] for p in passed],
            "remediation_suggestions": self._generate_remediations(violations),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def compare_clusters(
        self,
        cluster_uid_1: str,
        cluster_uid_2: str
    ) -> dict[str, Any]:
        """
        Compare two clusters for configuration differences.
        
        Useful for:
        - Debugging environment-specific issues
        - Detecting configuration drift
        - Ensuring consistency
        """
        
        # Get both cluster states
        cluster_1 = await self._gather_cluster_state(cluster_uid_1)
        cluster_2 = await self._gather_cluster_state(cluster_uid_2)
        
        # Compare configurations
        differences = self._compare_configs(cluster_1, cluster_2)
        
        # Analyze significance
        analysis = await self._analyze_differences(differences, cluster_1, cluster_2)
        
        return {
            "cluster_1": {
                "uid": cluster_uid_1,
                "name": cluster_1.get("name")
            },
            "cluster_2": {
                "uid": cluster_uid_2,
                "name": cluster_2.get("name")
            },
            "comparison_summary": {
                "total_differences": len(differences),
                "significant_differences": len([d for d in differences if d.get("significance") == "high"]),
                "drift_detected": any(d.get("type") == "drift" for d in differences)
            },
            "differences": differences,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # =========================================================================
    # ANALYZER IMPLEMENTATIONS
    # =========================================================================
    
    async def _gather_cluster_state(self, cluster_uid: str) -> dict:
        """Gather comprehensive cluster state for analysis."""
        # In production, this would call Palette APIs
        # For demo, return mock state
        
        return {
            "uid": cluster_uid,
            "name": f"cluster-{cluster_uid[-4:]}",
            "cloud_type": "aws",
            "status": "Running",
            "k8s_version": "1.28.5",
            "node_count": 3,
            "nodes": [
                {"name": "node-1", "status": "Ready", "conditions": []},
                {"name": "node-2", "status": "Ready", "conditions": []},
                {"name": "node-3", "status": "NotReady", "conditions": [
                    {"type": "MemoryPressure", "status": "True"}
                ]}
            ],
            "events": [
                {"type": "Warning", "reason": "NodeNotReady", "message": "Node node-3 is not ready"},
                {"type": "Warning", "reason": "FailedMount", "message": "Unable to mount volume for pod test-pod"}
            ],
            "resources": {
                "cpu_utilization": 75,
                "memory_utilization": 85,
                "storage_utilization": 60
            },
            "profile": {
                "name": "aws-production-standard",
                "version": "1.2.0"
            }
        }
    
    async def _run_analyzers(self, cluster_state: dict) -> dict:
        """Run built-in analyzers on cluster state."""
        
        issues = []
        
        # Analyzer 1: Node Health
        for node in cluster_state.get("nodes", []):
            if node["status"] != "Ready":
                issues.append({
                    "analyzer": "NodeHealth",
                    "severity": "critical",
                    "resource": f"Node/{node['name']}",
                    "issue": f"Node {node['name']} is not ready",
                    "details": node.get("conditions", [])
                })
            
            # Check for pressure conditions
            for condition in node.get("conditions", []):
                if condition.get("status") == "True" and "Pressure" in condition.get("type", ""):
                    issues.append({
                        "analyzer": "NodePressure",
                        "severity": "warning",
                        "resource": f"Node/{node['name']}",
                        "issue": f"{condition['type']} detected on {node['name']}",
                        "details": condition
                    })
        
        # Analyzer 2: Resource Utilization
        resources = cluster_state.get("resources", {})
        if resources.get("cpu_utilization", 0) > 80:
            issues.append({
                "analyzer": "ResourceUtilization",
                "severity": "warning",
                "resource": "Cluster",
                "issue": f"High CPU utilization: {resources['cpu_utilization']}%",
                "details": {"threshold": 80, "current": resources["cpu_utilization"]}
            })
        
        if resources.get("memory_utilization", 0) > 80:
            issues.append({
                "analyzer": "ResourceUtilization",
                "severity": "warning",
                "resource": "Cluster",
                "issue": f"High memory utilization: {resources['memory_utilization']}%",
                "details": {"threshold": 80, "current": resources["memory_utilization"]}
            })
        
        # Analyzer 3: Event Analysis
        for event in cluster_state.get("events", []):
            if event.get("type") == "Warning":
                issues.append({
                    "analyzer": "EventAnalysis",
                    "severity": "warning",
                    "resource": "Event",
                    "issue": event.get("message"),
                    "details": {"reason": event.get("reason")}
                })
        
        return {
            "issues": issues,
            "analyzers_run": ["NodeHealth", "NodePressure", "ResourceUtilization", "EventAnalysis"],
            "analysis_duration_ms": 150
        }
    
    async def _get_enriched_analysis(
        self, 
        cluster_state: dict, 
        analyzer_results: dict
    ) -> dict:
        """
        Use LLM to provide intelligent analysis and recommendations.
        
        In production, this would call the configured LLM (OpenAI, LocalAI, etc.)
        """
        
        # Build prompt for LLM
        issues_summary = "\n".join([
            f"- [{i['severity'].upper()}] {i['issue']}"
            for i in analyzer_results["issues"]
        ])
        
        # For demo, return pre-generated analysis
        # In production: await self._call_llm(prompt)
        
        return {
            "root_cause_analysis": (
                "The cluster is experiencing memory pressure on node-3, which is likely "
                "causing the node to become NotReady. This could be due to: "
                "1) Memory-intensive workloads without proper limits, "
                "2) Memory leak in an application, or "
                "3) Undersized node for the workload."
            ),
            "recommendations": [
                {
                    "priority": 1,
                    "action": "Investigate memory usage on node-3",
                    "command": "kubectl top pods --all-namespaces --sort-by=memory | head -20",
                    "rationale": "Identify which pods are consuming the most memory"
                },
                {
                    "priority": 2,
                    "action": "Add resource limits to pods without them",
                    "command": "kubectl get pods --all-namespaces -o json | jq '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.name'",
                    "rationale": "Prevent unbounded memory consumption"
                },
                {
                    "priority": 3,
                    "action": "Consider scaling the cluster or upgrading node size",
                    "rationale": "If workload legitimately needs more resources"
                }
            ],
            "next_steps": [
                "Monitor memory utilization after applying fixes",
                "Review Palette cluster profile for resource quota policies",
                "Consider enabling cluster autoscaler if not already enabled"
            ],
            "estimated_resolution_time": "15-30 minutes"
        }
    
    def _calculate_health_score(self, analyzer_results: dict) -> int:
        """Calculate health score from analyzer results."""
        score = 100
        
        for issue in analyzer_results.get("issues", []):
            if issue["severity"] == "critical":
                score -= 25
            elif issue["severity"] == "warning":
                score -= 10
            elif issue["severity"] == "info":
                score -= 2
        
        return max(0, score)
    
    def _score_to_status(self, score: int) -> str:
        """Convert health score to status string."""
        if score >= 90:
            return "Healthy"
        elif score >= 70:
            return "Degraded"
        elif score >= 50:
            return "Warning"
        else:
            return "Critical"
    
    async def _get_available_packs(self, cloud_provider: str) -> list:
        """Get available packs for a cloud provider."""
        # Mock data - in production, call Palette API
        return [
            {"name": "ubuntu", "layer": "os", "versions": ["22.04", "20.04"]},
            {"name": "kubernetes", "layer": "k8s", "versions": ["1.29.2", "1.28.5"]},
            {"name": "calico", "layer": "cni", "versions": ["3.27.0", "3.26.0"]},
            {"name": "prometheus-operator", "layer": "addon", "versions": ["45.0.0"]}
        ]
    
    async def _generate_profile_recommendations(self, context: dict) -> list:
        """Generate profile recommendations using AI."""
        
        workload = context["workload"].lower()
        cloud = context["cloud_provider"]
        reqs = context["requirements"]
        
        recommendations = []
        
        # Rule-based + AI recommendations
        if "gpu" in workload or "ml" in workload or "ai" in workload:
            recommendations.append({
                "rank": 1,
                "profile_name": "ai-workload-gpu",
                "confidence": 0.95,
                "rationale": "GPU-enabled profile recommended for AI/ML workloads",
                "suggested_packs": [
                    {"name": "nvidia-gpu-operator", "version": "23.9.0"},
                    {"name": "kubeflow", "version": "1.8.0"}
                ],
                "estimated_cost": "$2.50/hour",
                "trade_offs": [
                    "Higher cost due to GPU instances",
                    "May require GPU quota approval in cloud provider"
                ]
            })
        
        if "edge" in workload or "retail" in workload or "iot" in workload:
            recommendations.append({
                "rank": 1 if not recommendations else 2,
                "profile_name": "edge-lightweight",
                "confidence": 0.90,
                "rationale": "Lightweight profile suitable for edge/IoT deployments",
                "suggested_packs": [
                    {"name": "k3s", "version": "1.28.5"},
                    {"name": "flannel", "version": "0.22.0"}
                ],
                "estimated_cost": "$0.10/hour",
                "trade_offs": [
                    "Limited to single-node or small clusters",
                    "Some enterprise features may not be available"
                ]
            })
        
        # Default production recommendation
        if not recommendations:
            recommendations.append({
                "rank": 1,
                "profile_name": f"{cloud}-production-standard",
                "confidence": 0.85,
                "rationale": "Standard production profile with monitoring and security",
                "suggested_packs": [
                    {"name": "kubernetes", "version": "1.28.5"},
                    {"name": "calico", "version": "3.27.0"},
                    {"name": "prometheus-operator", "version": "45.0.0"}
                ],
                "estimated_cost": "$0.75/hour",
                "trade_offs": []
            })
        
        return recommendations
    
    async def _load_policies(self, policy_set: str) -> list:
        """Load validation policies."""
        # Default policies - in production, load from files
        return [
            {
                "name": "require_resource_limits",
                "description": "All containers must have resource limits defined",
                "severity": "warning"
            },
            {
                "name": "no_privileged_containers",
                "description": "Containers should not run in privileged mode",
                "severity": "critical"
            },
            {
                "name": "require_health_checks",
                "description": "Pods should have liveness and readiness probes",
                "severity": "warning"
            },
            {
                "name": "minimum_replicas",
                "description": "Production deployments should have at least 2 replicas",
                "severity": "warning"
            }
        ]
    
    async def _evaluate_policy(self, policy: dict, config: dict) -> dict:
        """Evaluate a single policy against configuration."""
        # Simplified evaluation - in production, use proper policy engine
        return {
            "policy_name": policy["name"],
            "description": policy["description"],
            "status": "pass",  # or "violation", "warning"
            "severity": policy["severity"]
        }
    
    def _detect_config_type(self, config: dict) -> str:
        """Detect the type of configuration being validated."""
        if "spec" in config and "machinePools" in config.get("spec", {}):
            return "cluster"
        elif "spec" in config and "packs" in config.get("spec", {}):
            return "cluster_profile"
        else:
            return "unknown"
    
    def _generate_remediations(self, violations: list) -> list:
        """Generate remediation suggestions for violations."""
        remediations = []
        for v in violations:
            remediations.append({
                "violation": v["policy_name"],
                "suggestion": f"Address {v['policy_name']} violation",
                "documentation": f"https://docs.spectrocloud.com/best-practices/{v['policy_name']}"
            })
        return remediations
    
    def _compare_configs(self, cluster_1: dict, cluster_2: dict) -> list:
        """Compare two cluster configurations."""
        differences = []
        
        # Compare K8s versions
        if cluster_1.get("k8s_version") != cluster_2.get("k8s_version"):
            differences.append({
                "field": "kubernetes_version",
                "cluster_1": cluster_1.get("k8s_version"),
                "cluster_2": cluster_2.get("k8s_version"),
                "significance": "high",
                "type": "version_mismatch"
            })
        
        # Compare node counts
        if cluster_1.get("node_count") != cluster_2.get("node_count"):
            differences.append({
                "field": "node_count",
                "cluster_1": cluster_1.get("node_count"),
                "cluster_2": cluster_2.get("node_count"),
                "significance": "medium",
                "type": "scale_difference"
            })
        
        # Compare profiles
        if cluster_1.get("profile", {}).get("version") != cluster_2.get("profile", {}).get("version"):
            differences.append({
                "field": "profile_version",
                "cluster_1": cluster_1.get("profile", {}).get("version"),
                "cluster_2": cluster_2.get("profile", {}).get("version"),
                "significance": "high",
                "type": "drift"
            })
        
        return differences
    
    async def _analyze_differences(
        self, 
        differences: list, 
        cluster_1: dict, 
        cluster_2: dict
    ) -> dict:
        """Analyze the significance of differences."""
        return {
            "summary": f"Found {len(differences)} configuration differences",
            "risk_assessment": "medium" if any(d["significance"] == "high" for d in differences) else "low",
            "recommendation": (
                "Consider synchronizing configurations to ensure consistency"
                if differences else "Clusters are in sync"
            )
        }
