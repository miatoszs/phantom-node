import os
import shutil
import time
from typing import Optional, Union, Dict
import psutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import BASE_DIR, SESSION_TTL_SECONDS
from core.auth_manager import AuthManager
from core import audit_log, opsec_score
from core.docker_manager import DockerManager, is_valid_app_id
from core.tor_manager import TorManager
from core.opsec_manager import OpsecManager
from core.system_manager import SystemManager

# Interactive API docs are disabled: they would advertise every privileged endpoint
app = FastAPI(title="PhantomNode OS Dashboard", version="1.2.0", docs_url=None, redoc_url=None, openapi_url=None)

# Setup static files and templates
STATIC_DIR = BASE_DIR / "dashboard" / "static"
TEMPLATES_DIR = BASE_DIR / "dashboard" / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Managers
docker_mgr = DockerManager()
tor_mgr = TorManager()
opsec_mgr = OpsecManager()
system_mgr = SystemManager()
auth_mgr = AuthManager()
auth_mgr.ensure_initialized()

SESSION_COOKIE = "phantom_session"
PUBLIC_PATHS = {"/login", "/api/auth/login"}
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

def _client(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    # Tor delivers onion traffic from loopback, so label it instead of showing 127.0.0.1
    return "tor/localhost" if host in ("127.0.0.1", "::1") else host

@app.middleware("http")
async def require_session(request: Request, call_next):
    """Every page and API call requires a valid session, except the login flow and static assets."""
    path = request.url.path
    if path.startswith("/static/") or path in PUBLIC_PATHS:
        authed = True
    else:
        authed = auth_mgr.validate_session(request.cookies.get(SESSION_COOKIE))

    if not authed:
        if path.startswith("/api/"):
            response = JSONResponse({"detail": "Authentication required."}, status_code=401)
        else:
            response = RedirectResponse("/login", status_code=303)
    elif request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("x-phantom-request") != "1":
        # CSRF guard on top of SameSite=Strict: cross-site forms cannot set custom headers
        response = JSONResponse({"detail": "Missing request header."}, status_code=403)
    else:
        response = await call_next(request)
        # Audit every privileged (state-changing) call; login events are recorded in the handler
        if request.method == "POST" and path.startswith("/api/") and not path.startswith("/api/auth/"):
            audit_log.record("api", _client(request), method=request.method, path=path, status=response.status_code)

    if not path.startswith("/static/"):
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
    return response

# Ensure public Tor onion cache is populated on startup
try:
    tor_mgr.sync_onion_cache()
except Exception:
    pass

START_TIME = time.time()

def _safe_service(service_id: str) -> str:
    if service_id != "dashboard" and not is_valid_app_id(service_id):
        raise HTTPException(status_code=400, detail="Invalid service id.")
    return service_id

class PanicRequest(BaseModel):
    mode: str = "poweroff"
    confirm: bool

class UsbToggleRequest(BaseModel):
    arm: bool

class LoginRequest(BaseModel):
    password: str
    code: Optional[str] = None

class ClientAuthRequest(BaseModel):
    name: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class AppInstallRequest(BaseModel):
    web_port: Optional[int] = None
    onion_port: Optional[int] = None
    extra_ports: Optional[Dict[str, int]] = None
    custom_env: Optional[Union[Dict[str, str], str]] = None

@app.get("/login", response_class=FileResponse)
async def login_page(request: Request):
    if auth_mgr.validate_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse("/", status_code=303)
    return FileResponse(TEMPLATES_DIR / "login.html", media_type="text/html")

@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    client = _client(request)
    locked, retry_after = auth_mgr.is_locked_out(client)
    if locked:
        raise HTTPException(status_code=429, detail=f"Too many failed attempts. Try again in {retry_after}s.")
    if not auth_mgr.verify_password(req.password):
        auth_mgr.record_failure(client)
        audit_log.record("login_failed", client, reason="password")
        raise HTTPException(status_code=401, detail="Incorrect password.")
    if auth_mgr.totp_enabled():
        if not req.code:
            # Password was right; ask the client for the second factor without counting a failure
            return JSONResponse({"detail": "Enter the 6-digit code from your authenticator app.", "totp_required": True}, status_code=401)
        if not auth_mgr.verify_totp(req.code):
            auth_mgr.record_failure(client)
            audit_log.record("login_failed", client, reason="totp")
            return JSONResponse({"detail": "Invalid or already used authentication code.", "totp_required": True}, status_code=401)
    auth_mgr.clear_failures(client)
    audit_log.record("login", client)
    response = JSONResponse({"success": True})
    # No Secure flag: the dashboard is served over plain HTTP on the LAN and over .onion
    response.set_cookie(
        SESSION_COOKIE, auth_mgr.create_session(),
        max_age=SESSION_TTL_SECONDS, httponly=True, samesite="strict", path="/"
    )
    return response

@app.post("/api/auth/logout")
async def logout():
    response = JSONResponse({"success": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response

@app.post("/api/auth/password")
def change_password(req: PasswordChangeRequest, request: Request):
    audit_log.record("password_change", _client(request))
    if not auth_mgr.verify_password(req.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    res = auth_mgr.set_password(req.new_password)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.get("/", response_class=FileResponse)
async def index():
    """Renders the main CasaOS-style PhantomNode Dashboard."""
    index_file = TEMPLATES_DIR / "index.html"
    return FileResponse(index_file, media_type="text/html")

@app.get("/api/status")
async def get_system_status():
    """Returns current hardware, Tor and OPSEC telemetry."""
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime_sec = int(time.time() - psutil.boot_time())

    tor_active = tor_mgr.is_tor_active()
    opsec_status = opsec_mgr.get_opsec_status()

    # Get Master Dashboard Onion address
    dashboard_onion = tor_mgr.get_onion_address("dashboard")

    return {
        "cpu_percent": cpu_percent,
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent
        },
        "uptime": f"{uptime_sec // 3600}h {(uptime_sec % 3600) // 60}m",
        "tor_active": tor_active,
        "dashboard_onion": dashboard_onion,
        "opsec": opsec_status,
        "version": system_mgr.version
    }

@app.get("/api/apps")
async def list_apps():
    """Returns all catalog apps with live installation and Tor status."""
    return docker_mgr.list_available_apps()

@app.post("/api/apps/install/{app_id}")
async def install_app(app_id: str, req: Optional[AppInstallRequest] = None):
    """Installs and launches a privacy app stack with optional advanced config."""
    config_dict = req.dict(exclude_none=True) if req else None
    res = docker_mgr.install_app(app_id, custom_config=config_dict)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Installation failed."))
    return res

@app.post("/api/apps/start/{app_id}")
async def start_app(app_id: str):
    res = docker_mgr.start_app(app_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to start app."))
    return res

@app.post("/api/apps/stop/{app_id}")
async def stop_app(app_id: str):
    res = docker_mgr.stop_app(app_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to stop app."))
    return res

@app.post("/api/apps/restart/{app_id}")
async def restart_app(app_id: str):
    res = docker_mgr.restart_app(app_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to restart app."))
    return res

@app.post("/api/apps/remove/{app_id}")
async def remove_app(app_id: str):
    res = docker_mgr.remove_app(app_id, purge_volumes=False)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to remove app."))
    return res

@app.post("/api/apps/update/{app_id}")
async def update_app(app_id: str):
    """Pulls the latest container image and restarts the app stack."""
    res = docker_mgr.update_app(app_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to update container."))
    return res

@app.post("/api/apps/update-all")
async def update_all_apps():
    """Pulls the latest images and restarts all installed apps."""
    return docker_mgr.update_all_apps()

@app.get("/api/apps/logs/{app_id}")
async def get_app_logs(app_id: str, lines: int = 100):
    lines = max(1, min(lines, 2000))
    logs = docker_mgr.get_logs(app_id, lines=lines)
    return {"app_id": app_id, "logs": logs}

@app.get("/api/qr")
async def qr_code(data: str):
    """Renders a QR code locally as SVG (keeps onion addresses away from third-party QR APIs)."""
    import io
    import segno
    if len(data) > 512:
        raise HTTPException(status_code=400, detail="QR payload too long.")
    buf = io.BytesIO()
    segno.make(data, error="m").save(buf, kind="svg", scale=5, border=2, dark="#000000", light="#ffffff")
    return Response(buf.getvalue(), media_type="image/svg+xml")

@app.get("/api/tor/services")
async def list_tor_services():
    """Lists all configured Tor v3 Hidden Services."""
    return tor_mgr.list_services()

@app.get("/api/tor/auth/{service_id}")
async def list_client_auth(service_id: str):
    """Lists Tor v3 authorized clients (device names) for a hidden service."""
    return {"service_id": service_id, "clients": tor_mgr.list_client_auth(_safe_service(service_id))}

@app.post("/api/tor/auth/{service_id}")
async def add_client_auth(service_id: str, req: ClientAuthRequest):
    """Authorizes a new client device; the private key is returned exactly once."""
    res = tor_mgr.add_client_auth(_safe_service(service_id), req.name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.post("/api/tor/auth/{service_id}/remove")
async def remove_client_auth(service_id: str, req: ClientAuthRequest):
    res = tor_mgr.remove_client_auth(_safe_service(service_id), req.name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.get("/api/opsec/score")
def get_opsec_score():
    """Grades the node against OPSEC levels 1-3 with a fix command for each failing check."""
    return opsec_score.build_report(auth_mgr, tor_mgr, opsec_mgr, system_mgr)

@app.get("/api/audit")
async def get_audit_log(lines: int = 50):
    """Most recent privileged actions and login attempts, newest first."""
    return audit_log.tail(max(1, min(lines, 500)))

@app.post("/api/opsec/usb")
async def toggle_usb_shield(req: UsbToggleRequest):
    """Arms or disarms the USB Dead Man's Switch."""
    return opsec_mgr.set_usb_switch(req.arm)

@app.post("/api/opsec/panic")
async def trigger_panic(req: PanicRequest):
    """Emergency Panic Button execution."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Panic trigger confirmation required.")
    res = opsec_mgr.trigger_panic(req.mode)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.get("/api/system/update")
async def check_system_update():
    """Checks remote repository for upstream updates."""
    return system_mgr.check_for_updates()

@app.post("/api/system/update")
async def apply_system_update():
    """Applies upstream updates and triggers daemon reload."""
    res = system_mgr.apply_update()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Update application failed."))
    return res

class MirrorRequest(BaseModel):
    mirror_url: str

@app.get("/api/system/mirror")
async def get_system_mirror():
    """Returns current update mirror configuration."""
    mirror_url = system_mgr.get_mirror_url()
    return {
        "success": True,
        "mirror_url": mirror_url,
        "default_url": system_mgr.default_repo_url,
        "is_onion": system_mgr.is_onion_url(mirror_url),
        "is_custom": (mirror_url != system_mgr.default_repo_url)
    }

@app.post("/api/system/mirror")
async def set_system_mirror(req: MirrorRequest):
    """Sets a custom git mirror URL (supports Tor .onion and Clearnet)."""
    res = system_mgr.set_mirror_url(req.mirror_url)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to update mirror."))
    return res

@app.post("/api/system/mirror/reset")
async def reset_system_mirror():
    """Resets the update mirror to the official GitHub repository."""
    return system_mgr.reset_mirror_url()
