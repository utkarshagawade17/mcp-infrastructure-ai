# MCP Infrastructure Management Server

Model Context Protocol server implementation for Kubernetes and Spectro Cloud Palette infrastructure operations.

## Overview

This project implements MCP (Model Context Protocol) servers for managing cloud-native infrastructure through programmatic interfaces. The implementation includes two variants:

- **Kubernetes MCP Server**: Production-ready server for Kubernetes cluster management
- **Palette MCP Server**: Spectro Cloud Palette integration for multi-cloud operations

## Architecture

The system uses MCP to expose infrastructure operations as callable tools, enabling automation, monitoring, and management workflows.

### Components

```
mcp-infrastructure-ai/
├── k8s-mcp-live/           # Kubernetes MCP implementation
│   ├── mcp_server.py       # Core server with 11 operational tools
│   ├── demo_cli.py         # Command-line interface
│   └── setup_demo.sh       # Environment setup script
│
├── palette-mcp/            # Palette MCP implementation
│   ├── mcp_server/         # Server core
│   │   ├── palette_mcp.py  # Main server logic
│   │   ├── config.py       # Configuration management
│   │   └── tools/          # Operational tool implementations
│   │
│   └── guardrails/         # Policy enforcement layer
│       ├── policy_engine.py
│       └── policies/
│
├── mcp_chat.py            # Interactive management console
└── tests/                 # Test suite
```

## Quick Start

### Prerequisites

- Python 3.9+
- kubectl configured (for Kubernetes variant)
- Kubernetes cluster access (minikube, kind, or cloud provider)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd mcp-infrastructure-ai

# Install dependencies
pip install -r k8s-mcp-live/requirements.txt
```

### Running Kubernetes MCP Server

```bash
# 1. Start a Kubernetes cluster
minikube start
# or
kind create cluster --name mcp-demo

# 2. Deploy sample workloads
cd k8s-mcp-live
./setup_demo.sh

# 3. Start MCP server
python mcp_server.py
```

### Running Interactive Console

```bash
python mcp_chat.py
```

## Features

### Kubernetes MCP Server

**Cluster Operations**
- Cluster information retrieval
- Node status monitoring
- Namespace management
- Resource inventory

**Workload Management**
- Pod lifecycle operations
- Deployment status tracking
- Service discovery
- Event monitoring

**Diagnostics & Analysis**
- Automated health checks
- Issue detection and classification
- Resource utilization analysis
- Performance metrics

**Policy & Governance**
- Resource limit validation
- Security policy checks
- Compliance monitoring
- Cost analysis

### Palette MCP Server

**Multi-Cloud Management**
- Cluster lifecycle operations
- Cross-cloud resource management
- Unified monitoring interface

**Cluster Profiles**
- Profile application and management
- Configuration drift detection
- Pack version tracking

**Enterprise Features**
- Policy-based governance
- Approval workflows
- Audit logging
- Cost optimization

## MCP Tools Reference

### Kubernetes Server Tools

| Tool | Description |
|------|-------------|
| `get_cluster_info` | Retrieve cluster metadata and status |
| `list_pods` | List pods across namespaces |
| `list_deployments` | Get deployment status |
| `get_node_status` | Check node health and capacity |
| `diagnose_cluster` | Run comprehensive health analysis |
| `get_resource_usage` | Analyze resource allocation |
| `describe_pod` | Get detailed pod information |
| `get_pod_logs` | Retrieve container logs |
| `get_pod_events` | Fetch pod lifecycle events |
| `list_services` | Service discovery |
| `get_namespaces` | List available namespaces |

### Palette Server Tools

| Tool | Description |
|------|-------------|
| `list_clusters` | Get managed clusters inventory |
| `get_cluster_details` | Detailed cluster information |
| `diagnose_cluster` | Health and compliance analysis |
| `recommend_profile` | Suggest optimal cluster profiles |
| `validate_configuration` | Policy validation |
| `get_cluster_nodes` | Node status across clouds |
| `analyze_cluster_cost` | Cost breakdown and optimization |

## Configuration

### Environment Variables

```bash
# Palette API credentials
export PALETTE_API_KEY="your-api-key"
export PALETTE_PROJECT_UID="project-uid"

# For interactive console
export ANTHROPIC_API_KEY="your-key"
```

### Kubernetes Access

Ensure kubectl is configured:

```bash
kubectl cluster-info
kubectl get nodes
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding New Tools

1. Implement tool function in appropriate module
2. Register with MCP server using `@mcp.tool()` decorator
3. Add type hints and documentation
4. Write tests

Example:

```python
@mcp.tool()
async def new_tool(param: str) -> dict:
    """
    Tool description for documentation.

    Args:
        param: Parameter description

    Returns:
        Result dictionary
    """
    # Implementation
    return result
```

### Policy Configuration

Edit `palette-mcp/guardrails/policies/security.yaml` to define custom policies:

```yaml
policies:
  - name: require-resource-limits
    severity: medium
    check: resources.limits
    message: Containers must define resource limits
```

## Production Deployment

### Security Considerations

- Use read-only API credentials where possible
- Enable audit logging
- Implement rate limiting
- Secure credential storage
- Network policy enforcement

### Scaling

- Deploy as containerized service
- Use connection pooling for API clients
- Implement caching layer
- Set up monitoring and alerting

### High Availability

- Run multiple server instances
- Use load balancer for distribution
- Implement health checks
- Set up failover mechanisms

## Integration Examples

### Automation Workflows

```python
from mcp_server import tools

# Automated cluster health check
health = await tools.diagnose_cluster()
if health['score'] < 80:
    # Trigger alerts
    send_alert(health['issues'])
```

### CI/CD Pipeline

```bash
# Pre-deployment validation
python -m mcp_server.tools.validate_configuration deployment.yaml

# Post-deployment verification
python -m mcp_server.tools.diagnose_cluster
```

## Troubleshooting

### Connection Issues

**Kubernetes API not accessible**
```bash
# Verify cluster connection
kubectl cluster-info
export KUBECONFIG=/path/to/kubeconfig
```

**Palette API authentication failure**
```bash
# Verify credentials
echo $PALETTE_API_KEY
# Check API endpoint connectivity
curl -H "Authorization: Bearer $PALETTE_API_KEY" https://api.spectrocloud.com/v1/health
```

### Performance Issues

- Enable caching for frequently accessed resources
- Increase API client timeout values
- Use batch operations where available
- Monitor API rate limits

## Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [Usage Guide](USAGE.md)
- [API Reference](https://modelcontextprotocol.io/)

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions, open a GitHub issue or contact the development team.
