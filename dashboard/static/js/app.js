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
    settings: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
    refresh: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>`,
    info: `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
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
            updateCounters();
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

    const updateAllBtnContainer = document.getElementById('installed-actions');
    if (updateAllBtnContainer) {
        updateAllBtnContainer.style.display = (currentTab === 'installed' && installedCount > 0) ? 'flex' : 'none';
    }
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

        let portsPreviewHtml = '';
        if (app.is_installed) {
            const chips = [];
            if (app.web_port) {
                const label = app.web_port_label || 'Web UI';
                chips.push(`<span class="port-chip primary" title="${label}: ${app.web_port}">:${app.web_port} <span style="opacity:0.75;font-size:9px;">(${label})</span></span>`);
            }
            if (app.extra_ports && Array.isArray(app.extra_ports)) {
                app.extra_ports.forEach(ep => {
                    const portVal = ep.port || ep.default;
                    if (portVal) {
                        const proto = (ep.protocol || 'tcp').toUpperCase();
                        chips.push(`<span class="port-chip" title="${ep.label || ep.key}: ${portVal} (${proto})">:${portVal} <span style="opacity:0.75;font-size:9px;">(${ep.label || ep.key})</span></span>`);
                    }
                });
            }
            if (chips.length > 0) {
                portsPreviewHtml = `
                    <div class="app-ports-preview" onclick="showAppInfoModal('${app.id}')" title="Click to view detailed network endpoints & client configuration">
                        <div class="ports-preview-header">
                            <span>Network Ports</span>
                            <span style="font-size:10px;color:var(--accent-cyan);text-transform:none;font-weight:600;">Details &rarr;</span>
                        </div>
                        <div class="ports-chips-wrap">
                            ${chips.join('')}
                        </div>
                    </div>
                `;
            }
        }

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
            <button class="btn btn-secondary" onclick="showAppInfoModal('${app.id}')" title="App Information & Network Ports">
                ${ICONS.info}
                <span>Info</span>
            </button>
            <button class="btn btn-secondary" onclick="toggleAppState('${app.id}', ${isRunning})">
                ${isRunning ? ICONS.pause : ICONS.play}
                <span>${isRunning ? 'Stop' : 'Start'}</span>
            </button>
            <button class="btn btn-secondary" id="btn-update-${app.id}" onclick="updateApp('${app.id}', '${app.name}')" title="Pull latest Docker image & restart container">
                ${ICONS.refresh}
                <span>Update</span>
            </button>
            <button class="btn btn-secondary" onclick="showLogsModal('${app.id}', '${app.name}')">
                ${ICONS.terminal}
                <span>Logs</span>
            </button>
            <button class="btn btn-danger" onclick="uninstallApp('${app.id}', '${app.name}')" title="Uninstall service">
                ${ICONS.trash}
            </button>
        ` : `
            <div style="display: flex; gap: 8px; width: 100%;">
                <button class="btn btn-primary" id="btn-install-${app.id}" onclick="installApp('${app.id}', '${app.name}')" style="flex: 1; justify-content: center;">
                    ${ICONS.deploy}
                    <span>1-Click Deploy</span>
                </button>
                <button class="btn btn-secondary" onclick="openAdvancedInstallModal('${app.id}', '${app.name}', ${app.web_port || 80}, ${app.onion_port || 80})" title="Advanced Custom Settings" style="padding: 0 12px; display: inline-flex; align-items: center; justify-content: center;">
                    ${ICONS.settings}
                </button>
            </div>
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
                ${portsPreviewHtml}
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
            if (data.port_reallocated) {
                showToast(`${appName} deployed! Auto-assigned to free port ${data.web_port}.`, 'success');
            } else {
                showToast(`${appName} deployed successfully!`, 'success');
            }
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

