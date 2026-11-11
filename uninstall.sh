#!/bin/bash
# Stops the thermal alert and removes what install.sh added. Leaves macmon installed.
LABEL="local.thermal-alert"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist" "$HOME/.local/bin/thermal-alert.py" \
      "$HOME/Library/Application Support/thermal-alert.json"
echo "Removed. The log at ~/Library/Logs/thermal-alert.log is kept; delete it if you like."
