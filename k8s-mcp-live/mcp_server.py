"""
Kubernetes MCP Server - Production Implementation

MCP server for Kubernetes cluster operations. Connects to Kubernetes clusters
(minikube, kind, EKS, GKE, AKS) and exposes operational tools via MCP protocol.

Capabilities:
- Resource inspection and monitoring
- Workload diagnostics and analysis
- Health scoring and recommendations
- Policy compliance validation

Compatible with any Kubernetes distribution and cloud provider.
"""

import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Kubernetes client
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    print("WARNING: kubernetes package not installed. Run: pip install kubernetes")

# Initialize MCP Server
mcp = FastMCP("Kubernetes Operations Server")

# Global K8s clients
core_v1 = None
apps_v1 = None
cluster_connected = False


def init_kubernetes():
    """Initialize Kubernetes client - tries kubeconfig first, then in-cluster."""
    global core_v1, apps_v1, cluster_connected

    if not K8S_AVAILABLE:
        return False

    try:
        # Try loading from kubeconfig (local development)
        config.load_kube_config()
        print("Connected using kubeconfig")
    except Exception:
        try:
            # Try in-cluster config (running inside K8s)
            config.load_incluster_config()
            print("Connected using in-cluster config")
        except Exception:
            print("Could not connect to Kubernetes cluster")
            return False

    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    cluster_connected = True
    return True


# =============================================================================
# MCP TOOLS - Exposed operations for cluster management
# =============================================================================


