#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - Installer ISO builder
#
# Remasters the official Debian netinst ISO (signature-verified) with:
#   - a PhantomNode boot menu entry (BIOS + UEFI) that loads iso/preseed.cfg
#   - this repository bundled at /phantom-node, installed on first boot
#
# Usage: scripts/build-iso.sh [output.iso]
# Needs: curl, gpg, xorriso, sha512sum
# Env:   DEBIAN_VERSION   Debian netinst release (default below)
#        ISO_CACHE        download cache (default ~/.cache/phantom-iso)
#        PHANTOM_ISO_TEST=1  test build: serial console + fully unattended
#                            (fixed test passphrases, first disk). NEVER release.
# ==============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEBIAN_VERSION="${DEBIAN_VERSION:-13.7.0}"
VERSION="$(sed -n 's/^PHANTOM_VERSION = "\(.*\)"/\1/p' "${ROOT}/core/config.py")"
ISO_CACHE="${ISO_CACHE:-${HOME}/.cache/phantom-iso}"
OUT="${1:-${ROOT}/dist/phantomnode-${VERSION}-amd64.iso}"
BASE_URL="https://cdimage.debian.org/debian-cd/${DEBIAN_VERSION}/amd64/iso-cd"
BASE_ISO="debian-${DEBIAN_VERSION}-amd64-netinst.iso"
# Debian CD signing key
DEBIAN_CD_KEY="DF9B9C49EAA9298432589D76DA87E80D6294BE9B"

for tool in curl gpg xorriso sha512sum; do
    command -v "${tool}" >/dev/null || { echo "[!] Missing tool: ${tool}" >&2; exit 1; }
done

# ------------------------------------------------------------------ download
mkdir -p "${ISO_CACHE}"
cd "${ISO_CACHE}"
if [ ! -f "${BASE_ISO}" ]; then
    echo "[*] Downloading ${BASE_ISO}"
    curl -fL -o "${BASE_ISO}.part" "${BASE_URL}/${BASE_ISO}"
    mv "${BASE_ISO}.part" "${BASE_ISO}"
fi
curl -fsSL -o SHA512SUMS "${BASE_URL}/SHA512SUMS"
curl -fsSL -o SHA512SUMS.sign "${BASE_URL}/SHA512SUMS.sign"

echo "[*] Verifying Debian signature and checksum"
GNUPGHOME="$(mktemp -d)"
export GNUPGHOME
trap 'rm -rf "${GNUPGHOME}" "${WORK:-}"' EXIT
gpg -q --keyserver hkps://keyring.debian.org --recv-keys "${DEBIAN_CD_KEY}"
gpg -q --verify SHA512SUMS.sign SHA512SUMS
grep " ${BASE_ISO}\$" SHA512SUMS | sha512sum -c --quiet
echo "[+] ${BASE_ISO} verified"

# ------------------------------------------------------------------ assemble
WORK="$(mktemp -d)"
TREE="${WORK}/tree"
mkdir -p "${TREE}"
# Only the files that change are extracted; the rest is replayed from the base ISO
xorriso -osirrox on -indev "${ISO_CACHE}/${BASE_ISO}" \
    -extract /isolinux/menu.cfg "${TREE}/menu.cfg" \
    -extract /isolinux/gtk.cfg "${TREE}/gtk.cfg" \
    -extract /boot/grub/grub.cfg "${TREE}/grub.cfg" >/dev/null 2>&1
