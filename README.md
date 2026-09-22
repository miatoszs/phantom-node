# PhantomNode OS 👻
## The Sovereign, Privacy-First & Anti-Forensics Server OS (Debian-based)
*Engineered for maximum data sovereignty, strict operational security (OPSEC), and physical anti-forensics.*

---

## 🌟 What is PhantomNode OS?

**PhantomNode OS** is a self-hosted, sovereign server operating environment built on Debian 12 (Bookworm) and Kicksecure. It combines the clean, visual user experience of **CasaOS and Umbrel** (responsive Web Dashboard, 1-Click App Store, real-time system telemetry) with stringent **OPSEC Level 1–4** cybersecurity, cryptography, and anti-forensics principles.

### Why standard CasaOS or Umbrel are not enough for high-threat OPSEC models:
- **IP & Geolocation Leaks:** Conventional home cloud systems require router port forwarding (UPnP / NAT traversal) or centralized dynamic DNS. This exposes the operator's real residential IP address, ISP identity, and physical location to network observers and automated port scanners.
- **Lack of Tor v3 Service Isolation:** Traditional setups do not dynamically generate isolated, per-service Tor v3 `.onion` endpoints with end-to-end cryptographic authentication.
- **DNS Leak Vectors:** Default container configurations frequently bypass local recursive DNS resolvers and leak domain queries to ISP or upstream DNS servers.
- **No Physical Anti-Forensics Protections:** Standard home servers provide zero hardware-level defenses against physical device seizure, cold-boot memory extraction, or unauthorized USB access.

---

## 🛡️ PhantomNode Defense Architecture

1. **Zero-Port-Forwarding & Tor v3 Isolation:**
   Every deployed application runs strictly without router port forwarding. Remote access is powered by cryptographic **Tor v3 Hidden Services (`.onion`)**, accessible from anywhere in the world via Tor Browser or Orbot without leaking the server's public IP address.
2. **Local LAN + Tor Dual Accessibility:**
   Containers bind to all local network interfaces (`0.0.0.0`) inside a hardened UFW firewall zone, allowing seamless local network access (`http://<LAN_IP>:<Port>`) alongside the private `.onion` link.
3. **Automated Port Conflict Resolution:**
   Before deploying any container, PhantomNode scans both host sockets and installed service manifests. If a requested port is already occupied (e.g. port 3000), it automatically allocates the nearest available free port, preventing deployment failures.
4. **DNS Leak Proofing:**
   Containers are prevented from querying external commercial DNS resolvers. All queries are resolved through local recursive Unbound instances, AdGuard Home, or Tor-based encrypted resolvers.
5. **Kernel & Network Sysctl Hardening:**
   TCP timestamps are disabled to prevent uptime-based OS fingerprinting. Additional protections include reverse-path filtering (`rp_filter`), ICMP redirect denial, BPF JIT hardening, restricted `dmesg` access, and kernel panic reboot mitigations.
6. **Physical Anti-Forensics Triggers:**
   - **USB Dead Man's Switch (`nukeusb`):** If an unauthorized USB device is inserted (or a monitored USB token is pulled), the system instantly flushes memory buffers and forces an emergency power shutdown (`poweroff -f`).
   - **HID Input Trap (`emergency-hid`):** Monitored mouse movement or unauthorized keyboard input on a headless server immediately triggers an emergency halt.
   - **1-Click Emergency Panic Button:** Instant memory flush, swap wipe, and forced shutdown directly from the Web Dashboard.

---

## 📦 Built-In Privacy Application Catalog (18 Tools)

| Application | Category | OPSEC Level | Description |
| :--- | :--- | :--- | :--- |
| **AdGuard Home** | Network & DNS | OPSEC Level 1 | Network-wide ad, tracker, and malware blocker with encrypted upstream DNS (DoH, DoT, DoQ). |
| **Monero Node & Dashboard** | Financial Privacy | OPSEC Level 3 | Full validating Monero (XMR) blockchain node with real-time web dashboard (block height, sync progress, peers). |
| **Nextcloud Hub** | Cloud & Storage | OPSEC Level 2 | Self-hosted sovereign cloud storage, calendar, and contacts behind isolated Tor onion routing. |
| **Vaultwarden** | Passwords & Auth | OPSEC Level 1 | Lightweight Bitwarden-compatible password vault written in Rust with zero-knowledge client encryption. |
| **WireGuard (WG-Easy)** | Encrypted Network | OPSEC Level 2 | High-performance WireGuard VPN server with responsive Web UI and 1-click QR code client profile generator. |
| **I2Pd Darknet Router** | Encrypted Network | OPSEC Level 3 | Lightweight C++ Invisible Internet Project (I2P) router with built-in HTTP and SOCKS5 client proxies. |
| **SimpleX Chat Server** | Encrypted Comms | OPSEC Level 3 | Sovereign SMP message broker and XFTP media relay without user identifiers, phone numbers, or metadata graphs. |
| **Matrix Synapse** | Encrypted Comms | OPSEC Level 2 | Federated, end-to-end encrypted team chat and voice communications server compatible with Element. |
| **Syncthing** | Continuous Sync | OPSEC Level 1 | Decentralized, peer-to-peer file synchronization system encrypted in transit without central storage. |
| **FileBrowser** | Cloud & Storage | OPSEC Level 1 | Clean, lightweight web-based file manager for uploading, editing, and sharing files over LAN or Tor. |
| **Pi-hole + Unbound** | Network & DNS | OPSEC Level 1 | Network-wide telemetry blocker paired with an independent, local recursive root DNS resolver. |
| **Ollama + Open WebUI** | Private AI | OPSEC Level 2 | 100% offline local neural language models (Gemma, DeepSeek, Qwen) with ChatGPT-style web interface. |
| **SearXNG** | Private Search | OPSEC Level 1 | Privacy-respecting metasearch engine combining results across 70+ engines without search profiling. |
| **Invidious** | Media & Streaming | OPSEC Level 1 | Lightweight, ad-free YouTube frontend operating without Google accounts, cookies, or JavaScript bloat. |
| **Redlib** | Private Social | OPSEC Level 1 | Private, privacy-friendly Reddit frontend with clean UI and zero tracking cookies. |
| **Forgejo** | Development | OPSEC Level 1 | Self-hosted Git software forge (Gitea community fork) with SSH repository access over LAN and Tor. |
| **BorgBackup Server** | Backup & Recovery | OPSEC Level 2 | Deduplicating, authenticated, and AES-256 encrypted remote backup repository over SSH. |
| **Cockpit Console** | System Admin | OPSEC Level 1 | System and hardware management web console for monitoring CPU, RAM, storage, and system services. |

