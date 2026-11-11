# mac-thermal-alert

A small background check for Apple Silicon Macs. Once a minute it reads the CPU, GPU and battery temperatures, and it warns you when they reach a level that can hurt the machine. A warning is a notification with a sound plus a dialog that stays on screen until you click OK.

It needs no admin password and no app running in the menu bar. Temperatures come from [macmon](https://github.com/vladkens/macmon), which reads the chip's sensors without sudo. The battery temperature comes from `ioreg`.

## When it warns you

| Alert | Trigger | Why |
|---|---|---|
| Laptop running hot | CPU or GPU at 95°C or higher for 2 checks in a row | Sustained heavy heat, not a short spike |
| 🔥 Laptop overheating | CPU or GPU at 105°C or higher, or macOS limiting CPU speed | The chip is throttling to protect itself |
| Battery warm | Battery at 40°C or higher | Heat wears a lithium battery out faster |
| 🔥 Battery too hot | Battery at 45°C or higher | Unplug the charger and let it cool |

Each alert repeats at most once every 15 minutes. Apple Silicon throttles and, as a last resort, shuts down before the chip itself is damaged, so the battery limits matter as much as the chip limits. For reference, these chips usually run at 40 to 60°C under light use and 80 to 100°C under heavy load.

## Install

Requirements: an Apple Silicon Mac (M1 or later), the Xcode command line tools (`xcode-select --install`) and [Homebrew](https://brew.sh).

```bash
git clone https://github.com/masterA88/mac-thermal-alert.git
cd mac-thermal-alert
./install.sh
```

The installer sets up two free, open-source apps with Homebrew, skipping any that is already installed:

- [macmon](https://github.com/vladkens/macmon), a command-line monitor that reads the chip's temperature sensors without sudo. The alert depends on it. Run `macmon` in Terminal for a live dashboard.
- [Stats](https://github.com/exelban/stats), a menu-bar app that shows the temperature live. The alert does not need it, so it is there for you to glance at. To show the temperature in the menu bar, click the Stats icon, open Settings, then Sensors, and turn on CPU temperature.

It then copies the script to `~/.local/bin/thermal-alert.py`, and registers a LaunchAgent (`local.thermal-alert`) that runs every 60 seconds and starts again after each login.

Then check that alerts reach your screen:

```bash
/usr/bin/python3 ~/.local/bin/thermal-alert.py --test
```

You should see four notifications and four dialogs showing your current readings. If no banner appears, open System Settings, then Notifications, then Script Editor, and turn on Allow Notifications. Setting the style to Persistent keeps banners on screen as well.

## Change the limits

The limits are at the top of `thermal-alert.py`. Edit them in your clone and run `./install.sh` again. Each limit can also be set with an environment variable of the same name (`CHIP_WARN`, `CHIP_CRIT`, `BATT_WARN`, `BATT_CRIT`, `SUSTAIN`, `COOLDOWN`).

## Check that it is running

```bash
tail ~/Library/Logs/thermal-alert.log
```

Every check writes one line with the readings and any alert sent:

```
2026-11-11 20:30:20 cpu=59.7 gpu=60.2 batt=31.1 throttled=False hot=0 sent=-
```

Errors go to the same log, so a broken check does not fail silently.

## Limits of the approach

- It runs inside your user session, so it starts when you log in and does not run at the login screen.
- It pauses while the Mac sleeps. If the Mac stays awake in a closed bag, the check still runs and the sound plays, but you will see the dialog only when you open the lid.
- It stops working if macmon is uninstalled.

## Uninstall

```bash
./uninstall.sh
```

This removes the LaunchAgent, the script and its state file. macmon, Stats and the log stay. To remove the two apps as well, run `brew uninstall macmon` and `brew uninstall --cask stats`.

## License

MIT. See [LICENSE](LICENSE).

## Author

Hilmi, https://master-hilmi.vercel.app/
