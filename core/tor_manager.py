import base64
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .config import TORRC_DIR, TORRC_FILE, TOR_PHANTOM_HS_DIR, ONION_CACHE_DIR

CLIENT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

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

    # ------------------------------------------------------------------
    # Tor v3 client authorization: only devices holding a private key can
    # even fetch the onion descriptor. Without any authorized client the
    # service stays public (anyone with the address reaches the login page).
    # ------------------------------------------------------------------

    def _auth_dir(self, service_id: str) -> Path:
        return self.hs_base_dir / service_id / "authorized_clients"

    def _chown_tor(self, path: Path):
        try:
            import pwd
            tor_user = pwd.getpwnam("debian-tor")
            os.chown(path, tor_user.pw_uid, tor_user.pw_gid)
        except Exception:
            pass

    def list_client_auth(self, service_id: str) -> List[str]:
        auth_dir = self._auth_dir(service_id)
        try:
            return sorted(p.stem for p in auth_dir.glob("*.auth"))
        except (PermissionError, OSError):
            return []

    def add_client_auth(self, service_id: str, client_name: str) -> Dict:
        """Generates an x25519 keypair, authorizes its public half and returns the private key once."""
        if not CLIENT_NAME_RE.match(client_name or ""):
            return {"success": False, "error": "Client name must be 1-32 letters, digits, '-' or '_'."}
        onion = self.get_onion_address(service_id)
        if not onion:
            return {"success": False, "error": f"No onion address found for '{service_id}'."}
        try:
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
            from cryptography.hazmat.primitives import serialization
        except ImportError:
            return {"success": False, "error": "Python package 'cryptography' is missing. Run: phantom update"}

        auth_dir = self._auth_dir(service_id)
        auth_file = auth_dir / f"{client_name}.auth"
        if auth_file.exists():
            return {"success": False, "error": f"Client '{client_name}' already exists. Remove it first to rotate its key."}

        key = X25519PrivateKey.generate()
        raw_priv = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
        raw_pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        b32 = lambda b: base64.b32encode(b).decode().rstrip("=")

        try:
            auth_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(auth_dir, 0o700)
            self._chown_tor(auth_dir)
            auth_file.write_text(f"descriptor:x25519:{b32(raw_pub)}\n", encoding="utf-8")
            os.chmod(auth_file, 0o600)
            self._chown_tor(auth_file)
        except Exception as e:
            return {"success": False, "error": f"Could not write client key: {e}"}

        self.reload_tor()
        onion_id = onion.replace(".onion", "")
        private_key = b32(raw_priv)
        return {
            "success": True,
            "client": client_name,
            "onion": onion,
            "private_key": private_key,
            # Line for a Tor daemon's ClientOnionAuthDir (<name>.auth_private), e.g. Orbot / Whonix
            "auth_private_line": f"{onion_id}:descriptor:x25519:{private_key}",
            "message": "Client authorized. Store this key now - it cannot be shown again."
        }

    def remove_client_auth(self, service_id: str, client_name: str) -> Dict:
        if not CLIENT_NAME_RE.match(client_name or ""):
            return {"success": False, "error": "Invalid client name."}
        auth_file = self._auth_dir(service_id) / f"{client_name}.auth"
        if not auth_file.exists():
            return {"success": False, "error": f"Client '{client_name}' not found."}
        try:
            auth_file.unlink()
        except Exception as e:
            return {"success": False, "error": str(e)}
        self.reload_tor()
        remaining = self.list_client_auth(service_id)
        msg = f"Client '{client_name}' revoked."
        if not remaining:
            msg += " No authorized clients left: the onion is public again."
        return {"success": True, "message": msg, "clients": remaining}
