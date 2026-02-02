# Palette MCP Server

This is the **Spectro Cloud Palette** adaptation of the MCP server.

## Status

🔶 **Ready to connect** - Runs with mock data until Palette API access is provided.

## What's Different from K8s Version

| K8s Version | Palette Version |
|-------------|-----------------|
| Queries K8s API directly | Queries Palette REST API |
| Lists pods, deployments | Lists clusters, profiles |
| Basic health checks | Profile drift, pack compatibility |
| - | AI profile recommendations |
| - | Enterprise guardrails |

## Structure

```
palette-mcp/
├── mcp_server/
│   ├── palette_mcp.py        # Main MCP server
│   ├── config.py             # Configuration
│   └── tools/
│       ├── cluster_tools.py  # Cluster operations
│       ├── profile_tools.py  # Cluster Profiles
│       └── diagnostic_tools.py # AI diagnostics
│
├── guardrails/
│   ├── policy_engine.py      # Policy validation
│   └── policies/
│       └── security.yaml     # Security rules
│
└── terraform/
    ├── main.tf               # Deployment config
    ├── variables.tf          # Input variables
    └── outputs.tf            # Outputs
```

## Running (Mock Mode)

```bash
pip install -r requirements.txt
python -m mcp_server.palette_mcp
```

## Running (With API Access)

```bash
export PALETTE_API_KEY="your-key"
export PALETTE_PROJECT_UID="your-project"
python -m mcp_server.palette_mcp
```

## Palette-Specific Tools

| Tool | Description |
|------|-------------|
| `list_clusters` | All Palette-managed clusters |
| `get_cluster_details` | Deep dive into a cluster |
| `list_cluster_profiles` | Available profiles |
| `get_profile_details` | Profile layers and packs |
| `recommend_profile` | **AI suggests best profile** |
| `diagnose_cluster` | **AI health check** |
| `validate_configuration` | **Policy compliance check** |
| `compare_clusters` | Drift detection |

## Guardrails

Enterprise governance for AI operations:

```python
# Every AI action is validated
result = policy_engine.validate_action(action)

if result.requires_approval:
    # Human approval needed
if result.violations:
    # Action blocked
```

**Policies include:**
- No privileged containers
- Approved registries only
- Resource limits required
- Public load balancers need approval
- GPU usage needs approval
