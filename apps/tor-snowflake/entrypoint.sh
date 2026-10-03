#!/bin/bash
set -e

TOR_USE_SNOWFLAKE=${TOR_USE_SNOWFLAKE:-1}
SOCKS_PORT=${SOCKS_PORT:-9050}
HTTP_PORT=${HTTP_PORT:-8118}
WEB_PORT=${WEB_PORT:-9080}

mkdir -p /var/lib/tor /var/log/tor /run/tor /var/log/privoxy /run/privoxy
chown -R debian-tor:debian-tor /var/lib/tor /var/log/tor /run/tor
chmod 700 /var/lib/tor

# Generate torrc
cat << TORRC > /etc/tor/torrc
SocksPort 0.0.0.0:${SOCKS_PORT}
DNSPort 0.0.0.0:9053
DataDirectory /var/lib/tor
PidFile /run/tor/tor.pid
RunAsDaemon 1
Log notice file /var/log/tor/notices.log
TORRC

if [ "$TOR_USE_SNOWFLAKE" = "1" ]; then
    echo "[PhantomNode] Configuring Tor to use Snowflake WebRTC Pluggable Transport..."
    cat << SNOWFLAKE >> /etc/tor/torrc
ClientTransportPlugin snowflake exec /usr/bin/snowflake-client -url https://snowflake-broker.torproject.net.global.prod.fastly.net/ -front cdn.sstatic.net -ice stun:stun.l.google.com:19302,stun:stun.voip.blackberry.com:3478,stun:stun.altariproductions.com:3478,stun:stun.antisip.com:3478
Bridge snowflake 192.0.2.3:1 2B280B23E1107BB62B72614777F6FFFE1952CC9F
UseBridges 1
SNOWFLAKE
fi

# Configure Privoxy
cat << PRIVOXY > /etc/privoxy/config
user-manual /usr/share/doc/privoxy/user-manual
confdir /etc/privoxy
logdir /var/log/privoxy
actionsfile match-all.action
actionsfile default.action
actionsfile user.action
filterfile default.filter
filterfile user.filter
logfile privoxy.log
listen-address 0.0.0.0:${HTTP_PORT}
toggle 1
enable-remote-toggle 0
enable-remote-http-toggle 0
enable-edit-actions 0
buffer-limit 4096
forward-socks5t / 127.0.0.1:${SOCKS_PORT} .
PRIVOXY

echo "[PhantomNode] Launching Tor daemon..."
su -s /bin/bash debian-tor -c "/usr/bin/tor -f /etc/tor/torrc"

echo "[PhantomNode] Launching Privoxy HTTP proxy on :${HTTP_PORT}..."
privoxy --pidfile /run/privoxy/privoxy.pid /etc/privoxy/config

echo "[PhantomNode] Launching Proxy Web Console on :${WEB_PORT}..."
exec python3 /app/web_server.py
