"""
Cluster Profile tools for Palette MCP Server.

Provides tools for:
- Listing cluster profiles
- Getting profile details
- Listing available packs
"""

import logging
from typing import Any, Optional
from datetime import datetime
import httpx

from ..config import PaletteConfig

logger = logging.getLogger(__name__)


class ProfileTools:
    """Tools for Palette cluster profile operations."""
    
    def __init__(self, config: PaletteConfig):
        self.config = config
        self.base_url = f"{config.api_endpoint}/v1"
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: dict = None
    ) -> dict:
        """Make authenticated request to Palette API."""
        
        if self.config.is_demo_mode:
            return self._get_mock_data(endpoint)
        
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.config.auth_headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def list_profiles(
        self,
        profile_type: Optional[str] = None,
        cloud_type: Optional[str] = None
    ) -> dict[str, Any]:
        """List available cluster profiles."""
        
        try:
            # GET /v1/clusterprofiles
            result = await self._make_request("GET", "clusterprofiles")
            
            profiles = result.get("items", [])
            
            # Apply filters
            if profile_type:
                profiles = [p for p in profiles if p.get("spec", {}).get("type") == profile_type]
            if cloud_type:
                profiles = [p for p in profiles if cloud_type in p.get("spec", {}).get("cloudTypes", [])]
            
            # Format profiles
            formatted_profiles = []
            for profile in profiles:
                formatted_profiles.append({
                    "uid": profile.get("metadata", {}).get("uid"),
                    "name": profile.get("metadata", {}).get("name"),
                    "version": profile.get("spec", {}).get("version", "1.0.0"),
                    "type": profile.get("spec", {}).get("type", "cluster"),
                    "cloud_types": profile.get("spec", {}).get("cloudTypes", []),
                    "description": profile.get("spec", {}).get("description", ""),
                    "pack_count": len(profile.get("spec", {}).get("packs", [])),
                    "created_at": profile.get("metadata", {}).get("creationTimestamp")
                })
            
            return {
                "total": len(formatted_profiles),
                "items": formatted_profiles,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            raise
    
    async def get_profile_details(self, profile_uid: str) -> dict[str, Any]:
        """Get detailed information about a cluster profile."""
        
        try:
            # GET /v1/clusterprofiles/{uid}
            profile = await self._make_request("GET", f"clusterprofiles/{profile_uid}")
            
            # Get pack details
            packs = profile.get("spec", {}).get("packs", [])
            formatted_packs = []
            
            for pack in packs:
                formatted_packs.append({
                    "name": pack.get("name"),
                    "type": pack.get("type"),
                    "layer": self._determine_layer(pack),
                    "version": pack.get("version"),
                    "registry": pack.get("registry"),
                    "values": pack.get("values", "")[:500] + "..." if len(pack.get("values", "")) > 500 else pack.get("values", "")
                })
            
            return {
                "metadata": {
                    "uid": profile.get("metadata", {}).get("uid"),
                    "name": profile.get("metadata", {}).get("name"),
                    "created_at": profile.get("metadata", {}).get("creationTimestamp"),
                    "labels": profile.get("metadata", {}).get("labels", {})
                },
                "spec": {
                    "version": profile.get("spec", {}).get("version"),
                    "type": profile.get("spec", {}).get("type"),
                    "cloud_types": profile.get("spec", {}).get("cloudTypes", []),
                    "description": profile.get("spec", {}).get("description", "")
                },
                "packs": formatted_packs,
                "pack_layers": {
                    "os": [p for p in formatted_packs if p["layer"] == "os"],
                    "kubernetes": [p for p in formatted_packs if p["layer"] == "k8s"],
                    "cni": [p for p in formatted_packs if p["layer"] == "cni"],
                    "csi": [p for p in formatted_packs if p["layer"] == "csi"],
                    "addon": [p for p in formatted_packs if p["layer"] == "addon"]
                },
                "associated_clusters": await self._get_associated_clusters(profile_uid),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting profile details: {e}")
            raise
    
    async def list_packs(
        self,
        layer: Optional[str] = None,
        registry: Optional[str] = None
    ) -> dict[str, Any]:
        """List available packs from registries."""
        
        try:
            # GET /v1/packs
            result = await self._make_request("GET", "packs")
            
            packs = result.get("items", [])
            
            # Apply filters
            if layer:
                packs = [p for p in packs if self._determine_layer(p) == layer]
            if registry:
                packs = [p for p in packs if p.get("spec", {}).get("registryUid") == registry]
            
            # Group by category
            categorized = {
                "os": [],
                "k8s": [],
                "cni": [],
                "csi": [],
                "addon": []
            }
            
            for pack in packs:
                pack_info = {
                    "name": pack.get("spec", {}).get("name"),
                    "display_name": pack.get("spec", {}).get("displayName"),
                    "version": pack.get("spec", {}).get("version"),
                    "registry": pack.get("spec", {}).get("registryUid"),
                    "cloud_types": pack.get("spec", {}).get("cloudTypes", [])
                }
                
                layer_type = self._determine_layer(pack)
                if layer_type in categorized:
                    categorized[layer_type].append(pack_info)
            
            return {
                "total": len(packs),
                "by_layer": categorized,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error listing packs: {e}")
            raise
    
    def _determine_layer(self, pack: dict) -> str:
        """Determine the layer type of a pack."""
        pack_type = pack.get("type", pack.get("spec", {}).get("type", "")).lower()
        name = pack.get("name", pack.get("spec", {}).get("name", "")).lower()
        
        if pack_type in ["os", "operating-system"]:
            return "os"
        elif pack_type == "kubernetes" or "kubernetes" in name:
            return "k8s"
        elif pack_type == "cni" or name in ["calico", "cilium", "flannel"]:
            return "cni"
        elif pack_type == "csi" or "csi" in name:
            return "csi"
        else:
            return "addon"
    
    async def _get_associated_clusters(self, profile_uid: str) -> list:
        """Get clusters using this profile."""
        # In production, filter clusters by profile
        return []
    
    def _get_mock_data(self, endpoint: str) -> dict:
        """Return mock data for demo mode."""
        
        mock_profiles = {
            "items": [
                {
                    "metadata": {
                        "uid": "profile-001",
                        "name": "aws-production-standard",
                        "creationTimestamp": "2025-01-01T00:00:00Z"
                    },
                    "spec": {
                        "version": "1.2.0",
                        "type": "cluster",
                        "cloudTypes": ["aws"],
                        "description": "Production-ready AWS cluster with monitoring and security",
                        "packs": [
                            {"name": "ubuntu", "type": "os", "version": "22.04"},
                            {"name": "kubernetes", "type": "kubernetes", "version": "1.28.5"},
                            {"name": "calico", "type": "cni", "version": "3.26.0"},
                            {"name": "ebs-csi", "type": "csi", "version": "1.25.0"},
                            {"name": "prometheus-operator", "type": "addon", "version": "45.0.0"},
                            {"name": "cert-manager", "type": "addon", "version": "1.13.0"}
                        ]
                    }
                },
                {
                    "metadata": {
                        "uid": "profile-002",
                        "name": "edge-lightweight",
                        "creationTimestamp": "2025-01-10T00:00:00Z"
                    },
                    "spec": {
                        "version": "1.0.0",
                        "type": "cluster",
                        "cloudTypes": ["edge"],
                        "description": "Lightweight edge cluster for retail/IoT",
                        "packs": [
                            {"name": "kairos", "type": "os", "version": "2.4.3"},
                            {"name": "k3s", "type": "kubernetes", "version": "1.28.5"},
                            {"name": "flannel", "type": "cni", "version": "0.22.0"}
                        ]
                    }
                },
                {
                    "metadata": {
                        "uid": "profile-003",
                        "name": "ai-workload-gpu",
                        "creationTimestamp": "2025-01-20T00:00:00Z"
                    },
                    "spec": {
                        "version": "1.0.0",
                        "type": "cluster",
                        "cloudTypes": ["aws", "gcp"],
                        "description": "GPU-enabled cluster for AI/ML workloads with NVIDIA operators",
                        "packs": [
                            {"name": "ubuntu", "type": "os", "version": "22.04"},
                            {"name": "kubernetes", "type": "kubernetes", "version": "1.29.2"},
                            {"name": "calico", "type": "cni", "version": "3.27.0"},
                            {"name": "ebs-csi", "type": "csi", "version": "1.26.0"},
                            {"name": "nvidia-gpu-operator", "type": "addon", "version": "23.9.0"},
                            {"name": "kubeflow", "type": "addon", "version": "1.8.0"}
                        ]
                    }
                }
            ]
        }
        
        mock_packs = {
            "items": [
                {"spec": {"name": "ubuntu", "displayName": "Ubuntu", "version": "22.04", "type": "os", "cloudTypes": ["all"]}},
                {"spec": {"name": "rhel", "displayName": "RHEL", "version": "9.2", "type": "os", "cloudTypes": ["all"]}},
                {"spec": {"name": "kubernetes", "displayName": "Kubernetes", "version": "1.29.2", "type": "kubernetes", "cloudTypes": ["all"]}},
                {"spec": {"name": "k3s", "displayName": "K3s", "version": "1.28.5", "type": "kubernetes", "cloudTypes": ["edge"]}},
                {"spec": {"name": "calico", "displayName": "Calico", "version": "3.27.0", "type": "cni", "cloudTypes": ["all"]}},
                {"spec": {"name": "cilium", "displayName": "Cilium", "version": "1.14.0", "type": "cni", "cloudTypes": ["all"]}},
                {"spec": {"name": "prometheus-operator", "displayName": "Prometheus", "version": "45.0.0", "type": "addon", "cloudTypes": ["all"]}},
                {"spec": {"name": "nvidia-gpu-operator", "displayName": "NVIDIA GPU Operator", "version": "23.9.0", "type": "addon", "cloudTypes": ["aws", "gcp", "azure"]}}
            ]
        }
        
        if "packs" in endpoint:
            return mock_packs
        return mock_profiles