async function updateApp(appId, appName) {
    const btn = document.getElementById(`btn-update-${appId}`);
    if (btn) {
        btn.innerHTML = `${ICONS.spinner} <span>Updating...</span>`;
        btn.disabled = true;
    }

    showToast(`Pulling latest Docker image for ${appName || appId}...`, 'info');

    try {
        const res = await fetch(`/api/apps/update/${appId}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            showToast(`${appName || appId} updated to latest image!`, 'success');
            await fetchApps();
        } else {
            showToast(`Update error: ${data.detail || data.error || 'Failed to update.'}`, 'error');
            if (btn) {
                btn.innerHTML = `${ICONS.refresh} <span>Update</span>`;
                btn.disabled = false;
            }
        }
    } catch (e) {
        showToast(`Network error while updating ${appName || appId}.`, 'error');
        if (btn) {
            btn.innerHTML = `${ICONS.refresh} <span>Update</span>`;
            btn.disabled = false;
        }
    }
}

async function updateAllApps() {
    const btn = document.getElementById('btn-update-all-apps');
    if (btn) {
        btn.innerHTML = `${ICONS.spinner} <span>Updating Containers...</span>`;
        btn.disabled = true;
    }

    showToast('Pulling latest Docker images for all installed apps...', 'info');

    try {
        const res = await fetch('/api/apps/update-all', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            showToast(`Updated ${data.updated}/${data.total} containers successfully!`, 'success');
            await fetchApps();
        } else {
            showToast(`Failed to update containers: ${data.detail || 'Error'}`, 'error');
        }
    } catch (e) {
        showToast('Network error while updating containers.', 'error');
    } finally {
        if (btn) {
            btn.innerHTML = `
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>Update All Containers</span>
            `;
            btn.disabled = false;
        }
    }
}

function openApp(appId, port, onion) {
    const host = window.location.hostname;
    if (host.endsWith('.onion')) {
        if (onion) {
            window.open(`http://${onion}`, '_blank');
        } else {
            showToast('Tor onion address not available for this app yet.', 'warning');
        }
    } else {
        window.open(`http://${host}:${port}`, '_blank');
    }
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
        let data = {};
        try {
            data = await res.json();
        } catch (_) {}

        if (!res.ok || data.success === false) {
            const errMsg = data.error || data.detail || (res.status === 404 ? 'Update API endpoint not found. Please restart phantom-dashboard service.' : 'Failed to verify updates with GitHub.');
            if (statusMsg) {
                statusMsg.innerHTML = `<span style="color:var(--accent-red);">${errMsg}</span>`;
            }
            if (remoteVer) {
                remoteVer.innerText = 'offline';
            }
            if (manual) {
                showToast(errMsg, 'error');
            }
            return;
        }

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
            statusMsg.innerText = e.message || 'Could not verify updates (network error).';
        }
        if (remoteVer) {
            remoteVer.innerText = 'error';
        }
        if (manual) {
            showToast('Unable to check for updates: ' + (e.message || 'Network error'), 'error');
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

// ==============================================================================
// Advanced App Deployment Modal Handlers
// ==============================================================================

function openAdvancedInstallModal(appId, appName, defWebPort, defOnionPort) {
    const modal = document.getElementById('advanced-install-modal');
    if (!modal) return;

    const app = appsData.find(a => a.id === appId);

    document.getElementById('adv-app-id').value = appId;
    document.getElementById('adv-install-title').innerText = `${appName} – Advanced Deployment`;
    document.getElementById('adv-install-subtitle').innerText = `Configure port routing, Tor onion bindings, and custom environment variables for ${appName}.`;

    // Dynamic label for web port if specified (e.g. Dashboard Web Port vs Web Admin Console Port)
    const webPortLabel = document.getElementById('adv-web-port-label');
    if (webPortLabel) {
        webPortLabel.innerText = (app && app.web_port_label) ? app.web_port_label.toUpperCase() : 'LOCAL WEB PORT';
    }

    const effectiveWebPort = (app && app.suggested_web_port) ? app.suggested_web_port : (defWebPort || 80);
    document.getElementById('adv-web-port').value = effectiveWebPort;
    document.getElementById('adv-onion-port').value = defOnionPort || 80;
    document.getElementById('adv-env-vars').value = '';

    const webPortHint = document.getElementById('adv-web-port-hint');
    if (webPortHint) {
        if (app && app.port_conflict) {
            webPortHint.innerHTML = `<span style="color: var(--amber-glow); font-weight: 600;">⚠ Default port ${defWebPort} is busy; auto-suggested free port: ${effectiveWebPort}</span>`;
            webPortHint.style.display = 'block';
        } else {
            webPortHint.style.display = 'none';
        }
    }

    // Render extra service ports if defined in the manifest (e.g. Monero Node RPC/P2P, DNS, VPN)
    const extraWrapper = document.getElementById('adv-extra-ports-wrapper');
    const extraGrid = document.getElementById('adv-extra-ports-grid');
    if (extraWrapper && extraGrid) {
        extraGrid.innerHTML = '';
        if (app && app.extra_ports && Array.isArray(app.extra_ports) && app.extra_ports.length > 0) {
            extraWrapper.style.display = 'block';
            app.extra_ports.forEach(ep => {
                const effectiveEpVal = ep.suggested_port || ep.default;
                const col = document.createElement('div');
                col.innerHTML = `
                    <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; letter-spacing: 0.5px;">${ep.label.toUpperCase()}</label>
                    <input type="number" class="adv-extra-port-input" data-key="${ep.key}" required min="1" max="65535" value="${effectiveEpVal}" style="width: 100%; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-main); padding: 10px 14px; border-radius: var(--radius-sm); font-size: 14px; font-family: monospace;">
                    ${ep.conflict ? `<div style="font-size: 10px; color: var(--amber-glow); margin-top: 4px; font-weight: 600;">⚠ Default port ${ep.default} busy; suggested: ${effectiveEpVal}</div>` : (ep.description ? `<div style="font-size: 10px; color: var(--text-dim); margin-top: 4px;">${ep.description}</div>` : '')}
                `;
                extraGrid.appendChild(col);
            });
        } else {
            extraWrapper.style.display = 'none';
        }
    }

    const submitBtn = document.getElementById('btn-adv-submit');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            <span>Deploy with Custom Settings</span>
        `;
    }

    modal.classList.add('open');
}

function closeAdvancedInstallModal() {
    const modal = document.getElementById('advanced-install-modal');
    if (modal) modal.classList.remove('open');
}

async function submitAdvancedInstall(e) {
    e.preventDefault();
    const appId = document.getElementById('adv-app-id').value;
    const webPort = parseInt(document.getElementById('adv-web-port').value, 10);
    const onionPort = parseInt(document.getElementById('adv-onion-port').value, 10);
    const envRaw = document.getElementById('adv-env-vars').value;
    const submitBtn = document.getElementById('btn-adv-submit');

    if (!appId) return;

    // Collect extra ports overrides (e.g. Node RPC, P2P, DNS, VPN)
    const extraPorts = {};
    document.querySelectorAll('.adv-extra-port-input').forEach(input => {
        const key = input.dataset.key;
        const val = parseInt(input.value, 10);
        if (key && !isNaN(val)) {
            extraPorts[key] = val;
        }
    });

    // Parse custom environment overrides into key=value mapping
    const customEnv = {};
    if (envRaw) {
        envRaw.split('\n').forEach(line => {
            line = line.trim();
            if (line && !line.startsWith('#') && line.includes('=')) {
                const idx = line.indexOf('=');
                const k = line.substring(0, idx).trim();
                const v = line.substring(idx + 1).trim();
                if (k) customEnv[k] = v;
            }
        });
    }

    if (submitBtn) {
        submitBtn.innerHTML = `${ICONS.spinner} <span>Deploying container...</span>`;
        submitBtn.disabled = true;
    }

    showToast(`Deploying ${appId} with custom configuration...`, 'info');

    try {
        const payload = {
            web_port: webPort,
            onion_port: onionPort,
            extra_ports: Object.keys(extraPorts).length > 0 ? extraPorts : null,
            custom_env: Object.keys(customEnv).length > 0 ? customEnv : (envRaw.trim() ? envRaw.trim() : null)
        };

        const res = await fetch(`/api/apps/install/${appId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            if (data.port_reallocated) {
                showToast(`${appId} custom deployment succeeded! (Allocated port: ${data.web_port})`, 'success');
            } else {
                showToast(`${appId} custom deployment succeeded!`, 'success');
            }
            closeAdvancedInstallModal();
            await fetchApps();
        } else {
            showToast(`Deployment error: ${data.detail || 'Failed to deploy.'}`, 'error');
            if (submitBtn) {
                submitBtn.innerHTML = `
                    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    <span>Deploy with Custom Settings</span>
                `;
                submitBtn.disabled = false;
            }
        }
    } catch (err) {
        showToast('Network error during deployment.', 'error');
        if (submitBtn) {
            submitBtn.innerHTML = `
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>Deploy with Custom Settings</span>
            `;
            submitBtn.disabled = false;
        }
    }
}

