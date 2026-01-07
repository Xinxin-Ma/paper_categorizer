#!/bin/bash
# Demo script for Paper Categorizer - Interactive Mode
# This demonstrates entering a paper title and getting a category

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

type_input() {
    echo "$1" | pv -qL 20
}

print_slow() {
    echo "$1" | pv -qL 300
}

clear
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}       ${WHITE}Paper Categorizer - Interactive Mode${NC}                   ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
sleep 1

echo -e "${BLUE}Interactive mode lets you categorize papers one by one.${NC}"
echo -e "${BLUE}Just enter a paper title and get the category instantly.${NC}"
echo ""
sleep 1

type_cmd "./paper_categorizer/run.sh --interactive"
sleep 0.5

echo ""
print_slow "============================================================"
echo ""
print_slow "Paper Categorization - Interactive Mode (using gemini)"
echo ""
print_slow "============================================================"
echo ""
print_slow "Enter a paper title to get its category."
echo ""
print_slow "Type 'quit' to exit."
echo ""
sleep 0.5

# Example 1: Attention Is All You Need
echo "----------------------------------------"
echo -ne "Paper Title: "
sleep 0.3
type_input "Attention Is All You Need"
echo ""
sleep 0.3

echo -ne "Abstract (optional, press Enter to skip): "
sleep 0.3
echo ""
sleep 0.3

print_slow "Categorizing..."
echo ""
sleep 0.8

echo ""
echo "=================================================="
echo -e "Category: ${GREEN}1.1 Architectures & Models${NC}"
echo "Folder:   1. Deep Learning/1.1 Architectures & Models"
echo "Confidence: high"
echo -e "Reasoning: ${GRAY}Seminal transformer architecture paper introducing${NC}"
echo -e "           ${GRAY}self-attention mechanism for sequence modeling${NC}"
echo "=================================================="
echo ""
sleep 1.5

# Example 2: GPT-4 Technical Report
echo "----------------------------------------"
echo -ne "Paper Title: "
sleep 0.3
type_input "GPT-4 Technical Report"
echo ""
sleep 0.3

echo -ne "Abstract (optional, press Enter to skip): "
sleep 0.3
echo ""
sleep 0.3

print_slow "Categorizing..."
echo ""
sleep 0.8

echo ""
echo "=================================================="
echo -e "Category: ${GREEN}3.1 Model Architecture${NC}"
echo "Folder:   3. Large Language Models/3.1 Model Architecture"
echo "Confidence: high"
echo -e "Reasoning: ${GRAY}Technical report on GPT-4 large language model${NC}"
echo "=================================================="
echo ""
sleep 1.5

# Example 3: AgentBench
echo "----------------------------------------"
echo -ne "Paper Title: "
sleep 0.3
type_input "AgentBench: Evaluating LLMs as Agents"
echo ""
sleep 0.3

echo -ne "Abstract (optional, press Enter to skip): "
sleep 0.3
echo ""
sleep 0.3

print_slow "Categorizing..."
echo ""
sleep 0.8

echo ""
echo "=================================================="
echo -e "Category: ${GREEN}4.2 Agent Benchmarks${NC}"
echo "Folder:   4. AI Agents/4.2 Agent Benchmarks"
echo "Confidence: high"
echo -e "Reasoning: ${GRAY}Benchmark paper for evaluating LLM-based agents${NC}"
echo "=================================================="
echo ""
sleep 1.5

# Example 4: Random Forest
echo "----------------------------------------"
echo -ne "Paper Title: "
sleep 0.3
type_input "Random Forests"
echo ""
sleep 0.3

echo -ne "Abstract (optional, press Enter to skip): "
sleep 0.3
echo ""
sleep 0.3

print_slow "Categorizing..."
echo ""
sleep 0.8

echo ""
echo "=================================================="
echo -e "Category: ${GREEN}2.3 Ensemble Methods${NC}"
echo "Folder:   2. Traditional Machine Learning/2.3 Ensemble Methods"
echo "Confidence: high"
echo -e "Reasoning: ${GRAY}Classic ensemble learning method paper${NC}"
echo "=================================================="
echo ""
sleep 1.5

# Quit
echo "----------------------------------------"
echo -ne "Paper Title: "
sleep 0.3
type_input "quit"
echo ""
sleep 0.3
print_slow "Goodbye!"
echo ""
sleep 1

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Interactive mode is great for quick categorization!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
sleep 2
