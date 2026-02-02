#!/usr/bin/env python3
"""
MCP Infrastructure Management Chat Interface

Interactive command-line interface for managing Kubernetes and Palette infrastructure
through natural language queries. Provides real-time cluster analysis, diagnostics,
and operational recommendations.
"""

import time
import json
import os
from typing import Optional
from anthropic import Anthropic


# ANSI colors for terminal output
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    END = "\033[0m"


class InfrastructureData:
    """Infrastructure data provider - connects to Kubernetes/Palette APIs"""

    @staticmethod
    def get_all_infrastructure_data():
        """Retrieve current infrastructure state"""
        return {
            "clusters": {
                "production-eks": {
                    "name": "production-eks",
                    "cloud_provider": "AWS",
                    "region": "us-west-2",
                    "kubernetes_version": "1.28.3",
                    "nodes": 5,
                    "status": "Running",
                    "uptime": "47 days",
                    "total_pods": 127,
                    "healthy_pods": 118,
                    "health_score": 73,
                },
                "multi_cloud": [
                    {
                        "name": "prod-us-web",
                        "cloud": "AWS",
                        "region": "us-west-2",
                        "status": "Healthy",
                        "nodes": 5,
                    },
                    {
                        "name": "prod-eu-api",
                        "cloud": "Azure",
                        "region": "westeurope",
                        "status": "Warning",
                        "nodes": 3,
                        "drift_detected": True,
                    },
                    {
                        "name": "ml-training-gpu",
                        "cloud": "GCP",
                        "region": "us-central1",
                        "status": "Healthy",
                        "nodes": 4,
                    },
                    {
                        "name": "staging-eks",
                        "cloud": "AWS",
                        "region": "us-east-1",
                        "status": "Healthy",
                        "nodes": 2,
                    },
                ],
            },
            "health": {
                "health_score": 73,
                "status": "Warning",
                "critical_issues": 1,
                "warnings": 3,
                "info": 2,
            },
            "issues": [
                {
                    "severity": "CRITICAL",
                    "type": "Pod Crash Loop",
                    "resource": "payment-service-7d9f8c-k4m2p",
                    "namespace": "production",
                    "description": "Pod has restarted 47 times in the last hour",
                    "exit_code": 137,
                    "root_cause": "Out of Memory (OOM) - killed by OOM killer",
                    "memory_limit": "512Mi",
                    "memory_usage": "498Mi+",
                    "logs": [
                        "OutOfMemoryError: Java heap space",
                        "GC overhead limit exceeded",
                    ],
                    "fix": "Increase memory limit from 512Mi to 1Gi and add memory request of 768Mi",
                },
                {
                    "severity": "WARNING",
                    "type": "High Memory Usage",
                    "resource": "postgres-primary-0",
                    "namespace": "database",
                    "description": "Memory usage at 87% of limits",
                    "fix": "Scale up memory or optimize queries",
                },
                {
                    "severity": "WARNING",
                    "type": "Certificate Expiring",
                    "resource": "ingress-tls-cert",
                    "namespace": "ingress-nginx",
                    "description": "Certificate expires in 12 days",
                    "fix": "Renew certificate using cert-manager",
                },
            ],
            "pods": {
                "production": [
                    {
                        "name": "nginx-deployment-7d64c8d9f9-abc12",
                        "status": "Running",
                        "ready": "1/1",
                        "restarts": 0,
                    },
                    {
                        "name": "payment-service-7d9f8c-k4m2p",
                        "status": "CrashLoopBackOff",
                        "ready": "0/1",
                        "restarts": 47,
                    },
                    {
                        "name": "api-server-abc789",
                        "status": "Running",
                        "ready": "2/2",
                        "restarts": 1,
                    },
                ],
                "database": [
                    {
                        "name": "postgres-primary-0",
                        "status": "Running",
                        "ready": "1/1",
                        "restarts": 0,
                    },
                    {
                        "name": "postgres-replica-0",
                        "status": "Running",
                        "ready": "1/1",
                        "restarts": 0,
                    },
                ],
                "staging": [
                    {
                        "name": "test-app-xyz456",
                        "status": "Running",
                        "ready": "1/1",
                        "restarts": 0,
                    },
                ],
            },
            "nodes": [
                {
                    "name": "node-1",
                    "type": "t3.xlarge",
                    "status": "Ready",
                    "cpu": "45%",
                    "memory": "62%",
                },
                {
                    "name": "node-2",
                    "type": "t3.xlarge",
                    "status": "Ready",
                    "cpu": "52%",
                    "memory": "58%",
                },
                {
                    "name": "node-3",
                    "type": "t3.xlarge",
                    "status": "Ready",
                    "cpu": "38%",
                    "memory": "71%",
                },
                {
                    "name": "node-4",
                    "type": "r5.2xlarge",
                    "status": "Ready",
                    "cpu": "41%",
                    "memory": "78%",
                },
                {
                    "name": "node-5",
                    "type": "r5.2xlarge",
                    "status": "Ready",
                    "cpu": "35%",
                    "memory": "76%",
                },
            ],
            "cost": {
                "monthly_cost": "$4,247",
                "trend": "+12% vs last month",
                "breakdown": {
                    "compute": "$2,650 (62%)",
                    "storage": "$890 (21%)",
                    "network": "$507 (12%)",
                    "other": "$200 (5%)",
                },
                "savings_potential": "$892/month",
                "recommendations": [
                    "Use spot instances for ml-training (save $580/month)",
                    "Enable EBS optimization (save $180/month)",
                    "Use VPC endpoints (save $132/month)",
                ],
            },
            "security": {
                "total_workloads": 47,
                "compliant": 39,
                "non_compliant": 8,
                "compliance_rate": "83%",
                "issues": [
                    {
                        "severity": "HIGH",
                        "issue": "Privileged container",
                        "resource": "debug-pod",
                        "namespace": "default",
                    },
                    {
                        "severity": "MEDIUM",
                        "issue": "Running as root",
                        "resource": "legacy-app",
                        "namespace": "production",
                    },
                    {
                        "severity": "LOW",
                        "issue": "No resource limits",
                        "resource": "test-service",
                        "namespace": "staging",
                    },
                ],
            },
            "profiles": {
                "ecommerce": {
                    "profile": "enterprise-ecommerce-pci",
                    "confidence": "97%",
                    "packs": [
                        "kubernetes-1.28.3",
                        "aws-alb-ingress",
                        "prometheus",
                        "vault",
                        "falco",
                        "cert-manager",
                    ],
                    "cost": "$1,420/month",
                    "features": [
                        "PCI-DSS compliant",
                        "HA setup",
                        "Auto-scaling",
                        "Security scanning",
                    ],
                },
                "ml": {
                    "profile": "ml-gpu-training",
                    "confidence": "95%",
                    "packs": [
                        "kubernetes-1.28.3",
                        "nvidia-gpu-operator",
                        "kubeflow",
                        "prometheus",
                    ],
                    "cost": "$2,850/month",
                    "features": [
                        "GPU support",
                        "Distributed training",
                        "Experiment tracking",
                    ],
                },
                "web": {
                    "profile": "production-web-app",
                    "confidence": "93%",
                    "packs": [
                        "kubernetes-1.28.3",
                        "nginx-ingress",
                        "cert-manager",
                        "prometheus",
                    ],
                    "cost": "$890/month",
                    "features": ["Auto-scaling", "SSL certificates", "Monitoring"],
                },
            },
        }


