# Odoo HRMS - GCP VM Deployment Guide

## Overview
This configuration is designed for a single Google Cloud Platform (GCP) Compute Engine instance hosting both the Odoo application and the PostgreSQL database.

## Architecture
- **Single VM**: e2-medium (2 vCPU, 4GB RAM)
- **OS**: Ubuntu 22.04 LTS (Recommended)
- **Database**: PostgreSQL 14+ (Local on VM, Dockerized)
- **Application**: Odoo 19.0 (Local on VM, Dockerized)
- **Web Server**: Nginx (Reverse Proxy)

## Production Configuration Details

### Database Settings (Local)
The configuration is set to use the local PostgreSQL socket or localhost.
- **Host**: `localhost` / `127.0.0.1` or socket
- **Port**: 5432
- **User**: `odoo`
- **Password**: Securely generated password (store in env var)

### Worker Calculation
Formula: `(vCPU * 2) + 1` = 5 workers for 2 vCPU.
**However**, memory is the bottleneck on 4GB RAM.
- **Workers Configured**: 3
- **Memory Limit Soft**: 512MB
- **Memory Limit Hard**: 640MB
- **Total RAM Required**: ~2GB for Odoo workers + ~1GB for Postgres + ~1GB OS.
- **Note**: This is a tight configuration. Monitor memory closely.
- **Memory Limit Soft**: 640MB
- **Memory Limit Hard**: 768MB
- **Total RAM Required**: ~7GB for workers + 1-2GB for Postgres + 1GB OS ≈ 10GB+ recommended.

### High Availability & Scaling
This single-VM setup is "Pet" architecture. For HA, migrate to:
- Cloud SQL for database
- Managed Instance Groups for Odoo
- Internal Load Balancer

## GCP Deployment Best Practices

### 1. Environment Variables
Store secrets in `.env` file or use Secret Manager.
- `DB_PASSWORD`
- `ADMIN_MASTER_PASSWORD`
- `SMTP_PASSWORD`

### 2. Monitoring (Stackdriver)
Enable the Cloud Ops Agent on the VM to track:
- Memory utilization (Critical for Odoo)
- Disk space (Log growth, filestore growth)
- PostgreSQL metrics

### 3. Backup Strategy
Since connection is local:
- **Database**: Scheduled `pg_dump` to Google Cloud Storage (GCS) bucket.
- **Filestore**: Scheduled `rsync` of `/opt/odoo/data` to GCS bucket.
- **Snapshots**: Daily disk snapshots of the VM.

### 4. Security
- **Firewall**: Allow Ingress TCP 80/443 only. Block 8069/5432 external access.
- **Service Account**: Use a custom service account with minimal permissions (Storage Object Creator for backups).

## Performance Tuning
- **Postgres**: Tune `shared_buffers` (25% RAM), `effective_cache_size` (50% RAM), and `work_mem`.
- **System**: Increase max open files (`ulimit -n`).
