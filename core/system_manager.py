import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from .config import BASE_DIR, PHANTOM_VERSION, DEFAULT_REPO_URL, UPDATE_MIRROR_FILE, TOR_SOCKS_PORT

class SystemManager:
    """Manages PhantomNode OS updates, configurable mirrors (including Tor .onion), and system lifecycle."""

    def __init__(self):
        self.base_dir = BASE_DIR
        self.version = PHANTOM_VERSION
        self.default_repo_url = DEFAULT_REPO_URL
        self.mirror_file = UPDATE_MIRROR_FILE
        self.fallback_mirror_file = self.base_dir / ".update_mirror"
        self.tor_socks_port = TOR_SOCKS_PORT

    def get_mirror_url(self) -> str:
        """Returns the configured update mirror URL or the default official GitHub repository."""
        for p in [self.mirror_file, self.fallback_mirror_file]:
            if p.exists():
                try:
                    url = p.read_text(encoding="utf-8").strip()
                    if url:
                        return url
                except Exception:
                    pass
        return self.default_repo_url

    def is_onion_url(self, url: Optional[str] = None) -> bool:
        """Determines if the given or configured mirror URL is a Tor .onion service."""
        target_url = url or self.get_mirror_url()
        return ".onion" in target_url.lower()

    def _get_git_proxy_args(self, url: Optional[str] = None) -> List[str]:
        """Returns git command-line config arguments for Tor proxying if target is .onion."""
        if self.is_onion_url(url):
            proxy_url = f"socks5h://127.0.0.1:{self.tor_socks_port}"
            args = ["-c", f"http.proxy={proxy_url}"]
            if shutil.which("torsocks"):
                args.extend(["-c", "core.sshCommand=torsocks ssh"])
            return args
        return []

    def _ensure_git_repo(self, custom_url: Optional[str] = None) -> bool:
        """Ensures that base_dir has an initialized git repository tracking origin with safe.directory and Tor proxy if needed."""
        try:
            repo_url = custom_url or self.get_mirror_url()

            # Mark directory as safe in git config to prevent dubious ownership errors
            subprocess.run(
                ["git", "config", "--global", "--add", "safe.directory", str(self.base_dir)],
                capture_output=True
            )
            
            git_dir = self.base_dir / ".git"
            if not git_dir.exists():
                subprocess.run(["git", "init", "-b", "main"], cwd=str(self.base_dir), check=True, capture_output=True)

            # Check or configure remote origin
            remotes = subprocess.run(["git", "remote"], cwd=str(self.base_dir), capture_output=True, text=True)
            if "origin" not in remotes.stdout.split():
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=str(self.base_dir), check=True, capture_output=True)
            else:
                subprocess.run(["git", "remote", "set-url", "origin", repo_url], cwd=str(self.base_dir), check=True, capture_output=True)

            # Configure Tor proxy for origin if .onion
            if self.is_onion_url(repo_url):
                proxy_url = f"socks5h://127.0.0.1:{self.tor_socks_port}"
                subprocess.run(
                    ["git", "config", "remote.origin.proxy", proxy_url],
                    cwd=str(self.base_dir),
                    capture_output=True
                )
                if shutil.which("torsocks"):
                    subprocess.run(
                        ["git", "config", "remote.origin.sshCommand", "torsocks ssh"],
                        cwd=str(self.base_dir),
                        capture_output=True
                    )
            else:
                subprocess.run(
                    ["git", "config", "--unset", "remote.origin.proxy"],
                    cwd=str(self.base_dir),
                    capture_output=True
                )
                subprocess.run(
                    ["git", "config", "--unset", "remote.origin.sshCommand"],
                    cwd=str(self.base_dir),
                    capture_output=True
                )
            return True
        except Exception as e:
            print(f"[SystemManager] Git init error: {e}")
            return False

    def _test_mirror_connection(self, url: str) -> Dict:
        """Tests connectivity to a git mirror repository using git ls-remote."""
        proxy_args = self._get_git_proxy_args(url)
        timeout = 45 if self.is_onion_url(url) else 15
        cmd = ["git"] + proxy_args + ["ls-remote", "--heads", url]
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if res.returncode == 0:
                return {"reachable": True, "message": "Connection to git mirror successful."}
            else:
                err = res.stderr.strip() or res.stdout.strip() or "Connection failed."
                return {"reachable": False, "message": f"Connection test notice: {err}"}
        except subprocess.TimeoutExpired:
            return {"reachable": False, "message": "Connection timed out. (If using Tor .onion, ensure the Tor daemon is running)."}
        except Exception as e:
            return {"reachable": False, "message": f"Connection check failed: {str(e)}"}

    def set_mirror_url(self, url: str) -> Dict:
        """
        Configures a custom upstream mirror URL (clearnet or Tor .onion).
        Validates URL, saves it persistently, updates git remote origin, and tests connection.
        """
        url = url.strip()
        if not url:
            return {"success": False, "error": "Mirror URL cannot be empty."}

        # Check basic syntax
        valid_protocols = ("http://", "https://", "git@", "ssh://")
        if not any(url.startswith(p) for p in valid_protocols):
            return {
                "success": False,
                "error": "Invalid repository URL format. Must start with http://, https://, git@, or ssh://."
            }

        try:
            # Save persistently
            try:
                self.mirror_file.parent.mkdir(parents=True, exist_ok=True)
                self.mirror_file.write_text(url, encoding="utf-8")
            except Exception:
                self.fallback_mirror_file.write_text(url, encoding="utf-8")

            # Update git remote configuration
            self._ensure_git_repo(custom_url=url)

            # Test connection
            test_res = self._test_mirror_connection(url)
            is_onion = self.is_onion_url(url)
            return {
                "success": True,
                "mirror_url": url,
                "is_onion": is_onion,
                "is_default": (url == self.default_repo_url),
                "connection_test": test_res,
                "message": f"Update mirror successfully set to: {url}" + (" (Routed via Tor SOCKS5)" if is_onion else "")
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to save mirror URL: {str(e)}"}

    def reset_mirror_url(self) -> Dict:
        """Resets the update mirror to the official GitHub repository."""
        try:
            if self.mirror_file.exists():
                self.mirror_file.unlink()
            if self.fallback_mirror_file.exists():
                self.fallback_mirror_file.unlink()

            self._ensure_git_repo(custom_url=self.default_repo_url)
            return {
                "success": True,
                "mirror_url": self.default_repo_url,
                "is_onion": False,
                "is_default": True,
                "message": f"Update mirror reset to official GitHub repository: {self.default_repo_url}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to reset mirror URL: {str(e)}"}

    def check_for_updates(self) -> Dict:
        """
        Fetches upstream repository metadata and compares local commit with origin/main.
        Returns whether an update is available along with commit logs and mirror details.
        """
        self._ensure_git_repo()
        mirror_url = self.get_mirror_url()
        is_onion = self.is_onion_url(mirror_url)
        proxy_args = self._get_git_proxy_args(mirror_url)
        fetch_timeout = 60 if is_onion else 20

        try:
            # 1. Fetch remote origin with Tor proxy if .onion
            cmd = ["git"] + proxy_args + ["fetch", "origin", "main"]
            fetch_res = subprocess.run(
                cmd,
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=fetch_timeout
            )

            if fetch_res.returncode != 0:
                err_text = fetch_res.stderr.strip() or fetch_res.stdout.strip() or "Git fetch failed."
                return {
                    "success": False,
                    "update_available": False,
                    "current_version": self.version,
                    "mirror_url": mirror_url,
                    "is_onion": is_onion,
                    "is_custom_mirror": (mirror_url != self.default_repo_url),
                    "error": err_text
                }

            # 2. Get local HEAD commit
            local_commit_res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=5
            )
            has_head = (local_commit_res.returncode == 0)
            local_commit = local_commit_res.stdout.strip() if has_head else "untracked"

            # 3. Get remote origin/main commit
            remote_commit_res = subprocess.run(
                ["git", "rev-parse", "--short", "origin/main"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=5
            )
            remote_commit = remote_commit_res.stdout.strip() if remote_commit_res.returncode == 0 else "unknown"

            # 4. Count commits behind and extract changelog
            changelog = []
            if not has_head or local_commit == "untracked":
                # Local repository has no committed HEAD - needs initial sync to origin/main
                commits_behind = 1
                update_available = True
                changelog.append({
                    "hash": remote_commit,
                    "subject": "Initial synchronization with upstream mirror",
                    "time": "latest"
                })
            else:
                count_res = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD..origin/main"],
                    cwd=str(self.base_dir),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                commits_behind = int(count_res.stdout.strip()) if count_res.returncode == 0 and count_res.stdout.strip().isdigit() else 0
                update_available = (commits_behind > 0)

                if commits_behind > 0:
                    log_res = subprocess.run(
                        ["git", "log", "-n", "8", "--pretty=format:%h|%s|%cr", "HEAD..origin/main"],
                        cwd=str(self.base_dir),
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if log_res.returncode == 0 and log_res.stdout.strip():
                        for line in log_res.stdout.strip().split("\n"):
                            parts = line.split("|")
                            if len(parts) >= 3:
                                changelog.append({
                                    "hash": parts[0],
                                    "subject": parts[1],
                                    "time": parts[2]
                                })

            return {
                "success": True,
                "update_available": update_available,
                "current_version": self.version,
                "current_commit": local_commit,
                "remote_commit": remote_commit,
                "commits_behind": commits_behind,
                "changelog": changelog,
                "mirror_url": mirror_url,
                "is_onion": is_onion,
                "is_custom_mirror": (mirror_url != self.default_repo_url)
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "update_available": False,
                "current_version": self.version,
                "mirror_url": mirror_url,
                "is_onion": is_onion,
                "is_custom_mirror": (mirror_url != self.default_repo_url),
                "error": "Update check timed out. Verify network connection or Tor status."
            }
        except Exception as e:
            return {
                "success": False,
                "update_available": False,
                "current_version": self.version,
                "mirror_url": mirror_url,
                "is_onion": is_onion,
                "is_custom_mirror": (mirror_url != self.default_repo_url),
                "error": str(e)
            }

    def apply_update(self) -> Dict:
        """
        Pulls latest code from origin/main, updates dependencies, and schedules service restart.
        """
        self._ensure_git_repo()
        mirror_url = self.get_mirror_url()
        is_onion = self.is_onion_url(mirror_url)
        proxy_args = self._get_git_proxy_args(mirror_url)
        fetch_timeout = 90 if is_onion else 35

        try:
            # 1. Fetch latest with Tor proxy if .onion
            cmd = ["git"] + proxy_args + ["fetch", "origin", "main"]
            fetch_res = subprocess.run(
                cmd,
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=False,
                timeout=fetch_timeout
            )
            if fetch_res.returncode != 0:
                err_text = fetch_res.stderr.strip() or fetch_res.stdout.strip()
                return {
                    "success": False,
                    "error": f"Failed to fetch updates from mirror ({mirror_url}): {err_text}"
                }

            # 2. Reset hard to origin/main (ensures clean sync without conflicts)
            subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            # 3. Ensure permissions
            subprocess.run(
                ["chmod", "+x", "phantom"],
                cwd=str(self.base_dir),
                capture_output=True
            )
            for sh_file in (self.base_dir / "scripts").glob("*.sh"):
                os.chmod(sh_file, 0o755)

            # 4. Update pip dependencies if venv exists
            venv_pip = self.base_dir / "venv" / "bin" / "pip"
            req_file = self.base_dir / "requirements.txt"
            if venv_pip.exists() and req_file.exists():
                try:
                    subprocess.run(
                        [str(venv_pip), "install", "-r", str(req_file)],
                        cwd=str(self.base_dir),
                        capture_output=True,
                        timeout=60
                    )
                except Exception as ep:
                    print(f"[SystemManager] Pip update warning: {ep}")

            # 5. Automatically migrate installed apps to LAN port bindings & update firewall rules
            try:
                from .docker_manager import DockerManager
                DockerManager().fix_installed_port_bindings()
            except Exception as em:
                print(f"[SystemManager] Port migration notice: {em}")

            try:
                hardening_script = self.base_dir / "scripts" / "hardening.sh"
                if hardening_script.exists():
                    subprocess.run(["bash", str(hardening_script)], capture_output=True, timeout=15)
            except Exception as eh:
                print(f"[SystemManager] Hardening notice: {eh}")

            try:
                welcome_script = self.base_dir / "scripts" / "phantom-welcome.sh"
                if welcome_script.exists():
                    shutil.copy(str(welcome_script), "/etc/profile.d/phantom-welcome.sh")
                    os.chmod("/etc/profile.d/phantom-welcome.sh", 0o755)
                    hook = "\n# PhantomNode OS Welcome Banner\nif [ -f /etc/profile.d/phantom-welcome.sh ]; then\n    . /etc/profile.d/phantom-welcome.sh\nfi\n"
                    for bashrc_file in ["/etc/bash.bashrc", "/root/.bashrc"]:
                        bp = Path(bashrc_file)
                        if bp.exists():
                            content = bp.read_text(encoding="utf-8", errors="ignore")
                            if "phantom-welcome.sh" not in content:
                                with open(bp, "a", encoding="utf-8") as f:
                                    f.write(hook)
                    for udir in Path("/home").glob("*"):
                        user_bashrc = udir / ".bashrc"
                        if user_bashrc.exists():
                            content = user_bashrc.read_text(encoding="utf-8", errors="ignore")
                            if "phantom-welcome.sh" not in content:
                                with open(user_bashrc, "a", encoding="utf-8") as f:
                                    f.write(hook)
            except Exception as ew:
                print(f"[SystemManager] Welcome banner setup notice: {ew}")

            # 6. Schedule daemon restart in 1.5 seconds so API response finishes cleanly
            restart_cmd = "sleep 1.5 && systemctl restart phantom-dashboard.service"
            subprocess.Popen(["bash", "-c", restart_cmd])

            return {
                "success": True,
                "message": "Update successfully applied! System services are restarting."
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to apply update: {str(e)}"
            }
