import json
import os
import time
from collections import deque
from typing import Dict, List

from .config import AUDIT_LOG_FILE

# Rotate once the log grows past this size, keeping one previous file
_MAX_BYTES = 2 * 1024 * 1024


def record(event: str, client: str = "local", **details):
    """Appends one privileged action to the root-only audit log (JSON lines)."""
    entry = {"ts": int(time.time()), "event": event, "client": client}
    entry.update({k: v for k, v in details.items() if v is not None})
    try:
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if AUDIT_LOG_FILE.exists() and AUDIT_LOG_FILE.stat().st_size > _MAX_BYTES:
            AUDIT_LOG_FILE.replace(AUDIT_LOG_FILE.with_suffix(".log.1"))
        fd = os.open(str(AUDIT_LOG_FILE), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[Audit] Could not write audit log: {e}")


def tail(lines: int = 50) -> List[Dict]:
    """Returns the newest entries first."""
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            last = deque(f, maxlen=lines)
    except FileNotFoundError:
        return []
    entries = []
    for line in reversed(last):
        try:
            entries.append(json.loads(line))
        except ValueError:
            continue
    return entries
