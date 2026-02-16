# Odoo HRMS Production Deployment Guide

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed on your GCP e2-medium instance
- Domain DNS pointing to your instance IP (hr.cleardeals.xyz)
- Ports 80 and 443 open in firewall

### 2. Build and Deploy

```bash
# Build the Odoo image
docker build -t odoo-hrms:latest .

# Start the entire stack
docker-compose up -d

# View logs
docker-compose logs -f odoo

# Check status
docker-compose ps
```

### 3. First-Time Setup

1. **Access Odoo**: Navigate to `https://hr.cleardeals.xyz`
2. **Create Database**:
   - Master Password: Set a strong password
   - Database Name: `production`
   - Email: Your admin email
   - Password: Admin password
   - Load demonstration data: **No** (for production)

### 4. Monitoring

```bash
# View all logs
docker-compose logs -f

# View only Odoo logs
docker-compose logs -f odoo

# View Traefik dashboard
# Access: http://your-server-ip:8080
# ⚠️  Disable this in production or add authentication

# Check container health
docker ps
```

### 5. Maintenance

```bash
# Restart services
docker-compose restart odoo

# Stop all services
docker-compose down

# Backup database
docker exec odoo-db pg_dump -U odoo postgres > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i odoo-db psql -U odoo postgres < backup_file.sql
```

### 6. Updating

```bash
# Pull latest code
git pull

# Rebuild image
docker build -t odoo-hrms:latest .

# Recreate containers
docker-compose up -d --build

# Update Odoo modules
docker exec -it odoo-app odoo -u all -d production --stop-after-init
```

## Architecture

```
Internet
   ↓
Traefik (Port 80/443)
   ├─→ SSL Termination (Let's Encrypt)
   ├─→ HTTP → HTTPS Redirect
   └─→ Routing
       ├─→ Odoo Main (Port 8069)
       └─→ Longpolling (Port 8072)
          ↓
PostgreSQL 17 (Internal)
```

## Resource Allocation (e2-medium: 2 vCPU, 4GB RAM)

- **Odoo**: ~2.5GB RAM (3 workers)
- **PostgreSQL**: ~1GB RAM
- **Traefik**: ~100MB RAM
- **System**: ~400MB RAM

## Security Checklist

- [x] Non-root user in Docker containers
- [x] Read-only config mounts
- [x] SSL/TLS with automatic renewal
- [x] Security headers (HSTS, X-Frame-Options, etc.)
- [x] HTTP to HTTPS redirect
- [ ] Change database password (update .env)
- [ ] Disable Traefik dashboard or add authentication
- [ ] Configure firewall (allow only 80, 443, SSH)
- [ ] Enable fail2ban for SSH protection
- [ ] Regular backups (database + filestore)

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs odoo

# Check if ports are available
sudo netstat -tlnp | grep -E ':(80|443|8069|8072)'
```

### Database connection error
```bash
# Verify database is healthy
docker-compose ps db

# Test connection
docker exec odoo-db pg_isready -U odoo
```

### SSL certificate issues
```bash
# Check Traefik logs
docker-compose logs traefik

# Verify domain DNS
nslookup hr.cleardeals.xyz

# Check Let's Encrypt rate limits
# Max 5 failures per hour per hostname
```

### Out of memory errors
```bash
# Check resource usage
docker stats

# Reduce Odoo workers in odoo.conf
# workers = 2 (instead of 3)
```

## File Structure

```
Odoo-HRMS/
├── Dockerfile              # Odoo 19 with venv
├── docker-compose.yml      # Full stack orchestration
├── entrypoint.sh          # Custom startup script
├── odoo.conf              # Odoo configuration
├── requirements.txt       # Python dependencies
├── custom_addons/         # Your custom modules
├── odoo-web-data/         # Filestore (persistent)
├── odoo-db-data/          # PostgreSQL data (persistent)
└── letsencrypt/           # SSL certificates
```

## Performance Tips

1. **After initial setup, enable page caching** in odoo.conf
2. **Monitor slow queries** in PostgreSQL logs
3. **Use CDN** for static assets if traffic grows
4. **Schedule regular VACUUM** on PostgreSQL
5. **Archive old data** to keep database lean

## Support

- Odoo Documentation: https://www.odoo.com/documentation/19.0/
- Community Forum: https://www.odoo.com/forum/help-1
- Issues: Check container logs first
