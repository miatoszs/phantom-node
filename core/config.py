import os
from pathlib import Path

# Base paths & Version
PHANTOM_VERSION = "1.1.0"
DEFAULT_REPO_URL = "https://github.com/miatoszs/phantom-node.git"
GITHUB_REPO_URL = DEFAULT_REPO_URL
BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / "apps"
DATA_DIR = Path(os.environ.get("PHANTOM_DATA_DIR", "/var/lib/phantom-node"))
INSTALLED_APPS_DIR = DATA_DIR / "installed_apps"
SCRIPTS_DIR = BASE_DIR / "scripts"
UPDATE_MIRROR_FILE = DATA_DIR / "update_mirror.txt"
ONION_CACHE_DIR = DATA_DIR / "onions"

# Tor configurations
TORRC_FILE = Path("/etc/tor/torrc")
TORRC_DIR = Path("/etc/tor/torrc.d")
TOR_DATA_DIR = Path("/var/lib/tor")
TOR_PHANTOM_HS_DIR = TOR_DATA_DIR / "phantom_services"
TOR_SOCKS_PORT = int(os.environ.get("TOR_SOCKS_PORT", 9050))

# Web dashboard settings
DASHBOARD_HOST = os.environ.get("PHANTOM_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.environ.get("PHANTOM_PORT", 7426))
SECRET_KEY = os.environ.get("PHANTOM_SECRET_KEY", "phantom-node-super-secret-key-change-me")

# Ensure required runtime directories exist if writable
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INSTALLED_APPS_DIR.mkdir(parents=True, exist_ok=True)
    ONION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        os.chmod(DATA_DIR, 0o755)
        os.chmod(INSTALLED_APPS_DIR, 0o755)
        os.chmod(ONION_CACHE_DIR, 0o755)
except Exception:
    pass
