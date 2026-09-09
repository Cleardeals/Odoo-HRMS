# Odoo HRMS — deployment

> **This instance is mid-migration.** Infrastructure is being moved to Terraform
> and deploys to Cloud Build; see
> [docs/infrastructure_migration_plan.md](docs/infrastructure_migration_plan.md)
> for the phases, the gates, and what has already been done.
>
> **There is currently no automated deploy path.** The GitHub Actions workflow
> that used to deploy has been removed, and the Cloud Build trigger that
> replaces it is not enabled yet. Read "Deploying right now", below.
>
> **Phases 4b, 4c, 5, 6, 7 and 8 are done (2026-09-09).** In short:
>
> * the application lives at `/opt/odoo-hrms`, **not** `/home/tech/odoo-project`;
> * OS Login is on — SSH lands as `tech_cleardeals_in`, and the old metadata SSH
>   keys no longer work on this VM;
> * **IAP is the only route to port 22**; the world-open SSH and RDP rules are gone;
> * logs and metrics reach Cloud Logging and Monitoring, and five alert policies
>   are live and confirmed to deliver;
> * snapshots run 4-hourly with 30-day retention, and `gs://cleardeals-hrms-backups`
>   exists for logical dumps — though **nothing writes to it on a schedule yet**.
>
> Secret Manager is reachable from the box, so the only thing still blocking
> Cloud Build CD is the one-time GitHub App install.

---

## How this is meant to work

```
pull request  ->  Cloud Build CI (cloudbuild.ci.yaml)
                  gates only: tests, config, OpenAPI parity, image contents.
                  Builds no production image. Touches no VM.

merge to main ->  Cloud Build CD (cloudbuild.yaml)
                  re-runs every gate, builds, pushes to Artifact Registry
                  tagged by commit SHA, then QUEUES FOR HUMAN APPROVAL.

approval      ->  scripts/deploy.sh, over an IAP tunnel, on the VM:
                  render config from Secret Manager into tmpfs, pull the image,
                  optional module upgrade, swap, health gate, edge gate,
                  rollback on failure, prune by image count.
```

Config is never written by CI. `odoo.prod.conf` is committed with placeholders;
`scripts/render_odoo_conf.sh` injects the two Secret Manager values into
`/dev/shm/odoo.conf` — tmpfs, so the only file containing both the config and
the secrets is memory-backed and never lands in a disk snapshot.

Application code is **baked into the image** at `/opt/cleardeals-addons`. It is
not bind-mounted, which is what makes the SHA tag an honest answer to "what is
in production" and makes rollback real.

## Deploying right now (before Cloud Build CD is enabled)

Two things must happen before the pipeline can run, and neither is optional:

1. **A GitHub org admin installs the Cloud Build GitHub App** and grants it
   `Cleardeals/Odoo-HRMS`, once, at
   <https://console.cloud.google.com/cloud-build/triggers/connect>. Terraform
   cannot do this. Then set `cloudbuild_github_connected = true`.
2. ~~**The Phase 4b maintenance window.**~~ **DONE 2026-09-09.**
   `hrms-prod-vm@` is attached with the `cloud-platform` scope, and
   `gcloud secrets versions access latest` was verified working from the VM for
   both `odoo-db-password` and `odoo-admin-passwd`. So `cloudbuild_cd_enabled`
   can be set to `true` as soon as item 1 is done.

Until both are done, deploy by hand, on the VM:

```bash
gcloud compute ssh tech@odoo-hrms-prod \
  --project=<project-id> --zone=us-central1-c --tunnel-through-iap
```

```bash
cd /opt/odoo-hrms && sudo git -c safe.directory='*' fetch --depth 1 origin main && sudo git -c safe.directory='*' reset --hard FETCH_HEAD
```

then follow `scripts/deploy.sh` by hand. The render step now works — 4b is
done. Odoo must still never be started without a config: its built-in defaults
include `list_db = True`, which serves the database manager to unauthenticated
requests.

Note that the VM's checkout is still on the pre-migration commit and the running
container is still the old `odoo-hrms:latest` with addons **bind-mounted**. The
first real deploy is what moves it onto the SHA-tagged image with addons baked
in.

### Why the old workflow was removed rather than left as a fallback

`.github/workflows/deploy.yml` SSHed in with a long-lived private key from a
repository secret, wrote `odoo.conf` from another secret, ran
`docker compose build` **on the production VM** in competition with Odoo and
Postgres, and reported success whether or not Odoo came back up.

It was deleted in the same commit that changed `docker-compose.yml` and the
`Dockerfile`, because from that commit onward it was **actively dangerous**, not
merely obsolete:

* it writes `./odoo.conf`, which compose no longer mounts — compose now mounts
  `/dev/shm/odoo.conf`, which that workflow never creates. Odoo would start on
  its **built-in defaults**, including `list_db = True`;
* the config in the `ODOO_CONF` secret sets
  `addons_path = /mnt/extra-addons/custom`, and the base image declares
  `/mnt/extra-addons` as a `VOLUME`, so with the bind mount now gone the addons
  are hidden by an anonymous volume and **every custom module disappears**.

So merging that compose change while the workflow was still armed would have
produced an outage *and* an exposed database manager on the next push to `main`.
Leaving it in place "just in case" would have been the more dangerous choice.

## Operating notes

**IAP is now the only way in (Phase 5).** `default-allow-ssh`,
`default-allow-rdp` and both health-check rules were deleted; `allow-iap-ssh`
permits port 22 only from `35.235.240.0/20`. Ports 80 and 443 remain open, and
port 80 must stay open or Traefik's ACME renewal breaks.

