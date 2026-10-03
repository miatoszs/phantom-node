#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - Interactive Shell & SSH Welcome Banner
# ==============================================================================

# Only run in interactive shells or when explicitly invoked
if [ "${1:-}" != "--force" ]; then
    # Return immediately in non-interactive sessions (e.g. scp, sftp, automated rsync)
    if [ ! -t 1 ] && [ -z "${SSH_TTY:-}" ] && [ -z "${PS1:-}" ]; then
        return 0 2>/dev/null || exit 0
    fi

    # Prevent showing multiple times in the same session/subshell
    if [ -n "${PHANTOM_BANNER_SHOWN:-}" ]; then
        return 0 2>/dev/null || exit 0
    fi
fi
export PHANTOM_BANNER_SHOWN=1

C_CYAN='\033[1;36m'
C_PURPLE='\033[1;35m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'
C_WHITE='\033[1;37m'
C_DIM='\033[0;90m'
C_RESET='\033[0m'

# Determine Primary LAN IP
PRIMARY_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7}' | tr -d '\n')
if [ -z "$PRIMARY_IP" ] || [ "$PRIMARY_IP" = "localhost" ]; then
    PRIMARY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
[ -z "$PRIMARY_IP" ] && PRIMARY_IP="127.0.0.1"

DASHBOARD_PORT=7426

# Read Tor v3 Master Onion
DASHBOARD_ONION=""
ONION_FILE="/var/lib/tor/phantom_services/dashboard/hostname"
if [ -f "$ONION_FILE" ]; then
    DASHBOARD_ONION=$(cat "$ONION_FILE" 2>/dev/null | tr -d '\n')
fi

# Quick resource metrics
UPTIME_STR=$(uptime -p 2>/dev/null | sed 's/up //' || uptime | awk -F'( |,)' '{print $2}')
MEM_INFO=$(free -m 2>/dev/null | awk '/Mem:/ {printf "%d / %d MB (%d%%)", $3, $2, ($3*100)/$2}')
DISK_INFO=$(df -h / 2>/dev/null | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')

echo -e "${C_CYAN}"
cat << "BANNER"
  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
BANNER
echo -e "${C_PURPLE}       --- The Sovereign Privacy & Anti-Forensics Server OS ---${C_RESET}\n"

echo -e "  ${C_WHITE}🌐 Web Dashboard:${C_RESET}       ${C_GREEN}http://${PRIMARY_IP}:${DASHBOARD_PORT}${C_RESET}"
echo -e "  ${C_WHITE}📍 Host IP Address:${C_RESET}     ${C_CYAN}${PRIMARY_IP}${C_RESET}"
echo -e "  ${C_WHITE}🔌 Dashboard Port:${C_RESET}      ${C_CYAN}${DASHBOARD_PORT}${C_RESET}"
if [ -n "$DASHBOARD_ONION" ]; then
    echo -e "  ${C_WHITE}🧅 Tor v3 Master Onion:${C_RESET} ${C_PURPLE}http://${DASHBOARD_ONION}${C_RESET}"
else
    echo -e "  ${C_WHITE}🧅 Tor v3 Master Onion:${C_RESET} ${C_YELLOW}Active (run 'phantom onion list')${C_RESET}"
fi

echo -e "\n  ${C_WHITE}📊 System Overview:${C_RESET}"
echo -e "    ${C_DIM}Uptime:${C_RESET}   ${UPTIME_STR}"
echo -e "    ${C_DIM}Memory:${C_RESET}   ${MEM_INFO}"
echo -e "    ${C_DIM}Disk /:${C_RESET}   ${DISK_INFO}"

echo -e "\n  ${C_WHITE}⌨️  CLI Management Shortcuts:${C_RESET}"
echo -e "    ${C_CYAN}phantom status${C_RESET}              - System telemetry, Tor daemon & app containers"
echo -e "    ${C_CYAN}phantom app list${C_RESET}            - List installed & available privacy apps"
echo -e "    ${C_CYAN}phantom app install <id>${C_RESET}    - 1-Click deploy an app stack"
echo -e "    ${C_CYAN}phantom app update-all${C_RESET}      - Pull latest Docker images & restart containers"
echo -e "    ${C_CYAN}phantom update${C_RESET}              - 1-Click OTA system updates from GitHub"
echo -e "    ${C_CYAN}phantom opsec status${C_RESET}        - Anti-forensics & USB Dead Man's Switch\n"
