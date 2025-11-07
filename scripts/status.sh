#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Thrall Defender - Status Report     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if namespace exists
if ! kubectl get namespace thrall-defender &> /dev/null; then
    echo -e "${RED}❌ Thrall Defender is not deployed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Thrall Defender namespace exists${NC}"
echo ""

# Pods status
echo -e "${YELLOW}📦 Pods:${NC}"
kubectl get pods -n thrall-defender -o wide

echo ""

# Services
echo -e "${YELLOW}🌐 Services:${NC}"
kubectl get svc -n thrall-defender

echo ""

# PVCs
echo -e "${YELLOW}💾 Persistent Volumes:${NC}"
kubectl get pvc -n thrall-defender

echo ""

# Resource usage (if metrics-server is installed)
if kubectl top nodes &> /dev/null; then
    echo -e "${YELLOW}📊 Resource Usage:${NC}"
    kubectl top pods -n thrall-defender
    echo ""
fi

# Get backend pod name
BACKEND_POD=$(kubectl get pod -n thrall-defender -l app=thrall-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ ! -z "$BACKEND_POD" ]; then
    echo -e "${YELLOW}🔍 Backend Health Check:${NC}"
    kubectl exec -n thrall-defender $BACKEND_POD -- wget -q -O- http://localhost:8000/ || echo "Backend not responding"
    echo ""
fi

# Get frontend service external IP
FRONTEND_IP=$(kubectl get svc -n thrall-defender thrall-frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)

if [ ! -z "$FRONTEND_IP" ]; then
    echo -e "${GREEN}🌍 Frontend accessible at: http://$FRONTEND_IP${NC}"
else
    echo -e "${YELLOW}ℹ️  Frontend LoadBalancer IP pending. Use port-forward:${NC}"
    echo "   kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0"
fi

echo ""

# Recent events
echo -e "${YELLOW}📋 Recent Events:${NC}"
kubectl get events -n thrall-defender --sort-by='.lastTimestamp' | tail -n 5

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
