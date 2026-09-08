# HRMS infrastructure migration — Terraform, Cloud Build, IAP, observability

Bring `odoo-hrms-prod` to the same operational standard as the Odoo CRM
instance: infrastructure declared in Terraform and imported from what already
runs, deploys moved off GitHub Actions onto Cloud Build with an approval gate,
SSH reachable only through IAP, secrets out of CI variables and into Secret
Manager, and the Ops Agent actually shipping logs and metrics so alerts can
exist at all.

The Odoo migration is the template. It is not copied blindly: this document
records where HRMS genuinely differs, because four of those differences change
the order of the work and one of them is a harder failure than anything the
Odoo migration hit.

> **This repository is PUBLIC.** No project identifier, address, or secret
> belongs in it. `<PROJECT_ID>` and `<PROJECT_NUMBER>` below are placeholders;
> real values live in `infrastructure/terraform/terraform.tfvars`, which is
> gitignored.

**Explicitly out of scope** (per instruction): machine-type upgrade and boot
disk growth. §7 explains why the disk does not need growing anyway — there is
~10 GB of reclaimable garbage on a 30 GB disk, and reclaiming it is cheaper and
safer than resizing.

---

## 0. Verified current state

Everything in this section was measured against the live project and the running
VM on 8 Sep 2026, not assumed. Anything not measured is marked as such and
appears as a Phase 0 gate.

### Project and platform

| Fact | Value |
| --- | --- |
| Project | `<PROJECT_ID>` (number `<PROJECT_NUMBER>`) — dedicated to HRMS |
| Instance | `odoo-hrms-prod`, `us-central1-c`, `e2-medium`, deletion protection **on** |
| Boot disk | `odoo-hrms-prod`, 30 GB `pd-balanced`, Debian 12 bookworm, **`autoDelete: true`** |
| Static address | `odoo-hrms-production`, `IN_USE`, PREMIUM tier |
| Public host | `hr.cleardeals.xyz` |
| Snapshots | `default-schedule-1` — daily 12:00 UTC, 14-day retention, attached, working (6 consecutive dailies confirmed) |
| Load balancers | **none** (0 forwarding rules, 0 target pools) |
| Staging | **none** — there is no second environment to rehearse on |

### What does not exist yet

Zero of each, confirmed via API: GCS buckets, Artifact Registry repositories,
Secret Manager secrets, Cloud Build triggers, alert policies, notification
channels, uptime checks, log-based metrics, dedicated service accounts.

APIs **not** enabled: `artifactregistry`, `secretmanager`, `cloudbuild`, `iap`.
Already enabled: `compute`, `logging`, `monitoring`, `osconfig`, `oslogin`,
`storage`, `bigquery` (unused — see §1.5).

### On the VM

| Fact | Value |
| --- | --- |
| Checkout | `/home/tech/odoo-project` — a **personal home directory**, shallow clone, 228 MB `.git` |
| Compose project name | `odoo-project`, **derived from the directory** (no `name:` pin) |
| Containers | `odoo-app` / `odoo-db` / `traefik`, all **up 3 months** |
| Running image | `odoo-hrms:latest` — a floating tag, built on this VM. No `.env`, nothing pins a SHA |
| Docker | Engine 28.5.2, Compose v5.0.2, `overlay2`, **no `/etc/docker/daemon.json`** |
| Docker packages | `docker-ce`/`-cli` **held** at 28.5.2 (downgraded from 29.2.1 on 2026-02-16); `containerd.io` 2.2.1 **unheld**; candidates 29.8.0 / 2.3.4 |
| Last boot | `2026-05-19` — daemon and all containers started together, 16 weeks ago |
| Database | single DB `odoo_hrms_db` |
| Runtime config | `/home/tech/odoo-project/odoo.conf`, mode **644**, contains a live `db_password` |
| Config delivery | written on every deploy from the GitHub Actions secret `ODOO_CONF` |
| Disk | 30 GB, **21 GB used (74%), 7.4 GB free** |
| VM service account | `<PROJECT_NUMBER>-compute@developer.gserviceaccount.com` (compute default) |
| VM scopes | `devstorage.read_only`, `logging.write`, `monitoring.write`, `service.management.readonly`, `servicecontrol`, `trace.append` — **not** `cloud-platform` |
| OS Login | **off** on the instance; 5 never-expiring SSH keys in project metadata |
| Ops Agent | installed, `active`, `enabled` — **and shipping nothing** |

### Disk breakdown (measured)

| Consumer | Size | Reclaimable |
| --- | --- | --- |
| `/var/lib/docker/overlay2` | 7.8 GB | no (live layers) |
| `/var/lib/containerd/…snapshotter.v1.overlayfs` | 5.2 GB | **yes, pending verification** |
| `/var/log/journal` | 2.9 GB | **yes** (~2.7 GB) |
| `/home/tech` (checkout + filestore + DB) | 2.5 GB | partly (`.git` 228 MB) |
| `/var/lib/containerd/…content.v1.content` | 1.3 GB | **yes, pending verification** |
| `/var/log/google-cloud-ops-agent` | 599 MB | **yes** |
| container `*-json.log` | 534 MB | **yes** |
| `/var/lib/docker/volumes` | 159 MB | no |
| `/var/lib/apt` | 147 MB | yes (~140 MB) |

Application data is small: `odoo-db-data` 224 MB, `odoo-web-data` (filestore)
759 MB. The disk is 74% full almost entirely because of logs and an untracked
container store.

---

## 1. Where HRMS differs from the Odoo migration

These are the differences that change the plan. Everything else ports across
nearly verbatim.

### 1.1 The Ops Agent failure is worse here, and the cause is different

On Odoo, the agent was dropping data because the attached service account held
BigQuery roles only. Here the attached service account — the compute default —
**holds no project IAM role whatsoever.** Verified directly:

```
gcloud projects get-iam-policy <PROJECT_ID> \
  --flatten="bindings[].members" \
  --filter="bindings.members:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --format="value(bindings.role)"
→ (empty)
```

The consequences, all measured:

* `agent.googleapis.com/memory/percent_used` — **0 time series.**
* `agent.googleapis.com/disk/percent_used` — **0 time series.**
* Cloud Logging holds only `cloudaudit.googleapis.com/activity`,
  `cloudaudit.googleapis.com/system_event`, and
  `networkanalyzer.googleapis.com/analyzer_reports`. **No syslog, no agent logs,
  no container logs — ever.**
* `journalctl -u google-cloud-ops-agent-opentelemetry-collector` shows **120
  PermissionDenied entries in a 20-minute window**, with `dropped_items: 910` in
  a single batch.
* `gcloud compute instances os-inventory describe` returns *"OS inventory data
  was not found"* despite `enable-osconfig=TRUE` and the
  `goog-ops-agent-policy` label.

So this is not "alerting is missing". It is that **no telemetry from this
machine has ever reached Google**, and the agent has spent months writing 599 MB
of its own failure messages onto a disk that is 74% full. Every diagnosis of
every past incident on this box came from `docker logs` over SSH, and a deploy
recreates the container that holds them.

Nothing in Phase 7 can be built before this is fixed. It is the same dependency
the Odoo migration hit, and it is the reason the service-account work is
Phase 4a rather than something to tidy up later.

### 1.2 The VM's scopes, not just its roles, block the deploy pipeline

Odoo's VM already had `cloud-platform` scope, so attaching a better service
account was purely an IAM change. Here the scopes are the restricted default
set. Scopes are a hard ceiling *above* IAM: granting a role changes nothing if
the access token cannot carry it.

Two pipeline requirements sit outside the current scope set:

* pulling the deploy image from Artifact Registry;
* reading `odoo-admin-passwd` / `odoo-db-password` from Secret Manager during
  `render_odoo_conf.sh`.

Secret Manager unambiguously requires `cloud-platform`. Artifact Registry
docker-pull *may* be satisfied by the existing `devstorage.read_only` scope —
this is genuinely uncertain and **must be tested, not assumed** (Phase 4b gate).
Either way Secret Manager forces the change, so the outcome is the same.

**Changing service account or scopes requires the instance to be STOPPED.**
That is the one unavoidable stop in this plan, and it is why §5 defines a single
maintenance window even though no machine or disk change is wanted. It is a
stop-and-start of a few minutes, not a resize.

### 1.3 The addons are baked to a path Docker will hide

`Dockerfile:64` copies `custom_addons` to `/mnt/extra-addons/custom`, and
`odoo.conf` sets `addons_path = /mnt/extra-addons/custom,…`. But the base image
declares that path as a volume — verified directly:

```
docker image inspect odoo:19.0 --format '{{json .Config.Volumes}}'
→ {"/mnt/extra-addons":{},"/var/lib/odoo":{}}
```

At runtime Docker mounts an anonymous empty volume over `/mnt/extra-addons`,
silently hiding anything baked beneath it. **This is the exact failure that took
Odoo production down** — addons vanished, modules never loaded, the UI failed on
a view controller and crons died on a `KeyError`.

HRMS is not broken today only because `docker-compose.yml` bind-mounts
`./custom_addons` over the same path, which masks it. That mask is precisely
what Phase 3 must remove: baking the addons into the image is what makes a SHA
tag an honest answer to "what is in production" and what makes rollback real.

