# Kubernetes MCP Server - Live Demo

This is the **working demo** that runs against a real Kubernetes cluster.

## Quick Start

```bash
# 1. Start minikube
minikube start

# 2. Deploy sample workloads
./setup_demo.sh

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run interactive demo
python demo_cli.py
```

## What's Here

- `mcp_server.py` - Complete MCP server with 11 tools
- `demo_cli.py` - Interactive CLI for demonstrations
- `setup_demo.sh` - Creates sample healthy + broken workloads
- `requirements.txt` - Python dependencies

## Tools Available

| Tool | Description |
|------|-------------|
| `get_cluster_info` | Cluster version, node count |
| `list_namespaces` | All namespaces |
| `list_pods` | Pods with status |
| `list_deployments` | Deployment health |
| `list_services` | Service inventory |
| `get_node_status` | Node health + resources |
| `diagnose_cluster` | **automated health check** |
| `get_resource_usage` | Resource limits analysis |
| `describe_pod` | Pod details |
| `get_pod_logs` | Container logs |
| `get_pod_events` | Events for debugging |

## The Key Demo

```
Select: 8 - DIAGNOSE CLUSTER
```

This runs an automated health check that:
1. Scans all nodes, pods, deployments
2. Identifies issues (failures, high restarts, resource pressure)
3. Calculates health score
4. Generates recommendations

**Same pattern used in the Palette version** - just different API.
