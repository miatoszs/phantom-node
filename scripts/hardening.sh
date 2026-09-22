#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - System & Kernel Hardening Script
# Based on OPSEC Bible & Hardened Linux Standards
# ==============================================================================
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "[+] Applying PhantomNode OS Kernel & Network Privacy Hardening..."

SYSCTL_CONF="/etc/sysctl.d/99-phantom-hardening.conf"

cat <<'EOF' > "$SYSCTL_CONF"
# --- PhantomNode Privacy & Anti-Fingerprinting Hardening ---

# Disable TCP Timestamps (Prevents uptime calculation and remote OS fingerprinting)
net.ipv4.tcp_timestamps = 0

# Prevent IP Spoofing (Reverse Path Filtering)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP Echo Broadcasts (Prevent Smurf Attacks)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP error responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Do NOT accept or send ICMP redirects (Mitigate MITM route hijacking)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Do NOT accept IP Source Routed Packets
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Log Martians (Packets with impossible source addresses)
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# BPF JIT Hardening (Protect against eBPF kernel exploitation)
net.core.bpf_jit_harden = 2

# Restrict dmesg access to root only
kernel.dmesg_restrict = 1

# Restrict kptr (Kernel pointer leaks in /proc)
kernel.kptr_restrict = 2

# Disable core dumps for setuid binaries to prevent RAM credential harvesting
fs.suid_dumpable = 0

# IPv6 Privacy Extensions (Random temporary IPv6 addresses)
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
EOF

if command -v sysctl >/dev/null 2>&1; then
    sysctl --system > /dev/null 2>&1 || true
    echo "[+] Sysctl hardening rules loaded successfully."
elif [ -x /sbin/sysctl ]; then
    /sbin/sysctl --system > /dev/null 2>&1 || true
    echo "[+] Sysctl hardening rules loaded successfully."
elif [ -x /usr/sbin/sysctl ]; then
    /usr/sbin/sysctl --system > /dev/null 2>&1 || true
    echo "[+] Sysctl hardening rules loaded successfully."
elif [ -x /lib/systemd/systemd-sysctl ]; then
    /lib/systemd/systemd-sysctl > /dev/null 2>&1 || true
    echo "[+] Systemd-sysctl hardening rules loaded successfully."
else
    echo "[!] Notice: sysctl utility not found in PATH or /sbin; settings preserved in $SYSCTL_CONF."
fi

# --- UFW Firewall Setup ---
if command -v ufw >/dev/null 2>&1; then
    echo "[+] Configuring UFW Zero-WAN Firewall Policy..."
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow Loopback (Required for Tor Hidden Service reverse proxies)
    ufw allow in on lo to any

    # Allow Local Private Networks (LAN only for Dashboard & SSH)
    # 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12
    ufw allow from 192.168.0.0/16 to any port 7426 proto tcp comment 'PhantomNode Dashboard LAN'
    ufw allow from 10.0.0.0/8 to any port 7426 proto tcp comment 'PhantomNode Dashboard LAN'
    ufw allow from 172.16.0.0/12 to any port 7426 proto tcp comment 'PhantomNode Dashboard LAN'

    ufw allow from 192.168.0.0/16 to any port 22 proto tcp comment 'SSH LAN'
    ufw allow from 10.0.0.0/8 to any port 22 proto tcp comment 'SSH LAN'
    ufw allow from 172.16.0.0/12 to any port 22 proto tcp comment 'SSH LAN'

    ufw --force enable
    echo "[+] UFW Firewall enabled with strict LAN-only rules."
fi

echo "[+] PhantomNode OS Hardening Completed."
