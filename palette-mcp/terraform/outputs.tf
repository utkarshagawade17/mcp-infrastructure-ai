# =============================================================================
# Palette AI Ops Toolkit - Terraform Outputs
# =============================================================================

output "namespace" {
  description = "Kubernetes namespace where toolkit is deployed"
  value       = kubernetes_namespace.ai_ops.metadata[0].name
}

output "mcp_server_service" {
  description = "MCP server service name"
  value       = kubernetes_service.mcp_server.metadata[0].name
}

output "mcp_server_endpoint" {
  description = "Internal endpoint for MCP server"
  value       = "${kubernetes_service.mcp_server.metadata[0].name}.${kubernetes_namespace.ai_ops.metadata[0].name}.svc.cluster.local:3000"
}

output "ai_profile_uid" {
  description = "UID of the created AI cluster profile (if created)"
  value       = var.create_ai_profile ? spectrocloud_cluster_profile.ai_ops_profile[0].id : null
}

output "service_account" {
  description = "Service account used by the toolkit"
  value       = kubernetes_service_account.ai_ops.metadata[0].name
}

output "configuration_summary" {
  description = "Summary of the deployed configuration"
  value = {
    llm_provider      = var.llm_provider
    llm_model         = var.llm_model
    guardrails        = var.enable_guardrails
    cost_analysis     = var.enable_cost_analysis
    security_scan     = var.enable_security_scan
    recommendations   = var.enable_recommendations
  }
}