So the move to `/opt/cleardeals-addons` is not a stylistic port from the Odoo
repo. **Removing the bind mount without also moving the bake path takes HRMS
down**, and the failure appears at runtime with no build error.

### 1.4 The runtime config has three defects that must be fixed while templating

Read from the live `odoo.conf`. These are not migration artifacts — they are
current production state, and the migration is the moment they get fixed because
the file becomes reviewable for the first time.

**`dbfilter = ^.*$` and no `db_name`.** The instance is not pinned to a
database. `list_db = False` is already set, which is the important half, but the
Odoo standard is both: `db_name = odoo_hrms_db`, `dbfilter = ^odoo_hrms_db$`.
The database name was confirmed on the box — a single DB, `odoo_hrms_db`.

**`admin_passwd` is commented out** (`odoo.conf:35`). With no value set, Odoo
falls back to its default master password. `list_db = False` gates the database
manager UI, so this is not currently an open door — but it is one config change
away from being one, and the placeholder-plus-Secret-Manager pattern removes the
question entirely.

**`db_maxconn = 64` against `max_connections = 60`.** This is a latent
capacity trap, and the arithmetic is the same one documented in Odoo's
`odoo.prod.conf`. `db_maxconn` is per *process*, and Odoo maintains **two**
pools per process (`_Pool` and `_Pool_readonly`; `http.py` takes a readonly
cursor on every request, and with no replica configured those are separate
physical connections to the same Postgres). With `workers = 3` and
`max_cron_threads = 1`, `process_spawn()` yields 3 HTTP + 1 cron + 1 gevent = 5
processes:

```
5 processes × 2 pools × 64 = 640 possible connections
docker-compose.yml sets  max_connections = 60
```

Checked before reporting: `docker logs odoo-db` over the last 30 days contains
**zero** `"too many clients"` entries. Pools fill lazily and load is low, so it
has not bitten. It will present as intermittent `FATAL: sorry, too many clients
already` under load, which reads like an application bug for weeks.

**FIXED in Phase 2:** `db_maxconn = 5`, giving 5 × 2 × 5 = **50** against
`max_connections = 60`. Five rather than six deliberately — Postgres reserves 3
connections for superusers by default (`superuser_reserved_connections`), so the
usable ceiling is 57 and 50 leaves real headroom instead of an exact fit. The
arithmetic and the process count are in a comment in `odoo.prod.conf`, next to
the value, because the next person to change `workers` needs to see it.

Also checked and **not** a problem: `limit_memory_soft`/`hard` (512 MB / 640 MB)
look low against Odoo's typical per-worker virtual memory, but
`docker logs odoo-app` shows **zero** `"virtual memory limit reached"` in 30
days. Workers are not recycling. Worth watching once metrics exist; not worth
changing blind.

### 1.5 Simplifications HRMS gets for free

* **No BigQuery.** `requirements.txt` contains no `google-cloud-*` package, and
  `entrypoint.sh`'s BigQuery probe is `… || echo`, so it has always printed
  `✗ BigQuery not available` harmlessly. Every BigQuery service account, role,
  and cross-project grant in the Odoo Terraform is **dropped**. (Worth cleaning
  the misleading probe and the `description="…with BigQuery support"` label.)
* **No staging instance**, so no `stage_*` resources, no second zone, no
  `odoo-stage-web` firewall rule. The flip side is there is nowhere to rehearse
  — §6 covers that risk.
* **Traefik v3.2, and the Engine mismatch already happened here.** Odoo had to
  move v2.10 → v2.11 mid-migration because v2.10's Docker client spoke API 1.24
  against an Engine that required 1.44, killing the provider so it served 404
  for everything. HRMS hit the same wall on **2026-02-16** and resolved it the
  other way round: Traefik went to v3.2 and Docker was *downgraded* 29.2.1 →
  28.5.2 and pinned with `apt-mark hold`. So this migration inherits a fought
  battle rather than a pending one — but also an undocumented pin. Phase 0b has
  the full timeline and the two live consequences.
* **IAP and OS Login prerequisites are already granted.** `developer1@` and
  `developer2@` hold `roles/iap.tunnelResourceAccessor` and
  `roles/compute.osLogin`. The Odoo migration had to have those granted first.
  Verified working: an IAP-tunnelled SSH session to this VM succeeds today.

### 1.6 Firewall differences

| Rule | State | Action |
| --- | --- | --- |
| `default-allow-ssh` | tcp:22 from `0.0.0.0/0`, priority 65534, untagged | **replace** with `allow-iap-ssh` (`35.235.240.0/20`) |
| `default-allow-rdp` | tcp:3389 from `0.0.0.0/0` | **delete** — nothing here runs Windows |
| `default-allow-health-check` | tcp **all ports** from Google LB ranges, tag `lb-health-check` | **delete** — 0 load balancers exist, and the tag *is* on the instance |
| `default-allow-health-check-ipv6` | same, IPv6 | **delete** |
| `default-allow-http` / `-https` | tcp:80 / 443, tags `http-server` / `https-server` | keep — this is what serves production |
| `default-allow-icmp`, `default-allow-internal` | defaults | keep |

The health-check rules deserve emphasis: they permit **all TCP ports** from
Google-owned ranges to any instance carrying `lb-health-check`, and this
instance carries that tag while no load balancer exists. Unlike Odoo's
`allow-postgres-from-script`, this is not world-open — but it is a live,
unnecessary path to every port on the box, including Postgres and the Traefik
API, and it exists to serve a load balancer that was never built.

Also, unlike Odoo: HRMS's Traefik publishes its dashboard as `"8080:8080"` with
`--api.insecure=true` — i.e. an unauthenticated admin API of the production
reverse proxy bound to `0.0.0.0`. No firewall rule admits 8080 from the
internet, but `default-allow-internal` permits all TCP between instances.
Narrow it to `"127.0.0.1:8080:8080"` as Odoo did, keeping the diagnostic
reachable over the IAP tunnel:

```bash
gcloud compute ssh odoo-hrms-prod --zone=us-central1-c --tunnel-through-iap -- -L 8080:localhost:8080
```

### 1.7 Deploy pipeline differences

| | Odoo | HRMS |
| --- | --- | --- |
| Deploy branch | `19.0` | **`main`** |
| Dev branch | `development_19` | **`development`** |
| Current deploy | GH Actions, SSH with a repo-secret private key, `docker compose build` on the VM | **identical anti-pattern** |
| Health verification | none (reported success regardless) | **none** |
| Config delivery | 212-byte GH Actions secret | GH Actions secret `ODOO_CONF` |
| Extra CI gate to preserve | — | **OpenAPI spec validation + route parity** (`docs/api/check_route_parity.py`) |
| Modules under test | derived from `custom_addons/` | **2 of 22 hardcoded** |

Two HRMS-specific notes:

* `.github/workflows/test.yml` carries a real gate the Odoo pipeline does not:
  it validates the two OpenAPI specs and runs `check_route_parity.py` to prove
  they describe the routes the controllers actually expose. **This must be
  ported into `cloudbuild.ci.yaml`**, or it is silently lost when `deploy.yml`
  is deleted.
* That same workflow installs only `hr_employee_cleardeals` and
  `document_template_manager`. There are **22 modules** in `custom_addons/`.
  Twenty of them ship to production through a gate that never installs them.
  Use the Odoo pipeline's derived module list, which walks `custom_addons/*/`
  and skips `installable: False`. Expect this to surface pre-existing breakage
  in modules that have never been installed in CI — that is the gate working,
  and Phase 4 should budget for it rather than be surprised.

### 1.8 The boot disk is destroyed with the instance

`autoDelete: true`, and the disk is an inline attachment rather than a
standalone resource. Odoo's prod disk is `auto_delete = false` with a snapshot
schedule attached through its own resource, deliberately outliving its instance.

Deletion protection is on, so this is not an immediate hazard. But it means the
one operation that would destroy production data is a single unprotected step
away, and flipping it is **safe, online, and needs no stop**. Do it in Phase 1
as a deliberate one-line change, declared as a standalone
`google_compute_disk` + `google_compute_disk_resource_policy_attachment`, matching
the Odoo layout.

---

## 2. Blockers requiring an Owner

`developer2@cleardeals.in` holds `roles/editor`, `roles/secretmanager.admin`,
`roles/container.admin`, `roles/iap.tunnelResourceAccessor`,
`roles/compute.osLogin`, `roles/iam.workloadIdentityPoolAdmin`,
`roles/logging.viewer`. Tested via `testIamPermissions`, exactly one relevant
permission is **denied**:

```
resourcemanager.projects.setIamPolicy   →  DENIED
```

Granted and confirmed: `iam.serviceAccounts.create`, `storage.buckets.create`,
`secretmanager.secrets.create`, `monitoring.alertPolicies.create`,
`logging.logMetrics.create`, `compute.instances.setServiceAccount`,
`compute.firewalls.delete`, `serviceusage.services.enable`, and all five
`cloudbuild.builds.*` permissions — `create`, `get`, `list`, `update` and
**`approve`**.

