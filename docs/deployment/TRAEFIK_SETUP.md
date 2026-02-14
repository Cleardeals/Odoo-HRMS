# Traefik Deployment Guide

## 1. Create the External Network
Traefik needs a common network to discover other containers.

```bash
docker network create proxy-net
```

## 2. Deploy Traefik (The Gateway)
This stack handles SSL certificates and routing.

```bash
# Start Traefik
docker-compose -f docker-compose.traefik.yml up -d
```

## 3. Deploy Odoo
The Odoo stack attaches to the `proxy-net` network.

```bash
# Start Odoo
docker-compose up -d
```

## Verification
- **Odoo**: https://hr.cleardeals.xyz
- **Traefik Dashboard**: https://traefik.cleardeals.xyz (Requires DNS record)

## Troubleshooting
- Ensure DNS `hr.cleardeals.xyz` points to your VM IP.
- Check Traefik logs: `docker logs traefik-proxy` to see certificate generation status.