// ---------------------------------------------------------
// App Information & Network Port Mapping Modal
// ---------------------------------------------------------
let currentInfoApp = null;

function showAppInfoModal(appId) {
    const app = appsData.find(a => a.id === appId);
    if (!app) return;
    currentInfoApp = app;

    const host = window.location.hostname || '127.0.0.1';

    // Header & Icon
    const iconWrap = document.getElementById('info-modal-icon-wrap');
    if (iconWrap) {
        iconWrap.innerHTML = getAppIconHtml(app.icon, app.name);
    }
    const titleEl = document.getElementById('info-modal-title');
    if (titleEl) titleEl.innerText = app.name;
    const subEl = document.getElementById('info-modal-subtitle');
    if (subEl) subEl.innerText = `${app.category} • Ports & Endpoints`;

    // Status Badges
    const statusEl = document.getElementById('info-status-badge');
    if (statusEl) {
        statusEl.className = `status-badge ${app.is_running ? 'running' : 'stopped'}`;
        statusEl.innerHTML = `<span class="status-dot ${app.is_running ? 'active pulse' : 'inactive'}" style="width:6px;height:6px;"></span> ${app.is_running ? 'Running' : 'Stopped'}`;
    }

    let opsecClass = 'tag-opsec-1';
    if (app.opsec_level === 'Level 2') opsecClass = 'tag-opsec-2';
    if (app.opsec_level === 'Level 3') opsecClass = 'tag-opsec-3';
    const opsecEl = document.getElementById('info-opsec-badge');
    if (opsecEl) {
        opsecEl.className = `tag-badge ${opsecClass}`;
        opsecEl.innerText = app.opsec_level;
    }

    const ramEl = document.getElementById('info-ram-badge');
    if (ramEl) ramEl.innerText = `${app.memory_mb} MB RAM`;

    const catEl = document.getElementById('info-cat-badge');
    if (catEl) catEl.innerText = app.category;

    // Description
    const descEl = document.getElementById('info-modal-desc');
    if (descEl) descEl.innerText = app.description;

    // Host IP label
    const hostIpLabel = document.getElementById('info-host-ip-label');
    if (hostIpLabel) hostIpLabel.innerText = `Host IP: ${host}`;

    // Ports Table
    const portsTable = document.getElementById('info-ports-table');
    if (portsTable) {
        let rowsHtml = '';

        // Primary Web Port
        if (app.web_port) {
            const webLabel = app.web_port_label || 'Web UI / HTTP Console';
            const endpoint = `http://${host}:${app.web_port}`;
            rowsHtml += `
                <div class="info-port-row">
                    <div class="info-port-badge">${app.web_port} / TCP</div>
                    <div class="info-port-details">
                        <div class="info-port-name">${webLabel}</div>
                        <div class="info-port-desc">Browser web management interface & dashboard</div>
                    </div>
                    <div class="info-port-endpoint">
                        <code>${host}:${app.web_port}</code>
                        <button class="btn btn-secondary" onclick="copyEndpoint('${endpoint}')" title="Copy URL" style="padding: 3px 8px; font-size: 11px;">Copy</button>
                    </div>
                </div>
            `;
        }

        // Extra Ports
        if (app.extra_ports && Array.isArray(app.extra_ports)) {
            app.extra_ports.forEach(ep => {
                const portVal = ep.port || ep.default;
                if (!portVal) return;
                const proto = (ep.protocol || 'tcp').toUpperCase();
                const epLabel = ep.label || ep.key;
                const epDesc = ep.description || 'Application service port';
                const endpoint = `${host}:${portVal}`;
                rowsHtml += `
                    <div class="info-port-row">
                        <div class="info-port-badge" style="background:rgba(255,255,255,0.06);border-color:rgba(255,255,255,0.15);color:var(--text-main);">${portVal} / ${proto}</div>
                        <div class="info-port-details">
                            <div class="info-port-name">${epLabel}</div>
                            <div class="info-port-desc">${epDesc}</div>
                        </div>
                        <div class="info-port-endpoint">
                            <code>${endpoint}</code>
                            <button class="btn btn-secondary" onclick="copyEndpoint('${endpoint}')" title="Copy Endpoint" style="padding: 3px 8px; font-size: 11px;">Copy</button>
                        </div>
                    </div>
                `;
            });
        }

        portsTable.innerHTML = rowsHtml || '<div style="color:var(--text-muted);font-size:12px;padding:8px;">No exposed host network ports.</div>';
    }

    // Tor Onion Section
    const onionSection = document.getElementById('info-onion-section');
    const onionAddr = document.getElementById('info-onion-address');
    if (app.onion) {
        if (onionSection) onionSection.style.display = 'block';
        if (onionAddr) onionAddr.innerHTML = `<a href="http://${app.onion}" target="_blank" style="color:#c084fc;text-decoration:none;">http://${app.onion}</a>`;
    } else {
        if (onionSection) onionSection.style.display = 'none';
    }

    // Client Connection Guide
    const guideSection = document.getElementById('info-guide-section');
    const guideContent = document.getElementById('info-guide-content');
    const guideHtml = getClientGuide(app.id, host, app);
    if (guideSection && guideContent && guideHtml) {
        guideContent.innerHTML = guideHtml;
        guideSection.style.display = 'block';
    } else if (guideSection) {
        guideSection.style.display = 'none';
    }

    // Open Web button
    const openBtn = document.getElementById('btn-info-open-web');
    if (openBtn) {
        if (app.web_port && app.is_running) {
            openBtn.style.display = 'inline-flex';
            openBtn.onclick = () => {
                closeAppInfoModal();
                openApp(app.id, app.web_port, app.onion);
            };
        } else {
            openBtn.style.display = 'none';
        }
    }

    const modal = document.getElementById('app-info-modal');
    if (modal) modal.classList.add('active');
}

