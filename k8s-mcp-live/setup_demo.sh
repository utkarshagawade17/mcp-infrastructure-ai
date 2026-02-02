#!/bin/bash
# =============================================================================
# Setup Demo Environment
# Creates sample workloads in your K8s cluster for the MCP server demo
# =============================================================================

set -e

echo "=============================================="
echo "Setting up Kubernetes Demo Environment"
echo "=============================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if cluster is reachable
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster."
    echo "   Start minikube: minikube start"
    echo "   Or kind: kind create cluster"
    exit 1
fi

echo "✓ Connected to Kubernetes cluster"
echo ""

# Create namespaces
echo "Creating namespaces..."
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace staging --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
echo "✓ Namespaces created"

# Deploy healthy workloads
echo ""
echo "Deploying healthy workloads..."

# Nginx in production
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
  namespace: production
  labels:
    app: web-frontend
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: web-frontend
  namespace: production
spec:
  selector:
    app: web-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF
echo "✓ web-frontend deployed in production"

# Redis in production
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache-redis
  namespace: production
  labels:
    app: cache-redis
    tier: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cache-redis
  template:
    metadata:
      labels:
        app: cache-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
EOF
echo "✓ cache-redis deployed in production"

# API service in staging
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: staging
  labels:
    app: api-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api
        image: hashicorp/http-echo:0.2.3
        args:
          - "-text=Hello from API"
        ports:
        - containerPort: 5678
        resources:
          requests:
            cpu: "50m"
            memory: "32Mi"
          limits:
            cpu: "100m"
            memory: "64Mi"
EOF
echo "✓ api-server deployed in staging"

# Deploy PROBLEMATIC workloads (for diagnosis demo)
echo ""
echo "Deploying problematic workloads (for diagnosis demo)..."

# Deployment with non-existent image (will be in ImagePullBackOff)
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-service
  namespace: staging
  labels:
    app: broken-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: broken-service
  template:
    metadata:
      labels:
        app: broken-service
    spec:
      containers:
      - name: app
        image: nonexistent-registry.io/fake-image:v1.0.0
        ports:
        - containerPort: 8080
EOF
echo "✓ broken-service deployed (intentionally failing)"

# Deployment without resource limits (for resource analysis demo)
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: no-limits-app
  namespace: staging
  labels:
    app: no-limits-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: no-limits-app
  template:
    metadata:
      labels:
        app: no-limits-app
    spec:
      containers:
      - name: busybox
        image: busybox
        command: ["sleep", "3600"]
        # Intentionally NO resource limits
EOF
echo "✓ no-limits-app deployed (no resource limits)"

# Monitoring namespace with prometheus-like deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-collector
  namespace: monitoring
  labels:
    app: metrics-collector
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-collector
  template:
    metadata:
      labels:
        app: metrics-collector
    spec:
      containers:
      - name: collector
        image: prom/prometheus:v2.45.0
        ports:
        - containerPort: 9090
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
EOF
echo "✓ metrics-collector deployed in monitoring"

# Wait for pods to start
echo ""
echo "Waiting for pods to start (30 seconds)..."
sleep 30

# Show summary
echo ""
echo "=============================================="
echo "Demo Environment Ready!"
echo "=============================================="
echo ""
echo "Namespaces:"
kubectl get namespaces | grep -E "production|staging|monitoring"
echo ""
echo "All Pods:"
kubectl get pods -A | grep -E "production|staging|monitoring|NAMESPACE"
echo ""
echo "What to expect in the demo:"
echo "  ✓ Healthy pods in production namespace"
echo "  ✓ Mixed health in staging (one broken deployment)"
echo "  ✓ Monitoring namespace with metrics collector"
echo "  ⚠ broken-service will show ImagePullBackOff"
echo "  ⚠ no-limits-app has no resource limits"
echo ""
echo "Run the demo:"
echo "  python demo_cli.py"
echo ""
