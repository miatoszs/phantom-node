import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from .config import SCRIPTS_DIR

PANIC_MODES = ("poweroff", "reboot", "nuke")

class OpsecManager:
    """Manages physical OPSEC triggers, USB Dead Man's Switch and Emergency Hardening."""

    def __init__(self):
        self.systemd_dir = Path("/etc/systemd/system")

    def get_opsec_status(self) -> Dict:
        """Returns the status of all OPSEC shields and triggers."""
        return {
            "usb_switch_armed": self._is_service_active("nukeusb.service"),
            "usb_timer_active": self._is_service_active("nukeusb.timer"),
            "hid_trap_armed": self._is_service_active("emergency-hid.service"),
            "ufw_active": self._is_ufw_active(),
            "sysctl_hardened": self._check_sysctl_hardening(),
            "lsusb_available": shutil.which("lsusb") is not None,
            "evtest_available": shutil.which("evtest") is not None
        }

    def _is_service_active(self, service_name: str) -> bool:
        """Checks if a systemd unit is currently active."""
        try:
            res = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=2
            )
            return res.returncode == 0 and "active" in res.stdout.strip()
        except Exception:
            return False

    def _is_ufw_active(self) -> bool:
        """Checks if UFW firewall is active."""
        try:
            res = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return "Status: active" in res.stdout
        except Exception:
            return False

    def _check_sysctl_hardening(self) -> bool:
        """Checks if core sysctl privacy hardenings are in effect."""
        try:
            res = subprocess.run(
                ["sysctl", "net.ipv4.tcp_timestamps"],
                capture_output=True,
                text=True,
                timeout=2
            )
            # TCP timestamps disabled = 0 means hardened
            return "= 0" in res.stdout
        except Exception:
            return False

    def set_usb_switch(self, arm: bool) -> Dict:
        """Arms or disarms the USB Dead Man's Switch."""
        action = "start" if arm else "stop"
        enable = "enable" if arm else "disable"

        try:
            subprocess.run(["systemctl", enable, "nukeusb.timer"], check=True)
            subprocess.run(["systemctl", action, "nukeusb.timer"], check=True)
            return {"success": True, "armed": arm, "message": f"USB Switch {'Armed' if arm else 'Disarmed'}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_panic(self, mode: str = "poweroff") -> Dict:
        """
        Runs the shared emergency sequence (scripts/panic.sh): flush caches, swapoff,
        optional LUKS key wipe (mode="nuke"), then a forced power-off or reboot.
        """
        if mode not in PANIC_MODES:
            return {"success": False, "error": f"Unknown panic mode '{mode}'. Use one of: {', '.join(PANIC_MODES)}."}
        script = SCRIPTS_DIR / "panic.sh"
        try:
            # Detached so the HTTP response can still be sent before the machine goes down
            subprocess.Popen(["bash", str(script), mode], start_new_session=True)
            return {"success": True, "message": f"Emergency {mode} initiated."}
        except Exception as e:
            return {"success": False, "error": str(e)}
