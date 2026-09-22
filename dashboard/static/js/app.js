// ==============================================================================
// PhantomNode OS - Sovereign Privacy Dashboard Controller
// ==============================================================================

let currentTab = 'installed';
let appsData = [];

// Reusable SVG Icons for UI Actions
const ICONS = {
    open: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`,
    onion: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path><path d="M2 12h20"></path></svg>`,
    play: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`,
    pause: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>`,
    terminal: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>`,
    trash: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`,
    deploy: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`,
    spinner: `<svg class="btn-icon spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="12"></circle></svg>`
};

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    fetchStatus();
    fetchApps();
    setInterval(fetchStatus, 3000);
    setTimeout(() => checkUpdates(false), 2000);
    setInterval(() => checkUpdates(false), 600000);
});

function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTab = btn.dataset.tab;
            renderApps();
        });
    });
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const data = await res.json();

        // CPU
        document.getElementById('cpu-val').innerText = `${data.cpu_percent}%`;
        document.getElementById('cpu-bar').style.width = `${data.cpu_percent}%`;

        // RAM
        document.getElementById('ram-val').innerText = `${data.memory.used_gb} / ${data.memory.total_gb} GB`;
        document.getElementById('ram-bar').style.width = `${data.memory.percent}%`;

        // Disk
        document.getElementById('disk-val').innerText = `${data.disk.used_gb} / ${data.disk.total_gb} GB`;
        document.getElementById('disk-bar').style.width = `${data.disk.percent}%`;

        // Uptime
        document.getElementById('uptime-val').innerText = data.uptime;

        // Tor Status Badge
        const torDot = document.getElementById('tor-status-dot');
        const torText = document.getElementById('tor-status-text');
        const torBadge = document.getElementById('tor-badge');
        if (data.tor_active) {
            torBadge.className = 'badge badge-green';
            torDot.className = 'status-dot active pulse';
            torText.innerText = 'Tor v3 Active';
        } else {
            torBadge.className = 'badge badge-red';
            torDot.className = 'status-dot inactive';
            torText.innerText = 'Tor Offline';
        }

        // OPSEC Badge
        const opsecText = document.getElementById('opsec-status-text');
        const usbTag = document.getElementById('usb-status-tag');
        if (data.opsec && data.opsec.usb_switch_armed) {
            opsecText.innerText = 'USB Shield: ARMED';
            if (usbTag) {
                usbTag.className = 'tag-badge tag-opsec-1';
                usbTag.innerText = 'ARMED';
            }
        } else {
            opsecText.innerText = 'OPSEC Shield';
            if (usbTag) {
                usbTag.className = 'tag-badge tag-ram';
                usbTag.innerText = 'Disarmed';
            }
        }

    } catch (e) {
        console.error('Telemetry fetch error:', e);
    }
}

async function fetchApps() {
    try {
        const res = await fetch('/api/apps');
        if (!res.ok) return;
        appsData = await res.json();
        updateCounters();
        renderApps();
    } catch (e) {
        console.error('App catalog fetch error:', e);
    }
}

function updateCounters() {
    const installedCount = appsData.filter(a => a.is_installed).length;
    const catalogCount = appsData.filter(a => !a.is_installed).length;

    const elInstalled = document.getElementById('installed-counter');
    const elCatalog = document.getElementById('catalog-counter');
    if (elInstalled) elInstalled.innerText = installedCount;
    if (elCatalog) elCatalog.innerText = catalogCount;
}

