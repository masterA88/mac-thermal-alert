#!/usr/bin/python3
"""Thermal alert for Apple Silicon Macs. Run every minute by launchd (local.thermal-alert).

Reads CPU/GPU temperature from macmon (no sudo) and battery temperature from
ioreg, and posts a macOS notification when a limit is crossed. Each level
alerts at most once per COOLDOWN seconds so it never spams.
"""
import json, os, re, shutil, subprocess, sys, time

# Limits in degrees C. Override any of them with an env var of the same name.
CHIP_WARN = float(os.environ.get("CHIP_WARN", 95))      # sustained heavy heat
CHIP_CRIT = float(os.environ.get("CHIP_CRIT", 105))     # throttling territory
BATT_WARN = float(os.environ.get("BATT_WARN", 40))      # battery ages faster above this
BATT_CRIT = float(os.environ.get("BATT_CRIT", 45))
SUSTAIN = int(os.environ.get("SUSTAIN", 2))             # warn only after N hot readings in a row
COOLDOWN = int(os.environ.get("COOLDOWN", 900))

STATE = os.path.expanduser("~/Library/Application Support/thermal-alert.json")
LOG = os.path.expanduser("~/Library/Logs/thermal-alert.log")
MACMON = (os.environ.get("MACMON") or shutil.which("macmon")
          or next((p for p in ("/opt/homebrew/bin/macmon", "/usr/local/bin/macmon")
                   if os.path.exists(p)), "macmon"))


def chip_temps():
    out = subprocess.run([MACMON, "pipe", "-s", "1", "-i", "1000"],
                         capture_output=True, text=True, timeout=30).stdout
    t = json.loads(out.strip().splitlines()[-1])["temp"]
    return t["cpu_temp_avg"], t["gpu_temp_avg"]


def battery_temp():
    out = subprocess.run(["ioreg", "-rn", "AppleSmartBattery"],
                         capture_output=True, text=True, timeout=10).stdout
    m = re.search(r'"Temperature" = (\d+)', out)
    return int(m.group(1)) / 100 if m else None


def throttled():
    out = subprocess.run(["pmset", "-g", "therm"], capture_output=True, text=True).stdout
    m = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", out)
    return m is not None and int(m.group(1)) < 100


def notify(title, msg, sound):
    script = f'display notification "{msg}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", script])
    # A banner vanishes after a few seconds, so also open a dialog that stays
    # on screen until it is dismissed. Detached, so this run is not blocked.
    level = "critical" if title.startswith("🔥") else "warning"
    dialog = (f'display alert "{title}" message "{msg}" as {level} '
              f'buttons {{"OK"}} default button "OK"')
    subprocess.Popen(["osascript", "-e", dialog], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    try:
        state = json.load(open(STATE))
    except Exception:
        state = {}
    now = time.time()
    cpu, gpu = chip_temps()
    batt = battery_temp()
    chip = max(cpu, gpu)
    thr = throttled()

    hot = state.get("hot_count", 0) + 1 if chip >= CHIP_WARN else 0
    state["hot_count"] = hot

    alerts = []
    if chip >= CHIP_CRIT or thr:
        alerts.append(("chip_crit", "🔥 Laptop overheating",
                       f"CPU {cpu:.0f}°C, GPU {gpu:.0f}°C{' (throttling)' if thr else ''}. Quit heavy apps and let it cool.", "Sosumi"))
    elif hot >= SUSTAIN:
        alerts.append(("chip_warn", "Laptop running hot",
                       f"CPU {cpu:.0f}°C, GPU {gpu:.0f}°C for {hot} min. Check Activity Monitor.", "Funk"))
    if batt is not None and batt >= BATT_CRIT:
        alerts.append(("batt_crit", "🔥 Battery too hot",
                       f"Battery {batt:.0f}°C. Unplug the charger and let it cool.", "Sosumi"))
    elif batt is not None and batt >= BATT_WARN:
        alerts.append(("batt_warn", "Battery warm",
                       f"Battery {batt:.0f}°C. Heat wears the battery; avoid charging under load.", "Funk"))

    sent = []
    for key, title, msg, sound in alerts:
        if now - state.get("last_" + key, 0) >= COOLDOWN:
            notify(title, msg, sound)
            state["last_" + key] = now
            sent.append(key)

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(state, open(STATE, "w"))
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%F %T')} cpu={cpu:.1f} gpu={gpu:.1f} batt={batt} "
                f"throttled={thr} hot={hot} sent={','.join(sent) or '-'}\n")
    # keep the log small
    lines = open(LOG).readlines()
    if len(lines) > 20000:
        open(LOG, "w").writelines(lines[-10000:])


def test():
    """Show all four alerts with the current readings. Does not touch the state file."""
    cpu, gpu = chip_temps()
    batt = battery_temp() or 0
    print(f"CPU {cpu:.1f}°C  GPU {gpu:.1f}°C  battery {batt:.1f}°C  throttled={throttled()}")
    notify("Laptop running hot", f"TEST. CPU {cpu:.0f}°C, GPU {gpu:.0f}°C.", "Funk")
    notify("Battery warm", f"TEST. Battery {batt:.0f}°C.", "Funk")
    notify("🔥 Laptop overheating", f"TEST. CPU {cpu:.0f}°C, GPU {gpu:.0f}°C.", "Sosumi")
    notify("🔥 Battery too hot", f"TEST. Battery {batt:.0f}°C.", "Sosumi")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
        sys.exit(0)
    try:
        main()
    except Exception as e:
        with open(LOG, "a") as f:
            f.write(f"{time.strftime('%F %T')} ERROR {e!r}\n")
        sys.exit(1)
