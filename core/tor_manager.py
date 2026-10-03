import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .config import TORRC_DIR, TORRC_FILE, TOR_PHANTOM_HS_DIR, ONION_CACHE_DIR

class TorManager:
    """Manages Tor v3 Hidden Services dynamically for PhantomNode apps."""

    def __init__(self):
        self.hs_base_dir = TOR_PHANTOM_HS_DIR
        self.torrc_dir = TORRC_DIR
        self.onion_cache_dir = ONION_CACHE_DIR
        self._ensure_setup()

    def _ensure_setup(self):
        """Ensures torrc.d include exists and directories are initialized."""
        try:
            if not self.torrc_dir.exists():
                self.torrc_dir.mkdir(parents=True, exist_ok=True)
            if not self.hs_base_dir.exists():
                self.hs_base_dir.mkdir(parents=True, exist_ok=True)
            if not self.onion_cache_dir.exists():
                self.onion_cache_dir.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                os.chmod(self.onion_cache_dir, 0o755)
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

    def _cache_onion_address(self, service_id: str, onion: str):
        """Saves a public .onion address to the world-readable cache directory."""
        if not onion:
            return
        try:
            self.onion_cache_dir.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                os.chmod(self.onion_cache_dir, 0o755)
            cache_file = self.onion_cache_dir / f"{service_id}.onion"
            cache_file.write_text(onion.strip(), encoding="utf-8")
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                os.chmod(cache_file, 0o644)
        except Exception:
            pass

    def get_onion_address(self, service_id: str) -> Optional[str]:
        """
        Reads the generated .onion address.
        Safely attempts to read Tor hidden service directory, syncing to public cache if privileged,
        or falls back to reading from world-readable onion cache for unprivileged users.
        """
        # 1. Try reading directly from Tor's HiddenServiceDir if accessible
        try:
            hostname_path = self.hs_base_dir / service_id / "hostname"
            if hostname_path.exists():
                with open(hostname_path, "r", encoding="utf-8") as f:
                    onion = f.read().strip()
                    if onion:
                        self._cache_onion_address(service_id, onion)
                        return onion
        except (PermissionError, OSError):
            pass
        except Exception:
            pass

        # 2. Check world-readable public cache (works for all users without sudo)
        try:
            cache_path = self.onion_cache_dir / f"{service_id}.onion"
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = f.read().strip()
                    if cached:
                        return cached
        except Exception:
            pass

        return None

    def sync_onion_cache(self):
        """Syncs all available Tor v3 Hidden Service hostnames to the public cache."""
        try:
            self.onion_cache_dir.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                os.chmod(self.onion_cache_dir, 0o755)
        except Exception:
            pass

        try:
            if self.hs_base_dir.exists():
                for hs_dir in self.hs_base_dir.iterdir():
                    if hs_dir.is_dir():
                        service_id = hs_dir.name
                        try:
                            hostname_file = hs_dir / "hostname"
                            if hostname_file.exists():
                                onion = hostname_file.read_text(encoding="utf-8").strip()
                                if onion:
                                    self._cache_onion_address(service_id, onion)
                        except (PermissionError, OSError):
                            pass
        except (PermissionError, OSError):
            pass
        except Exception:
            pass

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

    def remove_hidden_service(self, service_id: str) -> bool:
        """Removes the hidden service config, data directory, and cached hostname."""
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

        cache_file = self.onion_cache_dir / f"{service_id}.onion"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                pass

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
        """Lists all configured hidden services safely without PermissionError."""
        services = []
        service_ids = set()

        # 1. Collect service IDs from torrc.d configs if accessible
        try:
            if self.torrc_dir.exists():
                for conf in self.torrc_dir.glob("phantom_*.conf"):
                    sid = conf.stem.replace("phantom_", "")
                    service_ids.add(sid)
        except (PermissionError, OSError):
            pass
        except Exception:
            pass

        # 2. Collect from public cache directory (world-readable for non-root users)
        try:
            if self.onion_cache_dir.exists():
                for onion_file in self.onion_cache_dir.glob("*.onion"):
                    service_ids.add(onion_file.stem)
        except Exception:
            pass

        # 3. Always include dashboard
        service_ids.add("dashboard")

        for sid in sorted(service_ids):
            onion = self.get_onion_address(sid)
            conf_path = self.torrc_dir / f"phantom_{sid}.conf"
            # Include service if onion address is known or config exists
            if onion or conf_path.exists():
                services.append({
                    "service_id": sid,
                    "onion": onion or "Generating...",
                    "config_file": str(conf_path)
                })
        return services
