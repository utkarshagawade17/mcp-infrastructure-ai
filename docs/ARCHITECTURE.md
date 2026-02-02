# Architecture Overview

## System Architecture

The Palette AI Ops Toolkit follows a modular architecture designed for enterprise deployment:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI Assistants (Claude, ChatGPT, etc.)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ MCP Protocol
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP Server Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Cluster Tools  │  │  Profile Tools  │  │ Diagnostic Tools│              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                        │
│           └────────────────────┴────────────────────┘                        │
│                                │                                             │
└────────────────────────────────┼─────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│     Guardrails Layer      │   │      AI Agents Layer      │
│  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │
│  │   Policy Engine     │  │   │  │   Cluster Doctor    │  │
│  ├─────────────────────┤  │   │  ├─────────────────────┤  │
│  │  Prompt Validator   │  │   │  │  Profile Advisor    │  │
│  ├─────────────────────┤  │   │  ├─────────────────────┤  │
│  │  Action Validator   │  │   │  │ Compliance Checker  │  │
│  └─────────────────────┘  │   │  └─────────────────────┘  │
└───────────────────────────┘   └───────────────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Palette API Layer                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    api.spectrocloud.com/v1                          │    │
│  │  /spectroclusters  /clusterprofiles  /packs  /events  /metrics     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Palette-Managed Clusters                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  AWS EKS    │  │ Azure AKS   │  │  GCP GKE    │  │    Edge     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. MCP Server Layer

The Model Context Protocol server exposes Palette operations as tools for automation tools:

**Design Principles:**
- Stateless request handling for scalability
- Async I/O for high throughput
- Structured tool definitions with clear schemas
- Demo mode for offline development

**Key Tools:**
| Tool | Purpose | Palette API Endpoint |
|------|---------|---------------------|
| `list_clusters` | Get all clusters | `GET /v1/spectroclusters` |
| `get_cluster_details` | Cluster deep dive | `GET /v1/spectroclusters/{uid}` |
| `diagnose_cluster` | automated health check | Multiple endpoints |
| `recommend_profile` | Profile suggestions | `GET /v1/clusterprofiles`, `/v1/packs` |
| `validate_configuration` | Policy validation | Local policy engine |

### 2. Guardrails Layer

Enterprise governance for AI operations:

```
┌────────────────────────────────────────────────────┐
│                 Guardrails Flow                     │
│                                                     │
│  User Request → Prompt Validator → MCP Tool        │
│                        │                            │
│                        ▼                            │
│               [Check for injection,                 │
│                out-of-scope requests]               │
│                        │                            │
│                        ▼                            │
│  AI Response → Action Validator → Execution        │
│                        │                            │
│                        ▼                            │
│               [Check against policies,              │
│                require approval if needed]          │
│                        │                            │
│                        ▼                            │
│                   Audit Log                         │
└────────────────────────────────────────────────────┘
```

**Policy Categories:**
- **Security**: Container security, network isolation, image provenance
- **Cost**: Resource limits, approval for expensive resources
- **Compliance**: Framework-specific rules (CIS, HIPAA, etc.)

### 3. AI Agents Layer

Intelligent analysis and recommendations:

**Cluster Doctor Agent:**
```python
# Analyzer Pipeline
1. Gather State → Events, Metrics, Conditions
2. Run Analyzers → NodeHealth, ResourceUtil, EventAnalysis
3. Calculate Score → 0-100 health score
4. LLM Enrichment → Root cause, recommendations
5. Return Report → Structured diagnosis
```

**Profile Advisor Agent:**
```python
# Recommendation Pipeline
1. Parse Requirements → Workload description, constraints
2. Query Packs → Available packs for cloud provider
3. Match Patterns → GPU workloads, edge, HA, etc.
4. Rank Options → By fit, cost, trade-offs
5. Return Recommendations → Prioritized list
```

### 4. Data Flow

**Read Operations (Diagnosis, Listing):**
```
AI Assistant
    │
    ▼ [MCP Request]
MCP Server
    │
    ▼ [HTTP GET]
Palette API
    │
    ▼ [Response]
MCP Server
    │
    ▼ [Formatted Response]
AI Assistant
```

**Write Operations (with Guardrails):**
```
AI Assistant
    │
    ▼ [Proposed Action]
Prompt Validator ──[Block]──> Rejection
    │
    │ [Pass]
    ▼
MCP Server
    │
    ▼ [Prepare Action]
Action Validator
    │
    ├──[Requires Approval]──> Approval Queue
    │
    │ [Approved/Auto-pass]
    ▼
Palette API
    │
    ▼ [Audit Log]
Result
```

## Deployment Architecture

### Kubernetes Deployment

```yaml
Namespace: ai-ops-toolkit
│
├── Deployment: palette-mcp-server
│   ├── Replicas: 1-3 (based on load)
│   ├── Resources: 256Mi-512Mi memory
│   └── Probes: liveness, readiness
│
├── ConfigMap: ai-ops-config
│   ├── Palette endpoint
│   ├── LLM configuration
│   └── Feature flags
│
├── Secret: ai-ops-secrets
│   ├── PALETTE_API_KEY
│   └── LLM_API_KEY
│
├── ServiceAccount: ai-ops-toolkit
│   └── ClusterRole: read-only cluster access
│
└── Service: palette-mcp-server
    ├── Port 8080: HTTP/health
    └── Port 3000: MCP protocol
```

### LLM Backend Options

| Provider | Use Case | Configuration |
|----------|----------|---------------|
| LocalAI/Ollama | Air-gapped, privacy | `LLM_PROVIDER=local` |
| OpenAI | Best quality, SaaS | `LLM_PROVIDER=openai` |
| Anthropic | Alternative SaaS | `LLM_PROVIDER=anthropic` |
| Azure OpenAI | Enterprise Azure | `LLM_PROVIDER=azure` |

## Security Considerations

### Authentication Flow

```
1. MCP Server authenticates to Palette using API Key
2. API Key scoped to specific project (ProjectUid header)
3. All operations inherit RBAC permissions of API key owner
4. Audit logs capture all API calls
```

### Secrets Management

- API keys passed via environment variables
- Kubernetes Secrets for deployment
- Never logged or exposed in responses
- Support for external secret managers (Vault, AWS SM)

### Network Security

- Internal service only (no public exposure)
- mTLS optional for high-security environments
- Network policies restrict egress to Palette API only

## Scalability

### Horizontal Scaling

```
Load Balancer
      │
      ├── MCP Server Pod 1
      ├── MCP Server Pod 2
      └── MCP Server Pod 3
             │
             ▼
      Palette API (rate limited)
```

### Rate Limiting

- Palette API: 10-50 req/s depending on endpoint
- MCP Server implements client-side rate limiting
- Exponential backoff for retries

## Monitoring

### Metrics Exposed

- `mcp_requests_total` - Total MCP requests by tool
- `mcp_request_duration_seconds` - Latency histogram
- `guardrails_violations_total` - Policy violations
- `palette_api_calls_total` - API calls by endpoint

### Health Endpoints

- `/health` - Liveness check
- `/ready` - Readiness check (Palette API connectivity)
- `/metrics` - Prometheus metrics

## Future Enhancements

1. **Multi-tenant Support**: Project-level isolation
2. **Caching Layer**: Redis for frequently accessed data
3. **Event-driven**: Webhook integration for real-time updates
4. **PaletteAI Studio Integration**: Direct integration with PaletteAI
