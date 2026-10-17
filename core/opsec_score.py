import subprocess
from pathlib import Path
from typing import Dict, List


def _sysctl(key: str) -> str:
    try:
        return Path("/proc/sys/" + key.replace(".", "/")).read_text().strip()
    except Exception:
        return ""


def _root_on_luks() -> bool:
    """True when / sits on a dm-crypt device (directly or through LVM)."""
    try:
        source = subprocess.run(["findmnt", "-no", "SOURCE", "/"], capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception:
        return False
    return bool(source) and _on_crypt(source)


def _on_crypt(device: str) -> bool:
    """True when `device` sits on dm-crypt anywhere below it (e.g. LVM inside LUKS)."""
    try:
        tree = subprocess.run(["lsblk", "-s", "-n", "-o", "TYPE", device], capture_output=True, text=True, timeout=3).stdout
        return "crypt" in tree.split()
    except Exception:
        return False


def _swap_safe() -> bool:
    """No swap at all, or swap only on zram or encrypted devices."""
    try:
        lines = Path("/proc/swaps").read_text().splitlines()[1:]
    except Exception:
        return False
    for line in lines:
        dev = line.split()[0]
        if dev.startswith("/dev/zram") or _on_crypt(dev):
            continue
        return False
    return True


def build_report(auth_mgr, tor_mgr, opsec_mgr, system_mgr) -> Dict:
    """
    Grades the node against the PhantomNode OPSEC levels. Each check carries the
    command that fixes it so the dashboard can show actionable next steps.
    """
    st = opsec_mgr.get_opsec_status()
    checks: List[Dict] = [
        # Level 1 - baseline
        {"level": 1, "id": "custom_password", "label": "Dashboard password changed from first-boot default",
         "ok": auth_mgr.get_initial_password() is None, "fix": "sudo phantom password set"},
        {"level": 1, "id": "firewall", "label": "UFW firewall active (zero WAN exposure)",
         "ok": st.get("ufw_active", False), "fix": "sudo ufw enable"},
        {"level": 1, "id": "tor", "label": "Tor daemon running",
         "ok": tor_mgr.is_tor_active(), "fix": "sudo systemctl enable --now tor"},
        {"level": 1, "id": "sysctl", "label": "Kernel network hardening (TCP timestamps off)",
         "ok": st.get("sysctl_hardened", False), "fix": "sudo bash /opt/phantom-node/scripts/hardening.sh"},
        {"level": 1, "id": "kptr", "label": "Kernel pointers and dmesg hidden from users",
         "ok": _sysctl("kernel.kptr_restrict") == "2" and _sysctl("kernel.dmesg_restrict") == "1",
         "fix": "sudo bash /opt/phantom-node/scripts/hardening.sh"},
        # Level 2 - targeted protection
        {"level": 2, "id": "totp", "label": "Two-factor login (TOTP) enabled",
         "ok": auth_mgr.totp_enabled(), "fix": "sudo phantom password 2fa enable"},
        {"level": 2, "id": "onion_auth", "label": "Dashboard onion restricted to authorized Tor clients",
         "ok": bool(tor_mgr.list_client_auth("dashboard")), "fix": "sudo phantom onion auth add <device-name>"},
        {"level": 2, "id": "signed_updates", "label": "OTA updates require a trusted signature",
         "ok": system_mgr.signature_required(), "fix": "sudo phantom update trust add \"<ssh public key>\""},
        # Level 3 - physical / forensic resistance
        {"level": 3, "id": "luks_root", "label": "Root filesystem on LUKS full-disk encryption",
         "ok": _root_on_luks(), "fix": "Reinstall with encrypted LVM (Debian installer: 'Guided - use entire disk and set up encrypted LVM')"},
        {"level": 3, "id": "swap", "label": "No unencrypted swap (decrypted RAM never hits disk)",
         "ok": _swap_safe(), "fix": "Use zram or a random-key encrypted swap in /etc/crypttab"},
        {"level": 3, "id": "core_dumps", "label": "Core dumps of privileged processes disabled",
         "ok": _sysctl("fs.suid_dumpable") == "0", "fix": "sudo bash /opt/phantom-node/scripts/hardening.sh"},
        {"level": 3, "id": "usb_switch", "label": "USB dead man's switch armed",
         "ok": st.get("usb_switch_armed", False), "fix": "sudo phantom opsec arm-usb"},
    ]

    passed = sum(1 for c in checks if c["ok"])
    # Highest level whose checks (and all lower levels) fully pass
    achieved = 0
    for level in (1, 2, 3):
        if all(c["ok"] for c in checks if c["level"] <= level):
            achieved = level
    return {
        "score": round(100 * passed / len(checks)),
        "passed": passed,
        "total": len(checks),
        "level": achieved,
        "checks": checks,
    }
