# =============================================================================
# Palette AI Ops Toolkit - Terraform Variables
# =============================================================================

# -----------------------------------------------------------------------------
# PALETTE CONFIGURATION
# -----------------------------------------------------------------------------

variable "palette_endpoint" {
  description = "Palette API endpoint URL"
  type        = string
  default     = "https://api.spectrocloud.com"
}

variable "palette_api_key" {
  description = "Palette API key for authentication"
  type        = string
  sensitive   = true
}

variable "palette_project" {
  description = "Palette project name"
  type        = string
  default     = "Default"
}

variable "target_cluster_name" {
  description = "Name of the target cluster for deployment"
  type        = string
}

# -----------------------------------------------------------------------------
# DEPLOYMENT CONFIGURATION
# -----------------------------------------------------------------------------

variable "namespace" {
  description = "Kubernetes namespace for AI Ops Toolkit"
  type        = string
  default     = "ai-ops-toolkit"
}

variable "cloud_type" {
  description = "Cloud provider type (aws, azure, gcp, vsphere, edge)"
  type        = string
  default     = "aws"
  
  validation {
    condition     = contains(["aws", "azure", "gcp", "vsphere", "edge", "maas"], var.cloud_type)
    error_message = "Cloud type must be one of: aws, azure, gcp, vsphere, edge, maas"
  }
}

variable "kubernetes_version" {
  description = "Kubernetes version for the cluster profile"
  type        = string
  default     = "1.28.5"
}

variable "create_ai_profile" {
  description = "Whether to create an AI-optimized cluster profile"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = list(string)
  default     = ["ai-ops", "managed-by-terraform"]
}

# -----------------------------------------------------------------------------
# MCP SERVER CONFIGURATION
# -----------------------------------------------------------------------------

variable "mcp_server_image" {
  description = "Docker image for the MCP server"
  type        = string
  default     = "ghcr.io/spectrocloud/palette-mcp-server:latest"
}

variable "mcp_server_replicas" {
  description = "Number of MCP server replicas"
  type        = number
  default     = 1
}

variable "mcp_server_cpu_request" {
  description = "CPU request for MCP server"
  type        = string
  default     = "100m"
}

variable "mcp_server_cpu_limit" {
  description = "CPU limit for MCP server"
  type        = string
  default     = "500m"
}

variable "mcp_server_memory_request" {
  description = "Memory request for MCP server"
  type        = string
  default     = "256Mi"
}

variable "mcp_server_memory_limit" {
  description = "Memory limit for MCP server"
  type        = string
  default     = "512Mi"
}

# -----------------------------------------------------------------------------
# LLM CONFIGURATION
# -----------------------------------------------------------------------------

variable "llm_provider" {
  description = "LLM provider (local, openai, anthropic)"
  type        = string
  default     = "local"
  
  validation {
    condition     = contains(["local", "openai", "anthropic", "azure"], var.llm_provider)
    error_message = "LLM provider must be one of: local, openai, anthropic, azure"
  }
}

variable "llm_model" {
  description = "LLM model name"
  type        = string
  default     = "llama3"
}

variable "llm_endpoint" {
  description = "LLM API endpoint (for local or custom providers)"
  type        = string
  default     = "http://localhost:11434/v1"
}

variable "llm_api_key" {
  description = "API key for LLM provider (if required)"
  type        = string
  default     = ""
  sensitive   = true
}

# -----------------------------------------------------------------------------
# GUARDRAILS CONFIGURATION
# -----------------------------------------------------------------------------

variable "enable_guardrails" {
  description = "Enable AI guardrails for governance"
  type        = bool
  default     = true
}

variable "guardrails_strict_mode" {
  description = "Enable strict mode for guardrails (blocks instead of warns)"
  type        = bool
  default     = false
}

variable "guardrails_policies" {
  description = "List of guardrails policies to enable"
  type        = list(string)
  default     = [
    "require_resource_limits",
    "no_privileged_containers",
    "require_health_checks"
  ]
}

# -----------------------------------------------------------------------------
# FEATURE FLAGS
# -----------------------------------------------------------------------------

variable "enable_cost_analysis" {
  description = "Enable cost analysis features"
  type        = bool
  default     = true
}

variable "enable_security_scan" {
  description = "Enable security scanning features"
  type        = bool
  default     = true
}

variable "enable_recommendations" {
  description = "Enable AI-powered recommendations"
  type        = bool
  default     = true
}
