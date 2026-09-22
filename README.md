# PhantomNode OS 👻
## The Sovereign, Privacy-First & Anti-Forensics Server OS (Debian-based)
*Inspirálva az OPSEC Bible és a "Digitális Eltűnés, Üzleti Anonimitás és Adatszuverenitás" kurzus által.*

---

## 🌟 Mi az a PhantomNode OS?

A **PhantomNode OS** egy Debian 12 (Bookworm) vagy Kicksecure alapra épülő, önálló szerver operációs környezet, amely a **CasaOS és az Umbrel** felhasználóbarát, vizuális élményét (reszponzív Web Dashboard, 1-kattintásos App Store, egyszerű menedzsment) ötvözi a legszigorúbb **OPSEC Level 1–4** adatvédelmi, kiberbiztonsági és anonimitási követelményekkel.

### Miért nem biztonságos a sima CasaOS vagy Umbrel a tanfolyamod fenyegetettségi modelljéhez?
- **IP-kiszivárgás:** A hagyományos otthoni felhő OS-ek megkövetelik a router port-továbbítást (UPnP / port forwarding) és a felhős dinamikus DNS regisztrációt. Ezzel a felhasználó otthoni IP-címe és valós földrajzi tartózkodási helye azonnal lelepleződik az internetszolgáltatók és támadók előtt.
- **Nincs Tor v3 szeparáció:** Nem biztosítanak izolált Tor rejtett szolgáltatásokat alkalmazásonként.
- **DNS szivárgások:** Nem akadályozzák meg, hogy a konténerek megkerüljék a helyi DNS-szűrőket.
- **Hiányzó Anti-Forensics védelem:** Nem tartalmaznak vészhelyzeti hardveres megsemmisítő vagy újraindító védelmeket fizikai rajtaütés esetén.

---

## 🛡️ A PhantomNode Védelmi Architektúrája

1. **Zero-Port-Forwarding (Nulla Router Módosítás):**
   Minden telepített alkalmazás kizárólag a helyi loopback felületen (`127.0.0.1`) és egy automatikusan legenerált, kriptográfiailag hitelesített **Tor v3 Hidden Service (`.onion`)** címen érhető el. Bárhonnan elérhető a világból Tor Browser vagy mobil Orbot segítségével, miközben a szerver otthoni IP-je sosem szivárog ki.
2. **DNS Leak Proofing:**
   A konténerek nem tudnak külső Google/Cloudflare DNS szerverekre kijutni (`dns: 127.0.0.1` és belső Unbound/Tor feloldás).
3. **Kernel & Network Sysctl Hardening:**
   Letiltott TCP időbélyegek (anti-uptime fingerprinting), spoofing elleni védelem (rp_filter), ICMP redirect tiltás, BPF JIT védelem, dmesg korlátozás.
4. **Fizikai Anti-Forensics Védelmi Triggerek:**
   - **USB Dead Man's Switch (`nukeusb`):** Ha egy támadó vagy hatóság külső USB eszközt csatlakoztat (vagy kihúzza a meglévőt), a szerver azonnal kiüríti a memóriát és kényszerített leállítást (`poweroff -f`) hajt végre.
   - **HID Input Trap (`emergency-hid`):** Fizikai egérmozgásra vagy billentyűzetleütésre reagáló pánikleállítás.
   - **1-Kattintásos Vészhelyzeti Pánik Gomb:** Azonnali lemez/RAM gyorsítótár ürítés és leállítás a Dashboardról.

---

## 📦 Beépített Privacy Alkalmazáskatalógus (18 Tool)

