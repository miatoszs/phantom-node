FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    tor \
    snowflake-client \
    privoxy \
    curl \
    ca-certificates \
    python3 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/lib/tor /var/log/tor /etc/tor /etc/privoxy /app \
    && chown -R debian-tor:debian-tor /var/lib/tor /var/log/tor

COPY entrypoint.sh /app/entrypoint.sh
COPY web_server.py /app/web_server.py
COPY privoxy.conf /etc/privoxy/config.template

RUN chmod +x /app/entrypoint.sh

EXPOSE 9080 9050 8118

ENTRYPOINT ["/app/entrypoint.sh"]