chmod u+w "${TREE}"/*.cfg

# Bundle the repository (tracked files only, no .git / venv / build output)
mkdir -p "${TREE}/phantom-node"
git -C "${ROOT}" ls-files -z | (cd "${ROOT}" && xargs -0 cp --parents -t "${TREE}/phantom-node")
git -C "${ROOT}" rev-parse HEAD > "${TREE}/phantom-node/.build-commit"

PRESEED="${TREE}/phantom-node/iso/preseed.cfg"
KERNEL_ARGS="file=/cdrom/phantom-node/iso/preseed.cfg locale=en_US.UTF-8"
# Parameters after "---" are also copied into the installed system's boot entry
POST_ARGS="quiet"
if [ "${PHANTOM_ISO_TEST:-0}" = "1" ]; then
    echo "[!] TEST BUILD: unattended with fixed test credentials - do not distribute"
    cat >> "${PRESEED}" <<'EOF'

### --- TEST BUILD ONLY (PHANTOM_ISO_TEST=1) ---
d-i keyboard-configuration/xkb-keymap select us
d-i passwd/user-password password phantom-test-pass
d-i passwd/user-password-again password phantom-test-pass
d-i partman-auto/disk string /dev/vda
d-i partman-crypto/passphrase password phantom-test-luks
d-i partman-crypto/passphrase-again password phantom-test-luks
d-i partman-crypto/weak_passphrase boolean true
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true
d-i partman-auto/confirm boolean true
d-i grub-installer/bootdev string /dev/vda
d-i finish-install/reboot_in_progress note
EOF
    KERNEL_ARGS="${KERNEL_ARGS} auto=true priority=critical"
    POST_ARGS="console=ttyS0,115200n8"
fi

# BIOS (isolinux): PhantomNode entries first and default
cat > "${TREE}/phantom.cfg" <<EOF
default phantomgui
label phantomgui
	menu label ^PhantomNode OS - Graphical install
	menu default
	kernel /install.amd/vmlinuz
	append vga=788 initrd=/install.amd/gtk/initrd.gz ${KERNEL_ARGS} --- ${POST_ARGS}
label phantomtxt
	menu label PhantomNode OS - ^Text install
	kernel /install.amd/vmlinuz
	append vga=788 initrd=/install.amd/initrd.gz ${KERNEL_ARGS} --- ${POST_ARGS}
EOF
sed -i '/menu default/d; /^default /d' "${TREE}/gtk.cfg"
sed -i 's/^include gtk.cfg/include phantom.cfg\ninclude gtk.cfg/' "${TREE}/menu.cfg"
sed -i 's/^menu title .*/menu title PhantomNode OS installer (BIOS mode)/' "${TREE}/menu.cfg"
# Debian auto-starts the speech-synthesis installer on timeout; on a headless
# server box the timeout should start the PhantomNode install instead
TIMEOUT_INITRD="/install.amd/gtk/initrd.gz"
[ "${PHANTOM_ISO_TEST:-0}" = "1" ] && TIMEOUT_INITRD="/install.amd/initrd.gz"
cat >> "${TREE}/menu.cfg" <<EOF
timeout 300
ontimeout /install.amd/vmlinuz vga=788 initrd=${TIMEOUT_INITRD} ${KERNEL_ARGS} --- ${POST_ARGS}
menu autoboot Press a key, otherwise PhantomNode OS install starts in # second{,s}...
EOF

# UEFI (GRUB): PhantomNode entries before the stock Debian ones
GRUB_ENTRIES="${WORK}/grub-entries.cfg"
cat > "${GRUB_ENTRIES}" <<EOF
set default=0
menuentry --hotkey=p 'PhantomNode OS - Graphical install' {
    set background_color=black
    linux    /install.amd/vmlinuz vga=788 ${KERNEL_ARGS} --- ${POST_ARGS}
    initrd   /install.amd/gtk/initrd.gz
}
menuentry --hotkey=t 'PhantomNode OS - Text install' {
    set background_color=black
    linux    /install.amd/vmlinuz vga=788 ${KERNEL_ARGS} --- ${POST_ARGS}
    initrd   /install.amd/initrd.gz
}
EOF
if [ "${PHANTOM_ISO_TEST:-0}" = "1" ]; then
    # Text installer first so it runs on the serial console
    sed -i 's/^set default=0/set default=1\nset timeout=3/' "${GRUB_ENTRIES}"
    sed -i 's/^default phantomgui/default phantomtxt\ntimeout 30/' "${TREE}/phantom.cfg"
    sed -i '/menu default/d' "${TREE}/phantom.cfg"
fi
# Insert before the first stock menuentry
awk -v f="${GRUB_ENTRIES}" '!done && /^menuentry/ { while ((getline l < f) > 0) print l; done=1 } { print }' \
    "${TREE}/grub.cfg" > "${TREE}/grub.cfg.new"
mv "${TREE}/grub.cfg.new" "${TREE}/grub.cfg"

# ------------------------------------------------------------------ write ISO
mkdir -p "$(dirname "${OUT}")"
rm -f "${OUT}"
echo "[*] Writing ${OUT}"
xorriso -indev "${ISO_CACHE}/${BASE_ISO}" -outdev "${OUT}" \
    -volid "PHANTOMNODE_${VERSION//./_}" \
    -map "${TREE}/phantom-node" /phantom-node \
    -map "${TREE}/phantom.cfg" /isolinux/phantom.cfg \
    -map "${TREE}/menu.cfg" /isolinux/menu.cfg \
    -map "${TREE}/gtk.cfg" /isolinux/gtk.cfg \
    -map "${TREE}/grub.cfg" /boot/grub/grub.cfg \
    -boot_image any replay \
    -compliance no_emul_toc \
    -padding included >/dev/null 2>&1

(cd "$(dirname "${OUT}")" && sha512sum "$(basename "${OUT}")" > "$(basename "${OUT}").sha512")
echo "[+] Built $(du -h "${OUT}" | cut -f1) ${OUT}"
echo "[+] SHA512: $(cut -d' ' -f1 "${OUT}.sha512")"
