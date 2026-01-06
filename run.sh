#!/bin/bash
# Wrapper script to run paper_categorizer with venv
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/venv/bin/activate"
cd "$(dirname "$DIR")"
python -m paper_categorizer "$@"
