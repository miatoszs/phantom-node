#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - Emergency Panic Sequence (panic.sh)
# Shared by the dashboard Panic button, `phantom opsec panic`, nukeusb.sh and
# emergency-hid.sh so every trigger runs the same anti-forensics steps.
#
# Usage: panic.sh [poweroff|reboot|nuke]
#   poweroff  flush caches, pull swap back into RAM, hard power-off (default)
#   reboot    same, but hard reboot
#   nuke      also luksSuspend every dm-crypt volume (erases the volume keys
#             from kernel memory) before an instant SysRq power-off
# ==============================================================================
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

MODE="${1:-poweroff}"
logger -t phantom-panic "Panic sequence started (mode=${MODE})" 2>/dev/null || true

# 1. Flush pending writes so filesystems are consistent on next unlock
sync

# 2. Drop page cache, dentries and inodes (decrypted file contents cached in RAM)
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

# 3. Disable swap so no decrypted memory pages stay on disk. Bounded so a huge
#    swap cannot delay the shutdown.
timeout 10 swapoff -a 2>/dev/null || true

# 4. Nuke mode: wipe LUKS volume keys from kernel memory
if [ "${MODE}" = "nuke" ] && command -v cryptsetup >/dev/null 2>&1; then
    for dev in $(dmsetup ls --target crypt 2>/dev/null | awk '{print $1}'); do
        timeout 5 cryptsetup luksSuspend "${dev}" 2>/dev/null || true
    done
fi

# 5. Power off / reboot without waiting for services. SysRq is used for nuke
#    because a suspended root volume would block a normal systemd shutdown.
if [ "${MODE}" = "reboot" ]; then
    systemctl reboot -f || echo b > /proc/sysrq-trigger
elif [ "${MODE}" = "nuke" ]; then
    echo o > /proc/sysrq-trigger
else
    systemctl poweroff -f || echo o > /proc/sysrq-trigger
fi