---

## 🚀 Quick Installation (Debian 12 / Kicksecure)

On a clean installation of **Debian 12 Minimal** or **Kicksecure**, run the following commands:

```bash
git clone https://github.com/miatoszs/phantom-node.git
cd phantom-node
sudo ./install.sh
```

### What the installer automatically configures:
1. Installs Docker Engine, Docker Compose plugin, and Tor daemon.
2. Creates an isolated Python virtual environment and sets up the asynchronous FastAPI Web Dashboard.
3. Automatically provisions the Master Dashboard Tor v3 Hidden Service (`.onion`).
4. Applies strict kernel sysctl hardening and configures the UFW firewall.
5. Registers and enables `phantom-dashboard.service` under systemd.
6. Displays the local LAN dashboard URL (`http://<LAN_IP>:7426`) and the private Master `.onion` address.

---

## 🖥️ Web Dashboard Features

Open the dashboard in your web browser:
- **Local Network:** `http://<server-ip>:7426`
- **Remote Access (Worldwide):** `http://<master-onion-address>.onion` (in Tor Browser)

### Key Dashboard Capabilities:
- **Live Telemetry:** Real-time monitoring of CPU load, RAM allocation, NVMe/SSD storage, uptime, and Tor status.
- **Privacy App Store:** 1-Click deployment for sovereign privacy tools with auto-generated onion services.
- **Advanced Custom Deployment:** Configure custom web ports, custom Tor onion ports, and `.env` environment overrides before starting containers.
- **App Information & Port Mapping Modal:** Dedicated **Info** button on installed apps displaying:
  - Complete list of active network ports (Web console, Node RPC, P2P sync, DNS, SOCKS/HTTP proxy, SSH, etc.).
  - 1-Click endpoint clipboard copy (e.g. `192.168.2.229:18081`).
  - Tailored client setup guides (Feather Wallet, Bitwarden extension, WireGuard profiles, DNS resolvers, etc.).
- **1-Click Container Updates:** Update individual container stacks with a single button or click **Update All Containers** to pull the latest images and restart all active apps.
- **1-Click System OTA Updater:** Check GitHub for new PhantomNode OS releases directly from the header version badge and apply updates with zero downtime.
- **Tor v3 & QR Center:** Display dedicated `.onion` addresses with one-click copy and scannable QR codes for mobile Tor Browser access.
- **OPSEC Control Center:** Arm or disarm the hardware USB Dead Man's Switch, check defensive triggers, or execute an emergency memory wipe and shutdown.

---

## ⌨️ `phantom` CLI Reference

Full command-line system management is available directly from the terminal:

```bash
# View system health, Tor status, and active containers
phantom status

# List all available catalog apps and their installation status
phantom app list

# 1-Click app deployment
phantom app install adguard-home
phantom app install nextcloud

# Deploy with custom port or interactive advanced settings
phantom app install adguard-home --port 8053
phantom app install vaultwarden --advanced

# Manage container lifecycle
phantom app start <app_id>
phantom app stop <app_id>
phantom app restart <app_id>
phantom app logs <app_id>
phantom app remove <app_id>

# Update containers (pull latest Docker images & restart stacks)
phantom app update <app_id>     # Update a specific container
phantom app update-all          # Update all installed containers simultaneously

# List all active Tor v3 Hidden Service addresses
phantom onion list

# OPSEC Shield and hardware protection
phantom opsec status
phantom opsec arm-usb       # Arm the USB Dead Man's Switch
phantom opsec disarm-usb    # Disarm USB defense
phantom opsec panic         # Trigger immediate emergency shutdown & memory flush

# System OTA Updates
phantom update check        # Check for upstream releases on GitHub
phantom update              # Download latest changes and restart services
```

---

## 🔒 Security & Operational Notice
- PhantomNode OS is designed strictly for personal and business data sovereignty, legitimate privacy preservation, and cybersecurity defense.
- Container configurations and network isolation mechanisms are built around the **4-Tier OPSEC Model**.
