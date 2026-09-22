import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .config import TORRC_DIR, TORRC_FILE, TOR_PHANTOM_HS_DIR

class TorManager:
    """Manages Tor v3 Hidden Services dynamically for PhantomNode apps."""

    def __init__(self):
        self.hs_base_dir = TOR_PHANTOM_HS_DIR
        self.torrc_dir = TORRC_DIR
        self._ensure_setup()

    def _ensure_setup(self):
        """Ensures torrc.d include exists and directories are initialized."""
        try:
            if not self.torrc_dir.exists():
                self.torrc_dir.mkdir(parents=True, exist_ok=True)
            if not self.hs_base_dir.exists():
                self.hs_base_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            pass

    def is_tor_active(self) -> bool:
        """Checks if the Tor systemd daemon is active."""
        try:
            res = subprocess.run(
                ["systemctl", "is-active", "tor"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if res.returncode == 0 and "active" in res.stdout.strip():
                return True
            # Also check tor@default
            res_default = subprocess.run(
                ["systemctl", "is-active", "tor@default"],
                capture_output=True,
                text=True,
                timeout=3
            )
            return res_default.returncode == 0 and "active" in res_default.stdout.strip()
        except Exception:
            return False

    def add_hidden_service(self, service_id: str, ports: Dict[int, int]) -> Optional[str]:
        """
        Creates or updates a Tor v3 hidden service configuration.
        ports: {virtual_port: local_target_port}, e.g. {80: 7426}
        Returns the .onion hostname if available.
        """
        service_hs_dir = self.hs_base_dir / service_id
        config_file = self.torrc_dir / f"phantom_{service_id}.conf"

        lines = [
            f"# PhantomNode Hidden Service for: {service_id}",
            f"HiddenServiceDir {service_hs_dir}",
            "HiddenServiceVersion 3"
        ]
        for virt_port, target_port in ports.items():
            lines.append(f"HiddenServicePort {virt_port} 127.0.0.1:{target_port}")

        # Also support HiddenServicePoWDefenses for protection against DoS if desired
        lines.append("")

        try:
            # Write config file in /etc/tor/torrc.d/
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            # Ensure directory permissions are 700 and owned by debian-tor if running as root
            if os.geteuid() == 0:
                service_hs_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(service_hs_dir, 0o700)
                try:
                    import pwd
                    tor_user = pwd.getpwnam("debian-tor")
                    os.chown(service_hs_dir, tor_user.pw_uid, tor_user.pw_gid)
                except Exception:
                    pass

            self.reload_tor()
            return self.get_onion_address(service_id)
        except Exception as e:
            print(f"[TorManager] Error configuring hidden service {service_id}: {e}")
            return None

    def get_onion_address(self, service_id: str) -> Optional[str]:
        """Reads the generated .onion address from hostname file."""
        hostname_path = self.hs_base_dir / service_id / "hostname"
        if hostname_path.exists():
            try:
                with open(hostname_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                pass
        return None

    def remove_hidden_service(self, service_id: str) -> bool:
        """Removes the hidden service config and data directory."""
        config_file = self.torrc_dir / f"phantom_{service_id}.conf"
        service_hs_dir = self.hs_base_dir / service_id

        removed = False
        if config_file.exists():
            try:
                config_file.unlink()
                removed = True
            except Exception as e:
                print(f"[TorManager] Error removing config {config_file}: {e}")

        if service_hs_dir.exists():
            try:
                shutil.rmtree(service_hs_dir)
            except Exception as e:
                print(f"[TorManager] Error removing dir {service_hs_dir}: {e}")

        if removed:
            self.reload_tor()
        return removed

    def reload_tor(self) -> bool:
        """Reloads the Tor configuration."""
        for cmd in [["systemctl", "reload", "tor@default"], ["systemctl", "reload", "tor"]]:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
        return False

    def list_services(self) -> List[Dict]:
        """Lists all configured hidden services."""
        services = []
        if not self.torrc_dir.exists():
            return services

        for conf in self.torrc_dir.glob("phantom_*.conf"):
            service_id = conf.stem.replace("phantom_", "")
            onion = self.get_onion_address(service_id)
            services.append({
                "service_id": service_id,
                "onion": onion or "Generating...",
                "config_file": str(conf)
            })
        return services
