#!/bin/bash
# Installs the thermal alert as a per-user LaunchAgent that runs every minute.
set -euo pipefail

LABEL="local.thermal-alert"
BIN="$HOME/.local/bin/thermal-alert.py"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
HERE="$(cd "$(dirname "$0")" && pwd)"

[[ "$(uname -m)" == "arm64" ]] || { echo "This needs an Apple Silicon Mac (M1 or later)."; exit 1; }
[[ -x /usr/bin/python3 ]] && /usr/bin/python3 -c 'pass' 2>/dev/null \
  || { echo "python3 is missing. Run: xcode-select --install"; exit 1; }

if ! command -v macmon >/dev/null && [[ ! -x /opt/homebrew/bin/macmon && ! -x /usr/local/bin/macmon ]]; then
  if command -v brew >/dev/null; then
    echo "Installing macmon with Homebrew..."
    brew install macmon
  else
    echo "macmon is missing. Install Homebrew (https://brew.sh) and run: brew install macmon"
    exit 1
  fi
fi

mkdir -p "$HOME/.local/bin" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
install -m 755 "$HERE/thermal-alert.py" "$BIN"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>$BIN</string>
  </array>
  <key>StartInterval</key><integer>60</integer>
  <key>RunAtLoad</key><true/>
  <key>LowPriorityIO</key><true/>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/thermal-alert.err</string>
</dict></plist>
PLIST

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "Installed. It checks every minute and starts again after each login."
echo "Run a test:  /usr/bin/python3 $BIN --test"
echo "Log:         ~/Library/Logs/thermal-alert.log"