> **The approval gate needs no extra grant.** The Odoo repo's `cloudbuild.tf`
> states that `roles/editor` does not include `cloudbuild.builds.approve` and
> that an explicit `roles/cloudbuild.builds.approver` binding is therefore
> required. On this project, now, that is **not true** — verified two ways:
>
> ```
> gcloud iam roles describe roles/editor --format="value(includedPermissions)" \
>   | tr ';' '\n' | grep '^cloudbuild.builds.'
> → approve, create, get, list, update
> ```
>
> and a live `testIamPermissions` on the project returns
> `cloudbuild.builds.approve` as granted for `developer2@`. (Note `value()`
> returns the list `;`-separated — splitting on `,` yields one long line and an
> anchored grep silently matches nothing, which is how the wrong conclusion is
> easy to reach.)
>
> So `developer1@` and `developer2@` can already release a queued production
> deploy, alongside the two Owners. Keep the `cloudbuild_approvers` variable in
> the Terraform, because it is the only way to make someone an approver *without*
> making them an editor — but it is optional, not a blocker, and it needs no
> Owner action to leave empty.

So everything in this plan can be applied by the current operator **except
project-level IAM bindings**. Project Owners are `tech@cleardeals.in` and
`solutionanalysts@cleardeals.in`.

Owner action is needed for every `google_project_iam_member` — concretely:

1. `hrms-prod-vm@` → `roles/logging.logWriter`, `roles/monitoring.metricWriter`,
   `roles/artifactregistry.reader`, `roles/secretmanager.secretAccessor`
2. `hrms-cloudbuild@` → `roles/artifactregistry.writer`,
   `roles/logging.logWriter`, `roles/compute.osAdminLogin`,
   `roles/compute.viewer`, `roles/iap.tunnelResourceAccessor`
3. The operator → `roles/compute.osAdminLogin` (currently only
   `roles/compute.osLogin`, which is login **without sudo** — insufficient to
   run `deploy.sh` by hand, and §5 depends on being able to)

Service-account-level bindings (`google_service_account_iam_member` — the
`actAs` and `serviceAccountTokenCreator` grants) do **not** need Owner;
`iam.serviceAccounts.setIamPolicy` is available.

**Recommended:** ask an Owner for a time-boxed `roles/resourcemanager.projectIamAdmin`
grant on this project so the Terraform applies as one unit. Splitting IAM out to
a separate Owner-run apply works, but it means the plan is never green in one
pass, which is the property the empty-plan gate depends on.

The other one-time human step Terraform cannot do: **a GitHub org admin must
install the Cloud Build GitHub App and grant it `Cleardeals/Odoo-HRMS`**, once,
at `https://console.cloud.google.com/cloud-build/triggers/connect`. Until then
keep `cloudbuild_github_connected = false`.

---

## 3. Phases

Each phase states its gate. A phase is not done until its gate passes.

### Phase 0 — Establish and reclaim

No Terraform. Nothing here changes application behaviour.

**0a. Capture the live config.** `odoo.conf` exists only on the VM and in a
GitHub Actions secret. Copy it off, redact the two secrets, and keep the
redacted copy as the basis for `odoo.prod.conf`. Record the current values of
`admin_passwd` (unset) and `db_password` — they become the first Secret Manager
versions.

**0b. Baseline the serving path. DONE — and the restart is not needed.**

Measured:

```
routers: 5   (odoo@docker, odoo-chat@docker, web-to-websecure@internal,
              api@internal, dashboard@internal)
edge:    curl --resolve hr.cleardeals.xyz:443:127.0.0.1 /web/login
         → status=200, ssl_verify_result=0
odoo:    /web/health?db_server_status=1
         → {"status": "pass", "db_server_status": true}
```

Both docker-provider routers are present, TLS validates, and the database is
reachable. That is the pre-migration baseline every later gate compares against.

**The deliberate Traefik restart this phase originally called for has been
dropped, because the trap it was written to catch cannot exist here.** The Odoo
version of this gate exists because a Docker Engine upgrade had been sitting
*installed but inactive* on a VM that had not rebooted in months, so the first
container restart was when Traefik's provider died. On HRMS the timeline rules
that out:

| | |
| --- | --- |
| Last boot | `2026-05-19 04:03:56` |
| `dockerd` started | `2026-05-19 04:04:09` |
| All three containers started | `2026-05-19 04:04:14` |
| Last docker/containerd package change | **`2026-02-16`** |

The daemon and the containers are the same generation, and nothing has been
installed since. A restart cannot reveal a mismatch, so restarting production to
look for one is risk without information.

**What the investigation found instead — the February incident, and an
undocumented pin.** `docker version` reports server 28.5.2, but the package
history tells a story:

```
2026-02-16 06:51  install  docker-ce 5:29.2.1  containerd.io 2.2.1
2026-02-16 09:23  remove   docker-ce, docker-ce-cli, containerd.io
2026-02-16 09:25  install  docker-ce 5:28.5.2   ← downgrade, 2.5 h later
```

and `docker-ce` / `docker-ce-cli` are now on **`apt-mark hold`**. The containerd
image store still holds `traefik:v2.10` and `traefik:v3.0` (§0c), so somebody
spent that morning cycling Traefik versions against a Docker that had jumped to
29.x — Docker 29 raises `MinAPIVersion` past 1.24, which is exactly what killed
Traefik v2.10's client on Odoo. The resolution here was to pin Docker **down**
rather than move Traefik up. The running daemon still advertises
`minapi=1.24`, which is why the old clients kept working.

This is the same incident Odoo hit, already fought and already survived. Three
consequences worth recording:

* **The pin is invisible operational state.** It is not in git, not in
  Terraform, and nothing on the box says why 28.5.2. Anyone who runs
  `apt-mark unhold docker-ce` or rebuilds this VM from scratch gets Docker
  29.8.0 (the current candidate) and February back.
* **`containerd.io` is *not* held** (2.2.1 installed, 2.3.4 available). A manual
  `apt upgrade` would move containerd underneath a pinned Docker — an untested
  combination, and one command away from being reached accidentally during this
  very migration.
* **Automatic upgrades cannot cause it.** Checked rather than assumed:
  `Unattended-Upgrade::Origins-Pattern` admits only `origin=Debian` and
  `Debian-Security`, and the Docker packages come from `download.docker.com`.
  The empty `Package-Blacklist` is therefore irrelevant. So this is a
  manual-`apt upgrade` hazard, not a background one.

Since Traefik is already on v3.2, the pin is probably no longer needed — but
unpinning is a real change with its own verification and belongs in its own
window, not here. For this migration: **do not run `apt upgrade` on this VM**,
and use targeted commands only (§0c).

**0c. Reclaim disk.** 7.4 GB free is not enough headroom for a pipeline that
pulls ~3 GB images and retains several. Verified reclaimable, in ascending order
of risk:

```bash
# ~2.7 GB — journald has no SystemMaxUse, so it defaults to 10% of the filesystem
sudo journalctl --vacuum-size=200M
printf '[Journal]\nSystemMaxUse=200M\n' | sudo tee /etc/systemd/journald.conf.d/cap.conf
sudo systemctl restart systemd-journald

# ~600 MB — the Ops Agent's own failure logs; will stop growing once §1.1 is fixed
sudo find /var/log/google-cloud-ops-agent -type f -name '*.log*' -mtime +7 -delete

# ~140 MB — `clean` only empties the .deb cache. NEVER `apt upgrade` here (§0b).
sudo apt-get clean
```

Container `*-json.log` files hold 534 MB and are uncapped (no
`/etc/docker/daemon.json`). They are truncated as a side effect of the next
deploy recreating the containers, once Phase 3 adds the compose `logging` limits
— do not truncate a live container's log by hand.

**`/var/lib/containerd` holds 6.5 GB — verified as a stale image store, not a
live one.** The initial read ("not tracked by Docker at all") was too quick:
`ctr namespaces ls` shows a `moby` namespace holding the three *running*
containers, 5 images and 62 snapshots. That looks alarming until the details
resolve it, and the details are what make deletion safe:

* **All five containerd images are stale, and two do not exist in Docker.**
  The namespace holds `traefik:v2.10` and `traefik:v3.0` alongside
  `odoo-hrms:latest`, `postgres:17` and `traefik:v3.2`, while `docker images`
  lists only the last three. Two Traefik versions that Docker has no record of
  is the fingerprint of Docker's **containerd image store having been enabled
  at some point and then reverted** to the `overlay2` graph driver, leaving the
  content and snapshots behind.
* **Nothing is using a containerd snapshot.** Snapshot kinds are 48 `Committed`
  and 9 `View` — and **zero `Active`**. `Active` is the kind a running
  container's writable layer takes. Zero of them means no container's rootfs
  comes from this snapshotter.
* **Each running container confirms it independently.**
  `docker inspect --format '{{.GraphDriver.Name}}'` returns `overlay2` for all
  three, so their rootfs is served from `/var/lib/docker/overlay2`.
* **The two stores account for the same images separately.** containerd reports
  `odoo-hrms` at 964 MB (compressed content) against Docker's 3.12 GB
  (uncompressed layers), and the digests differ from Docker's image IDs.