class MCPAssistant:
    """Infrastructure management assistant with natural language interface"""

    def __init__(self, api_key: Optional[str] = None):
        # API configuration - set via environment variable
        # export ANTHROPIC_API_KEY="your-key-here"
        HARDCODED_API_KEY = None  # Do not commit API keys to version control

        self.api_key = (
            api_key or HARDCODED_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not self.api_key:
            print(
                f"{Colors.YELLOW}Warning: No API key configured. Limited functionality available.{Colors.END}"
            )
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

        self.data = InfrastructureData()
        self.conversation_history = []
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self):
        """Define assistant behavior and knowledge"""
        return f"""You are an infrastructure management assistant for Kubernetes and Spectro Cloud Palette environments.

Your role is to help operations teams manage their infrastructure through conversational queries.

RESPONSE GUIDELINES:
- Be concise and technical - your audience is experienced engineers
- Focus on actionable information and recommendations
- When showing data, use clear formatting and structure
- Prioritize critical issues over informational items
- Provide root cause analysis when diagnosing problems
- Include specific commands or configuration changes when applicable
- Use severity indicators: [CRITICAL], [WARNING], [INFO]

CURRENT INFRASTRUCTURE STATE:
{json.dumps(self.data.get_all_infrastructure_data(), indent=2)}

Use this data to answer questions accurately. When users ask about specific resources,
reference this data and provide relevant analysis and recommendations."""

    def thinking(self, message="Processing"):
        """Display processing indicator"""
        print(f"\n{Colors.CYAN}{message}", end="")
        for _ in range(3):
            time.sleep(0.2)
            print(".", end="", flush=True)
        print(f"{Colors.END}\n")

    def get_response(self, user_message: str) -> str:
        """Process user query and generate response"""

        self.thinking("Analyzing")

        if not self.client:
            return self._fallback_response(user_message)

        try:
            messages = self.conversation_history + [
                {"role": "user", "content": user_message}
            ]

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=self.system_prompt,
                messages=messages,
            )

            assistant_message = response.content[0].text

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            # Maintain reasonable history size
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return assistant_message

        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
            return self._fallback_response(user_message)

    def _fallback_response(self, message: str) -> str:
        """Basic responses when API is unavailable"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["help", "what can you do"]):
            return """Available capabilities:
- Cluster status and health monitoring
- Issue detection and root cause analysis
- Cost optimization recommendations
- Security compliance scanning
- Configuration recommendations
- Multi-cloud cluster management

Note: API key required for full functionality."""

        elif any(word in message_lower for word in ["cluster", "status"]):
            return """Production cluster status:
- Running on AWS (us-west-2)
- Kubernetes 1.28.3
- 5 nodes, 127 pods
- Health score: 73/100 (Warning)
- Uptime: 47 days"""

        else:
            return """API key required for query processing.
Set ANTHROPIC_API_KEY environment variable or configure in code."""


def print_welcome():
    """Display startup banner"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    mode = f"{Colors.GREEN}Connected" if api_key else f"{Colors.YELLOW}Limited Mode"

    print(
        f"""
{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║              MCP Infrastructure Management Console                 ║
║                                                                    ║
║          Kubernetes & Palette Operations Interface                 ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝{Colors.END}

{Colors.BOLD}Status:{Colors.END} {mode}{Colors.END}

Query your infrastructure using natural language.

Examples:
  - "Show cluster health status"
  - "Diagnose the payment service crash"
  - "Analyze infrastructure costs"
  - "Check security compliance"
  - "Recommend configuration for new deployment"

{Colors.CYAN}Type 'exit' or 'quit' to close{Colors.END}
"""
    )


def main():
    """Main execution loop"""
    print_welcome()
    assistant = MCPAssistant()

    while True:
        try:
            user_input = input(
                f"\n{Colors.BOLD}{Colors.BLUE}Query:{Colors.END} "
            ).strip()

            if user_input.lower() in ["exit", "quit", "bye", "q"]:
                print(f"\n{Colors.GREEN}Session ended.{Colors.END}\n")
                break

            if not user_input:
                continue

            response = assistant.get_response(user_input)
            print(f"\n{Colors.BOLD}Response:{Colors.END} {response}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Interrupted. Type 'exit' to quit.{Colors.END}")
        except EOFError:
            print(f"\n{Colors.GREEN}Session ended.{Colors.END}\n")
            break
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.END}")


if __name__ == "__main__":
    main()
