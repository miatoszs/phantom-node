#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - Turnkey Automated Installer for Debian 12 / Kicksecure
# "The Sovereign Privacy Server"
# ==============================================================================
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Visual styling
C_CYAN='\033[1;36m'
C_PURPLE='\033[1;35m'
C_GREEN='\033[1;32m'
C_RED='\033[1;31m'
C_YELLOW='\033[1;33m'
C_RESET='\033[0m'

print_banner() {
    echo -e "${C_CYAN}"
    cat << "EOF"
  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
                  N O D E   O S  v 1 . 0
EOF
    echo -e "${C_PURPLE}       --- The Sovereign Privacy & Anti-Forensics Server ---${C_RESET}\n"
}

print_banner

# Step 0: Privilege check
if [ "$EUID" -ne 0 ]; then
    echo -e "${C_RED}[!] Error: Please run this installer with root privileges (sudo ./install.sh).${C_RESET}"
    exit 1
fi

echo -e "${C_CYAN}[1/8] Updating package repositories and installing dependencies...${C_RESET}"
apt-get update -y
apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    lsb-release \
    git \
    rsync \
    procps \
    python3 \
    python3-pip \
    python3-venv \
    ufw \
    tor \
    torsocks \
    usbutils \
    evtest \
    psmisc

# Step 2: Install Docker Engine & Docker Compose Plugin if not installed
echo -e "${C_CYAN}[2/8] Checking Docker installation...${C_RESET}"
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${C_YELLOW}[*] Installing official Docker Engine & Docker Compose Plugin...${C_RESET}"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    CODENAME=$(lsb_release -cs 2>/dev/null || echo "bookworm")
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
    echo -e "${C_GREEN}[+] Docker installed and started successfully.${C_RESET}"
else
    echo -e "${C_GREEN}[+] Docker is already installed.${C_RESET}"
fi

# Step 3: Deploy PhantomNode Core to /opt/phantom-node
INSTALL_DIR="/opt/phantom-node"
DATA_DIR="/var/lib/phantom-node"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${C_CYAN}[3/8] Deploying PhantomNode to ${INSTALL_DIR}...${C_RESET}"
mkdir -p "${INSTALL_DIR}"
mkdir -p "${DATA_DIR}/installed_apps"

# Copy files if installing from external source folder, excluding any pre-existing venv or cache
if [ "${SOURCE_DIR}" != "${INSTALL_DIR}" ]; then
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude 'venv' --exclude '__pycache__' --exclude '.git' "${SOURCE_DIR}/" "${INSTALL_DIR}/"
    else
        cp -r "${SOURCE_DIR}"/* "${INSTALL_DIR}/"
    fi
    rm -rf "${INSTALL_DIR}/venv"
fi

# Ensure target directory is a valid git repository linked to origin for 1-click updates
if [ ! -d "${INSTALL_DIR}/.git" ]; then
    (
        cd "${INSTALL_DIR}"
        git init -b main >/dev/null 2>&1 || git init >/dev/null 2>&1
        git remote add origin https://github.com/miatoszs/phantom-node.git 2>/dev/null || git remote set-url origin https://github.com/miatoszs/phantom-node.git
        git fetch origin main >/dev/null 2>&1 || true
        git reset --mixed origin/main >/dev/null 2>&1 || true
    ) || true
fi

# Step 4: Python Virtual Environment
echo -e "${C_CYAN}[4/8] Setting up isolated Python runtime environment...${C_RESET}"
rm -rf "${INSTALL_DIR}/venv"
python3 -m venv --clear "${INSTALL_DIR}/venv"
"${INSTALL_DIR}/venv/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
"${INSTALL_DIR}/venv/bin/pip" install \
    fastapi \
    "uvicorn[standard]" \
    jinja2 \
    pydantic \
    psutil

# Step 5: Configure Tor Engine & Master Dashboard Onion
echo -e "${C_CYAN}[5/8] Configuring Tor v3 Engine & Master Hidden Service...${C_RESET}"
mkdir -p /etc/tor/torrc.d
mkdir -p /var/lib/tor/phantom_services/dashboard

# Make sure /etc/tor/torrc includes torrc.d
if ! grep -q "%include /etc/tor/torrc.d" /etc/tor/torrc 2>/dev/null; then
    echo -e "\n# Include PhantomNode dynamic hidden services\n%include /etc/tor/torrc.d/*.conf" >> /etc/tor/torrc
fi

# Configure Dashboard Onion Service
cat << 'EOF' > /etc/tor/torrc.d/phantom_dashboard.conf
# PhantomNode Master Dashboard Hidden Service
HiddenServiceDir /var/lib/tor/phantom_services/dashboard
HiddenServiceVersion 3
HiddenServicePort 80 127.0.0.1:7426
EOF

chmod 700 /var/lib/tor/phantom_services
chmod 700 /var/lib/tor/phantom_services/dashboard
chown -R debian-tor:debian-tor /var/lib/tor/phantom_services 2>/dev/null || true

systemctl enable --now tor
systemctl restart tor

# Wait for Tor to generate dashboard onion address
echo -n "[*] Waiting for Tor v3 .onion generation"
DASHBOARD_ONION=""
for i in {1..15}; do
    if [ -f "/var/lib/tor/phantom_services/dashboard/hostname" ]; then
        DASHBOARD_ONION=$(cat /var/lib/tor/phantom_services/dashboard/hostname)
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Step 6: Apply System & Kernel Hardening
echo -e "${C_CYAN}[6/8] Executing Kernel & Sysctl Anti-Forensics Hardening...${C_RESET}"
chmod +x "${INSTALL_DIR}/scripts/"*.sh
"${INSTALL_DIR}/scripts/hardening.sh"

# Step 7: Systemd Services Setup
echo -e "${C_CYAN}[7/8] Enabling PhantomNode Background Services...${C_RESET}"
cp "${INSTALL_DIR}/scripts/phantom-dashboard.service" /etc/systemd/system/
cp "${INSTALL_DIR}/scripts/nukeusb.service" /etc/systemd/system/
cp "${INSTALL_DIR}/scripts/nukeusb.timer" /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now phantom-dashboard.service

# Setup CLI symlink
ln -sf "${INSTALL_DIR}/phantom" /usr/local/bin/phantom
chmod +x /usr/local/bin/phantom

# Step 8: Final Summary
PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7}' | tr -d '\n' || echo "localhost")

echo -e "\n${C_GREEN}======================================================================${C_RESET}"
echo -e "${C_GREEN}   🎉 PhantomNode OS Installation Finished Successfully!${C_RESET}"
echo -e "${C_GREEN}======================================================================${C_RESET}\n"

echo -e "  ${C_CYAN}Local LAN Web Dashboard:${C_RESET}     http://${PRIMARY_IP}:7426"
if [ -n "${DASHBOARD_ONION}" ]; then
    echo -e "  ${C_PURPLE}Tor v3 Master .onion URL:${C_RESET}     http://${DASHBOARD_ONION}"
else
    echo -e "  ${C_YELLOW}Tor v3 Master .onion URL:${C_RESET}     Generating (check with 'phantom onion list')"
fi

echo -e "\n  ${C_CYAN}Command Line Management:${C_RESET}"
echo -e "    phantom status              - Show system health, Tor status, and apps"
echo -e "    phantom app list            - Browse Privacy App Store catalog"
echo -e "    phantom app install <id>    - 1-Click application deployment"
echo -e "    phantom onion list          - List all active Tor v3 onion services"
echo -e "    phantom opsec arm-usb       - Arm the USB Dead Man's Switch\n"
EOF