The containers appearing in the `moby` namespace is normal and not evidence of
the snapshotter being in use: Docker always drives containerd as its runtime
shim, passing a rootfs it manages itself.

So the 6.5 GB is reclaimable — but treat it as its own step, not a rider on the
log cleanup. `moby` is **Docker's own namespace**, so `ctr -n moby images rm`
reaches into the daemon's territory; take a manual disk snapshot first, and
verify the stack afterwards rather than assuming. The safe subset below
(journal + agent logs + apt ≈ 3.4 GB) needs none of that caution and can go
first.

**RESULT — done. 74% → 44%, free 7.4 GB → 16 GB.** A manual snapshot
(`odoo-hrms-prod-pre-reclaim-20260908`) was taken first. Measured, in order:

| Step | Reclaimed |
| --- | --- |
| `journalctl --vacuum-size=200M` + a `SystemMaxUse=200M` drop-in | 2.7 GB |
| `apt-get clean` | 304 MB |
| 5 stale containerd images (`ctr -n moby images rm --sync`) | 0.4 GB |
| 45 leaked BuildKit leases, then containerd's scheduled GC | ~4.5 GB |
| **Total** | **~8 GB** |

Two things worth carrying forward:

* **The Ops Agent's 627 MB did not shrink.** `-mtime +7` matched nothing,
  because the agent rewrites those files continuously — it is *live churn*, not
  old logs, and it keeps growing until the service-account fix in 4b/6. Do not
  bother pruning it again before then.
* **The leases were the real blocker, not the images.** Removing the images
  freed almost nothing: 47 leases, every one stamped `2026-02-16` between 07:08
  and 09:26, still pinned the snapshots. 45 were leaked
  `buildkit/lease.temporary` and orphan build leases — the builds ran at
  07:08–07:11 and Docker was removed underneath them at 09:23, so they were
  never cleaned up. Only 2 were Docker's own (`moby-image-*`, matching the
  current `traefik:v3.2` and `postgres:17` image IDs) and those were left
  alone. Deleting the 45 and waiting ~2 minutes for containerd's scheduled GC
  took the store from 6.1 GB to 851 MB.

Verified safe before deleting anything, and verified again after:

* 0 `Active` snapshots (48 `Committed`, 9 `View`) — `Active` is the kind a
  running container's writable layer takes, so nothing live depended on the
  snapshotter;
* all three containers reported `GraphDriver=overlay2`;
* afterwards, `docker run --rm postgres:17 postgres --version` printed
  `PostgreSQL 17.8` — Docker can still resolve, instantiate and run containers.
  (A `docker create` probe "failed" first; the name began with an underscore,
  which Docker rejects. The probe was wrong, not the cleanup.)
* stack healthy throughout: 3 containers up, edge 200 with valid TLS, 5 routers,
  `db_server_status: true`.

**Gate:** the 0b baseline recorded (5 routers, edge 200, `db_server_status:
true`) — **done**; `df -h /` shows ≥ 10 GB free (≥ 15 GB if the containerd store
is reclaimed); the redacted config captured — **done**; the Docker pin
documented so it survives the next person — **done, here**.

---

### Phase 1 — Terraform, importing what already runs

Create `infrastructure/terraform/` mirroring the Odoo layout: `versions.tf`,
`variables.tf`, `compute.tf`, `firewall.tf`, `iam.tf`, `storage.tf`,
`artifacts.tf`, `cloudbuild.tf`, `monitoring.tf`, plus `.gitignore`
(`terraform.tfvars`) and `terraform.tfvars.example`.

State bucket `cleardeals-hrms-tfstate` in **this** project, prefix `hrms-prod`,
with uniform bucket-level access, public access prevention, versioning, and
`prevent_destroy`. In this project and not a shared one, for the same reason the
Odoo module gives: sharing a state bucket ties one project's state to another's
lifecycle and IAM, and a project-level mistake should stop at that project.

**Import everything exactly as it is, including the parts that are wrong.** The
instance, the disk, the address, the snapshot policy and its attachment, all
eight firewall rules. Write the HCL to match reality — never the other way
round.

Fields that must match or Terraform will plan a destroy of production:

* `key_revocation_action_type = "NONE"` — live value; omitting it plans a change
  to null, and the field **forces replacement**. This is what tried to recreate
  Odoo production on its first plan.
* `labels = { "goog-ops-agent-policy" = "v2-x86-template-1-4-0" }` — note this
  differs from Odoo, where the label surfaced only in `effective_labels` and was
  deliberately **not** declared. Here it is a real Terraform-visible label;
  check `terraform plan` output and follow what the provider actually reports.
* `metadata = { enable-osconfig = "TRUE" }` — set by the Ops Agent policy;
  omitting it plans its removal, silently detaching the VM from that policy.
* `lifecycle { ignore_changes = [metadata["ssh-keys"]] }` — metadata SSH keys are
  rewritten by anyone running `gcloud compute ssh`. Terraform must not fight
  that churn, and must never be the thing that revokes someone's access
  mid-session.
* `snapshot_properties { guest_flush = false; labels = {}; storage_locations = [] }`
  on the imported `default-schedule-1` — the live policy carries the empty block,
  so omitting it plans a change forever. (The *new* 4-hourly policy in Phase 7
  must omit it, for the opposite reason. They are not inconsistent; see the Odoo
  `compute.tf` comment.)
* `deletion_protection = true`.
* The boot disk as it is: inline, `auto_delete = true`. Change it in the second
  apply, not the import.

**Gate: a completely empty first plan. PASSED** — `No changes. Your
infrastructure matches the configuration.` 14 resources under management, state
in `gs://cleardeals-hrms-tfstate/hrms-prod/`.

It took two corrections to get there, and both were mine rather than
production's — which is the gate earning its place:

* **Four firewall rules carry descriptions** (`Allow SSH from anywhere`,
  `Allow RDP from anywhere`, `Allow ICMP from anywhere`, `Allow internal traffic
  on the default network`). Omitting them planned their removal.
* **The `goog-ops-agent-policy` label must NOT be declared** — the opposite of
  what this plan originally said. `gcloud` reports it, so declaring it looks
  right; but the provider splits `labels` (config-managed) from
  `effective_labels` (everything present), import populated only the latter, and
  declaring it planned an ADD. That proved Terraform does not own it. `labels` is
  non-authoritative, so omitting it leaves the live label alone instead of
  fighting the OS Config policy every time that policy bumps its template
  version. The CRM module's reasoning was right and the HRMS-differs note here
  was wrong.

One residual diff is expected and is not infrastructure drift:
`allow_stopping_for_update` is a provider-only flag with no GCP API counterpart,
so it cannot be imported and always plans an update. Applying it wrote it to
state and made no API call — proven by capturing the instance, metadata and tag
fingerprints before and after (all three identical, status `RUNNING`,
`lastStartTimestamp` unchanged). Keep it: Phase 4b needs it. This gate caught three unintended production destroys during the
Odoo import; treat a non-empty plan as a blocker, never as noise to skim past.

**Second apply, once the plan is empty: DONE.** The boot disk is a standalone
`google_compute_disk` with `ignore_changes = [image, snapshot]`, the snapshot
policy is attached via `google_compute_disk_resource_policy_attachment`, and
`auto_delete` is flipped `true` → `false`.

Confirmed update-in-place, not replacement (`0 to add, 1 to change, 0 to
destroy`), and verified on GCP afterwards: `autoDelete: False`, instance
`RUNNING`, `deletionProtection: True`, plan empty again, site still serving 200.
The disk now outlives its instance, which also turns a whole-VM recovery into
re-attaching the disk rather than restoring a snapshot and losing everything
since.

---

### Phase 2 — Secrets and a reviewable config

Enable `secretmanager.googleapis.com`. Create `odoo-admin-passwd` and
`odoo-db-password`.

Rotate the database password. The current one lives in a mode-644 file in a home
directory and in a GitHub Actions secret; treat it as compromised on principle.
Port `infrastructure/rotate_db_password.sh` from the Odoo repo.

Commit `odoo.prod.conf` — the live config with `__ADMIN_PASSWD__` and
`__DB_PASSWORD__` placeholders, plus the §1.4 fixes (`db_name`, `dbfilter`,
`admin_passwd` uncommented as a placeholder) and `addons_path =
/usr/lib/python3/dist-packages/odoo/addons,/opt/cleardeals-addons`.

Port `scripts/render_odoo_conf.sh` verbatim in behaviour: fetch both secrets,
escape `%` as `%%` (a stray `%` breaks ConfigParser at startup with an error
that says nothing about passwords), substitute in the shell rather than with
`sed`, refuse to start if a placeholder survives, and write to **`/dev/shm`** so
the only file containing config and secrets together is memory-backed and never
lands in a disk snapshot.

Note the ordering dependency: this script needs `secretmanager.secretAccessor`
**and** `cloud-platform` scope on the VM, so it cannot run successfully until
Phase 4b. Land the code first, exercise it after the window.