@mcp.tool()
async def get_cluster_info() -> dict:
    """
    Get basic information about the connected Kubernetes cluster.
    Returns cluster version, node count, and namespace count.
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        # Get version info
        version_api = client.VersionApi()
        version = version_api.get_code()

        # Get node count
        nodes = core_v1.list_node()

        # Get namespace count
        namespaces = core_v1.list_namespace()

        return {
            "cluster_version": version.git_version,
            "platform": version.platform,
            "node_count": len(nodes.items),
            "namespace_count": len(namespaces.items),
            "namespaces": [ns.metadata.name for ns in namespaces.items],
            "status": "Connected",
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def list_namespaces() -> dict:
    """
    List all namespaces in the cluster with their status.
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        namespaces = core_v1.list_namespace()

        ns_list = []
        for ns in namespaces.items:
            ns_list.append(
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created": (ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None),
                    "labels": ns.metadata.labels or {},
                }
            )

        return {"total": len(ns_list), "namespaces": ns_list}
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def list_pods(namespace: str = "default", show_all: bool = False) -> dict:
    """
    List pods in a namespace with their status.

    Args:
        namespace: Kubernetes namespace (default: "default", use "all" for all namespaces)
        show_all: Include completed/terminated pods
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        if namespace == "all":
            pods = core_v1.list_pod_for_all_namespaces()
        else:
            pods = core_v1.list_namespaced_pod(namespace=namespace)

        pod_list = []
        for pod in pods.items:
            # Get container statuses
            container_statuses = []
            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    container_statuses.append(
                        {
                            "name": cs.name,
                            "ready": cs.ready,
                            "restart_count": cs.restart_count,
                            "state": (
                                "running"
                                if cs.state.running
                                else (
                                    "waiting"
                                    if cs.state.waiting
                                    else ("terminated" if cs.state.terminated else "unknown")
                                )
                            ),
                        }
                    )

            status = pod.status.phase
            if not show_all and status in ["Succeeded", "Failed"]:
                continue

            pod_list.append(
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": status,
                    "ready": (
                        f"{sum(1 for c in container_statuses if c['ready'])}/{len(container_statuses)}"
                        if container_statuses
                        else "0/0"
                    ),
                    "restarts": (sum(c["restart_count"] for c in container_statuses) if container_statuses else 0),
                    "age": _calculate_age(pod.metadata.creation_timestamp),
                    "node": pod.spec.node_name,
                    "containers": container_statuses,
                }
            )

        # Sort by status (problematic first)
        status_order = {
            "Failed": 0,
            "Pending": 1,
            "Unknown": 2,
            "Running": 3,
            "Succeeded": 4,
        }
        pod_list.sort(key=lambda x: status_order.get(x["status"], 5))

        return {"namespace": namespace, "total": len(pod_list), "pods": pod_list}
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def list_deployments(namespace: str = "default") -> dict:
    """
    List deployments in a namespace with their replica status.

    Args:
        namespace: Kubernetes namespace (default: "default", use "all" for all namespaces)
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        if namespace == "all":
            deployments = apps_v1.list_deployment_for_all_namespaces()
        else:
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

        dep_list = []
        for dep in deployments.items:
            ready = dep.status.ready_replicas or 0
            desired = dep.spec.replicas or 0

            dep_list.append(
                {
                    "name": dep.metadata.name,
                    "namespace": dep.metadata.namespace,
                    "ready": f"{ready}/{desired}",
                    "up_to_date": dep.status.updated_replicas or 0,
                    "available": dep.status.available_replicas or 0,
                    "age": _calculate_age(dep.metadata.creation_timestamp),
                    "healthy": ready == desired,
                }
            )

        return {
            "namespace": namespace,
            "total": len(dep_list),
            "healthy": sum(1 for d in dep_list if d["healthy"]),
            "unhealthy": sum(1 for d in dep_list if not d["healthy"]),
            "deployments": dep_list,
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def list_services(namespace: str = "default") -> dict:
    """
    List services in a namespace.

    Args:
        namespace: Kubernetes namespace (default: "default", use "all" for all namespaces)
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        if namespace == "all":
            services = core_v1.list_service_for_all_namespaces()
        else:
            services = core_v1.list_namespaced_service(namespace=namespace)

        svc_list = []
        for svc in services.items:
            ports = []
            if svc.spec.ports:
                for p in svc.spec.ports:
                    ports.append(f"{p.port}/{p.protocol}")

            svc_list.append(
                {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "external_ip": (
                        svc.status.load_balancer.ingress[0].ip
                        if svc.status.load_balancer and svc.status.load_balancer.ingress
                        else None
                    ),
                    "ports": ports,
                    "age": _calculate_age(svc.metadata.creation_timestamp),
                }
            )

        return {"namespace": namespace, "total": len(svc_list), "services": svc_list}
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def get_pod_logs(pod_name: str, namespace: str = "default", lines: int = 50) -> dict:
    """
    Get logs from a pod.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        lines: Number of lines to return (default: 50)
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=lines)

        return {"pod": pod_name, "namespace": namespace, "lines": lines, "logs": logs}
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def get_pod_events(pod_name: str, namespace: str = "default") -> dict:
    """
    Get events for a specific pod. Useful for debugging issues.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        # Get events for the pod
        field_selector = f"involvedObject.name={pod_name}"
        events = core_v1.list_namespaced_event(namespace=namespace, field_selector=field_selector)

        event_list = []
        for event in events.items:
            event_list.append(
                {
                    "type": event.type,  # Normal or Warning
                    "reason": event.reason,
                    "message": event.message,
                    "count": event.count,
                    "first_seen": (event.first_timestamp.isoformat() if event.first_timestamp else None),
                    "last_seen": (event.last_timestamp.isoformat() if event.last_timestamp else None),
                }
            )

        # Sort by last seen (most recent first)
        event_list.sort(key=lambda x: x["last_seen"] or "", reverse=True)

        return {
            "pod": pod_name,
            "namespace": namespace,
            "total_events": len(event_list),
            "warnings": sum(1 for e in event_list if e["type"] == "Warning"),
            "events": event_list,
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def describe_pod(pod_name: str, namespace: str = "default") -> dict:
    """
    Get detailed information about a pod.

    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        # Get container info
        containers = []
        for c in pod.spec.containers:
            container_info = {
                "name": c.name,
                "image": c.image,
                "ports": [{"container_port": p.container_port, "protocol": p.protocol} for p in (c.ports or [])],
                "resources": {
                    "requests": (dict(c.resources.requests) if c.resources and c.resources.requests else {}),
                    "limits": (dict(c.resources.limits) if c.resources and c.resources.limits else {}),
                },
                "env_vars": len(c.env or []),
                "volume_mounts": len(c.volume_mounts or []),
            }
            containers.append(container_info)

        # Get conditions
        conditions = []
        if pod.status.conditions:
            for cond in pod.status.conditions:
                conditions.append(
                    {
                        "type": cond.type,
                        "status": cond.status,
                        "reason": cond.reason,
                        "message": cond.message,
                    }
                )

        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node": pod.spec.node_name,
            "ip": pod.status.pod_ip,
            "created": (pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None),
            "labels": pod.metadata.labels or {},
            "annotations": pod.metadata.annotations or {},
            "containers": containers,
            "conditions": conditions,
            "restart_policy": pod.spec.restart_policy,
            "service_account": pod.spec.service_account_name,
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def get_node_status() -> dict:
    """
    Get status of all nodes in the cluster including resource usage.
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        nodes = core_v1.list_node()

        node_list = []
        for node in nodes.items:
            # Get conditions
            conditions = {}
            if node.status.conditions:
                for cond in node.status.conditions:
                    conditions[cond.type] = cond.status

            # Get capacity
            capacity = node.status.capacity or {}
            allocatable = node.status.allocatable or {}

            # Determine if node is ready
            is_ready = conditions.get("Ready") == "True"

            node_list.append(
                {
                    "name": node.metadata.name,
                    "status": "Ready" if is_ready else "NotReady",
                    "roles": [
                        k.replace("node-role.kubernetes.io/", "")
                        for k in (node.metadata.labels or {}).keys()
                        if k.startswith("node-role.kubernetes.io/")
                    ],
                    "age": _calculate_age(node.metadata.creation_timestamp),
                    "version": (node.status.node_info.kubelet_version if node.status.node_info else None),
                    "os": (node.status.node_info.os_image if node.status.node_info else None),
                    "capacity": {
                        "cpu": capacity.get("cpu"),
                        "memory": capacity.get("memory"),
                        "pods": capacity.get("pods"),
                    },
                    "allocatable": {
                        "cpu": allocatable.get("cpu"),
                        "memory": allocatable.get("memory"),
                        "pods": allocatable.get("pods"),
                    },
                    "conditions": conditions,
                }
            )

        return {
            "total_nodes": len(node_list),
            "ready": sum(1 for n in node_list if n["status"] == "Ready"),
            "not_ready": sum(1 for n in node_list if n["status"] != "Ready"),
            "nodes": node_list,
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def diagnose_cluster() -> dict:
    """
    Run a comprehensive health check on the cluster.
    Returns issues found and recommendations.
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    issues = []
    warnings = []
    recommendations = []

    try:
        # Check nodes
        nodes = core_v1.list_node()
        for node in nodes.items:
            if node.status.conditions:
                for cond in node.status.conditions:
                    if cond.type == "Ready" and cond.status != "True":
                        issues.append(
                            {
                                "severity": "critical",
                                "resource": f"node/{node.metadata.name}",
                                "issue": "Node is not ready",
                                "details": cond.message,
                            }
                        )
                    elif cond.type in ["MemoryPressure", "DiskPressure", "PIDPressure"] and cond.status == "True":
                        issues.append(
                            {
                                "severity": "warning",
                                "resource": f"node/{node.metadata.name}",
                                "issue": f"Node has {cond.type}",
                                "details": cond.message,
                            }
                        )

        # Check pods across all namespaces
        pods = core_v1.list_pod_for_all_namespaces()
        for pod in pods.items:
            # Check for non-running pods
            if pod.status.phase in ["Failed", "Unknown"]:
                issues.append(
                    {
                        "severity": "critical",
                        "resource": f"pod/{pod.metadata.namespace}/{pod.metadata.name}",
                        "issue": f"Pod is in {pod.status.phase} state",
                        "details": None,
                    }
                )
            elif pod.status.phase == "Pending":
                # Check why it's pending
                if pod.status.conditions:
                    for cond in pod.status.conditions:
                        if cond.status != "True" and cond.message:
                            issues.append(
                                {
                                    "severity": "warning",
                                    "resource": f"pod/{pod.metadata.namespace}/{pod.metadata.name}",
                                    "issue": f"Pod is Pending: {cond.reason}",
                                    "details": cond.message,
                                }
                            )
                            break

            # Check for high restart counts
            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    if cs.restart_count > 5:
                        warnings.append(
                            {
                                "severity": "warning",
                                "resource": f"pod/{pod.metadata.namespace}/{pod.metadata.name}",
                                "issue": f"Container {cs.name} has {cs.restart_count} restarts",
                                "details": "Investigate CrashLoopBackOff or OOMKilled",
                            }
                        )

        # Check deployments
        deployments = apps_v1.list_deployment_for_all_namespaces()
        for dep in deployments.items:
            ready = dep.status.ready_replicas or 0
            desired = dep.spec.replicas or 0
            if ready < desired:
                issues.append(
                    {
                        "severity": "warning",
                        "resource": f"deployment/{dep.metadata.namespace}/{dep.metadata.name}",
                        "issue": f"Deployment has {ready}/{desired} replicas ready",
                        "details": "Some replicas are not available",
                    }
                )

        # Generate recommendations
        if any(i["issue"].startswith("Node is not ready") for i in issues):
            recommendations.append("Check node status with 'kubectl describe node <name>'")

        if any("restart" in str(w.get("issue", "")).lower() for w in warnings):
            recommendations.append("Check pod logs for containers with high restart counts")

        if any("Pending" in str(i.get("issue", "")) for i in issues):
            recommendations.append("Check if cluster has sufficient resources for pending pods")

        if not issues and not warnings:
            recommendations.append("Cluster appears healthy. Continue monitoring.")

        # Calculate health score
        critical_count = sum(1 for i in issues if i["severity"] == "critical")
        warning_count = sum(1 for i in issues if i["severity"] == "warning") + len(warnings)

        if critical_count > 0:
            health_score = max(0, 50 - (critical_count * 20))
            health_status = "Critical"
        elif warning_count > 0:
            health_score = max(50, 90 - (warning_count * 10))
            health_status = "Degraded"
        else:
            health_score = 100
            health_status = "Healthy"

        return {
            "health_status": health_status,
            "health_score": health_score,
            "summary": {
                "critical_issues": critical_count,
                "warnings": warning_count,
                "nodes_checked": len(nodes.items),
                "pods_checked": len(pods.items),
                "deployments_checked": len(deployments.items),
            },
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


@mcp.tool()
async def get_resource_usage(namespace: str = "default") -> dict:
    """
    Get resource requests and limits for pods in a namespace.
    Helps identify over/under-provisioned workloads.

    Args:
        namespace: Kubernetes namespace (use "all" for all namespaces)
    """
    if not cluster_connected:
        return {"error": "Not connected to a Kubernetes cluster"}

    try:
        if namespace == "all":
            pods = core_v1.list_pod_for_all_namespaces()
        else:
            pods = core_v1.list_namespaced_pod(namespace=namespace)

        pod_resources = []
        total_cpu_requests = 0
        total_cpu_limits = 0
        total_memory_requests = 0
        total_memory_limits = 0
        pods_without_limits = 0

        for pod in pods.items:
            if pod.status.phase != "Running":
                continue

            pod_cpu_req = 0
            pod_cpu_lim = 0
            pod_mem_req = 0
            pod_mem_lim = 0
            has_limits = True

            for container in pod.spec.containers:
                if container.resources:
                    req = container.resources.requests or {}
                    lim = container.resources.limits or {}

                    pod_cpu_req += _parse_cpu(req.get("cpu", "0"))
                    pod_cpu_lim += _parse_cpu(lim.get("cpu", "0"))
                    pod_mem_req += _parse_memory(req.get("memory", "0"))
                    pod_mem_lim += _parse_memory(lim.get("memory", "0"))

                    if not lim:
                        has_limits = False
                else:
                    has_limits = False

            if not has_limits:
                pods_without_limits += 1

            total_cpu_requests += pod_cpu_req
            total_cpu_limits += pod_cpu_lim
            total_memory_requests += pod_mem_req
            total_memory_limits += pod_mem_lim

            pod_resources.append(
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "cpu_requests": f"{pod_cpu_req}m",
                    "cpu_limits": f"{pod_cpu_lim}m",
                    "memory_requests": f"{pod_mem_req}Mi",
                    "memory_limits": f"{pod_mem_lim}Mi",
                    "has_limits": has_limits,
                }
            )

        return {
            "namespace": namespace,
            "total_pods": len(pod_resources),
            "pods_without_limits": pods_without_limits,
            "totals": {
                "cpu_requests": f"{total_cpu_requests}m",
                "cpu_limits": f"{total_cpu_limits}m",
                "memory_requests": f"{total_memory_requests}Mi",
                "memory_limits": f"{total_memory_limits}Mi",
            },
            "pods": pod_resources,
            "recommendations": [
                (
                    f"{pods_without_limits} pods don't have resource limits set"
                    if pods_without_limits > 0
                    else "All pods have resource limits ✓"
                )
            ],
        }
    except ApiException as e:
        return {"error": f"API error: {e.reason}"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _calculate_age(timestamp) -> str:
    """Calculate human-readable age from timestamp."""
    if not timestamp:
        return "Unknown"

    now = datetime.now(timestamp.tzinfo)
    diff = now - timestamp

    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"


def _parse_cpu(cpu_str: str) -> int:
    """Parse CPU string to millicores."""
    if not cpu_str:
        return 0
    cpu_str = str(cpu_str)
    if cpu_str.endswith("m"):
        return int(cpu_str[:-1])
    else:
        return int(float(cpu_str) * 1000)


def _parse_memory(mem_str: str) -> int:
    """Parse memory string to Mi."""
    if not mem_str:
        return 0
    mem_str = str(mem_str)

    units = {
        "Ki": 1 / 1024,
        "Mi": 1,
        "Gi": 1024,
        "Ti": 1024 * 1024,
        "K": 1 / 1024,
        "M": 1,
        "G": 1024,
        "T": 1024 * 1024,
    }

    for unit, multiplier in units.items():
        if mem_str.endswith(unit):
            return int(float(mem_str[: -len(unit)]) * multiplier)

    # Assume bytes
    return int(int(mem_str) / (1024 * 1024))


# =============================================================================
# MCP RESOURCES - Provide context to AI
# =============================================================================


@mcp.resource("cluster://status")
async def cluster_status_resource() -> str:
    """Provide current cluster status as context."""
    if not cluster_connected:
        return "Not connected to Kubernetes cluster"

    info = await get_cluster_info()
    diagnosis = await diagnose_cluster()

    return json.dumps({"cluster_info": info, "health_check": diagnosis}, indent=2)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Kubernetes MCP Server")
    print("=" * 60)

    # Initialize Kubernetes connection
    if init_kubernetes():
        print("Ready to accept MCP connections")
    else:
        print("WARNING: Running without Kubernetes connection")
        print("Some tools will return errors")

    print("=" * 60)

    # Run the MCP server
    mcp.run()
