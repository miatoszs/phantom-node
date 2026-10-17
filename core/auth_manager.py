import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import time
from typing import Dict, Optional, Tuple

from .config import AUTH_FILE, INITIAL_PASSWORD_FILE, SESSION_TTL_SECONDS

# scrypt parameters (~16 MB RAM per hash, fast enough for a single admin login)
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_MIN_PASSWORD_LEN = 10

# Login throttling: max failures per client inside the window before lockout
_MAX_FAILURES = 5
_FAILURE_WINDOW = 300


class AuthManager:
    """Single-admin authentication for the dashboard: scrypt password hash + HMAC-signed session tokens."""

    def __init__(self):
        self.auth_file = AUTH_FILE
        self.initial_password_file = INITIAL_PASSWORD_FILE
        self.session_ttl = SESSION_TTL_SECONDS
        self._failures: Dict[str, list] = {}
        self._mtime = 0.0
        self._data = self._load()

    # ------------------------------------------------------------------ storage

    def _load(self) -> Optional[Dict]:
        try:
            if self.auth_file.exists():
                self._mtime = self.auth_file.stat().st_mtime
                return json.loads(self.auth_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[AuthManager] Could not read {self.auth_file}: {e}")
        return None

    def _write_private(self, path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(path, 0o600)

    def _save(self, data: Dict):
        self._write_private(self.auth_file, json.dumps(data))
        self._data = data

    def _refresh(self):
        """Picks up password changes made by the CLI while the dashboard is running."""
        try:
            if self.auth_file.exists() and self.auth_file.stat().st_mtime != self._mtime:
                self._data = self._load()
        except OSError:
            pass

    def is_configured(self) -> bool:
        self._refresh()
        return bool(self._data and self._data.get("hash"))

    def ensure_initialized(self) -> Optional[str]:
        """
        Creates admin credentials on first run. Returns the generated password if one was
        created (it is also stored in a root-only file so the operator can read it via the CLI).
        """
        if self.is_configured():
            return None
        password = secrets.token_urlsafe(12)
        self.set_password(password, keep_initial_file=True)
        try:
            self._write_private(self.initial_password_file, password + "\n")
        except Exception as e:
            print(f"[AuthManager] Could not store initial password: {e}")
        print("[AuthManager] Generated initial dashboard password. Read it with: sudo phantom password show")
        return password

    # ---------------------------------------------------------------- passwords

    @staticmethod
    def _hash(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
        )

    def set_password(self, password: str, keep_initial_file: bool = False) -> Dict:
        if len(password) < _MIN_PASSWORD_LEN:
            return {"success": False, "error": f"Password must be at least {_MIN_PASSWORD_LEN} characters."}
        salt = secrets.token_bytes(16)
        # Keep 2FA settings across password changes
        data = {k: v for k, v in (self._data or {}).items() if k.startswith("totp_")}
        data.update({
            "salt": base64.b64encode(salt).decode(),
            "hash": base64.b64encode(self._hash(password, salt)).decode(),
            # Rotating the signing key on every password change invalidates all existing sessions
            "session_key": secrets.token_hex(32),
            "updated": int(time.time()),
        })
        self._save(data)
        if not keep_initial_file and self.initial_password_file.exists():
            try:
                self.initial_password_file.unlink()
            except Exception:
                pass
        return {"success": True, "message": "Dashboard password updated. All existing sessions were signed out."}

    def verify_password(self, password: str) -> bool:
        if not self.is_configured():
            return False
        try:
            salt = base64.b64decode(self._data["salt"])
            expected = base64.b64decode(self._data["hash"])
            return hmac.compare_digest(self._hash(password, salt), expected)
        except Exception:
            return False

    def get_initial_password(self) -> Optional[str]:
        try:
            if self.initial_password_file.exists():
                return self.initial_password_file.read_text(encoding="utf-8").strip() or None
        except Exception:
            pass
        return None

    # --------------------------------------------------------------------- TOTP
    # RFC 6238 (SHA1, 6 digits, 30 s) - compatible with Aegis, 2FAS, KeePassXC, etc.

    def totp_enabled(self) -> bool:
        return self.is_configured() and bool(self._data.get("totp_secret"))

    @staticmethod
    def _totp_code(secret_b32: str, counter: int) -> str:
        key = base64.b32decode(secret_b32 + "=" * (-len(secret_b32) % 8))
        digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        return f"{value % 1_000_000:06d}"

    def _match_totp(self, secret: str, code: str, last_counter: int = -1) -> Optional[int]:
        code = (code or "").strip().replace(" ", "")
        if not (len(code) == 6 and code.isdigit()):
            return None
        now = int(time.time() // 30)
        for counter in (now - 1, now, now + 1):
            # Refuse to accept the same (or an older) code twice: blocks replay of an observed code
            if counter > last_counter and hmac.compare_digest(self._totp_code(secret, counter), code):
                return counter
        return None

    def verify_totp(self, code: str) -> bool:
        if not self.totp_enabled():
            return True
        counter = self._match_totp(self._data["totp_secret"], code, self._data.get("totp_last_counter", -1))
        if counter is None:
            return False
        data = dict(self._data)
        data["totp_last_counter"] = counter
        self._save(data)
        return True

    def begin_totp_setup(self, issuer: str = "PhantomNode") -> Dict:
        secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
        uri = f"otpauth://totp/{issuer}:admin?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
        return {"secret": secret, "uri": uri}

    def enable_totp(self, secret: str, code: str) -> Dict:
        if self._match_totp(secret, code) is None:
            return {"success": False, "error": "Code did not match. Check the authenticator app and the server clock."}
        data = dict(self._data)
        data["totp_secret"] = secret
        data["totp_last_counter"] = -1
        self._save(data)
        return {"success": True, "message": "Two-factor login enabled."}

    def disable_totp(self) -> Dict:
        data = {k: v for k, v in (self._data or {}).items() if not k.startswith("totp_")}
        self._save(data)
        return {"success": True, "message": "Two-factor login disabled."}

    # ----------------------------------------------------------------- throttle

    def is_locked_out(self, client: str) -> Tuple[bool, int]:
        now = time.time()
        recent = [t for t in self._failures.get(client, []) if now - t < _FAILURE_WINDOW]
        self._failures[client] = recent
        if len(recent) >= _MAX_FAILURES:
            return True, int(_FAILURE_WINDOW - (now - recent[0])) + 1
        return False, 0

    def record_failure(self, client: str):
        self._failures.setdefault(client, []).append(time.time())

    def clear_failures(self, client: str):
        self._failures.pop(client, None)

    # ----------------------------------------------------------------- sessions

    def _sign(self, payload: str) -> str:
        key = bytes.fromhex(self._data["session_key"])
        return hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()

    def create_session(self) -> str:
        expires = int(time.time()) + self.session_ttl
        payload = f"{expires}.{secrets.token_hex(8)}"
        return f"{payload}.{self._sign(payload)}"

    def validate_session(self, token: Optional[str]) -> bool:
        if not token or not self.is_configured():
            return False
        try:
            expires, nonce, sig = token.split(".")
            if int(expires) < time.time():
                return False
            return hmac.compare_digest(sig, self._sign(f"{expires}.{nonce}"))
        except Exception:
            return False