| Alkalmazás | Kategória | OPSEC Szint | Leírás |
| :--- | :--- | :--- | :--- |
| **AdGuard Home** | Network & DNS | OPSEC Level 1 | Teljes hálózati szintű DNS hirdetés-, tracking- és malware-blokkoló, DoH / DoT titkosított lekérdezésekkel. |
| **Nextcloud** | Cloud & Storage | OPSEC Level 2 | Saját felhőtárhely és szinkronizáció (Google Drive / OneDrive helyett) dedikált Tor proxyval. |
| **Vaultwarden** | Passwords & Auth | OPSEC Level 1 | Végponttól-végpontig titkosított (E2EE) jelszókezelő, hivatalos Bitwarden kliens támogatással. |
| **WireGuard (WG-Easy)** | Encrypted Network | OPSEC Level 2 | Rendkívül gyors és modern WireGuard VPN szerver webes felülettel és 1-kattintásos QR kliensgenerálással. |
| **Syncthing** | Continuous Sync | OPSEC Level 1 | Közvetlen P2P E2EE mappaszinkronizáció központi szerver nélkül, automatikus újracsatlakozással. |
| **FileBrowser** | Cloud & Storage | OPSEC Level 1 | Pehelykönnyű, letisztult webes fájlkezelő és privát dokumentumtár gyors fájlmegosztással. |
| **Pi-hole + Unbound** | Network & DNS | OPSEC Level 1 | Hálózati reklám- és telemetria-szűrő, teljesen független saját rekurzív gyökér-DNS szerverrel. |
| **SimpleX SMP & XFTP** | Encrypted Comms | OPSEC Level 3 | Metaadat-mentes, felhasználói azonosító nélküli (no user ID) chat- és média-kiszolgáló. |
| **Matrix Synapse** | Encrypted Comms | OPSEC Level 2 | Föderált, E2EE csoportos kommunikációs szerver (Discord/Slack helyett). |
| **Ollama + Open WebUI** | Private AI | OPSEC Level 2 | 100%-ban offline helyi AI (Gemma 3, Qwen, DeepSeek). Stylometry-védelem és fordítás felhő nélkül. |
| **SearXNG** | Private Search | OPSEC Level 1 | Megfigyelés-mentes metakereső (Google, Bing, DuckDuckGo párhuzamos lekérdezése). |
| **Invidious** | Media & Streaming | OPSEC Level 1 | Privát YouTube kliens reklámok, követők és Google-profilozás nélkül. |
| **Redlib** | Private Social | OPSEC Level 1 | Pehelykönnyű, JavaScript-mentes Reddit frontend LibRedirect integrációval. |
| **I2Pd Darknet Router** | Encrypted Network | OPSEC Level 3 | Pehelykönnyű C++ I2P router, end-to-end titkosított decentralizált darknet kommunikációhoz. |
| **Forgejo** | Development | OPSEC Level 1 | Ön-hosztolt Git szerver (GitHub alternatíva), Tor mögött, e-mail regisztráció nélkül. |
| **Monero Node & Dashboard** | Financial Privacy | OPSEC Level 3 | Saját teljes Monero blokklánc csomópont és beépített valós idejű webes felügyeleti dashboard (blokkmagasság, peer kapcsolatok, hashrate). |
| **BorgBackup Server** | Backup & Recovery | OPSEC Level 2 | Deduplikált, kliensoldali AES-256 titkosítású biztonsági mentési tárhely SSH over Tor-on át. |
| **Cockpit Console** | System Admin | OPSEC Level 1 | Rendszer- és hardverkezelő webkonzol (CPU, RAM, lemezek, virtuális gépek felügyelete). |

---

## 🚀 Gyors Telepítés (Debian 12 / Kicksecure)

Egy frissen telepített Debian 12 Minimal vagy Kicksecure rendszeren futtasd az alábbi egyetlen parancsot:

```bash
git clone https://github.com/miatoszs/phantom-node.git
cd phantom-node
sudo ./install.sh
```

A telepítő szkript automatikusan:
1. Telepíti a Docker Engine-t, Docker Compose plugint és a Tor komponenst.
2. Beállítja a virtuális Python környezetet és a FastAPI webes Dashboardot.
3. Bekapcsolja a Master Dashboard Tor v3 Hidden Service-t és legenerálja az `.onion` címet.
4. Alkalmazza a kernel sysctl és UFW Zero-WAN tűzfal szigorításokat.
5. Elindítja a `phantom-dashboard.service` háttérszolgáltatást.
6. Kiírja a helyi LAN IP-t (`http://192.168.x.x:7426`) és a privát Tor `.onion` címet.