**SSH is via IAP, under OS Login.** Pass `tech@` and gcloud maps it to the OS
Login account — it prints `Using OS Login user [tech_cleardeals_in] instead of
requested user [tech]`, which is expected, not a warning to fix. Your local
username does not resolve.

Access is IAM now, not metadata keys: `tech@` has sudo (`osAdminLogin`);
`developer1@`, `developer2@` and `solutionanalysts@` can log in without sudo
(`compute.osLogin`). The old project-metadata SSH keys are inert on this VM.

The Linux user `tech` still exists and still owns the checkout, which is why
every git command against `/opt/odoo-hrms` needs `-c safe.directory='*'`.

```bash
gcloud compute ssh tech@odoo-hrms-prod --project=<project-id> --zone=us-central1-c --tunnel-through-iap
```

**Traefik's dashboard is on loopback only.** Reach it over the tunnel — an empty
router table is the fastest diagnosis of a routing outage:

```bash
gcloud compute ssh tech@odoo-hrms-prod --zone=us-central1-c --tunnel-through-iap -- -L 8080:localhost:8080
```

A healthy stack reports **5** routers.

**Alerting is live (Phase 7).** Five policies mail the operator: site
unreachable (P1), disk above 85% (P2), snapshots stopped for over 5h (P2b),
memory above 85% (P3), TLS expiring within 15 days (P4). The notification path
was proven end to end by deliberately tripping an alert — a policy attached to
an *unverified* channel looks perfectly healthy in the console and pages nobody,
so if you ever recreate the channel, prove delivery rather than assuming it.

**Do not run `apt upgrade` on this VM.** `docker-ce` and `docker-ce-cli` are
held at 28.5.2 by `apt-mark hold`, after Docker 29 broke Traefik's provider on
2026-02-16. `containerd.io` is *not* held, so a blanket upgrade would move it
underneath a pinned Docker. See the migration plan, §0b.

**Health checks that actually mean something:**

```bash
sudo docker compose exec -T odoo curl -fsS "http://localhost:8069/web/health?db_server_status=1"
```

`/web/health` **without** `db_server_status=1` returns 200 without touching the
database, and `/web/database/selector` renders unconditionally — neither is a
health check. Both were in use here before this migration.

**The public path, from the outside in:**

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' --resolve hr.cleardeals.xyz:443:127.0.0.1 https://hr.cleardeals.xyz/web/login
```

It must speak TLS. A probe on port 80 returns 301 even for a hostname matching
no router, because the redirect is on the entrypoint and runs before routing —
so a port-80 check passes straight through a total routing outage.

## Backups

Automated disk snapshots run **every 4 hours from 02:00 UTC with 30-day
retention** (`hrms-prod-4h`, attached to the boot disk, managed in
`infrastructure/terraform/compute.tf`). The old `default-schedule-1` — daily at
12:00, 14 days — is still defined but **detached**.

The 4-hourly cadence is also what makes the "snapshots have stopped" alert
possible at all: Cloud Monitoring refuses an absence window longer than 23h30m,
so against a daily schedule there was no usable window.

Snapshots are **crash-consistent, not application-consistent**. A logical dump
is what makes a clean restore certain, and there is now a bucket for it —
`gs://cleardeals-hrms-backups`:

```bash
sudo docker exec odoo-db pg_dump -U odoo odoo_hrms_db | gzip > /tmp/odoo_hrms_$(date -u +%Y%m%d).sql.gz
```

```bash
gcloud storage cp /tmp/odoo_hrms_*.sql.gz gs://cleardeals-hrms-backups/
```

**Nothing does this automatically yet.** The bucket exists and the VM can write
to it, but no schedule writes anything, so the only logical dumps are the ones
somebody takes by hand.

The VM holds `objectCreator` + `objectViewer` on that bucket and deliberately
**not** `objectAdmin`: it can write and verify its own backups but cannot delete
them, so a compromise of this host cannot destroy them. (`objectViewer` is not
optional — `gcloud storage cp` issues a GET before writing and 403s without it.)
Note this does not protect against a project Editor or Owner, who still hold
`legacyObjectOwner`.

The boot disk now has `auto_delete = false`, so it survives deletion of the
instance and a whole-VM recovery is a matter of attaching it to a new one.

## Resource allocation (e2-medium: 2 shared vCPU, 4 GB)

`odoo.prod.conf` runs 3 HTTP workers + 1 cron + 1 gevent = 5 processes.

`db_maxconn = 5` is not arbitrary and should not be raised without reading the
comment next to it: it is per *process*, Odoo keeps **two** pools per process,
so the ceiling is `5 × 2 × 5 = 50` against `max_connections = 60` (57 usable
after Postgres's reserved superuser slots). The previous value of 64 gave a
ceiling of 640.

## Troubleshooting

| Symptom | First thing to check |
| --- | --- |
| Site 404s, Odoo healthy | Traefik's router count (see above). Zero routers means the docker provider died. |
| Site unreachable | Is the instance running; then Odoo's own health with `db_server_status=1`; then the router count; then the certificate. |
| Modules missing after a deploy | Is anything mounted over `/opt/cleardeals-addons`, and does `addons_path` still point there. |
| Odoo starts but config looks wrong | Does `/dev/shm/odoo.conf` exist. It is tmpfs — it does not survive a reboot, so `render_odoo_conf.sh` must run before compose. |
| Disk filling | `docker system df`, `journalctl --disk-usage`, `du -sh /var/log/google-cloud-ops-agent`. |

## Support

- Odoo 19 documentation: <https://www.odoo.com/documentation/19.0/>
- Migration plan and rationale: [docs/infrastructure_migration_plan.md](docs/infrastructure_migration_plan.md)
