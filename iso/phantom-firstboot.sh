#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - First boot (run once by phantom-firstboot.service)
# Waits for internet access, runs the bundled install.sh, then disables itself.
# Output goes to the console and to /var/log/phantom-firstboot.log.
# ==============================================================================
set -uo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME=/root
SRC="/opt/phantom-node-src"
LOG="/var/log/phantom-firstboot.log"

exec > >(tee -a "${LOG}") 2>&1
echo "[PhantomNode] First boot setup started $(date -u)"

# Docker, Tor and Python packages are downloaded during setup
for i in $(seq 1 60); do
    if curl -fsS -m 5 -o /dev/null https://deb.debian.org/debian/; then
        break
    fi
    echo "[PhantomNode] Waiting for network ($i/60)..."
    sleep 5
done

if bash "${SRC}/install.sh"; then
    echo "[PhantomNode] Setup finished. Disabling first-boot service."
    systemctl disable phantom-firstboot.service
    rm -rf "${SRC}"
    # Show the dashboard address on the local console login screen (\4 = IPv4 address)
    mkdir -p /etc/issue.d
    printf 'PhantomNode OS dashboard: http://\\4:7426\nPassword: log in and run  sudo phantom password show\n\n' > /etc/issue.d/phantom.issue
else
    echo "[PhantomNode] Setup FAILED. It will retry on the next boot. Log: ${LOG}"
    exit 1
fi