Change `docker-compose.yml` to mount `/dev/shm/odoo.conf:/etc/odoo/odoo.conf:ro`
and drop `POSTGRES_PASSWORD` from the `db` service — it is read only by
`initdb` on an empty data directory, and this one is not empty. That removes the
`${DB_PASSWORD:-odoo}` default, which currently means a public repository
documents `odoo` as the fallback production database password.

**RESULT — code landed. Rotation deferred to 4b by dependency, not by choice.**

APIs enabled (`secretmanager`, `artifactregistry`). Both secrets created and
seeded. `odoo.prod.conf`, `scripts/render_odoo_conf.sh` and
`infrastructure/rotate_db_password.sh` are committed.

**The live database password is FOUR CHARACTERS.** Read off the VM without
printing it, and its length settles what it is: the `odoo` default that
`docker-compose.yml` published as `${DB_PASSWORD:-odoo}` — in a public
repository, with no `.env` on the host to override it, and in git history
forever. `odoo-db-password` was seeded with that value as-is, deliberately, so
the render step can be proven working *before* and separately from the rotation.
`odoo-admin-passwd` got a fresh 40-character alphanumeric value, since the live
config had `admin_passwd` commented out and Odoo was falling back to its
built-in default.

**Rotation cannot run yet, and this is a genuine ordering constraint rather than
caution.** `rotate_db_password.sh` reads the secret *from the VM*, which needs
both `roles/secretmanager.secretAccessor` on the attached service account and
the `cloud-platform` scope on the instance. The VM has neither until 4b. Same
applies to `render_odoo_conf.sh`. Both are committed before they can succeed so
the code is reviewed before it is load-bearing.

Three defects fixed while the config became reviewable for the first time,
and one deliberately left alone:

| | Live | Now |
| --- | --- | --- |
| `dbfilter` / `db_name` | `^.*$`, no `db_name` | `^odoo_hrms_db$`, `db_name = odoo_hrms_db` |
| `admin_passwd` | commented out → built-in default | 40-char value from Secret Manager |
| `db_maxconn` | `64` → ceiling **640** vs 60 | `5` → ceiling **50** vs 60 |
| `limit_memory_soft`/`hard` | 512 MB / 640 MB | **unchanged — see below** |

The memory limits look wrong by analogy to the CRM instance, where measured
per-worker VIRT was 663–727 MB against limits of this shape. They were left
exactly as they are because this instance's own evidence contradicts the
analogy: 30 days of `docker logs odoo-app` contain **zero** "virtual memory
limit reached". Changing a working limit on the strength of another machine's
numbers is how a working system gets broken. Phase 6 will be the first time
there is real data to decide on.

**Secrets are declared in Terraform, but only the containers.** No
`google_secret_manager_secret_version`, ever — Terraform state records every
managed attribute, so a version resource would write the secret in cleartext
into the state bucket, making it exactly the thing the secret was meant to
avoid. Verified rather than asserted: after the apply, the state contains no
`secret_version` resource, and a direct content match confirms the 40-character
admin password does not appear anywhere in it. (A `"data"` grep hit turned out to
be `"mode": "data"` from the `google_project` data source.)

This diverges from the CRM module, which declares its secrets nowhere. That
reads as an omission rather than a decision — there is no comment defending it —
and the containers carry no sensitive data, so they are managed here.

**Gate:** `odoo.prod.conf` parses and passes every `config-check` assertion —
**passed** (`list_db = False`, `dbfilter` set, both secrets still placeholders,
`addons_path` on `/opt/cleardeals-addons` with no `/mnt/extra-addons`
reference). `bash -n` clean on all three scripts. `render_odoo_conf.sh` itself
can only be exercised after 4b.

---

### Phase 3 — Artifact Registry, and an image that tells the truth

Enable `artifactregistry.googleapis.com`; create repository `hrms`
(`DOCKER`, `us-central1`).

**Dockerfile:** change `COPY ./custom_addons /mnt/extra-addons/custom` to
`COPY --chown=odoo:odoo ./custom_addons /opt/cleardeals-addons`. See §1.3 — this
is mandatory, not cosmetic.

Replace the `HEALTHCHECK` on `/web/database/selector`. That route renders its
template unconditionally and returns 200 without touching the database (checked
in `addons/web/controllers/database.py:59` — no `list_db` guard on the route
itself; it is the *template* that hides the management UI). It is currently
answering every 30 seconds in the Odoo log. It is not a health check. Use
`/web/health?db_server_status=1`, which proves the database is reachable.

**docker-compose.yml:**

* `name: odoo-project` — pin it to the **current** name so applying this is a
  no-op today. Without the pin, Phase 4c's directory move renames every
  container, and old and new projects each own a separate network and set of
  anonymous volumes, so a rollback has to reason about two identities.
* `image: ${ODOO_IMAGE:-odoo-hrms:latest}` — pinned by SHA from `.env` by
  `deploy.sh`. Never a floating tag: it makes "what is in production"
  unanswerable and rollback impossible.
* **Remove** the `./custom_addons:/mnt/extra-addons/custom` bind mount. Only
  after the Dockerfile path change, and in the same commit.
* `logging: json-file, max-size 50m, max-file 5` on all three services. In git
  rather than `daemon.json`, so it needs no daemon restart and applies as each
  container is recreated.
* Narrow the Traefik dashboard to `127.0.0.1:8080:8080` (§1.6).
* Drop the inert `ODOO_PROXY` / `WEB_BASE_URL` environment variables — nothing
  reads them; `proxy_mode` belongs in `odoo.conf`, and the base URL is a system
  parameter (see commit `f0f3718c`).

**RESULT — done, and the trap was demonstrated rather than argued.** Artifact
Registry repository `hrms` created (`DOCKER`, `us-central1`). Dockerfile,
`docker-compose.yml` and `entrypoint.sh` all changed.

**Gate: PASSED, four ways.** The image was built locally and run with **no** bind
mount:

1. `ls /opt/cleardeals-addons` → **22 modules, byte-identical to
   `ls custom_addons`.** This is the same assertion `cloudbuild.ci.yaml`'s
   `image-contents` step will make.
2. **`/mnt/extra-addons` is EMPTY at runtime, with 1 mount over that path.**
   That is the anonymous volume, and it is the whole mechanism: had the addons
   stayed where they were, they would have been hidden at container start with no
   build error. The built image still declares
   `{"/mnt/extra-addons":{},"/var/lib/odoo":{}}`, inherited from the base — the
   declaration does not go away, the code just has to live outside it.
3. A manifest reads correctly from the new path.
4. **Odoo actually installs from it.** Against a throwaway Postgres 17:
   `-i hr_employee_cleardeals --stop-after-init` exited 0, and
   `ir_module_module` reports `hr_employee_cleardeals -> installed`.

On the 143 "ERROR" strings that run produced: **zero** are Odoo log records.
All 143 are docutils reStructuredText parse errors (`Unexpected indentation`,
`Undefined substitution referenced`) emitted while rendering the `description`
fields in the module manifests — pre-existing, cosmetic, and unrelated to this
change. Counting them without classifying them would have looked like a broken
build. Separately worth cleaning one day: the manifests' descriptions are
malformed RST, and the same run surfaced real field-declaration warnings
(`unknown parameter 'invisible'`, `'tracking'` on several models) that belong to
the modules rather than to the infrastructure.

One incidental measurement: the freshly built image is **~1.0 GB**, against the
3.12 GB `odoo-hrms:latest` currently on the VM. Whatever accumulated in that
older build, the deploy pipeline's images are a third the size, which makes
`IMAGE_KEEP=3` comfortable on a 30 GB disk rather than tight.

---

### Phase 4 — Cloud Build

#### 4a. Identities (Owner required — §2)

`hrms-prod-vm@` (runtime) and `hrms-cloudbuild@` (CI/CD), with the roles listed
in §2. Plus, not needing Owner:

* `hrms-cloudbuild@` → `roles/iam.serviceAccountUser` **on `hrms-prod-vm@`**.
  Non-obvious: OS Login roles alone are not enough. To `gcloud compute ssh` to
  an instance that has a service account attached, the caller must be able to
  act as *that* account, or the connection is refused after authentication
  succeeds.
* Cloud Build's **service agent** —
  `service-<PROJECT_NUMBER>@gcp-sa-cloudbuild.iam.gserviceaccount.com` —
  → `roles/iam.serviceAccountTokenCreator` on `hrms-cloudbuild@`. Careful: this
  is **not** `<PROJECT_NUMBER>@cloudbuild.gserviceaccount.com`, the legacy
  default build account. It is the service agent that impersonates a
  user-specified account. Granting it to the wrong one leaves the real
  impersonation path unauthorised while a binding sits there looking correct,
  and the failure is delayed and misleading: creating the trigger *succeeds*
  (the Terraform principal has `actAs` via its own role); only the first **build**
  fails, with an error that reads like a Cloud Build fault.
* Compose the service-agent address explicitly. Do **not** read it from
  `google_project_service_identity`, which returns the legacy account.

Keep the compute default service account in place until the swap is proven.
Grant it `artifactregistry.reader` too, if any deploy must run before 4b —
granting a permission to the identity a resource *will* have is not the same as
granting it to the one it *has*. That gap cost the Odoo migration two failed
deploys.

