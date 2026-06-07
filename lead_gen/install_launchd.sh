#!/bin/bash
# Installs the LinkedIn 10 AM daily job via launchd.
# Run once: bash install_launchd.sh

PLIST_SRC="$(dirname "$0")/com.leadgen.linkedin.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.leadgen.linkedin.plist"
LOG_DIR="$HOME/Desktop/lead_generation_runs"

mkdir -p "$LOG_DIR"
cp "$PLIST_SRC" "$PLIST_DST"
launchctl load "$PLIST_DST"

echo "✓ LinkedIn scraper scheduled for 10:00 AM daily."
echo "  Logs → $LOG_DIR/linkedin_run.log"
echo ""
echo "To uninstall:  launchctl unload $PLIST_DST && rm $PLIST_DST"
echo "To run now:    python3 $(dirname "$0")/main_linkedin.py"