function renderApps() {
    const grid = document.getElementById('apps-grid');
    grid.innerHTML = '';

    const filtered = appsData.filter(app => {
        if (currentTab === 'installed') return app.is_installed;
        if (currentTab === 'catalog') return !app.is_installed;
        return true;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 70px 20px; color: var(--text-muted);">
                <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">
                    ${currentTab === 'installed' ? 'No applications deployed yet.' : 'All available privacy tools are deployed!'}
                </div>
                <div style="font-size: 13px;">
                    ${currentTab === 'installed' ? 'Switch to the Privacy App Store tab to deploy sovereign services with one click.' : 'Your sovereign stack is fully configured.'}
                </div>
            </div>
        `;
        return;
    }

    filtered.forEach(app => {
        const card = document.createElement('div');
        card.className = 'app-card';

        const isRunning = app.is_running;
        const statusBadge = app.is_installed
            ? (isRunning 
                ? '<span class="status-badge running"><span class="status-dot active pulse" style="width:6px;height:6px;"></span> Running</span>' 
                : '<span class="status-badge stopped"><span class="status-dot inactive" style="width:6px;height:6px;"></span> Stopped</span>')
            : '';

        let opsecClass = 'tag-opsec-1';
        if (app.opsec_level === 'Level 2') opsecClass = 'tag-opsec-2';
        if (app.opsec_level === 'Level 3') opsecClass = 'tag-opsec-3';

        const actionButtons = app.is_installed ? `
            <button class="btn btn-primary" onclick="openApp('${app.id}', ${app.web_port}, '${app.onion || ''}')">
                ${ICONS.open}
                <span>Open</span>
            </button>
            ${app.onion ? `
            <button class="btn btn-onion" onclick="showOnionModal('${app.name}', '${app.onion}', ${app.onion_port})">
                ${ICONS.onion}
                <span>Tor v3</span>
            </button>` : ''}
            <button class="btn btn-secondary" onclick="toggleAppState('${app.id}', ${isRunning})">
                ${isRunning ? ICONS.pause : ICONS.play}
                <span>${isRunning ? 'Stop' : 'Start'}</span>
            </button>
            <button class="btn btn-secondary" onclick="showLogsModal('${app.id}', '${app.name}')">
                ${ICONS.terminal}
                <span>Logs</span>
            </button>
            <button class="btn btn-danger" onclick="uninstallApp('${app.id}', '${app.name}')" title="Uninstall service">
                ${ICONS.trash}
            </button>
        ` : `
            <button class="btn btn-primary" id="btn-install-${app.id}" onclick="installApp('${app.id}', '${app.name}')" style="width: 100%; justify-content: center;">
                ${ICONS.deploy}
                <span>1-Click Deploy</span>
            </button>
        `;

        const iconHtml = getAppIconHtml(app.icon, app.name);

        card.innerHTML = `
            <div>
                <div class="app-header">
                    <div class="app-icon-wrap">
                        ${iconHtml}
                    </div>
                    <div class="app-meta">
                        <div class="app-name-row">
                            <span class="app-name" title="${app.name}">${app.name}</span>
                            ${statusBadge}
                        </div>
                        <div class="app-cat">${app.category}</div>
                    </div>
                </div>
                <div class="app-tags">
                    <span class="tag-badge ${opsecClass}">${app.opsec_level}</span>
                    <span class="tag-badge tag-ram">${app.memory_mb} MB RAM</span>
                </div>
                <p class="app-desc">${app.description}</p>
            </div>
            <div class="app-actions">
                ${actionButtons}
            </div>
        `;
        grid.appendChild(card);
    });
}

function getAppIconHtml(iconSlug, appName) {
    const localPath = `/static/icons/${iconSlug}.svg`;
    const fallbackCdn = `https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/${iconSlug}.svg`;
    return `<img class="app-icon-img" src="${localPath}" onerror="this.onerror=null;this.src='${fallbackCdn}';" alt="${appName}" loading="lazy">`;
}

async function installApp(appId, appName) {
    const btn = document.getElementById(`btn-install-${appId}`);
    if (btn) {
        btn.innerHTML = `${ICONS.spinner} <span>Deploying container...</span>`;
        btn.disabled = true;
    }

    try {
        showToast(`Deploying ${appName}... Please wait.`, 'info');
        const res = await fetch(`/api/apps/install/${appId}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            showToast(`${appName} deployed successfully!`, 'success');
            await fetchApps();
        } else {
            showToast(`Installation error: ${data.detail || 'Failed to deploy.'}`, 'error');
            if (btn) {
                btn.innerHTML = `${ICONS.deploy} <span>1-Click Deploy</span>`;
                btn.disabled = false;
            }
        }
    } catch (e) {
        showToast('Network error during deployment.', 'error');
        if (btn) {
            btn.innerHTML = `${ICONS.deploy} <span>1-Click Deploy</span>`;
            btn.disabled = false;
        }
    }
}

async function toggleAppState(appId, isRunning) {
    const action = isRunning ? 'stop' : 'start';
    const actionLabel = isRunning ? 'Stopping' : 'Starting';
    showToast(`${actionLabel} ${appId}...`, 'info');

    try {
        const res = await fetch(`/api/apps/${action}/${appId}`, { method: 'POST' });
        if (res.ok) {
            showToast(`${appId} ${isRunning ? 'stopped' : 'started'}.`, 'success');
            await fetchApps();
        } else {
            showToast(`Failed to ${action} ${appId}.`, 'error');
        }
    } catch (e) {
        showToast(`Network error when attempting to ${action} ${appId}.`, 'error');
    }
}

