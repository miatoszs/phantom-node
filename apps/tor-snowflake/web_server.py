import os
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

WEB_PORT = int(os.environ.get("WEB_PORT", 9080))
SOCKS_PORT = int(os.environ.get("SOCKS_PORT", 9050))
HTTP_PORT = int(os.environ.get("HTTP_PORT", 8118))
USE_SNOWFLAKE = os.environ.get("TOR_USE_SNOWFLAKE", "1") == "1"

def check_tor():
    proxy_handler = urllib.request.ProxyHandler({
        'http': f'http://127.0.0.1:{HTTP_PORT}',
        'https': f'http://127.0.0.1:{HTTP_PORT}'
    })
    opener = urllib.request.build_opener(proxy_handler)
    try:
        req = urllib.request.Request(
            'https://check.torproject.org/api/ip',
            headers={'User-Agent': 'PhantomNode-TorCheck/1.0'}
        )
        resp = opener.open(req, timeout=4)
        data = json.loads(resp.read().decode())
        return {
            "connected": True,
            "ip": data.get("IP", "Unknown"),
            "is_tor": data.get("IsTor", False)
        }
    except Exception as e:
        return {
            "connected": False,
            "ip": None,
            "is_tor": False,
            "error": str(e)
        }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tor Snowflake & Proxy • PhantomNode OS</title>
    <style>
        :root {
            --bg-base: #06070a;
            --bg-card: rgba(15, 18, 28, 0.85);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent-cyan: #00f2fe;
            --accent-purple: #c084fc;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --success: #10b981;
            --danger: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px 16px;
        }
        .container {
            max-width: 720px;
            width: 100%;
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(12px);
        }
        .header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }
        .icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: rgba(192, 132, 252, 0.1);
            border: 1px solid rgba(192, 132, 252, 0.25);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .title h1 {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .title p {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }
        .badge {
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-snowflake {
            background: rgba(0, 242, 254, 0.12);
            color: var(--accent-cyan);
            border: 1px solid rgba(0, 242, 254, 0.3);
        }
        .status-box {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 18px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        .dot-green { background: var(--success); box-shadow: 0 0 8px var(--success); }
        .dot-red { background: var(--danger); }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 18px;
        }
        @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
        .port-box {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
        }
        .port-box .label {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-dim);
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .port-box .value {
            font-family: monospace;
            font-size: 14px;
            color: var(--accent-cyan);
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .btn-copy {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-copy:hover {
            background: var(--accent-cyan);
            color: #000;
            border-color: var(--accent-cyan);
        }
        .relay-banner {
            background: rgba(192, 132, 252, 0.06);
            border: 1px solid rgba(192, 132, 252, 0.2);
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 12px;
            color: #e9d5ff;
            line-height: 1.5;
            margin-bottom: 18px;
        }
        .guide-section {
            margin-top: 14px;
        }
        .guide-title {
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        pre {
            background: #000;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 10px 12px;
            font-family: monospace;
            font-size: 12px;
            color: #cbd5e1;
            overflow-x: auto;
            margin-bottom: 10px;
        }
        .btn-refresh {
            background: rgba(0, 242, 254, 0.1);
            border: 1px solid rgba(0, 242, 254, 0.3);
            color: var(--accent-cyan);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-refresh:hover {
            background: var(--accent-cyan);
            color: #000;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <div class="icon">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path>
                        <path d="M2 12h20"></path>
                    </svg>
                </div>
                <div class="title">
                    <h1>Tor Snowflake &amp; Proxy <span class="badge badge-snowflake">Snowflake WebRTC</span></h1>
                    <p>Censorship-Resistant SOCKS5 &amp; HTTP Tor Gateway + Volunteer Relay</p>
                </div>
            </div>

            <div class="status-box">
                <div>
                    <span class="status-dot dot-green" id="tor-dot"></span>
                    <strong id="tor-status-text">Tor Routing Active</strong>
                    <div style="font-size: 11px; color: var(--text-dim); margin-top: 2px;" id="tor-ip-label">Checking exit IP...</div>
                </div>
                <button class="btn-refresh" onclick="fetchStatus()">Refresh Status</button>
            </div>

            <div class="grid">
                <div class="port-box">
                    <div class="label">SOCKS5 Proxy (Tor)</div>
                    <div class="value">
                        <span id="socks-val">--</span>
                        <button class="btn-copy" onclick="copyText('socks-val')">Copy</button>
                    </div>
                </div>
                <div class="port-box">
                    <div class="label">HTTP / HTTPS Proxy (Privoxy)</div>
                    <div class="value">
                        <span id="http-val">--</span>
                        <button class="btn-copy" onclick="copyText('http-val')">Copy</button>
                    </div>
                </div>
            </div>

            <div class="relay-banner">
                <strong>❄️ Snowflake Relay Status:</strong> Running alongside your proxy stack. This container contributes ephemeral WebRTC bandwidth back to the Tor anti-censorship network, allowing blocked users in authoritarian regions to bypass internet firewalls.
            </div>

            <div class="guide-section">
                <div class="guide-title">Quick Connection Commands (CLI / Terminal)</div>
                <pre id="curl-cmd">curl -x http://HOST:HTTP_PORT https://check.torproject.org/api/ip</pre>
                <div class="guide-title">Environment Variables (Bash / Zsh)</div>
                <pre id="env-cmd">export http_proxy=http://HOST:HTTP_PORT\nexport https_proxy=http://HOST:HTTP_PORT\nexport all_proxy=socks5://HOST:SOCKS_PORT</pre>
            </div>
        </div>
    </div>

    <script>
        const host = window.location.hostname || '127.0.0.1';
        let currentSocks = 9050;
        let currentHttp = 8118;

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                currentSocks = data.socks_port;
                currentHttp = data.http_port;

                document.getElementById('socks-val').innerText = `${host}:${currentSocks}`;
                document.getElementById('http-val').innerText = `${host}:${currentHttp}`;
                document.getElementById('curl-cmd').innerText = `curl -x http://${host}:${currentHttp} https://check.torproject.org/api/ip`;
                document.getElementById('env-cmd').innerText = `export http_proxy=http://${host}:${currentHttp}\\nexport https_proxy=http://${host}:${currentHttp}\\nexport all_proxy=socks5://${host}:${currentSocks}`;

                const ipLabel = document.getElementById('tor-ip-label');
                const dot = document.getElementById('tor-dot');
                const statusText = document.getElementById('tor-status-text');

                if (data.tor_connected) {
                    dot.className = 'status-dot dot-green';
                    statusText.innerText = 'Tor & Snowflake Active';
                    ipLabel.innerText = `Exit IP: ${data.tor_ip} • Verified Tor: ${data.is_tor ? 'YES' : 'NO'}`;
                } else {
                    dot.className = 'status-dot dot-red';
                    statusText.innerText = 'Tor Bootstrap In Progress';
                    ipLabel.innerText = 'Connecting to Snowflake bridge peers...';
                }
            } catch(e) {
                console.error(e);
            }
        }

        function copyText(id) {
            const txt = document.getElementById(id).innerText;
            navigator.clipboard.writeText(txt);
            alert('Copied to clipboard: ' + txt);
        }

        fetchStatus();
    </script>
</body>
</html>
"""

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            tor_info = check_tor()
            resp = {
                "status": "online",
                "tor_connected": tor_info.get("connected", False),
                "tor_ip": tor_info.get("ip"),
                "is_tor": tor_info.get("is_tor", False),
                "socks_port": SOCKS_PORT,
                "http_port": HTTP_PORT,
                "snowflake_enabled": USE_SNOWFLAKE,
                "error": tor_info.get("error")
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', WEB_PORT), ProxyHandler)
    print(f"Proxy Web Console running on port {WEB_PORT}")
    server.serve_forever()
