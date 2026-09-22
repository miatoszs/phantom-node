#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - USB Dead Man's Switch (nukeusb.sh)
# Based on OPSEC Bible: "USB-triggered server shutdowns"
# ==============================================================================
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

INTERVAL=1
# Command to execute when an unauthorized USB change occurs
# Options: 'systemctl poweroff -f' or 'systemctl reboot -f'
TRIGGER="systemctl poweroff -f"

if ! command -v lsusb >/dev/null 2>&1; then
    echo "[!] Error: 'lsusb' is required. Install usbutils." >&2
    exit 1
fi

# Get initial list of authorized USB devices
prev_devices=$(lsusb)

echo "[*] PhantomNode USB Shield Active. Monitoring hardware tampering..."
echo "[*] Connected devices baselined: $(echo "$prev_devices" | wc -l)"

while true; do
    current_devices=$(lsusb)

    if [[ "$current_devices" != "$prev_devices" ]]; then
        echo "[ALERT] Unauthorized USB change detected! Triggering emergency wipe and shutdown..."
        sync
        echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
        $TRIGGER
        exit 0
    fi

    sleep "$INTERVAL"
done