**RESULT — done.** `hrms-prod-vm@` and `hrms-cloudbuild@` created with exactly
the roles listed, plus the two `actAs` grants and the service-agent
`serviceAccountTokenCreator`. Fourteen resources, zero changes to the instance —
attaching a different identity needs a stopped VM, so creating them is safe
outside a window and was done outside one.

**4b pre-flight satisfied early.** The swap is permission-additive, verified
rather than assumed: the compute default service account holds no project roles
**and** no resource-level grants — checked individually against the state
bucket, both secrets, and the Artifact Registry repository. So `hrms-prod-vm@`'s
four roles are a strict superset and nothing can regress.

#### 4b. The maintenance window — OS Login, IAP, service account, scopes

The only step that stops the VM. See §5.

#### 4c. Move the application out of a personal home directory

`/home/tech/odoo-project` → `/opt/odoo-hrms`. Port `scripts/phase4c_move.sh`.
The Odoo repo records three separate outage-class problems caused by this
location: `git` refusing to operate on a repo owned by another user; the OS
Login user being unable to even `cd` into a mode-750 home directory so a manual
command ran silently in the wrong place; and the location being *why* the addons
were bind-mounted, which made the image tag a lie.

All three apply here identically, and the OS Login one is about to become acute
— after 4b the interactive user is `developer2_cleardeals_in`, not `tech`.

The script must **not** `chown` anything. `odoo-db-data` is `drwx------` owned by
uid 999 and `odoo-web-data` is owned by `Debian-exim:crontab` — container uids
that map to unrelated host names. `mv` within one filesystem is an atomic
rename and preserves all of it; a `cp -a` would rewrite ownership and Postgres
would refuse to start. Assert the same-filesystem precondition, record
ownership/mode/git HEAD/size before, and verify them after.

Run with the stack **down**. Rollback is `mv` back; the pipeline resolves either
path so it keeps working both ways.

#### 4d. The pipelines

**`cloudbuild.ci.yaml`** — pull requests against `^(main|development)$`. Builds
no production image and touches no VM:

1. build the test image
2. start a throwaway Postgres 17
3. **derived** module list from `custom_addons/*/`, skipping
   `installable: False`; install all of them, `--test-enable`, `--test-tags`
   built from the same list so the two can never disagree
4. `config-check` on `odoo.prod.conf`: `list_db` must be `False`, `dbfilter`
   must be set, `admin_passwd` and `db_password` must still contain `__` (never
   commit a secret)
5. **the ported OpenAPI gate** — `openapi_spec_validator` on both specs, then
   `docs/api/check_route_parity.py`
6. `shell-syntax` — `bash -n` over `scripts/*.sh`
7. `image-contents` — `ls /opt/cleardeals-addons` inside the built image must
   equal `ls custom_addons`

**`cloudbuild.yaml`** — push to `main`, `approval_required = true`. Same gates
repeated (a merge can contain something no PR ever tested), then push both
`:$SHORT_SHA` and `:$COMMIT_SHA` tags, then deploy over IAP.

Two hard-won details to carry over verbatim:

* **Write the remote SSH command inline.** No intermediate shell variable. Cloud
  Build substitution and shell expansion act on the same `$`, and a variable
  that must survive both is fragile in a way no gate can see. A variable named
  `REMOTE` was parsed as a substitution and rejected at approval; escaping it as
  `$$` fixed the reference but rewrote the *assignment*, so the step died with
  `REMOTE: unbound variable`. Three Odoo deploys failed on exactly this.
* **Lowercase every shell variable inside `args`**, comments included. A `$`
  followed by capitals is read as a substitution and the build is rejected when
  the name is unknown — a *comment* in `cloudbuild.ci.yaml` spelling the pattern
  out literally failed a build once.

Set `_ZONE=us-central1-c`, `_INSTANCE=odoo-hrms-prod`, `_REGION=us-central1`.
No `included_files` filter on the CD trigger: a deploy trigger that skips files
is a deploy trigger that silently does not deploy something.

Keep the two flags independent — `cloudbuild_github_connected` and
`cloudbuild_cd_enabled`. CI runs gates only; CD deploys to production. Tying
them to one flag forces that blast-radius increase just to get PR checks.
Enable CD only after a green CI run on a real pull request.

Note on the approval gate: it is doing a job GitHub cannot. Branch protection
would be the right control, but GitHub refuses it on private repos under a free
plan — and while `Cleardeals/Odoo-HRMS` is currently **public**, relying on that
is relying on visibility never changing. A bad merge stays possible; a bad
deploy does not.

**`scripts/deploy.sh`** — port from Odoo, adjusted:

* `DEPLOY_BRANCH` defaults to `main`, `REPO_URL` to `Cleardeals/Odoo-HRMS`
* `EDGE_HOST` defaults to `hr.cleardeals.xyz` — must match the `Host()` rule on
  the `odoo` router, or it matches no router and returns 404
* `IMAGE_BASE` → `<region>-docker.pkg.dev/<project>/hrms/odoo-hrms`, project id
  read from the **metadata server**, never hardcoded (this repo is public, and a
  copy of the script on another host must not silently deploy to the wrong
  registry)
* `IMAGE_KEEP=3`, not 5. Odoo keeps 5 on a 60 GB disk; the HRMS image is 3.12 GB
  on a 30 GB disk. 3 keeps the running image, the rollback target, and one more.
* keep `APP_DIR` resolution (`/opt/odoo-hrms` then `/home/tech/odoo-project`) so
  the pipeline works on **both** sides of the 4c move — pinning either path
  breaks the deploy for the window between the directory moving and the code
  that knows about it being deployed, and the only way to deploy that code is
  the deploy that is broken

Keep every gate, and understand why each exists:

* `flock` — Cloud Build does not serialise approved builds.
* Rollback pointer read from the **running container**, not `.env`. A
  hand-edited `.env` describes an intention, not reality, and rollback would
  restore an image that never served traffic.
* Refuse to deploy if `git rev-parse HEAD` ≠ the built SHA. The pipeline fetches
  a branch *tip* because GitHub will not serve an arbitrary SHA to `fetch`; if
  someone pushed mid-build, the tip is no longer what was tested.
* `git fetch --depth 1` is **required**, not an optimisation. The checkout is a
  shallow clone (confirmed: `.git/shallow` exists) and a plain fetch unshallows
  it. Measured on Odoo: `.git` grew 980 MB → 5.3 GB before the fetch was killed,
  and it had not finished. HRMS's `.git` is 228 MB on a disk with 7.4 GB free
  today.
* `set_env_image` must rewrite only the `ODOO_IMAGE` line. `echo > .env`
  truncates the file and silently deletes every other key.
* Health gate: `/web/health?db_server_status=1` **and** `/web/login`. A bare
  `/web/health` returns 200 without touching the database — a gate polling it
  goes green with Postgres down and reports a successful deploy.
* Edge gate: `curl --resolve hr.cleardeals.xyz:443:127.0.0.1
  https://hr.cleardeals.xyz/web/login`. Every check above it asks Odoo about
  itself from inside its own container — a complete blind spot for "can a user
  reach the site". It must speak TLS: a port-80 probe returns 301 even for a
  host matching no router, because the redirect is on the entrypoint and runs
  before routing. **No rollback on edge failure** — Odoo has already proven
  healthy, so re-pinning the old tag cannot fix a broken proxy and would be a
  second unplanned change made during diagnosis of the first.
* Prune by **count, not age**. `docker image prune -a --filter until=…` deletes
  the rollback target: the moment the new image runs, the previous one is used
  by nothing, and an age filter does not save it either.

**Delete `.github/workflows/deploy.yml` in the same change that enables the CD
trigger.** Reduce `test.yml` to whatever is still wanted as a fast pre-Cloud-Build
signal, or delete it too — but only once its OpenAPI gate is confirmed running
in `cloudbuild.ci.yaml`.

**RESULT — code landed and locally exercised; triggers deliberately still off.**

`cloudbuild.ci.yaml`, `cloudbuild.yaml`, `scripts/deploy.sh` and
`cloudbuild.tf` are committed. Both flags remain `false`, so the Terraform plan
is empty and no trigger exists yet.

Verified without a trigger, because most of the pipeline can be proven locally:

* **The derived module list resolves to 21 modules**, and
  `custom_addons/hr_recruitment_cleardeals` is correctly skipped — it holds two
  markdown files and no manifest, so it is not a module at all. Note this makes
  the two gates legitimately disagree by one: `image-contents` compares
  *directory listings* (22 = 22) while the install list is 21.
* **All 21 install cleanly**, rehearsed against a throwaway Postgres 17 with the
  real derived list. This mattered: `history_employee` and `hr_employee_shift`
  are **uninstalled in production**, so a derived list risked putting two
  never-installed modules into every pull-request gate. They install fine, so
  the derived list is safe and no exception is needed.
* **The `config-check` and `api-docs` steps were extracted from the YAML and run
  verbatim.** config-check passes (`connection ceiling 50 of 57 usable`);
  api-docs validates both specifications and reports `12 operations` and
  `17 operations` matching, route parity passed.
