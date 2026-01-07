#!/bin/bash
# Demo script for Paper Categorizer - Init Mode
# This demonstrates the first-time initialization process

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Typing simulation
type_cmd() {
    echo -ne "${CYAN}$ ${NC}"
    echo "$1" | pv -qL 25
    sleep 0.3
}

print_slow() {
    echo "$1" | pv -qL 200
}

clear
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${WHITE}Paper Categorizer - First Time Setup${NC}                   ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
sleep 1

echo -e "${BLUE}First, let's initialize the paper categorization system...${NC}"
echo ""
sleep 1

type_cmd "cd ~/Documents/Papers"
sleep 0.5

type_cmd "./paper_categorizer/run.sh --init"
sleep 0.5

echo ""
print_slow "============================================================"
echo ""
print_slow "Paper Categorization System - Setup"
echo ""
print_slow "============================================================"
echo ""
sleep 0.3

echo -e "${GREEN}[OK]${NC} Created Inbox folder: ~/Documents/Papers/Inbox"
print_slow "     Place your PDFs here, then run: ./paper_categorizer/run.sh --batch"
echo ""
sleep 0.5

echo ""
print_slow "Creating categories.json template..."
echo ""
sleep 0.3

echo -e "${GREEN}Created:${NC} ~/Documents/Papers/paper_categorizer/categories.json"
echo ""
sleep 0.5

echo "------------------------------------------------------------"
echo -e "${YELLOW}IMPORTANT: Edit categories.json to define your categories!${NC}"
echo "------------------------------------------------------------"
echo ""
sleep 0.5

print_slow "The template includes example categories. You should:"
echo ""
print_slow "  1. Open categories.json in a text editor"
echo ""
print_slow "  2. Replace example categories with your own"
echo ""
print_slow "  3. Add as many categories and subcategories as needed"
echo ""
print_slow "  4. Run --init again to create the folder structure"
echo ""
sleep 1

echo ""
echo -e "${BLUE}Category format example:${NC}"
echo ""
cat << 'EOF'
  {
    "1": {
      "name": "1. Deep Learning",
      "description": "Neural networks and deep learning",
      "keywords": ["neural network", "transformer"],
      "subcategories": {
        "1.1": "1.1 Architectures & Models"
      }
    }
  }
EOF
echo ""
sleep 1

echo ""
print_slow "After editing, run:"
echo ""
echo -e "  ${CYAN}./paper_categorizer/run.sh --init${NC}"
echo ""
print_slow "To see your categories:"
echo ""
echo -e "  ${CYAN}./paper_categorizer/run.sh --list-categories${NC}"
echo ""
sleep 1

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Setup Complete! Your Inbox folder is ready.${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
sleep 2
