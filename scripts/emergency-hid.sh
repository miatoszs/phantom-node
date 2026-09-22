#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - HID Input Trap (emergency-hid.sh)
# Based on OPSEC Bible: "Home server emergency shutdowns triggered by mouse/keyboard"
# ==============================================================================
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Time window in seconds to safely detach before trap becomes active
ESCAPE_WINDOW=${1:-5}

if ! command -v evtest >/dev/null 2>&1; then
    echo "[!] Error: 'evtest' is required. Install evtest." >&2
    exit 1
fi

echo "[*] PhantomNode HID Trap: Arming in $ESCAPE_WINDOW seconds. Disconnect now!"
sleep "$ESCAPE_WINDOW"
echo "[*] HID Trap ARMED. Any physical keyboard or mouse input will trigger emergency shutdown!"

for device in /dev/input/event*; do
    if [[ -r "$device" ]]; then
        evtest "$device" 2>/dev/null | while IFS= read -r line; do
            if [[ "$line" =~ ^Event:.*\(EV_KEY\).*value\ 1$ ]] ||
               [[ "$line" =~ ^Event:.*\(EV_ABS\).*value\ -?[1-9] ]] ||
               [[ "$line" =~ ^Event:.*\(EV_REL\).*value\ -?[1-9] ]]; then
                echo "[ALERT] Physical tampering detected on $device! Powering off..."
                sync
                echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
                systemctl poweroff -f
            fi
        done &
    fi
done

wait
