# LiveKit SFU VPS Setup (systemd)

This project now uses LiveKit as an SFU for screen sharing. Gunicorn remains the signaling + dashboard backend.

## 1) Install LiveKit binary

Download the LiveKit server binary on the VPS and place it in `/usr/local/bin/livekit-server`.

## 2) LiveKit config (`/etc/livekit.yaml`)

```yaml
port: 7880

rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: true

redis:
  address: 127.0.0.1:6379

keys:
  LIVEKIT_API_KEY: LIVEKIT_API_SECRET
```

Notes:
- Reuse the existing Redis instance at `127.0.0.1:6379`.
- Use the same `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` that the app uses in `.env`.
- Keep TLS termination at your existing reverse proxy (Nginx/Caddy). Route `wss://livekit.your-domain.com` to `127.0.0.1:7880`.

## 3) systemd service (`/etc/systemd/system/livekit.service`)

```ini
[Unit]
Description=LiveKit SFU
After=network.target redis-server.service

[Service]
Type=simple
User=livekit
ExecStart=/usr/local/bin/livekit-server --config /etc/livekit.yaml
Restart=always
RestartSec=2
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
```

Then enable + start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable livekit
sudo systemctl start livekit
sudo systemctl status livekit
```

## 4) Firewall / ports

Allow:
- TCP 7880 (LiveKit HTTP/WSS)
- TCP 7881 (optional TCP transport)
- UDP 50000-60000 (RTP media)

## 5) App environment

Set in `.env` (VPS). If `.env` is protected, set `ENV_FILE=.env2` in your systemd service and place these values in `.env2`:

```
LIVEKIT_URL=wss://livekit.your-domain.com
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

## 6) LiveKit client JS (browser)

Place the LiveKit UMD bundle at `/opt/apps/confquiz/static/js/livekit-client.min.js` so clients do not depend on CDN access.

Example (VPS):

```bash
curl -L https://registry.npmjs.org/livekit-client/-/livekit-client-2.17.0.tgz -o /tmp/livekit-client.tgz
tar -xzf /tmp/livekit-client.tgz -C /tmp
sudo cp /tmp/package/dist/livekit-client.umd.js /opt/apps/confquiz/static/js/livekit-client.min.js
```

## 7) Redis reliability

LiveKit and the app both depend on Redis. Ensure Redis is supervised and has adequate memory. On VPS: `systemctl status redis`.
