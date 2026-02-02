#!/usr/bin/env python3
"""
Interactive CLI Demo for Kubernetes MCP Server

This lets you test the MCP tools directly from command line
without needing a full MCP client setup.

Perfect for Loom video demo!
"""

import asyncio
import json
import sys

# Add color support
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

def print_json(data):
    """Pretty print JSON with colors."""
    formatted = json.dumps(data, indent=2)
    # Simple colorization
    formatted = formatted.replace('"error"', f'{Colors.RED}"error"{Colors.ENDC}')
    formatted = formatted.replace('"critical"', f'{Colors.RED}"critical"{Colors.ENDC}')
    formatted = formatted.replace('"warning"', f'{Colors.YELLOW}"warning"{Colors.ENDC}')
    formatted = formatted.replace('"Healthy"', f'{Colors.GREEN}"Healthy"{Colors.ENDC}')
    formatted = formatted.replace('"Running"', f'{Colors.GREEN}"Running"{Colors.ENDC}')
    formatted = formatted.replace('"Ready"', f'{Colors.GREEN}"Ready"{Colors.ENDC}')
    formatted = formatted.replace('"Failed"', f'{Colors.RED}"Failed"{Colors.ENDC}')
    formatted = formatted.replace('"Pending"', f'{Colors.YELLOW}"Pending"{Colors.ENDC}')
    print(formatted)


async def main():
    print_header("Kubernetes MCP Server - Interactive Demo")
    
    # Import the MCP server module
    print_info("Loading MCP server module...")
    
    try:
        from mcp_server import (
            init_kubernetes,
            get_cluster_info,
            list_namespaces,
            list_pods,
            list_deployments,
            list_services,
            get_node_status,
            diagnose_cluster,
            get_resource_usage,
            describe_pod,
            get_pod_logs
        )
    except ImportError as e:
        print_error(f"Could not import mcp_server: {e}")
        print_info("Make sure you're in the k8s-mcp-server directory")
        sys.exit(1)
    
    # Initialize Kubernetes connection
    print_info("Connecting to Kubernetes cluster...")
    if init_kubernetes():
        print_success("Connected to Kubernetes cluster!")
    else:
        print_error("Could not connect to Kubernetes cluster")
        print_info("Make sure minikube/kind is running or kubectl is configured")
        sys.exit(1)
    
    # Menu
    tools = {
        "1": ("Get Cluster Info", get_cluster_info, {}),
        "2": ("List Namespaces", list_namespaces, {}),
        "3": ("List Pods (default namespace)", list_pods, {"namespace": "default"}),
        "4": ("List Pods (all namespaces)", list_pods, {"namespace": "all"}),
        "5": ("List Deployments (all)", list_deployments, {"namespace": "all"}),
        "6": ("List Services (all)", list_services, {"namespace": "all"}),
        "7": ("Get Node Status", get_node_status, {}),
        "8": ("🔍 DIAGNOSE CLUSTER (AI Feature)", diagnose_cluster, {}),
        "9": ("Get Resource Usage (all)", get_resource_usage, {"namespace": "all"}),
        "10": ("Describe Pod (enter name)", "describe_pod", {}),
        "11": ("Get Pod Logs (enter name)", "get_pod_logs", {}),
        "q": ("Quit", None, {})
    }
    
    while True:
        print_header("Available Tools")
        print("Available operational tools:\n")
        
        for key, (name, _, _) in tools.items():
            if key == "8":
                print(f"  {Colors.BOLD}{key}. {name}{Colors.ENDC}")  # Highlight diagnose
            else:
                print(f"  {key}. {name}")
        
        print()
        choice = input(f"{Colors.CYAN}Select tool (or 'q' to quit): {Colors.ENDC}").strip()
        
        if choice == 'q':
            print_info("Goodbye!")
            break
        
        if choice not in tools:
            print_warning("Invalid choice")
            continue
        
        name, func, kwargs = tools[choice]
        
        # Handle special cases that need input
        if func == "describe_pod":
            pod_name = input("Enter pod name: ").strip()
            namespace = input("Enter namespace (default: default): ").strip() or "default"
            func = describe_pod
            kwargs = {"pod_name": pod_name, "namespace": namespace}
        elif func == "get_pod_logs":
            pod_name = input("Enter pod name: ").strip()
            namespace = input("Enter namespace (default: default): ").strip() or "default"
            func = get_pod_logs
            kwargs = {"pod_name": pod_name, "namespace": namespace, "lines": 20}
        
        if func is None:
            continue
        
        print_header(f"Running: {name}")
        
        try:
            result = await func(**kwargs)
            print_json(result)
        except Exception as e:
            print_error(f"Error: {e}")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")


if __name__ == "__main__":
    asyncio.run(main())
