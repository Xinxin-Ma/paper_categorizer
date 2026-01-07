#!/bin/bash
# Demo script for Paper Categorizer - Batch Mode
# This demonstrates batch processing papers in the Inbox folder

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
echo -e "${GREEN}║${NC}       ${WHITE}Paper Categorizer - Batch Mode${NC}                          ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
sleep 1

echo -e "${BLUE}Batch mode processes all PDFs in your Inbox folder automatically.${NC}"
echo -e "${BLUE}Papers are moved to category folders after categorization.${NC}"
echo ""
sleep 1

# Show Inbox contents
type_cmd "ls Inbox/"
sleep 0.3
echo "AgentBench-Evaluating-LLMs-as-Agents.pdf"
echo "ToolLLM-Facilitating-LLMs-to-Master-Tools.pdf"
echo "WebArena-A-Realistic-Web-Environment-for-Agents.pdf"
echo ""
sleep 1

echo -e "${BLUE}Let's process these papers (with Zotero disabled)...${NC}"
echo ""
sleep 0.5

type_cmd "./paper_categorizer/run.sh --batch"
sleep 0.5

echo ""
print_slow "============================================================"
echo ""
print_slow "Batch Processing - Inbox Papers (using gemini)"
echo ""
print_slow "============================================================"
echo ""
echo -e "Zotero integration: ${YELLOW}DISABLED${NC}"
echo ""
sleep 0.3

print_slow "Found 3 PDF files to process."
echo ""
sleep 0.5

echo ""
echo "----------------------------------------"
print_slow "Step 1: Checking and renaming papers by title"
echo ""
echo "----------------------------------------"
sleep 0.3

echo "[1/3] AgentBench-Evaluating-LLMs-as-Agents.pdf..."
sleep 0.2
echo -e "  ${GREEN}OK${NC} Filename already matches title"
sleep 0.3

echo "[2/3] ToolLLM-Facilitating-LLMs-to-Master-Tools.pdf..."
sleep 0.2
echo -e "  ${GREEN}OK${NC} Filename already matches title"
sleep 0.3

echo "[3/3] WebArena-A-Realistic-Web-Environment-for-Agents.pdf..."
sleep 0.2
echo -e "  ${GREEN}OK${NC} Filename already matches title"
sleep 0.3

echo ""
print_slow "Renamed: 0, Kept original: 3"
echo ""
sleep 0.5

echo ""
echo "----------------------------------------"
print_slow "Step 2: Categorizing papers"
echo ""
echo "----------------------------------------"
sleep 0.3

# Paper 1
echo "[1/3] AgentBench-Evaluating-LLMs-as-Agents.pdf..."
sleep 0.5
echo -e "  -> ${GREEN}4.2 Agent Benchmarks${NC} (high)"
sleep 0.2
echo "  Moved to: 4. AI Agents/4.2 Agent Benchmarks"
sleep 0.5

# Paper 2
echo "[2/3] ToolLLM-Facilitating-LLMs-to-Master-Tools.pdf..."
sleep 0.5
echo -e "  -> ${GREEN}4.1 Agent Frameworks${NC} (high)"
sleep 0.2
echo "  Moved to: 4. AI Agents/4.1 Agent Frameworks"
sleep 0.5

# Paper 3
echo "[3/3] WebArena-A-Realistic-Web-Environment-for-Agents.pdf..."
sleep 0.5
echo -e "  -> ${GREEN}4.2 Agent Benchmarks${NC} (high)"
sleep 0.2
echo "  Moved to: 4. AI Agents/4.2 Agent Benchmarks"
sleep 0.5

# Summary
echo ""
echo "----------------------------------------"
echo -e "Processed: ${WHITE}3${NC} papers"
echo -e "Successful: ${GREEN}3${NC}"
echo -e "Failed: ${GREEN}0${NC}"
sleep 0.5

echo ""
print_slow "Summary saved to: Papers_Summary.md"
echo ""
sleep 1

# Show final structure
echo ""
echo -e "${BLUE}Let's see the organized folder structure:${NC}"
echo ""
sleep 0.5

type_cmd "ls -la 'Papers Auto Category/4. AI Agents/'"
sleep 0.3
echo "drwxr-xr-x  4 user  staff  128 Jan  6 12:00 4.1 Agent Frameworks"
echo "drwxr-xr-x  5 user  staff  160 Jan  6 12:00 4.2 Agent Benchmarks"
echo ""
sleep 1

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  All papers categorized and organized automatically!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
sleep 2