---

## 🖥️ A Vezérlőpult Használata

Nyisd meg a böngésződben a kapott címet:
- **Helyi hálózaton:** `http://<szerver-ip>:7426`
- **Távolról (bárhonnan a világból):** `http://<master-onion-address>.onion` (Tor Browserben)

### Funkciók a Dashboardon:
- **Rendszer Telemetria:** Valós idejű CPU, RAM, lemezhasználat és Tor állapot kijelzés.
- **Privacy App Store & 1-Kattintásos Telepítés:** Egyetlen gombnyomással azonnal üzembe helyezhető bármely privacy stack.
- **1-Kattintásos Konténer Frissítés:** A telepített alkalmazások kártyáján lévő **Update** gombbal egyetlen kattintással lehúzható a legújabb hivatalos Docker image és újraindul a konténer. A lap tetején lévő **Update All Containers** gombbal pedig az összes telepített alkalmazás egyszerre frissíthető.
- **Haladó Beállítások (Advanced Options):** A fogaskerék ikonra kattintva egyéni helyi web portot, egyéni Tor .onion portot (alapértelmezett 80) és környezeti változókat (.env overrides) adhatsz meg a konténer indítása előtt.
- **Onion & QR Center:** Bármely telepített alkalmazásnál a 🧅 Tor v3 gombra kattintva megjelenik a dedikált Tor `.onion` cím és egy azonnal beolvasható QR-kód a mobil Tor Browserhez.
- **OPSEC Központ:** A jobb felső pajzs ikonra kattintva élesítheted a fizikai USB Dead Man's Switch védelmet, vagy vészhelyzet esetén aktiválhatod az azonnali kényszerített memóriatörlést és leállítást.
- **1-Kattintásos Rendszerfrissítés (OTA):** A fejlécben lévő verziószámra kattintva a rendszer automatikusan ellenőrzi a GitHub kiadásokat és gombnyomásra frissíti a kódbázist valamint újraindítja a démont.

---

## ⌨️ `phantom` Parancssori Eszköz (CLI)

A terminálból elérhető a teljes rendszervezérlés:

```bash
# Általános rendszerállapot, Tor hálózat és futó alkalmazások
phantom status

# Elérhető és telepített alkalmazások listázása
phantom app list

# Alkalmazás gyors telepítése
phantom app install adguard-home
phantom app install nextcloud

# Alkalmazás telepítése egyéni porttal vagy interaktív haladó módban
phantom app install adguard-home --port 8053
phantom app install vaultwarden --advanced

# Alkalmazás kezelése
phantom app start <app_id>
phantom app stop <app_id>
phantom app restart <app_id>
phantom app logs <app_id>
phantom app remove <app_id>

# Konténerek frissítése (legújabb Docker image-ek lehúzása és újraindítás)
phantom app update <app_id>     # Egy adott konténer frissítése
phantom app update-all          # Összes telepített konténer frissítése egyszerre

# Aktív Tor v3 .onion címek listázása
phantom onion list

# OPSEC Shield és USB Dead Man's Switch kezelése
phantom opsec status
phantom opsec arm-usb       # USB védelem élesítése
phantom opsec disarm-usb    # USB védelem kikapcsolása
phantom opsec panic         # Vészhelyzeti azonnali leállítás

# Rendszerfrissítés (OTA 1-Click Update)
phantom update check        # Új verziók keresése a GitHubon
phantom update              # Rendszer automatikus frissítése és újraindítása
```

---

## 🔒 Biztonsági és Jogi Tudnivalók
- A rendszer kizárólag a személyes és üzleti adatszuverenitás, a törvényes magánszféra és a kiberbiztonsági védelem céljaira készült.
- A szoftverek konfigurációja a kurzus anyagában részletezett **4 Szintű OPSEC Modell** mentén lett optimalizálva.
