import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from .config import BASE_DIR, PHANTOM_VERSION, GITHUB_REPO_URL

class SystemManager:
    """Manages PhantomNode OS updates, versions, and system lifecycle."""

    def __init__(self):
        self.base_dir = BASE_DIR
        self.version = PHANTOM_VERSION
        self.repo_url = GITHUB_REPO_URL

    def _ensure_git_repo(self) -> bool:
        """Ensures that base_dir has an initialized git repository tracking origin."""
        git_dir = self.base_dir / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(["git", "init", "-b", "main"], cwd=str(self.base_dir), check=True, capture_output=True)
                subprocess.run(["git", "remote", "add", "origin", self.repo_url], cwd=str(self.base_dir), check=True, capture_output=True)
                return True
            except Exception as e:
                print(f"[SystemManager] Git init error: {e}")
                return False
        return True

    def check_for_updates(self) -> Dict:
        """
        Fetches upstream repository metadata and compares local commit with origin/main.
        Returns whether an update is available along with commit logs.
        """
        self._ensure_git_repo()

        try:
            # 1. Fetch remote origin with a 12s timeout
            fetch_res = subprocess.run(
                ["git", "fetch", "origin", "main"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=15
            )

            # 2. Get local HEAD commit
            local_commit_res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=5
            )
            local_commit = local_commit_res.stdout.strip() if local_commit_res.returncode == 0 else "unknown"

            # 3. Get remote origin/main commit
            remote_commit_res = subprocess.run(
                ["git", "rev-parse", "--short", "origin/main"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=5
            )
            remote_commit = remote_commit_res.stdout.strip() if remote_commit_res.returncode == 0 else local_commit

            # 4. Count commits behind
            count_res = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=5
            )
            commits_behind = int(count_res.stdout.strip()) if count_res.returncode == 0 and count_res.stdout.strip().isdigit() else 0

            # 5. Extract changelog (last 8 commits)
            changelog = []
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
                "update_available": commits_behind > 0,
                "current_version": self.version,
                "current_commit": local_commit,
                "remote_commit": remote_commit,
                "commits_behind": commits_behind,
                "changelog": changelog
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "update_available": False,
                "current_version": self.version,
                "error": "Update check timed out. Verify network connection."
            }
        except Exception as e:
            return {
                "success": False,
                "update_available": False,
                "current_version": self.version,
                "error": str(e)
            }

    def apply_update(self) -> Dict:
        """
        Pulls latest code from origin/main, updates dependencies, and schedules service restart.
        """
        self._ensure_git_repo()

        try:
            # 1. Fetch latest
            subprocess.run(
                ["git", "fetch", "origin", "main"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

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

            # 5. Schedule daemon restart in 1.5 seconds so API response finishes cleanly
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
