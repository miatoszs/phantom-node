import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .config import APPS_DIR, INSTALLED_APPS_DIR
from .tor_manager import TorManager

class DockerManager:
    """Manages Docker Compose services and privacy app lifecycles."""

    def __init__(self):
        self.apps_dir = APPS_DIR
        self.installed_dir = INSTALLED_APPS_DIR
        self.tor_manager = TorManager()

    def is_docker_running(self) -> bool:
        """Verifies if Docker daemon is responsive."""
        try:
            res = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=3
            )
            return res.returncode == 0
        except Exception:
            return False

    def list_available_apps(self) -> List[Dict]:
        """Scans catalog and returns metadata of all installable apps."""
        catalog = []
        if not self.apps_dir.exists():
            return catalog

        for manifest_file in self.apps_dir.glob("*/manifest.json"):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    app_id = manifest.get("id") or manifest_file.parent.name
                    manifest["id"] = app_id
                    manifest["is_installed"] = self.is_app_installed(app_id)
                    manifest["is_running"] = self.is_app_running(app_id) if manifest["is_installed"] else False
                    manifest["onion"] = self.tor_manager.get_onion_address(app_id) if manifest["is_installed"] else None
                    catalog.append(manifest)
            except Exception as e:
                print(f"[DockerManager] Error reading manifest {manifest_file}: {e}")
        return catalog

    def is_app_installed(self, app_id: str) -> bool:
        """Checks if app exists in installed directory."""
        app_path = self.installed_dir / app_id
        return (app_path / "docker-compose.yml").exists()

    def is_app_running(self, app_id: str) -> bool:
        """Checks if containers for this app are currently running."""
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return False

        try:
            res = subprocess.run(
                ["docker", "compose", "ps", "--status", "running", "-q"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            return res.returncode == 0 and bool(res.stdout.strip())
        except Exception:
            return False

    def get_app_manifest(self, app_id: str) -> Optional[Dict]:
        """Returns the app manifest from catalog or installed directory."""
        installed_manifest = self.installed_dir / app_id / "manifest.json"
        catalog_manifest = self.apps_dir / app_id / "manifest.json"

        target = installed_manifest if installed_manifest.exists() else catalog_manifest
        if target.exists():
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["id"] = app_id
                return data
        return None

    def install_app(self, app_id: str, custom_config: Optional[Dict] = None) -> Dict:
        """
        Installs an app from the catalog with optional custom port / env overrides:
        1. Copies app template to installed directory.
        2. Populates secure secrets in .env and applies custom env overrides.
        3. Replaces default ports in docker-compose.yml if custom_web_port is specified.
        4. Configures Tor v3 Hidden Service for its web port.
        5. Launches docker compose up -d.
        """
        source_dir = self.apps_dir / app_id
        target_dir = self.installed_dir / app_id

        if not source_dir.exists():
            return {"success": False, "error": f"App '{app_id}' not found in catalog."}

        manifest = self.get_app_manifest(app_id)
        if not manifest:
            return {"success": False, "error": "Invalid manifest."}

        try:
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy template files
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, target_dir / item.name)
                elif item.is_dir():
                    dest_subdir = target_dir / item.name
                    if not dest_subdir.exists():
                        shutil.copytree(item, dest_subdir)

            default_web_port = manifest.get("web_port")
            default_onion_port = manifest.get("onion_port", 80)

            # Check for custom overrides
            web_port = default_web_port
            onion_port = default_onion_port

            if custom_config:
                if custom_config.get("web_port"):
                    try:
                        web_port = int(custom_config["web_port"])
                    except (ValueError, TypeError):
                        pass
                if custom_config.get("onion_port"):
                    try:
                        onion_port = int(custom_config["onion_port"])
                    except (ValueError, TypeError):
                        pass

            # Update docker-compose.yml with custom web port if modified
            compose_file = target_dir / "docker-compose.yml"
            if compose_file.exists() and default_web_port and web_port != default_web_port:
                compose_content = compose_file.read_text(encoding="utf-8")
                compose_content = compose_content.replace(f"127.0.0.1:{default_web_port}:", f"127.0.0.1:{web_port}:")
                compose_content = compose_content.replace(f'"{default_web_port}:', f'"{web_port}:')
                compose_file.write_text(compose_content, encoding="utf-8")

            # Update installed manifest.json with effective ports
            installed_manifest_path = target_dir / "manifest.json"
            manifest["web_port"] = web_port
            manifest["onion_port"] = onion_port
            with open(installed_manifest_path, "w", encoding="utf-8") as fm:
                json.dump(manifest, fm, indent=2, ensure_ascii=False)

            # Generate .env with randomized secrets
            env_example = source_dir / ".env.example"
            target_env = target_dir / ".env"
            if env_example.exists() and not target_env.exists():
                with open(env_example, "r", encoding="utf-8") as fe:
                    content = fe.read()
                # Replace placeholders like GENERATE_PASSWORD
                content = content.replace("GENERATE_PASSWORD", secrets.token_urlsafe(18))
                content = content.replace("GENERATE_SECRET_KEY", secrets.token_hex(32))
                content = content.replace("GENERATE_TOKEN", secrets.token_urlsafe(24))
                with open(target_env, "w", encoding="utf-8") as ft:
                    ft.write(content)

            # Apply custom env vars if provided
            if custom_config and custom_config.get("custom_env"):
                custom_env_data = custom_config.get("custom_env")
                with open(target_env, "a", encoding="utf-8") as fa:
                    fa.write("\n# --- Custom User Overrides ---\n")
                    if isinstance(custom_env_data, dict):
                        for k, v in custom_env_data.items():
                            fa.write(f"{k}={v}\n")
                    elif isinstance(custom_env_data, str):
                        fa.write(custom_env_data.strip() + "\n")

            # Register Tor Hidden Service if ports defined
            if web_port:
                self.tor_manager.add_hidden_service(app_id, {onion_port: web_port})

            # Start container stack
            res = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                timeout=180
            )

            if res.returncode != 0:
                return {
                    "success": False,
                    "error": f"Docker Compose error: {res.stderr or res.stdout}"
                }

            onion_addr = self.tor_manager.get_onion_address(app_id)
            return {
                "success": True,
                "app_id": app_id,
                "onion": onion_addr,
                "web_port": web_port,
                "message": f"Successfully installed and started {manifest.get('name', app_id)}."
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_app(self, app_id: str) -> Dict:
        """Starts an existing installed app."""
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return {"success": False, "error": "App not installed."}

        try:
            res = subprocess.run(
                ["docker", "compose", "start"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"success": res.returncode == 0, "output": res.stdout or res.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_app(self, app_id: str) -> Dict:
        """Stops an installed app."""
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return {"success": False, "error": "App not installed."}

        try:
            res = subprocess.run(
                ["docker", "compose", "stop"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"success": res.returncode == 0, "output": res.stdout or res.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restart_app(self, app_id: str) -> Dict:
        """Restarts an installed app."""
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return {"success": False, "error": "App not installed."}

        try:
            res = subprocess.run(
                ["docker", "compose", "restart"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"success": res.returncode == 0, "output": res.stdout or res.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_app(self, app_id: str, purge_volumes: bool = False) -> Dict:
        """Stops and removes an installed app and its Tor hidden service."""
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return {"success": False, "error": "App not installed."}

        try:
            cmd = ["docker", "compose", "down"]
            if purge_volumes:
                cmd.append("-v")

            subprocess.run(cmd, cwd=str(app_path), capture_output=True, text=True, timeout=60)
            self.tor_manager.remove_hidden_service(app_id)
            shutil.rmtree(app_path)
            return {"success": True, "message": f"App '{app_id}' uninstalled successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_app(self, app_id: str) -> Dict:
        """
        Updates an installed container stack to its latest image:
        1. Executes `docker compose pull`.
        2. Executes `docker compose up -d` to recreate containers with the new image.
        3. Cleans up dangling unused images with `docker image prune -f`.
        """
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return {"success": False, "error": f"App '{app_id}' is not installed."}

        try:
            # 1. Pull latest Docker images
            pull_res = subprocess.run(
                ["docker", "compose", "pull"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            if pull_res.returncode != 0:
                err = pull_res.stderr.strip() or pull_res.stdout.strip()
                return {
                    "success": False,
                    "error": f"Docker pull failed: {err}"
                }

            # 2. Re-create / restart containers with latest images
            up_res = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=180
            )
            if up_res.returncode != 0:
                err = up_res.stderr.strip() or up_res.stdout.strip()
                return {
                    "success": False,
                    "error": f"Docker up failed: {err}"
                }

            # 3. Clean up dangling images
            try:
                subprocess.run(["docker", "image", "prune", "-f"], capture_output=True, timeout=30)
            except Exception:
                pass

            manifest = self.get_app_manifest(app_id) or {}
            app_name = manifest.get("name", app_id)
            return {
                "success": True,
                "message": f"{app_name} successfully updated to the latest container image and restarted.",
                "app_id": app_id
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Update timed out while pulling container images for {app_id}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_all_apps(self) -> Dict:
        """Updates all currently installed apps."""
        results = {}
        apps = self.list_available_apps()
        installed = [a for a in apps if a.get("is_installed")]

        if not installed:
            return {
                "success": True,
                "total": 0,
                "updated": 0,
                "message": "No applications are currently installed."
            }

        for app in installed:
            app_id = app["id"]
            results[app_id] = self.update_app(app_id)

        success_count = sum(1 for r in results.values() if r.get("success"))
        return {
            "success": True,
            "total": len(installed),
            "updated": success_count,
            "results": results
        }

    def get_logs(self, app_id: str, lines: int = 100) -> str:
        """Retrieves container logs for an app."""
        app_path = self.installed_dir / app_id
        if not app_path.exists():
            return "App not installed."

        try:
            res = subprocess.run(
                ["docker", "compose", "logs", f"--tail={lines}"],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=10
            )
            return res.stdout or res.stderr or "No logs available."
        except Exception as e:
            return f"Error reading logs: {e}"
