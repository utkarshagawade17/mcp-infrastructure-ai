"""
Cluster management tools for Palette MCP Server.

Provides tools for:
- Listing and filtering clusters
- Getting cluster details
- Retrieving cluster events
- Cost analysis
"""

import logging
from typing import Any, Optional
from datetime import datetime
import httpx

from ..config import PaletteConfig

logger = logging.getLogger(__name__)


class ClusterTools:
    """Tools for Palette cluster management operations."""

    def __init__(self, config: PaletteConfig):
        self.config = config
        self.base_url = f"{config.api_endpoint}/v1"

    async def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        """Make authenticated request to Palette API."""

        # If in demo mode, return mock data
        if self.config.is_demo_mode:
            return self._get_mock_data(endpoint)

        url = f"{self.base_url}/{endpoint}"

        async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.config.auth_headers,
                params=params,
                json=data,
            )
            response.raise_for_status()
            return response.json()

    async def list_clusters(
        self, project_uid: Optional[str] = None, status_filter: Optional[str] = None
    ) -> dict[str, Any]:
        """List all clusters with optional filtering."""

        try:
            # In production, this would call: GET /v1/spectroclusters
            result = await self._make_request("GET", "spectroclusters")

            clusters = result.get("items", [])

            # Apply status filter if provided
            if status_filter:
                clusters = [c for c in clusters if c.get("status", {}).get("state") == status_filter]

            # Transform to simplified format
            formatted_clusters = []
            for cluster in clusters:
                formatted_clusters.append(
                    {
                        "uid": cluster.get("metadata", {}).get("uid"),
                        "name": cluster.get("metadata", {}).get("name"),
                        "status": cluster.get("status", {}).get("state", "Unknown"),
                        "cloud_type": cluster.get("spec", {}).get("cloudType"),
                        "node_count": self._get_node_count(cluster),
                        "k8s_version": self._get_k8s_version(cluster),
                        "created_at": cluster.get("metadata", {}).get("creationTimestamp"),
                        "health_status": self._calculate_health_status(cluster),
                    }
                )

            return {
                "total": len(formatted_clusters),
                "items": formatted_clusters,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error listing clusters: {e}")
            raise

    async def get_cluster_details(self, cluster_uid: str) -> dict[str, Any]:
        """Get comprehensive details for a specific cluster."""

        try:
            # GET /v1/spectroclusters/{uid}
            cluster = await self._make_request("GET", f"spectroclusters/{cluster_uid}")

            # Get additional details
            profile = await self._get_cluster_profile(cluster)
            nodes = await self._get_cluster_nodes(cluster_uid)

            return {
                "metadata": {
                    "uid": cluster.get("metadata", {}).get("uid"),
                    "name": cluster.get("metadata", {}).get("name"),
                    "created_at": cluster.get("metadata", {}).get("creationTimestamp"),
                    "labels": cluster.get("metadata", {}).get("labels", {}),
                    "annotations": cluster.get("metadata", {}).get("annotations", {}),
                },
                "spec": {
                    "cloud_type": cluster.get("spec", {}).get("cloudType"),
                    "cloud_account": cluster.get("spec", {}).get("cloudAccountUid"),
                    "cluster_profile": profile,
                    "machine_pools": cluster.get("spec", {}).get("machinePools", []),
                },
                "status": {
                    "state": cluster.get("status", {}).get("state"),
                    "health": self._calculate_health_status(cluster),
                    "conditions": cluster.get("status", {}).get("conditions", []),
                    "endpoint": cluster.get("status", {}).get("apiEndpoint"),
                },
                "nodes": nodes,
                "resource_usage": await self._get_resource_usage(cluster_uid),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting cluster details: {e}")
            raise

    async def get_cluster_events(
        self, cluster_uid: str, severity: Optional[str] = None, limit: int = 50
    ) -> dict[str, Any]:
        """Get recent events for a cluster."""

        try:
            # GET /v1/events with cluster filter
            params = {"resourceUid": cluster_uid, "limit": limit}

            result = await self._make_request("GET", "events", params=params)

            events = result.get("items", [])

            # Filter by severity if specified
            if severity:
                events = [e for e in events if e.get("severity") == severity]

            # Format events
            formatted_events = []
            for event in events:
                formatted_events.append(
                    {
                        "timestamp": event.get("timestamp"),
                        "severity": event.get("severity", "Info"),
                        "type": event.get("type"),
                        "message": event.get("message"),
                        "component": event.get("component"),
                        "reason": event.get("reason"),
                    }
                )

            # Sort by timestamp descending
            formatted_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return {
                "cluster_uid": cluster_uid,
                "total": len(formatted_events),
                "events": formatted_events[:limit],
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting cluster events: {e}")
            raise

    async def get_cluster_cost(self, cluster_uid: str, time_range: str = "7d") -> dict[str, Any]:
        """Get cost analysis for a cluster."""

        try:
            # Parse time range
            days = int(time_range.replace("d", ""))

            # GET /v1/spectroclusters/{uid}/cost
            result = await self._make_request(
                "GET",
                f"spectroclusters/{cluster_uid}/cost",
                params={"duration": f"{days}d"},
            )

            return {
                "cluster_uid": cluster_uid,
                "time_range": time_range,
                "total_cost": result.get("totalCost", 0),
                "currency": "USD",
                "breakdown": {
                    "compute": result.get("computeCost", 0),
                    "storage": result.get("storageCost", 0),
                    "network": result.get("networkCost", 0),
                },
                "daily_average": result.get("totalCost", 0) / days if days > 0 else 0,
                "cost_trend": result.get("trend", "stable"),
                "recommendations": self._generate_cost_recommendations(result),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting cluster cost: {e}")
            raise

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_node_count(self, cluster: dict) -> int:
        """Extract total node count from cluster spec."""
        machine_pools = cluster.get("spec", {}).get("machinePools", [])
        return sum(pool.get("size", 0) for pool in machine_pools)

    def _get_k8s_version(self, cluster: dict) -> str:
        """Extract Kubernetes version from cluster."""
        return cluster.get("status", {}).get("kubernetes", {}).get("version", "Unknown")

    def _calculate_health_status(self, cluster: dict) -> dict:
        """Calculate overall health status from conditions."""
        conditions = cluster.get("status", {}).get("conditions", [])

        health_score = 100
        issues = []

        for condition in conditions:
            if condition.get("status") != "True" and condition.get("type") in [
                "Ready",
                "ClusterHealth",
                "NodeHealth",
            ]:
                health_score -= 20
                issues.append({"type": condition.get("type"), "message": condition.get("message")})

        health_score = max(0, health_score)

        if health_score >= 80:
            status = "Healthy"
        elif health_score >= 50:
            status = "Degraded"
        else:
            status = "Unhealthy"

        return {"status": status, "score": health_score, "issues": issues}

    async def _get_cluster_profile(self, cluster: dict) -> dict:
        """Get cluster profile information."""
        profile_uid = cluster.get("spec", {}).get("clusterProfileUid")
        if not profile_uid:
            return {}

        try:
            profile = await self._make_request("GET", f"clusterprofiles/{profile_uid}")
            return {
                "uid": profile.get("metadata", {}).get("uid"),
                "name": profile.get("metadata", {}).get("name"),
                "version": profile.get("spec", {}).get("version"),
            }
        except Exception:
            return {"uid": profile_uid}

    async def _get_cluster_nodes(self, cluster_uid: str) -> list:
        """Get node information for cluster."""
        # In production: GET /v1/spectroclusters/{uid}/machines
        return self._get_mock_data("nodes")

    async def _get_resource_usage(self, cluster_uid: str) -> dict:
        """Get resource utilization metrics."""
        # In production: GET /v1/metrics/spectroclusters/{uid}
        return {
            "cpu": {"used": 45, "total": 100, "unit": "cores"},
            "memory": {"used": 128, "total": 256, "unit": "GB"},
            "storage": {"used": 500, "total": 1000, "unit": "GB"},
        }

    def _generate_cost_recommendations(self, cost_data: dict) -> list:
        """Generate cost optimization recommendations."""
        recommendations = []

        # Example recommendations logic
        if cost_data.get("computeCost", 0) > cost_data.get("totalCost", 1) * 0.7:
            recommendations.append(
                {
                    "type": "compute",
                    "severity": "medium",
                    "recommendation": "Consider right-sizing nodes or using spot instances",
                    "potential_savings": "10-30%",
                }
            )

        return recommendations

    def _get_mock_data(self, endpoint: str) -> dict:
        """Return mock data for demo mode."""

        mock_data = {
            "spectroclusters": {
                "items": [
                    {
                        "metadata": {
                            "uid": "cluster-001",
                            "name": "prod-cluster-us-east",
                            "creationTimestamp": "2025-01-15T10:00:00Z",
                        },
                        "spec": {
                            "cloudType": "aws",
                            "machinePools": [{"size": 3}, {"size": 2}],
                        },
                        "status": {
                            "state": "Running",
                            "conditions": [{"type": "Ready", "status": "True"}],
                            "kubernetes": {"version": "1.28.5"},
                        },
                    },
                    {
                        "metadata": {
                            "uid": "cluster-002",
                            "name": "staging-cluster",
                            "creationTimestamp": "2025-01-20T14:30:00Z",
                        },
                        "spec": {"cloudType": "azure", "machinePools": [{"size": 2}]},
                        "status": {
                            "state": "Running",
                            "conditions": [
                                {"type": "Ready", "status": "True"},
                                {
                                    "type": "NodeHealth",
                                    "status": "False",
                                    "message": "1 node NotReady",
                                },
                            ],
                            "kubernetes": {"version": "1.29.2"},
                        },
                    },
                    {
                        "metadata": {
                            "uid": "cluster-003",
                            "name": "edge-retail-store-42",
                            "creationTimestamp": "2025-01-25T09:15:00Z",
                        },
                        "spec": {"cloudType": "edge", "machinePools": [{"size": 1}]},
                        "status": {
                            "state": "Running",
                            "conditions": [{"type": "Ready", "status": "True"}],
                            "kubernetes": {"version": "1.28.5"},
                        },
                    },
                ]
            },
            "nodes": [
                {"name": "node-1", "status": "Ready", "role": "control-plane"},
                {"name": "node-2", "status": "Ready", "role": "worker"},
                {"name": "node-3", "status": "Ready", "role": "worker"},
            ],
            "events": {
                "items": [
                    {
                        "timestamp": "2025-01-31T08:00:00Z",
                        "severity": "Info",
                        "type": "Normal",
                        "message": "Cluster reconciliation completed successfully",
                        "component": "palette-agent",
                    },
                    {
                        "timestamp": "2025-01-31T07:45:00Z",
                        "severity": "Warning",
                        "type": "Warning",
                        "message": "Node memory pressure detected",
                        "component": "kubelet",
                    },
                ]
            },
        }

        # Return appropriate mock data based on endpoint
        for key in mock_data:
            if key in endpoint:
                return mock_data[key]

        return mock_data.get("spectroclusters", {})
