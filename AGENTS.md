# Notes for AI coding agents

This file is for an AI assistant (Claude Code, Codex, Cursor and similar) helping someone install or change mac-thermal-alert. People should read [README.md](README.md) instead.

## What this repo does

`install.sh` sets up a per-user LaunchAgent that runs `thermal-alert.py` every 60 seconds. The script reads CPU and GPU temperature from macmon and battery temperature from `ioreg`, then shows a notification and a dialog when a limit is crossed. Nothing runs as root and nothing is sent over the network.

## Before you install

1. Confirm the Mac is Apple Silicon: `uname -m` must print `arm64`. On an Intel Mac, stop and tell the person this tool does not support it, because macmon reads Apple Silicon sensors only.
2. Confirm Homebrew is present: `command -v brew`. If it is missing, ask the person before installing Homebrew. Its installer needs their password and changes system folders.
3. Tell the person what the installer will add, and get their agreement:
   - macmon (command-line monitor, required) and Stats (menu-bar app, optional extra), both through Homebrew
   - `~/.local/bin/thermal-alert.py`
   - `~/Library/LaunchAgents/local.thermal-alert.plist`, a background job that runs every minute and starts again after each login

## Install

```bash
./install.sh
```

Never run it with `sudo`. The LaunchAgent must belong to the logged-in user, and a root install will not show alerts.

## Check that it works

These checks need no human:

```bash
launchctl print gui/$(id -u)/local.thermal-alert | grep -E "runs|last exit"   # expect last exit code = 0
tail -3 ~/Library/Logs/thermal-alert.log                                    # one line per minute with cpu=, gpu=, batt=
```

A log line that starts with `ERROR` means the check failed. The usual cause is macmon missing from `/opt/homebrew/bin` and `/usr/local/bin`.

The visual test needs the person, because you cannot see their screen:

```bash
/usr/bin/python3 ~/.local/bin/thermal-alert.py --test
```

Warn them first that four dialogs and four banners are about to appear and that each dialog needs an OK click. Then ask whether they saw them. The test does not change the alert state, so you can run it again.

If they saw the dialogs but no banners, macOS is blocking notifications from Script Editor. Ask them to open System Settings, then Notifications, then Script Editor, and turn on Allow Notifications.

## Changing the limits

The limits are constants at the top of `thermal-alert.py` (`CHIP_WARN`, `CHIP_CRIT`, `BATT_WARN`, `BATT_CRIT`, `SUSTAIN`, `COOLDOWN`). Edit them in the repo copy and run `./install.sh` again, which replaces the installed copy. Do not edit `~/.local/bin/thermal-alert.py` directly, because the next install overwrites it.

Ask before raising a limit. The defaults sit just below the point where Apple Silicon throttles (about 105°C for the chip) and where battery wear speeds up (about 40 to 45°C).

To make an alert fire on purpose without editing anything, lower a limit for one run through environment variables:

```bash
CHIP_CRIT=20 COOLDOWN=0 /usr/bin/python3 ~/.local/bin/thermal-alert.py
```

That run writes to the real state file and resets the 15-minute cooldown for that alert, so prefer `--test` unless you need the full code path.

## Uninstall

```bash
./uninstall.sh
```

This removes the LaunchAgent, the installed script and the state file. macmon, Stats and the log stay. Remove the apps only if the person asks: `brew uninstall macmon` and `brew uninstall --cask stats`.

## Files

| Path | What it is |
|---|---|
| `thermal-alert.py` | The check. Standard library only, runs on the system `/usr/bin/python3` |
| `install.sh`, `uninstall.sh` | Set up and remove the LaunchAgent and apps |
| `~/Library/Logs/thermal-alert.log` | One line per check, plus errors |
| `~/Library/Application Support/thermal-alert.json` | Cooldown and consecutive-reading state |