* Both pipelines parse, no step has a dangling `waitFor`, and — checked
  mechanically — **no `args` string contains a stray uppercase `$VAR`** that
  Cloud Build would misread as an unknown substitution.

**One real defect surfaced by the rehearsal**, and it is the only Odoo-level
ERROR in an otherwise clean 21-module install:

```
ERROR odoo.schema: column "hr_department" of relation "resource_calendar"
                   contains null values
```

`custom_addons/hr_employee_shift/models/resource_calendar.py:63` adds a
`required=True` Many2one to `resource.calendar` — a **core** model that already
has rows when the module installs. Odoo attempts `SET NOT NULL`, it fails on the
existing NULLs, Odoo logs the error and continues, so the database constraint is
**silently absent** and only ORM validation enforces it. Latent rather than live
(the module is uninstalled in production), but it will print on every CI run
until fixed, which is how people learn to ignore CI output. Tracked separately;
it belongs to the module, not the infrastructure.

**Gate:** a green CI run on a real pull request, then one approved end-to-end
deploy that pushes an image, swaps it, passes both health and edge gates, and
prunes. **Both still outstanding** — CI needs the GitHub App connection, and CD
must wait for 4b.

---

### Phase 5 — Firewall

Apply the §1.6 table. Order matters, and the Odoo migration is explicit about
why: **prove IAP works for both callers before narrowing anything.**

* Cloud Build — already deploying with `--tunnel-through-iap` by the end of
  Phase 4, successfully, repeatedly.
* The operator — verified interactively over the tunnel under OS Login.

Odoo's auth log showed real, recent, successful logins arriving *directly* on
the public address under legacy metadata keys, not through the tunnel; removing
the world-open rules first would have cut the only path anyone was using. HRMS
has five never-expiring metadata keys and five human home directories on the
box. Check `/var/log/auth.log` for who is actually connecting and how, before
deleting `default-allow-ssh`.

Recovery if this locks everyone out: firewall rules are Compute API calls, so a
replacement rule can be recreated from any authenticated machine in under a
minute. Losing SSH does not mean losing the instance. The serial console remains
as a backstop.

**Gate:** `gcloud compute ssh … --tunnel-through-iap` works for the operator and
for Cloud Build; plain `ssh <public-ip>` is refused; the site still serves.

---

### Phase 6 — The Ops Agent actually shipping

Only possible after 4b. Port `infrastructure/ops-agent/config.yaml` and
`install.sh`.

The config adds a `files` receiver for `/var/lib/docker/containers/*/*-json.log`
with a `parse_json` processor — without which the whole JSON blob lands in Cloud
Logging as an opaque, unsearchable string. Metrics stay at agent defaults; the
defaults already include the host disk and memory metrics Phase 7 needs.

Do **not** add a `parse_regex` processor to promote Odoo's log level into
severity. Ops Agent's `parse_regex` **drops** records that do not match, and this
pipeline carries Postgres and Traefik lines too — an Odoo-shaped regex would
silently discard both.

`install.sh` must validate the candidate config with the agent's own engine
before touching the live file, keep a timestamped backup, roll back
automatically if the agent does not come back, and then — critically — **prove
it is shipping rather than merely running**:

```bash
journalctl -u google-cloud-ops-agent-opentelemetry-collector \
  --since '1 min ago' --no-pager | grep -ci 'PermissionDenied'
```

This must be `0`. On HRMS it is currently in the hundreds per hour.
`systemctl is-active` is not evidence of anything on its own — this agent has
been `active` and `enabled` for months while shipping nothing.

**Gate:** all three of these return data, where all three return nothing today:

```bash
gcloud logging read 'resource.type="gce_instance"' --limit=5
gcloud compute instances os-inventory describe odoo-hrms-prod --zone=us-central1-c
# and agent.googleapis.com/disk/percent_used has > 0 time series
```

Then **record the actual device labels** on `disk/percent_used` before writing
Phase 7's filter. Odoo's host reported eleven series, eight of them `/dev/loopN`
snap squashfs mounts pinned at 100% forever, which a naive `disk > 85%` alert
would have matched on day one and never cleared. Debian 12 has no snaps, so
HRMS probably reports only `/dev/sda1` — **probably is not good enough**. Look
at the real labels and write the filter against them.

---

### Phase 7 — Snapshots and alerting

**Snapshot schedule first.** Create `hrms-prod-4h` — 4-hourly, `start_time`
offset from the current 12:00 slot so the first new snapshot is visibly
distinguishable from the last old one, retention 30 days,
`on_source_disk_delete = KEEP_AUTO_SNAPSHOTS`. Swap the disk attachment; leave
`default-schedule-1` **defined but detached** as a one-line rollback, and delete
it in a follow-up once the new schedule is observed producing snapshots.

This is not a nice-to-have, and it is not primarily about the recovery point
(though it moves worst-case data loss from 24 h to 4 h — snapshots are
incremental, so six a day cost far less than six times the storage). **It is
what makes backup alerting possible at all.** Cloud Monitoring refuses an
absence condition longer than 23 h 30 m. Against a daily schedule that is
unusable: consecutive snapshots are already 24 h apart, so any alert able to
detect a stopped schedule also fires shortly before every healthy one.

Then the log-based metric and the five policies. **Verified for HRMS
specifically:** scheduled snapshots here *do* appear as system events with
`protoPayload.methodName = "ScheduledSnapshots"` on `resource.type="gce_disk"`
in `us-central1-c` — three entries confirmed for the 7 Sep run. So the Odoo
approach ports directly. The obvious implementation — a metric on the
`createSnapshot` audit log — would sit permanently at zero while snapshots ran
perfectly, and be muted within a week.

Scope the metric by **zone**, not disk id: a disk id changes when the disk is
recreated, which is exactly what a whole-VM recovery does, so a filter pinned to
the current id goes silent right after a restore and alerts about the machine
that was just rescued.

| | Alert | Notes |
| --- | --- | --- |
| P1 | Site unreachable from the internet | Uptime check on `https://hr.cleardeals.xyz/web/login`, `validate_ssl = true`, `REDUCE_COUNT_FALSE > 1` so a single checker having a bad minute pages nobody. **`/web/login`, not `/`** — the root path redirects, and the redirect is served by Traefik's entrypoint *before* routing, so a check against `/` passes even when no router exists. |
| P2 | Root filesystem above 85% | Device filter from the Phase 6 measurement. HRMS starts at **74%**, so this is closer to firing than Odoo's was — reclaim first (Phase 0c), then set the threshold. |
| P2b | Automated snapshots stopped (>5 h) | `condition_absent`, not a threshold: a log-based counter emits *nothing* when no log arrives, it does not emit zero, so `count < 1` has no data to evaluate and stays silent through the very outage it was written for. |
| P3 | Host memory above 85% | Establish the real baseline from the first days of data. Do not reuse Odoo's ~20% figure — different machine, different workload, and `workers = 3` on an `e2-medium` is a tighter fit than Odoo's prefork on an `e2-standard-2`. |
| P4 | TLS certificate expires in under 15 days | Traefik renews via ACME automatically, so this firing means renewal is broken. It exists because the ACME contact on the resolver is a personal Gmail address — if renewal breaks, Let's Encrypt's warnings land where nobody looks. P1 catches an *expired* certificate; this is deliberately earlier. |

One notification channel, email, address from `var.alert_email` in gitignored
tfvars (this repo is public, and an address in it is an address that gets
scraped). **GCP sends a verification email and the channel delivers nothing
until the link is clicked.** A policy attached to an unverified channel looks
perfectly healthy in the console and pages nobody — the worst possible failure
mode for the thing whose whole job is to report failure. Click the link, then
confirm delivery by tripping one policy on purpose.

Every threshold must be validated against data this project is actually
producing. On Odoo that check changed two of five and would otherwise have
shipped two alerts that fire permanently on day one. An always-firing alert is
not neutral: it teaches everyone to close the notification without reading it.

**Gate:** every policy attached to a **verified** channel; each condition
evaluated against real time series; at least one deliberately tripped and the
email received.

---

### Phase 8 — Backups bucket (optional, for parity)

`cleardeals-hrms-backups`, uniform access, public access prevention,
versioning, `prevent_destroy`, and **no** deletion lifecycle rule — backups
ageing out silently is a worse failure than paying for storage.

Grant the VM identity `objectCreator` **and** `objectViewer`, not `objectAdmin`:
`gcloud storage cp` issues a GET before writing and 403s without the viewer
role, and this pair lets the VM write and verify its own backups while being
unable to delete them. If the box is ever compromised, the backups survive it.

Note the residual gap rather than treating it as done: legacy GCS bindings still
give any project Editor `legacyObjectOwner`, so backups are not immutable
against a project-level principal.

Disk snapshots are crash-consistent, not application-consistent. A logical
`pg_dump` to this bucket is what makes a clean restore possible, and matters
more here than on Odoo — the filestore is 759 MB of HR documents.

---

## 4. Change manifest

**New**

