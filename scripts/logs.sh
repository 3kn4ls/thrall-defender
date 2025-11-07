#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Thrall Defender - Logs${NC}"
echo "======================"
echo ""
echo "Choose which logs to view:"
echo "  1) Backend logs"
echo "  2) Frontend logs"
echo "  3) Both (split screen)"
echo "  4) All pods in namespace"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Viewing Backend logs (Ctrl+C to exit)...${NC}\n"
        kubectl logs -n thrall-defender -l app=thrall-backend -f
        ;;
    2)
        echo -e "\n${YELLOW}Viewing Frontend logs (Ctrl+C to exit)...${NC}\n"
        kubectl logs -n thrall-defender -l app=thrall-frontend -f
        ;;
    3)
        echo -e "\n${YELLOW}Opening split view (requires tmux)...${NC}\n"
        if ! command -v tmux &> /dev/null; then
            echo "tmux is not installed. Install it with: sudo apt install tmux"
            exit 1
        fi
        tmux new-session -d -s thrall-logs
        tmux split-window -v
        tmux select-pane -t 0
        tmux send-keys 'kubectl logs -n thrall-defender -l app=thrall-backend -f' C-m
        tmux select-pane -t 1
        tmux send-keys 'kubectl logs -n thrall-defender -l app=thrall-frontend -f' C-m
        tmux attach-session -t thrall-logs
        ;;
    4)
        echo -e "\n${YELLOW}All pods in thrall-defender namespace:${NC}\n"
        kubectl get pods -n thrall-defender
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
