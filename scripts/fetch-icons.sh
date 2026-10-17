#!/usr/bin/env bash
# ==============================================================================
# PhantomNode OS - Refresh app icons from the selfh.st icon set
# https://github.com/selfhst/icons
#
# Icons are downloaded once into dashboard/static/icons and committed, so the
# dashboard never contacts a CDN at runtime (that would reveal every visit).
# Usage: scripts/fetch-icons.sh      (run from a dev machine, then commit)
# ==============================================================================
set -euo pipefail

CDN="https://cdn.jsdelivr.net/gh/selfhst/icons/svg"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/dashboard/static/icons"

# Icons whose default artwork is black: use the white "-light" variant so they
# stay visible on the dashboard's dark tiles
LIGHT_VARIANT=" cockpit kiwix matrix vaultwarden "

# Every manifest "icon" value that exists in the selfh.st set
ICONS=$(grep -ho '"icon": *"[^"]*"' "${ROOT}"/apps/*/manifest.json | sed 's/.*"\([^"]*\)"$/\1/' | sort -u)

for icon in ${ICONS}; do
    tmp="$(mktemp)"
    src="${icon}"
    [[ "${LIGHT_VARIANT}" == *" ${icon} "* ]] && src="${icon}-light"
    if curl -fsL -m 20 -o "${tmp}" "${CDN}/${src}.svg" && grep -q "<svg" "${tmp}"; then
        mv "${tmp}" "${DEST}/${icon}.svg"
        echo "[+] ${icon} (${src})"
    else
        rm -f "${tmp}"
        echo "[-] ${icon}: not in selfh.st set, keeping local icon"
    fi
done