```
infrastructure/terraform/{versions,variables,compute,firewall,iam,
                          storage,artifacts,cloudbuild,monitoring}.tf
infrastructure/terraform/{.gitignore,terraform.tfvars.example}
infrastructure/ops-agent/{config.yaml,install.sh}
infrastructure/rotate_db_password.sh
cloudbuild.yaml
cloudbuild.ci.yaml
odoo.prod.conf
scripts/{deploy.sh,render_odoo_conf.sh,phase4c_move.sh}
docs/infrastructure_migration_plan.md   ← this file
```

**Modified**

| File | Change |
| --- | --- |
| `Dockerfile` | addons → `/opt/cleardeals-addons`; `HEALTHCHECK` → `/web/health?db_server_status=1`; drop the misleading BigQuery label |
| `docker-compose.yml` | pin `name:`; `${ODOO_IMAGE}`; remove addons bind mount; `/dev/shm/odoo.conf` mount; logging limits ×3; Traefik dashboard → loopback; drop `POSTGRES_PASSWORD` and the inert `ODOO_PROXY`/`WEB_BASE_URL` |
| `entrypoint.sh` | drop the BigQuery probe |
| `.gitignore` | `.env`, `/dev/shm` artefacts, terraform state |
| `DEPLOYMENT.md` | rewrite — it currently documents `docker build` on the VM and creating the database through the web manager |

**Deleted**

```
.github/workflows/deploy.yml          DELETED — see below, it became dangerous
.github/workflows/test.yml            (only after its OpenAPI gate is in CI)
docker-compose.traefik.yml            (if confirmed unused)
```

**`deploy.yml` was deleted earlier than this plan originally said**, and the
reason is a sequencing hazard worth stating plainly. The plan had it going in
"the same change that enables the CD trigger". That would have been wrong: from
the moment Phase 3 changed `docker-compose.yml` and the `Dockerfile`, that
workflow stopped being merely obsolete and became **actively destructive** on
the next push to `main`:

* it writes `./odoo.conf` from the `ODOO_CONF` secret, but compose now mounts
  `/dev/shm/odoo.conf`, which the workflow never creates — so Odoo would start
  on its **built-in defaults, including `list_db = True`**, serving the database
  manager to unauthenticated requests;
* the secret's config sets `addons_path = /mnt/extra-addons/custom`, and with
  the bind mount now gone that path is an empty anonymous volume — so **every
  custom module would disappear**.

An outage *and* an exposed database manager, triggered by an ordinary merge.
Leaving it armed "as a fallback" would have been the more dangerous choice, so
it goes in the commit that makes it dangerous. `test.yml` is kept: it is the
only pull-request gate until Cloud Build CI is connected, and it touches neither
the VM nor compose (verified: zero `ssh`/`docker compose`/`VM_IP` references).

The consequence is honest and must not be glossed: **there is no automated
deploy path between that commit and 4b.** `DEPLOYMENT.md` says so at the top and
documents the manual route.

---

## 5. Ordering and the single maintenance window

```
0 ─ establish + reclaim
    ↓
1 ─ Terraform import ── gate: EMPTY PLAN
    ↓
2 ─ Secret Manager + odoo.prod.conf ──┐
3 ─ Artifact Registry + image fix ────┤
    ↓                                 │  (code lands; needs 4b to run)
4a ─ service accounts  [OWNER]        │
    ↓                                 │
4b ─ ██ MAINTENANCE WINDOW ██ ────────┘
    ↓
4c ─ /opt move (stack down)
    ↓
4d ─ Cloud Build CI → CD ── gate: green PR, then one approved deploy
    ↓
5 ─ firewall  ── only after IAP is proven for both callers
    ↓
6 ─ Ops Agent ── gate: PermissionDenied == 0
    ↓
7 ─ snapshots + alerting ── gate: verified channel, one tripped alert
    ↓
8 ─ backups bucket
```

### The maintenance window (4b)

One stop, everything that requires it, bundled so the VM stops once:

1. `enable-oslogin = "TRUE"` on the **instance**, not project-wide, so the blast
   radius is one VM.
2. Attach `hrms-prod-vm@`.
3. Change scopes to `cloud-platform`.

**OS Login is a hard cutover.** The moment it is on, the five never-expiring
metadata SSH keys stop working on this machine, and anyone relying on them loses
access until granted `roles/compute.osLogin` or `osAdminLogin`. `developer1@`
and `developer2@` hold `osLogin` (login, **no sudo**). Confirm before flipping,
via `testIamPermissions` rather than assumption, that at least one principal
holds `compute.instances.osAdminLogin` — otherwise nobody can run `deploy.sh` or
`install.sh` by hand afterwards, and both are needed in later phases. This is
the §2 item 4 request.

It is also required, not merely tidy. Without OS Login, `gcloud compute ssh`
falls back to writing an ephemeral key into instance metadata, which needs
`compute.instances.setMetadata` — a permission the build service account must
**not** have, because `setMetadata` permits writing `startup-script`, which runs
as **root** at next boot. Granting it would hand permanent root on production to
anything that can trigger a build. OS Login is both the correct fix and the more
restrictive one.

**Pre-flight, before the window:**

* Prove `hrms-prod-vm@` is a **strict superset** of the compute default service
  account's effective access, role by role. Easy here — the current account holds
  no project roles at all — but check for resource-level grants outside the
  project IAM policy before concluding it.
* Test whether Artifact Registry docker-pull works under `devstorage.read_only`
  (§1.2), so the scope change is understood rather than hoped for.
* Confirm the serial console is reachable as a backstop.
* Take a manual snapshot immediately before the stop.

**Rollback:** stop, re-attach the compute default service account, restore the
scopes, remove `enable-oslogin`. Every step is reversible; only the stop costs
time.

---

## 6. Risks

| Risk | Mitigation |
| --- | --- |
| **No staging environment.** Odoo had `odoo-stage` to rehearse against; HRMS has one machine, and it is production. | Rehearse Phases 3–4 on a throwaway VM created from a recent snapshot in the same zone. Delete it afterwards. This is the single biggest structural difference in the plan and the one most worth spending money on. |
| **Addons path change takes the site down if half-applied.** | Dockerfile change and bind-mount removal in the **same** commit; Phase 3's gate runs the image with no mount before anything deploys. |
| **OS Login cutover locks out the operator.** | Verify `osAdminLogin` via `testIamPermissions` before the window; serial console as backstop; the change is reversible with a stop. |
| **Disk fills mid-migration.** 74% at 30 GB, and the pipeline retains 3.12 GB images. | Phase 0c reclaims ~10 GB before anything else; `IMAGE_KEEP=3`; compose logging limits; journald capped. |
| **Terraform destroys production on import.** | The empty-plan gate, and the specific replacement-forcing fields named in Phase 1. Never fix a resource during an import. |
| **Owner unavailable for IAM.** | Request the time-boxed `projectIamAdmin` grant up front (§2). Phases 0–3 need none of it, so start there regardless. |
| **Approval depends on individuals.** Approve rights currently ride on `roles/editor` held by two named developers, plus two Owners — so who can release a deploy is a side effect of a broad role rather than a deliberate list. | Not a blocker (§2), but point `cloudbuild_approvers` at a **group** once the pipeline is live. An approver list is a rota, not architecture, and it should change without a Terraform apply — and it should not be inherited from `editor`. |
| **CI newly installs 20 untested modules** and fails on pre-existing breakage. | Expected, and it is the gate working. Run the derived-list suite locally before wiring it into the CD path, and budget time to fix or mark `installable: False`. |
| **Docker is pinned to 28.5.2 by an undocumented `apt-mark hold`,** and `containerd.io` is not pinned. A stray `apt upgrade` moves containerd underneath it, or an `unhold` restores the February outage. | Documented in Phase 0b. Never run `apt upgrade` on this VM during the migration; use targeted commands. Automatic upgrades are already ruled out — unattended-upgrades admits Debian origins only. Unpin later, in its own window, now that Traefik is on v3.2. |

---

## 7. Out of scope, and why the disk does not need growing

**Machine type.** `e2-medium` stays. `workers = 3` with `max_cron_threads = 1`
is a tight fit on 2 shared vCPUs and 4 GB, but the evidence does not show it
hurting: zero worker recycling in 30 days of logs. Revisit once Phase 6 makes
real memory and CPU metrics exist — which is the honest order for that decision.

**Disk size.** 30 GB stays. The disk is 74% full, and of the 21 GB used, roughly
10 GB is reclaimable garbage: 2.9 GB of uncapped journal, 6.5 GB in an untracked
containerd store, 599 MB of the Ops Agent's own failure logs, 534 MB of uncapped
container logs, 147 MB of apt cache. Reclaiming that takes free space to ~17 GB
— comfortable for three retained 3.12 GB images plus the application. Capping
the journal and container logs also stops the growth that got it here.

A resize would paper over that without fixing any of it, and growing a disk is
one-way: `pd-balanced` grows online with no downtime, but **shrinking is
impossible**.

**Also deferred, deliberately:**

* Tightening `limit_memory_soft`/`hard` — no evidence they are wrong (§1.4).
* Consolidating the five human home directories and metadata SSH keys. Phase 5
  makes them non-load-bearing; removing them is separate work.
* GCS legacy-binding hardening on the backups bucket (§8).
* Moving Traefik's ACME contact off a personal address. P4 covers the symptom;
  the fix is a real change with its own verification.
