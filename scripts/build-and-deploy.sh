#!/bin/bash
set -e

echo "🚀 Thrall Defender - Build and Deploy Script"
echo "============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! uname -a | grep -q "aarch64"; then
    echo -e "${YELLOW}Warning: This script is optimized for Raspberry Pi (ARM64)${NC}"
fi

# Build Backend
echo -e "\n${GREEN}[1/6] Building Backend Docker Image...${NC}"
cd backend
docker build -t thrall-backend:latest .
cd ..

# Build Frontend
echo -e "\n${GREEN}[2/6] Building Frontend Docker Image...${NC}"
echo -e "${YELLOW}This may take 10-15 minutes on Raspberry Pi...${NC}"
cd frontend
docker build -t thrall-frontend:latest .
cd ..

# Import to k3s
echo -e "\n${GREEN}[3/6] Importing images to k3s...${NC}"
docker save thrall-backend:latest | sudo k3s ctr images import -
docker save thrall-frontend:latest | sudo k3s ctr images import -

# Apply Kubernetes manifests
echo -e "\n${GREEN}[4/6] Applying Kubernetes manifests...${NC}"

# Namespace
kubectl apply -f k8s/namespace.yaml

# Backend
kubectl apply -f k8s/backend/configmap.yaml
kubectl apply -f k8s/backend/pvc.yaml
kubectl apply -f k8s/backend/deployment.yaml
kubectl apply -f k8s/backend/service.yaml

# Frontend
kubectl apply -f k8s/frontend/deployment.yaml
kubectl apply -f k8s/frontend/service.yaml

# Wait for deployments
echo -e "\n${GREEN}[5/6] Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/thrall-backend -n thrall-defender
kubectl wait --for=condition=available --timeout=300s deployment/thrall-frontend -n thrall-defender

# Show status
echo -e "\n${GREEN}[6/6] Deployment Status:${NC}"
kubectl get all -n thrall-defender

echo -e "\n${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "\n${YELLOW}To access the application:${NC}"
echo "  1. Get the LoadBalancer IP:"
echo "     kubectl get svc -n thrall-defender thrall-frontend"
echo ""
echo "  2. Or use port-forward:"
echo "     kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0"
echo ""
echo "  3. View logs:"
echo "     kubectl logs -n thrall-defender -l app=thrall-backend -f"
