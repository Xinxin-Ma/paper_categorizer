#!/bin/bash
# Demo script for Paper Categorizer - Zotero Integration
# This demonstrates enabling Zotero and checking status

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'

# Typing simulation
type_cmd() {
    echo -ne "${CYAN}$ ${NC}"
    echo "$1" | pv -qL 25
    sleep 0.3
}

print_slow() {
    echo "$1" | pv -qL 300
}

clear
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${WHITE}Paper Categorizer - Zotero Integration${NC}                  ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
sleep 1

echo -e "${BLUE}Zotero integration is ${YELLOW}OFF by default${BLUE}.${NC}"
echo -e "${BLUE}Let's see how to enable it and check the status.${NC}"
echo ""
sleep 1.5

# Step 1: Show current .env config
echo -e "${WHITE}Step 1: Configure .env to enable Zotero${NC}"
echo ""
sleep 0.5

type_cmd "cat .env | grep ZOTERO"
sleep 0.3
echo -e "${GRAY}# Zotero Integration (OFF by default)${NC}"
echo "ZOTERO_ENABLED=true"
echo "ZOTERO_DB_PATH=~/Zotero/zotero.sqlite"
echo "ZOTERO_STORAGE_PATH=~/Zotero/storage"
echo ""
sleep 1.5

# Step 2: Check Zotero status
echo -e "${WHITE}Step 2: Check Zotero status${NC}"
echo ""
sleep 0.5

type_cmd "./paper_categorizer/run.sh --zotero-status"
sleep 0.5

echo ""
print_slow "=================================================="
echo ""
print_slow "Zotero Integration Status"
echo ""
print_slow "=================================================="
echo ""
sleep 0.3

echo -e "Enabled: ${GREEN}Yes${NC}"
sleep 0.2
echo "Database path: ~/Zotero/zotero.sqlite"
sleep 0.2
echo -e "Database exists: ${GREEN}Yes${NC}"
sleep 0.2
echo "Storage path: ~/Zotero/storage"
sleep 0.2
echo -e "Storage exists: ${GREEN}Yes${NC}"
sleep 0.2
echo "Papers in Zotero: 156"
sleep 0.2
echo "Collections: 24"
sleep 0.3
print_slow "=================================================="
echo ""
sleep 1.5

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Zotero integration ready!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
sleep 2
