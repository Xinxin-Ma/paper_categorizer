#!/bin/bash
# Record all demo GIFs for Paper Categorizer
# Requires: asciinema, agg, pv

set -e

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DEMO_DIR"

echo "Recording Paper Categorizer Demo GIFs..."
echo ""

# Check dependencies
for cmd in asciinema agg pv; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Record Demo 1: Init
echo "[1/4] Recording Init Demo..."
asciinema rec -c "./demo_init.sh" --overwrite demo_init.cast
agg --cols 80 --rows 24 --speed 1.0 demo_init.cast demo_init.gif
echo "      Created: demo_init.gif"
echo ""

# Record Demo 2: Interactive
echo "[2/4] Recording Interactive Demo..."
asciinema rec -c "./demo_interactive.sh" --overwrite demo_interactive.cast
agg --cols 80 --rows 30 --speed 1.0 demo_interactive.cast demo_interactive.gif
echo "      Created: demo_interactive.gif"
echo ""

# Record Demo 3: Batch
echo "[3/4] Recording Batch Demo..."
asciinema rec -c "./demo_batch.sh" --overwrite demo_batch.cast
agg --cols 80 --rows 30 --speed 1.0 demo_batch.cast demo_batch.gif
echo "      Created: demo_batch.gif"
echo ""

# Record Demo 4: Zotero
echo "[4/4] Recording Zotero Demo..."
asciinema rec -c "./demo_zotero.sh" --overwrite demo_zotero.cast
agg --cols 80 --rows 30 --speed 1.0 demo_zotero.cast demo_zotero.gif
echo "      Created: demo_zotero.gif"
echo ""

echo "============================================"
echo "All demos recorded successfully!"
echo ""
echo "Generated files:"
ls -la *.gif
echo "============================================"
