#!/bin/bash
set -e

echo "🗑️  Thrall Defender - Uninstall Script"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This will delete all Thrall Defender resources from your cluster.${NC}"
read -p "Are you sure? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo -e "${RED}[1/3] Deleting deployments and services...${NC}"
kubectl delete deployment thrall-backend -n thrall-defender --ignore-not-found
kubectl delete deployment thrall-frontend -n thrall-defender --ignore-not-found
kubectl delete service thrall-backend -n thrall-defender --ignore-not-found
kubectl delete service thrall-frontend -n thrall-defender --ignore-not-found

echo -e "${RED}[2/3] Deleting persistent data...${NC}"
kubectl delete pvc thrall-backend-data -n thrall-defender --ignore-not-found
kubectl delete configmap thrall-backend-config -n thrall-defender --ignore-not-found

echo -e "${RED}[3/3] Deleting namespace...${NC}"
kubectl delete namespace thrall-defender --ignore-not-found

echo -e "\n${GREEN}✅ Uninstall completed!${NC}"
echo -e "${YELLOW}Note: Docker images are still available locally.${NC}"
echo "To remove them, run:"
echo "  docker rmi thrall-backend:latest thrall-frontend:latest"