function closeAppInfoModal() {
    const modal = document.getElementById('app-info-modal');
    if (modal) modal.classList.remove('active');
    currentInfoApp = null;
}

function copyInfoOnion() {
    if (currentInfoApp && currentInfoApp.onion) {
        const url = `http://${currentInfoApp.onion}`;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url);
            showToast('Tor v3 Onion address copied!', 'info');
        } else {
            prompt('Copy Tor Onion Address:', url);
        }
    }
}

function copyEndpoint(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
        showToast(`Copied to clipboard: ${text}`, 'info');
    } else {
        prompt('Copy Endpoint:', text);
    }
}

function getClientGuide(appId, host, app) {
    const webPort = app.web_port;
    const onion = app.onion;

    const getPort = (key, fallback) => {
        if (app.extra_ports && Array.isArray(app.extra_ports)) {
            const found = app.extra_ports.find(p => p.key === key);
            if (found) return found.port || found.default || fallback;
        }
        return fallback;
    };

    switch (appId) {
        case 'monero-node': {
            const rpcPort = getPort('rpc_port', 18081);
            return `
                <div style="margin-bottom: 6px;"><strong>Feather Wallet / Monero GUI Connection:</strong></div>
                <div style="margin-bottom: 4px;">• In your wallet network settings, choose <em>Custom Node</em>.</div>
                <div style="margin-bottom: 4px;">• Node Address: <code style="color:var(--accent-cyan);">${host}</code> &nbsp; Port: <code style="color:var(--accent-cyan);">${rpcPort}</code></div>
                ${onion ? `<div>• Or via Tor Hidden Service: <code style="color:#c084fc;">${onion}</code> (Port 80)</div>` : ''}
                <div style="margin-top: 6px; font-size: 11px; color: var(--text-dim);">The web dashboard on port ${webPort} displays real-time sync progress, hashrate, and block height.</div>
            `;
        }
        case 'i2pd': {
            const httpProxy = getPort('http_proxy_port', 4444);
            const socksProxy = getPort('socks_proxy_port', 4447);
            return `
                <div style="margin-bottom: 6px;"><strong>Browser & Client Proxy Configuration:</strong></div>
                <div style="margin-bottom: 4px;">• HTTP Proxy (for .i2p eepsites): <code style="color:var(--accent-cyan);">${host}:${httpProxy}</code></div>
                <div style="margin-bottom: 4px;">• SOCKS5 Proxy: <code style="color:var(--accent-cyan);">${host}:${socksProxy}</code></div>
                <div>• Web Router Console: <a href="http://${host}:${webPort}" target="_blank" style="color:var(--accent-cyan);text-decoration:underline;">http://${host}:${webPort}</a></div>
            `;
        }
        case 'wg-easy': {
            const vpnPort = getPort('vpn_port', 51820);
            return `
                <div style="margin-bottom: 6px;"><strong>WireGuard Client Setup:</strong></div>
                <div style="margin-bottom: 4px;">1. Open the Admin Console at <a href="http://${host}:${webPort}" target="_blank" style="color:var(--accent-cyan);text-decoration:underline;">http://${host}:${webPort}</a></div>
                <div style="margin-bottom: 4px;">2. Click <em>+ New Client</em>, then download the profile or scan the QR code.</div>
                <div>• WireGuard tunnel connects to UDP port <code style="color:var(--accent-cyan);">${vpnPort}</code>.</div>
            `;
        }
        case 'adguard-home':
        case 'pihole-unbound': {
            const dnsPort = getPort('dns_port', appId === 'adguard-home' ? 5353 : 53);
            return `
                <div style="margin-bottom: 6px;"><strong>Network DNS Configuration:</strong></div>
                <div style="margin-bottom: 4px;">• Set your router Primary DNS or device DNS to: <code style="color:var(--accent-cyan);">${host}</code></div>
                <div style="margin-bottom: 4px;">• DNS Port: <code style="color:var(--accent-cyan);">${dnsPort} (UDP)</code></div>
                <div>• Web Admin Dashboard: <a href="http://${host}:${webPort}" target="_blank" style="color:var(--accent-cyan);text-decoration:underline;">http://${host}:${webPort}</a></div>
            `;
        }
        case 'simplex': {
            const xftpPort = getPort('xftp_port', 5233);
            return `
                <div style="margin-bottom: 6px;"><strong>SimpleX Chat Configuration:</strong></div>
                <div style="margin-bottom: 4px;">• SMP Server Web Port: <code style="color:var(--accent-cyan);">${webPort}</code></div>
                <div style="margin-bottom: 4px;">• XFTP File Transfer Port: <code style="color:var(--accent-cyan);">${xftpPort}</code> (TCP)</div>
                ${onion ? `<div>• Tor v3 Onion address available for anonymous E2EE routing.</div>` : ''}
            `;
        }
        case 'vaultwarden': {
            return `
                <div style="margin-bottom: 6px;"><strong>Bitwarden Client Setup:</strong></div>
                <div style="margin-bottom: 4px;">• In the Bitwarden extension or mobile app, click the Gear icon (Settings).</div>
                <div style="margin-bottom: 4px;">• Under <em>Self-hosted environment</em>, enter Server URL: <code style="color:var(--accent-cyan);">http://${host}:${webPort}</code></div>
                <div><em>Note: Bitwarden browser extension requires HTTPS or localhost for autofill, or connect through Tor onion.</em></div>
            `;
        }
        case 'forgejo': {
            const sshPort = getPort('ssh_port', 2222);
            return `
                <div style="margin-bottom: 6px;"><strong>Git Access:</strong></div>
                <div style="margin-bottom: 4px;">• Web Interface: <code style="color:var(--accent-cyan);">http://${host}:${webPort}</code></div>
                <div>• SSH Git Clones: <code style="color:var(--accent-cyan);">ssh://git@${host}:${sshPort}/[username]/[repo].git</code></div>
            `;
        }
        case 'syncthing': {
            const syncPort = getPort('sync_port', 22000);
            return `
                <div style="margin-bottom: 6px;"><strong>Syncthing Peer Sync:</strong></div>
                <div style="margin-bottom: 4px;">• Web GUI: <code style="color:var(--accent-cyan);">http://${host}:${webPort}</code></div>
                <div>• Peer Sync Listen Port: <code style="color:var(--accent-cyan);">${syncPort} (TCP)</code></div>
            `;
        }
        case 'ollama-webui': {
            const apiPort = getPort('ollama_api_port', 11434);
            return `
                <div style="margin-bottom: 6px;"><strong>LLM & API Endpoints:</strong></div>
                <div style="margin-bottom: 4px;">• Open WebUI Chat Interface: <code style="color:var(--accent-cyan);">http://${host}:${webPort}</code></div>
                <div>• Ollama REST API: <code style="color:var(--accent-cyan);">http://${host}:${apiPort}</code> (OpenAI-compatible)</div>
            `;
        }
        default:
            return `
                <div style="margin-bottom: 4px;">• Local Service Endpoint: <code style="color:var(--accent-cyan);">http://${host}:${webPort}</code></div>
                ${onion ? `<div>• Tor v3 Onion Service: <code style="color:#c084fc;">http://${onion}</code></div>` : ''}
            `;
    }
}