async function uninstallApp(appId, appName) {
    if (!confirm(`Are you sure you want to uninstall ${appName || appId}? This will stop the container and remove its Tor onion service.`)) {
        return;
    }

    showToast(`Removing ${appName || appId}...`, 'info');
    try {
        const res = await fetch(`/api/apps/remove/${appId}`, { method: 'POST' });
        if (res.ok) {
            showToast(`${appName || appId} removed successfully.`, 'success');
            await fetchApps();
        } else {
            showToast(`Failed to remove ${appId}.`, 'error');
        }
    } catch (e) {
        showToast('Network error during removal.', 'error');
    }
}

function openApp(appId, port, onion) {
    const host = window.location.hostname;
    window.open(`http://${host}:${port}`, '_blank');
}

function showOnionModal(appName, onion, port) {
    const modal = document.getElementById('onion-modal');
    document.getElementById('onion-title').innerText = `${appName} – Tor v3 Onion`;
    const fullOnion = port === 80 ? `http://${onion}` : `http://${onion}:${port}`;
    document.getElementById('onion-address').innerText = fullOnion;
    document.getElementById('onion-link').href = fullOnion;

    const qrImg = document.getElementById('onion-qr');
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(fullOnion)}`;

    modal.classList.add('open');
}

function closeOnionModal() {
    document.getElementById('onion-modal').classList.remove('open');
}

function copyOnion() {
    const text = document.getElementById('onion-address').innerText;
    navigator.clipboard.writeText(text);
    showToast('Tor .onion address copied to clipboard!', 'success');
}

async function showLogsModal(appId, appName) {
    const modal = document.getElementById('logs-modal');
    document.getElementById('logs-title').innerText = `${appName} – Container Logs`;
    document.getElementById('logs-content').innerText = 'Streaming logs from Docker daemon...';
    modal.classList.add('open');

    try {
        const res = await fetch(`/api/apps/logs/${appId}`);
        const data = await res.json();
        document.getElementById('logs-content').innerText = data.logs || 'No log entries available.';
    } catch (e) {
        document.getElementById('logs-content').innerText = 'Error fetching container logs.';
    }
}

function closeLogsModal() {
    document.getElementById('logs-modal').classList.remove('open');
}

function showOpsecModal() {
    document.getElementById('opsec-modal').classList.add('open');
}

function closeOpsecModal() {
    document.getElementById('opsec-modal').classList.remove('open');
}

function handleBackdropClick(event, modalId) {
    if (event.target.id === modalId) {
        document.getElementById(modalId).classList.remove('open');
    }
}

async function toggleUsb(arm) {
    try {
        const res = await fetch('/api/opsec/usb', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ arm })
        });
        const data = await res.json();
        showToast(arm ? 'USB Dead Man\'s Switch Armed!' : 'USB Dead Man\'s Switch Disarmed.', arm ? 'success' : 'info');
        fetchStatus();
    } catch (e) {
        showToast('Error configuring OPSEC USB switch.', 'error');
    }
}

async function triggerPanic() {
    if (!confirm('CRITICAL WARNING!\n\nThis will instantly purge RAM caches (/proc/sys/vm/drop_caches) and execute a FORCED HARD SHUTDOWN to defeat live physical forensic extraction.\n\nAre you sure you want to proceed?')) {
        return;
    }

    try {
        showToast('INITIATING EMERGENCY SHUTDOWN...', 'error');
        await fetch('/api/opsec/panic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'poweroff', confirm: true })
        });
    } catch (e) {
        showToast('Emergency trigger issued.', 'error');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.25s ease';
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

// ==============================================================================
// 1-Click System OTA Update Mechanism
// ==============================================================================

function showUpdateModal() {
    const modal = document.getElementById('update-modal');
    modal.classList.add('open');
    checkUpdates(true);
}

function closeUpdateModal() {
    document.getElementById('update-modal').classList.remove('open');
}

async function checkUpdates(manual = false) {
    const statusMsg = document.getElementById('update-status-msg');
    const remoteVer = document.getElementById('update-remote-ver');
    const changelogWrap = document.getElementById('update-changelog-wrap');
    const changelog = document.getElementById('update-changelog');
    const applyBtn = document.getElementById('btn-apply-update');
    const badgeText = document.getElementById('update-badge-text');

    if (manual && statusMsg) {
        statusMsg.innerText = 'Connecting to upstream GitHub repository...';
    }

    try {
        const res = await fetch('/api/system/update');
        if (!res.ok) throw new Error('API request failed');
        const data = await res.json();

        if (document.getElementById('update-current-ver')) {
            document.getElementById('update-current-ver').innerText = `v${data.current_version} (${data.current_commit || ''})`;
        }
        if (remoteVer) {
            remoteVer.innerText = data.remote_commit ? `origin/main (${data.remote_commit})` : 'online';
        }

        if (data.update_available) {
            if (badgeText) {
                badgeText.innerHTML = `<span class="status-dot active" style="background:#f59e0b;box-shadow:0 0 8px #f59e0b"></span> Update Ready`;
            }
            if (statusMsg) {
                statusMsg.innerHTML = `<strong style="color:var(--accent-amber);">${data.commits_behind} new update(s) available from GitHub.</strong>`;
            }
            if (changelogWrap && changelog && data.changelog && data.changelog.length > 0) {
                changelogWrap.style.display = 'block';
                changelog.innerHTML = data.changelog.map(c => `
                    <div style="margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color:var(--accent-cyan); font-weight:bold;">${c.hash}</span>: ${c.subject} <span style="color:var(--text-dim); font-size:11px;">(${c.time})</span>
                    </div>
                `).join('');
            }
            if (applyBtn) {
                applyBtn.style.display = 'inline-flex';
            }
            if (manual) {
                showToast(`${data.commits_behind} update(s) ready to install.`, 'info');
            }
        } else {
            if (badgeText) {
                badgeText.innerText = `v${data.current_version}`;
            }
            if (statusMsg) {
                statusMsg.innerText = 'PhantomNode OS is completely up to date.';
            }
            if (changelogWrap) changelogWrap.style.display = 'none';
            if (applyBtn) applyBtn.style.display = 'none';
            if (manual) {
                showToast('Your system is up to date.', 'success');
            }
        }
    } catch (e) {
        if (statusMsg) {
            statusMsg.innerText = 'Could not verify updates (offline or network error).';
        }
        if (manual) {
            showToast('Unable to check for updates.', 'error');
        }
    }
}

async function applySystemUpdate() {
    const applyBtn = document.getElementById('btn-apply-update');
    const statusMsg = document.getElementById('update-status-msg');

    if (applyBtn) {
        applyBtn.innerHTML = `${ICONS.spinner} <span>Applying Update...</span>`;
        applyBtn.disabled = true;
    }
    if (statusMsg) {
        statusMsg.innerHTML = '<span style="color:var(--accent-cyan);">Pulling latest components, updating dependencies, and restarting daemon...</span>';
    }

    showToast('Applying PhantomNode OS update...', 'info');

    try {
        const res = await fetch('/api/system/update', { method: 'POST' });
        const data = await res.json();

        if (res.ok) {
            showToast('Update installed! Waiting for daemon reload...', 'success');
            if (statusMsg) {
                statusMsg.innerHTML = '<span style="color:var(--accent-green); font-weight:bold;">Update installed successfully! Reconnecting in 3s...</span>';
            }

            // Poll for server reboot
            let retries = 0;
            const pollInterval = setInterval(async () => {
                retries++;
                try {
                    const check = await fetch('/api/status', { cache: 'no-store' });
                    if (check.ok) {
                        clearInterval(pollInterval);
                        showToast('Reconnected! Refreshing dashboard...', 'success');
                        setTimeout(() => window.location.reload(), 1000);
                    }
                } catch (_) {
                    if (retries > 30) {
                        clearInterval(pollInterval);
                        if (statusMsg) statusMsg.innerText = 'Please refresh the page manually.';
                    }
                }
            }, 1500);

        } else {
            showToast(`Update failed: ${data.detail || 'Error'}`, 'error');
            if (applyBtn) {
                applyBtn.innerHTML = `${ICONS.deploy} <span>Update System Now</span>`;
                applyBtn.disabled = false;
            }
        }
    } catch (e) {
        // Since the server restarts, fetch might drop network
        showToast('System is restarting with new updates. Reconnecting...', 'info');
        setTimeout(() => window.location.reload(), 4000);
    }
}
