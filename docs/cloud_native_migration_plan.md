# Estate migration — GKE, Cloud SQL, GCS filestore, Redis sessions

Companion to `docs/infrastructure_migration_plan.md`, which is **done**: Phases
0–8 there took `odoo-hrms-prod` from a hand-managed VM to imported Terraform,
Cloud Build CI/CD with an approval gate, IAP-only SSH under OS Login, secrets in
Secret Manager, a truthful image tag, a shipping Ops Agent, 4-hourly snapshots
and five proven alerts.

This document plans what the *Technical Architecture Proposal & Migration
Blueprint* (v1.0, Draft) asks for next: moving the estate off standalone
stateful VMs onto stateless GKE workloads backed by Cloud SQL, GCS and
Memorystore, and adding two new domain instances.

That plan numbers its phases 1–3, and the plan it continues from numbers its
phases 0–8. To avoid a third competing numbering, this document uses **Stages**
and maps them to the blueprint at §6.

> **Read §2 before costing or scheduling anything.** The blueprint's code-level
> premises were checked against the Odoo 19 source vendored in this repository,
> not against general knowledge. Four of them are wrong or incomplete in ways
> that change the work, and one of them — the attachment download path — would
> produce a PoC where uploads succeed and every download returns HTTP 500.

---

## 1. Verified current state

Everything in this section was read out of this repository or the source
vendored in it, at the paths given. Nothing here is inferred from the blueprint.

### The application

| Fact | Where |
| --- | --- |
| Odoo **19.0** final | `odoo/release.py` — `version_info = (19, 0, 0, FINAL, 0, '')` |
| 22 custom addons, 191 `.py` and 108 `.xml` | `custom_addons/` |
| Baked into the image at `/opt/cleardeals-addons`, **not** `/mnt/extra-addons` | `Dockerfile`, `odoo.prod.conf` → `addons_path` |
| `ohrms_core` depends on 18 other modules; `hrms_dashboard` on 11 | `custom_addons/*/__manifest__.py` |
| No BigQuery dependency, unlike the CRM instance | `entrypoint.sh`, `requirements.txt` |
| `requirements.txt` contains **no** `google-cloud-*` and **no** `redis` | `requirements.txt` |

`oh_employee_documents_expiry/models/ir_attachment.py` already inherits
`ir.attachment` — it adds two Many2many columns and nothing storage-related. It
is the only existing extension of that model, so a storage override will not
collide with local code.

### The runtime

Single VM, one Docker Compose stack:

- `odoo-hrms-prod`, **e2-medium** (2 *shared* vCPU, 4 GB), Debian 12 bookworm,
  `us-central1-c`, 30 GB `pd-balanced`, `auto_delete = false`,
  `deletion_protection = true`.
- `traefik:v3.2` terminating TLS, ACME `tlsChallenge`, routing on
  `Host('hr.cleardeals.xyz')`, with a second router sending `/websocket` and
  `/longpolling` to port 8072.
- `postgres:17` in a container, data on a bind mount (`./odoo-db-data`),
  `max_connections = 60`.
- `odoo` pinned by commit SHA from Artifact Registry, config rendered to
  `/dev/shm/odoo.conf` (tmpfs) by `scripts/render_odoo_conf.sh`.
- `workers = 3`, `max_cron_threads = 1`, `gevent_port = 8072`,
  `db_maxconn = 5`, `proxy_mode = True`, `db_name`/`dbfilter` pinned to
  `odoo_hrms_db`, `list_db = False`.

Data sizes, from the comment in `infrastructure/terraform/storage.tf`:
**119 MB database, 759 MB filestore** of HR documents (payroll and personnel
attachments).

### Invisible operational state that this migration must not trip over

- **Docker is held at 28.5.2 with `apt-mark hold`**, and that hold is not in
  this repo and not in Terraform. Engine 29.2.1 raised the minimum Docker API
  version above the 1.24 that older Traefik clients speak; the docker provider
  died and Traefik served 404 for every request for ~2.5 h on 2026-02-16 while
  Odoo was perfectly healthy behind it. `containerd.io` is *not* held. See
  `docker-compose.yml` and `docs/infrastructure_migration_plan.md` §0b.
- The `letsencrypt/acme.json` volume is the only copy of the certificate state.
- The ACME contact address is a personal mailbox outside the company.

### Access, which is the real constraint

From `docs/infrastructure_migration_plan.md` §2 and the OPEN finding at its end:

- `developer2@` — the sole developer across HRMS, CRM and WhatsApp — holds
  `roles/editor`, `roles/container.admin`, `roles/secretmanager.admin`,
  `roles/cloudbuild.admin`, `roles/iam.workloadIdentityPoolAdmin`,
  `roles/iap.tunnelResourceAccessor`, `roles/compute.osLogin`,
  `roles/logging.viewer`.
- `resourcemanager.projects.setIamPolicy` is **DENIED**, so every
  `google_project_iam_member` still needs an Owner.
- **`developer2@` cannot SSH to production at all.** `roles/compute.osLogin` is
  not sufficient on a VM with an attached service account; the user also needs
  `iam.serviceAccounts.actAs` on `hrms-prod-vm@`, which only
  `hrms-cloudbuild@` holds. This is an OPEN finding held deliberately
  unremediated for auditor review.
- `roles/container.admin` **is** held, which is the one piece of good news
  here — the GKE cluster itself is within the current ceiling.

The last two points are why Stage 0 exists and why it is a hard gate. A Cloud
SQL cutover you cannot SSH into is not a cutover you can abort.

---

## 2. Where the blueprint is wrong or incomplete

The blueprint's architecture is sound. Its **code-level premises** are not, and
the gaps are the kind that surface after the migration rather than during it.
Each item below names the file and line it was checked against.

### 2.1 The attachment override surface is not `create`/`write`/`unlink`/`read`

§4.3 says to override "write, create, unlink, and read methods" on
`ir_attachment.py`. Those are ORM methods, and overriding them means
reimplementing checksum, mimetype and `res_field` handling that already works.

The actual storage seam is three `@api.model` methods, and it is deliberately
narrow:

| Method | Line in `odoo/addons/base/models/ir_attachment.py` |
| --- | --- |
| `_file_read(self, fname, size=None)` | 147 |
| `_file_write(self, bin_value, checksum)` | 158 |
| `_file_delete(self, fname)` | 173 |
| `_storage(self)` — reads `ir_attachment.location`, default `'file'` | 88 |
| `_get_storage_domain(self)` | 96 |
| `_full_path(self, path)` / `_get_path(self, bin_data, sha)` | 125 / 132 |

`create` and `write` already funnel into `_inverse_datas` (276) →
`_get_datas_related_values` (306) → `_file_write`. Override the three file
methods and the ORM is untouched.

`_storage()` reading an **`ir.config_parameter`** is the most useful fact in
this section: the switch between local disk and GCS is a database row, so it can
be flipped and reverted from the UI without a deploy.

### 2.2 The download path bypasses `_file_read` entirely — and would 500

`_to_http_stream()` at `ir_attachment.py:896` does not call `_file_read`. It
does this:

```python
if self.store_fname:
    stream.type = 'path'
    stream.path = werkzeug.security.safe_join(
        os.path.abspath(config.filestore(request.db)),
        self.store_fname
    )
    stat = os.stat(stream.path)          # <-- FileNotFoundError with GCS
```

With objects in GCS there is no local file, so `os.stat` raises and **every
attachment download returns HTTP 500 while uploads appear to work perfectly**.
This is not mentioned anywhere in the blueprint. Implementing §4.3 exactly as
written produces that PoC.

`_to_http_stream` must be overridden too. The good news is that Odoo 19 already
supports the right answer: `Stream.type` accepts `'url'`
(`odoo/http.py:492`), and `Stream.get_response()` turns it into a redirect
(`odoo/http.py:591–596`):

```python
if self.type == 'url':
    if self.max_age is not None:
        res = request.redirect(self.url, code=302, local=False)
        res.headers['Cache-Control'] = f'max-age={self.max_age}'
        return res
    return request.redirect(self.url, code=301, local=False)
```

So a **V4 signed GCS URL** is a first-class option and attachment bytes never
traverse a pod — which matters a great deal on 759 MB of HR documents behind an
HPA.

Two traps in that path:

1. **Always set `max_age`.** Without it the branch above emits a **301
   permanent** redirect to a URL that expires. Browsers and intermediate caches
   are entitled to keep a 301 indefinitely, so users get a cached redirect to a
   dead signed URL. Set `max_age` well below the signature lifetime.
2. **Signing needs a key, and Workload Identity does not give you one.** With
   Workload Identity there is no private key on disk, so
   `blob.generate_signed_url` cannot sign locally. It has to go through the IAM
   `signBlob` API, which requires the pod's service account to hold
   `roles/iam.serviceAccountTokenCreator` **on itself**. That grant is easy to
   miss and the failure only appears on the first download.

If signed URLs are rejected for policy reasons, the fallback is
`stream.type = 'data'` with the bytes fetched from GCS — correct, but it loads
each file fully into worker memory, against `limit_memory_hard = 640 MB`.

**Scope the override precisely.** `ir.attachment` already has a `type = 'url'`
kind — an external link, not stored content — with its own handling
(`_is_remote_source`, 944; `_migrate_remote_to_local`, 963). The `store_fname`
branch at 896 is the only one to intervene in, and the condition must be
`self.store_fname and self._storage() == 'gcs'`. An override that fires on every
attachment will break link attachments and the `db_datas` fallback path, neither
of which has anything to do with GCS.

### 2.3 A third storage location raises `KeyError` in `force_storage()`

`_get_storage_domain()` (line 96) is a dict literal with exactly two keys:

```python
return {
    'db':   [('store_fname', '!=', False)],
    'file': [('db_datas',    '!=', False)],
}[self._storage()]
```

Set `ir_attachment.location = gcs` and this raises `KeyError: 'gcs'`. It is
called by `force_storage()` (104) — which is precisely the tool needed to
migrate the existing 759 MB. So the migration tool breaks first, before
anything else does. `_get_storage_domain` must be overridden.

### 2.4 Filestore garbage collection stops completely, and silently

`_gc_file_store` (191) opens with:

```python
if self._storage() != 'file':
    return
```

It is an `@api.autovacuum`. So with `location = gcs`:

- deleted attachments never have their GCS objects removed;
- orphaned objects accumulate for the life of the system and are billed;
- nothing logs a warning, because the early return is the intended behaviour
  for the `db` case.

Core's `_file_delete` (173) does not delete anything either — it only calls
`_mark_for_gc`, which writes an empty file into a **local** `checklist/`
directory. A stateless pod cannot rely on that: the pod that marks a file may
never be the pod that collects, and both may be gone.

A replacement GC has to respect one subtlety that is easy to miss.
`store_fname` is **content-addressed** — `_get_path` (132) builds it as
`sha[:2] + '/' + sha` — so two attachment records with identical content share
one object. Deleting eagerly on `unlink` will delete a blob another record still
references. Core avoids this by collecting out-of-band under
`LOCK ir_attachment IN SHARE MODE`; any replacement must do the equivalent
existence check against `store_fname` before removing a blob.

### 2.5 The session store has an in-tree reference implementation — with two bugs in it

§4.4 says to "override the native `session_store` handler in `odoo.http`". The
contract is larger than it looks, and Odoo ships a non-filesystem store to copy
from: `MemorySessionStore(SessionStore)` at
**`odoo/addons/test_http/utils.py:53`**. It is the canonical minimum surface —
`get`, `save`, `delete`, `delete_from_identifiers`,
`get_missing_session_identifiers`, `delete_old_sessions`, `rotate`,
`generate_key`, `is_valid_key`, `vacuum`.

**Do not copy it verbatim. It has two defects that are invisible in tests and
load-bearing in production.**

1. **`vacuum` has the wrong signature.** The test store defines
   `def vacuum(self):`, but `odoo/addons/base/models/ir_http.py:410` calls it as

   ```python
   http.root.session_store.vacuum(max_lifetime=http.get_session_max_inactivity(self.env))
   ```

   which is a `TypeError` in the daily autovacuum. The signature must be
   `vacuum(self, max_lifetime=SESSION_LIFETIME)`.

2. **`get_missing_session_identifiers` compares the wrong lengths.** It does
   `set(identifiers).difference(self.store)`. Identifiers are 42-character
   prefixes (`STORED_SESSION_BYTES = 42`, `odoo/http.py:321`); store keys are
   84-character sids. The difference therefore never matches and **every
   identifier is reported missing**. The filesystem store gets this right by
   comparing `sf.name[:42]` (`odoo/http.py:1068`).

   That method and `delete_from_identifiers` are what back `res.device` —
   `odoo/addons/base/models/res_device.py:157` and `:184`. Copying the bug means
   the "my devices / log out everywhere" feature reports every device as revoked.

**Redis mapping.** `SESSION_LIFETIME = 604800` s (7 days,
`odoo/http.py:308`), so a Redis TTL makes `vacuum` a genuine no-op rather than a
stub. Alongside `session:<sid>`, keep a secondary index — a Redis SET at
`sessidx:<sid[:42]>` — so `delete_from_identifiers` and
`get_missing_session_identifiers` are index lookups. **Never `SCAN` or `KEYS` on
a request path**; that is the version of this module that works in staging and
falls over at 200 concurrent users.

`rotate(soft=True)` (`odoo/http.py:985`) writes a `next_sid`, reads it back to
detect a concurrent rotation, and leans on `create_time` plus
`SESSION_DELETION_TIMER = 120` s in `delete_old_sessions` (964). Get that
read-back wrong and concurrent requests during rotation log users out at random
— which will be blamed on Redis, not on the rotation.

### 2.6 The session store cannot be a normal addon

`session_store` is a `functools.cached_property` on the `Application` singleton:

```python
# odoo/http.py:2716
@functools.cached_property
def session_store(self):
    path = odoo.tools.config.session_dir
    return FilesystemSessionStore(path, session_class=Session, renew_missing=True)
```

`root` is constructed when `odoo.http` is imported, and the store is consulted
**before any database registry exists** — nodb routing, `/web/database/selector`,
`odoo/http.py:1767`. A per-database addon loads far too late and would be
bypassed on every nodb request.

It has to be a **server-wide module**. `odoo/service/server.py:1546` calls
`load_server_wide_modules()` and only then imports `odoo.http`, which is the
window in which the patch has to land. `odoo.prod.conf` currently sets
`server_wide_modules = base,web`, so this is a one-line config change plus a new
module.

Because `cached_property` writes into the instance `__dict__` on first access,
the patch must either replace `Application.session_store` before that first
access or explicitly evict it with `root.__dict__.pop('session_store', None)`.
Getting this wrong yields a module that is installed, logs nothing, and stores
sessions on disk anyway — the worst possible failure, because it looks like it
worked.

### 2.7 The websocket is a separate OS process, not a second port

`odoo/service/server.py:1549`:

```python
if odoo.evented:
    server = GeventServer(odoo.http.root)
elif config['workers']:
    server = PreforkServer(odoo.http.root)
else:
    server = ThreadedServer(odoo.http.root)
```

`odoo.evented` is not a config option — it is set in
`odoo/_monkeypatches/site.py` (`False` at line 20, `True` at line 54). In
prefork mode the master forks the gevent process itself
(`process_spawn`, line 975), which is why `docker-compose.yml`'s
`/websocket` route to `:8072` is load-bearing today.

On GKE that leaves two shapes:

- **(a) one Deployment**, each pod running the full prefork tree (master + 3
  HTTP + 1 cron + 1 gevent). Simplest, and closest to today — but each pod is a
  small monolith and the HPA scales the bus and the cron along with web traffic.
- **(b) three Deployments** — `web` (`workers=N`, `max_cron_threads=0`), `bus`
  (evented, serving 8072), `cron` (`workers=0`, `max_cron_threads=N`) — with the
  Ingress routing `/websocket` and `/longpolling` to the `bus` Service. This is
  the same split the compose labels already encode, and it is the one that makes
  HPA meaningful.

**(b) is the recommendation**, and the mechanism for starting the `bus`
Deployment is now **verified** rather than open. It was resolved by reading
`ps auxf` on the live VM, which shows the master spawning:

```
/opt/odoo-venv/bin/python3 /usr/bin/odoo gevent
```

The switch is `argv[1]`, and the check is positional
(`odoo/_monkeypatches/site.py:29`):

```python
if odoo.evented or not (len(sys.argv) > 1 and sys.argv[1] == 'gevent'):
    return
```

`odoo/service/server.py:898` confirms the master does exactly that:
`cmd = [sys.executable, sys.argv[0], 'gevent'] + nargs[1:]`.

**`gevent` must be the FIRST argument**, not merely present. So
`odoo -c /etc/odoo/odoo.conf gevent` runs a normal prefork server and silently
serves no websockets — the pod comes up healthy and the bus is simply dead. The
container command is:

```yaml
command: ["odoo", "gevent", "-c", "/etc/odoo/odoo.conf"]
```

which `entrypoint.sh` rewrites to `python3 /usr/bin/odoo gevent -c ...`, keeping
`gevent` in position 1.

Two related options exist for that Deployment and are worth using, since the bus
process has a very different memory profile from an HTTP worker:
`limit_memory_soft_gevent` and `limit_memory_hard_gevent`
(`odoo/tools/config.py:467,477`; consumed at `server.py:94,733`). Both fall back
to the non-gevent limits when unset.

### 2.8 Cron is already safe across pods — but still wants its own Deployment

`odoo/addons/base/models/ir_cron.py:365` claims jobs with
`FOR NO KEY UPDATE SKIP LOCKED`. So N pods with cron enabled will not
double-run a job; this is not a correctness problem, and the blueprint is right
not to worry about it.

It is a resource problem. Every cron-enabled pod holds connections and polls,
and an HPA sized for web traffic would scale cron with it. Separate Deployment,
`replicas: 1`, cron disabled everywhere else.

### 2.9 What must never go in front of Cloud SQL

`addons/bus/models/bus.py:29` and `:164` use `pg_notify` (with an
`ODOO_NOTIFY_FUNCTION` env override), and the longpolling side `LISTEN`s on the
`imbus` channel.

- The **Cloud SQL Auth Proxy is a TCP proxy** and preserves `LISTEN`/`NOTIFY`.
  The blueprint's §4.2 choice is correct.
- **A transaction-pooling PgBouncer does not.** Notifications are silently lost;
  chat, activity counters and every realtime update stop, with nothing in any
  log.

This is worth writing down now because "put PgBouncer in front of it" is the
obvious optimisation the first time pod count pushes the connection count up,
and it is the change that breaks the bus with no error message.

### 2.10 The connection budget, which is how an autoscaled Odoo kills its own database

`odoo/sql_db.py:811` keeps **two** module-level pools, `_Pool` and
`_Pool_readonly`, and `http.py` takes a readonly cursor on every request. With
no `db_replica_host` configured, `connection_info_for` (769) falls back to the
primary — so those are separate physical connections to the same server.

`odoo.prod.conf` already documents today's arithmetic: 5 processes × 2 pools ×
`db_maxconn` 5 = 50, against `max_connections = 60`.

On GKE the multiplier becomes **the pod count**, and the HPA controls it. Two
consequences:

- `max_connections` on the Cloud SQL instance must be set **explicitly**, not
  left at the tier default.
- `maxReplicas` must be derived from the connection budget, not only from CPU.
  An HPA that can scale to a pod count whose connection ceiling exceeds
  `max_connections` will, under exactly the load it exists to absorb, take the
  database down for every instance sharing it.

### 2.11 GCS and Redis alone do not make the pod stateless

Still writing to local disk after both overrides land:

- `config.addons_data_dir` = `$data_dir/addons` (`odoo/tools/config.py:989`),
  used by `odoo/modules/module.py:147`.
- Report rendering temp files — and note
  `odoo/addons/base/models/ir_actions_report.py:558` calls
  `root.session_store.new()`, so the Redis store sits on the **PDF report
  path** too, not just on login.
- Traefik's `acme.json`, replaced by GKE-managed certificates or cert-manager.

None of these need to survive a pod restart, so the answer is an `emptyDir` for
`/var/lib/odoo` rather than a PVC. But "stateless" has to mean *nothing durable
on local disk*, not *no local disk* — a pod with a read-only root filesystem and
no writable data dir will not boot.

### 2.12 Cloud SQL, `unaccent`, and the restore

`odoo.prod.conf` sets `unaccent = True`. Per `odoo/tools/config.py:448` that
only means "try to enable the extension **when creating new databases**" — it is
not what makes search work on an existing one. What matters at boot is
`has_unaccent` (`odoo/modules/db.py:166`); if the extension is absent, search
behaviour changes silently rather than failing.

The restore is where this bites: a `pg_dump` of `odoo_hrms_db` contains
`CREATE EXTENSION unaccent`, and on Cloud SQL that requires membership of
`cloudsqlsuperuser`. Restore as the Cloud SQL default user, then reassign
ownership to the `odoo` role. A restore run directly as `odoo` fails part-way
through, which is the worst moment for it.

### 2.13 Cost is an order-of-magnitude change, and it multiplies by four

One `e2-medium` with a co-located Postgres and a local disk becomes: a GKE
cluster, a **regional-HA** Cloud SQL instance, and a Memorystore instance. That
is a large multiple of today's bill, not a marginal increase — and the blueprint
applies it four times over (HRMS, Ops, Sales, Invoicing).

The decision to surface before Stage 4, because it is expensive to reverse:
**one shared Cloud SQL instance holding four databases, or four instances?**

The blueprint says "a centralized, fully managed GCP Cloud SQL cluster" (§4.2),
i.e. shared. For four small databases — HRMS is 119 MB — that is almost
certainly right on cost and operational load. But it re-couples the four domains
at exactly two levels the architecture is otherwise trying to decouple
(§3): noisy-neighbour capacity, and the maintenance window. Name it as a
deliberate trade rather than letting it arrive by default, and if shared:

- a separate Postgres **role per domain**, with no cross-database grants, so
  Sales cannot read payroll;
- `max_connections` budgeted across all four instances' HPAs together (§2.10),
  not per instance.

The same question applies to Memorystore. One instance with a key prefix or
logical DB per domain is fine and much cheaper; four is cleaner. Sessions are
small and uniform, so shared is the easier call here than for the database.

### 2.15 Stage 1 adds two libraries, and there is 46 MiB of headroom

Measured on the live VM, not reasoned about. `ps auxf` inside `odoo-app`:

| PID | what | VSZ | RSS |
| --- | --- | --- | --- |
| 1 | master | 386,236 KB | 187,124 KB |
| 19 | WorkerHTTP | **477,508 KB** | 197,860 KB |
| 21 | WorkerHTTP | 475,596 KB | 220,284 KB |
| 23 | WorkerHTTP | 473,412 KB | 204,432 KB |
| 24 | gevent (`odoo gevent`) | 472,364 KB | 200,524 KB |
| 26 | WorkerCron (niced, `os.nice(10)` at `server.py:1432`) | 455,884 KB | 171,692 KB |

Against `odoo.prod.conf`:

```
limit_memory_soft = 536870912   =  524,288 KB   (512 MiB)
limit_memory_hard = 671088640   =  655,360 KB   (640 MiB)
```

These are **virtual** memory limits (`RLIMIT_AS`), so VSZ is the column that
matters. The largest worker is at **91% of the soft limit**, with about
**46 MiB** of address space to spare. Total RSS across the six processes is
~1.13 GiB on a 4 GB machine that also runs Postgres with
`shared_buffers = 512MB`.

**Why this lands on Stage 1.** Stage 1 adds `google-cloud-storage` and `redis`
to `requirements.txt`. Every import maps code and allocates, and it happens in
**each** worker. There is 46 MiB of room. `google-cloud-storage` pulls
`google-auth`, `google-api-core`, `requests` and `google-crc32c`; that may fit,
and it may not.

Crossing `limit_memory_soft` does not crash anything and does not look like an
error. Odoo finishes the current request and then recycles the worker. The
symptoms are latency, lost warm caches, and `virtual memory limit reached` lines
in the container log — easily mistaken for a problem with the new GCS code
rather than with the ceiling it is running into.

`odoo.prod.conf` explicitly deferred this decision, and its stated trigger has
now fired:

> Left exactly as they are. […] Revisit once Phase 6 makes real memory metrics
> exist — which is the first time there will be data to decide on.

Phase 6 is done. The data exists.

**So Stage 1 gains a gate:** record per-worker VSZ before and after adding the
two libraries. If the delta eats the headroom, raise `limit_memory_soft` and
`limit_memory_hard` **in the same change that adds the libraries** — deliberately
and with the measurement recorded, not reactively after someone reports the site
feeling slow. The limits are RLIMIT_AS, not RSS, so raising them costs no actual
memory; the 4 GB ceiling is governed by RSS, which has room.

### 2.14 Sales and Invoicing are product work, not infrastructure work

Blueprint Phase 3 bundles "deploy Sales Odoo and Invoices Odoo" with "codify all
cloud resources into Terraform". Those are unrelated efforts on very different
timelines: one is building two new applications, including replacing ROLO and
integrating Razorpay; the other is a Terraform module.

Keep them apart. The platform should be proven and codified by HRMS and Ops
before it is asked to host something that does not exist yet, and the Terraform
should not wait on a product build.

---

## 3. The single most important planning change

**The blueprint's Phase 1 bundles four independent changes into one PoC**:
database migration, filestore refactoring, session refactoring, and the move to
GKE. Its own step list (§5, Phase 1, items 1–5) runs them together and validates
at the end.

Do not do that. Run the first three **on the existing VM**, one at a time, and
move to GKE last.

The argument is entirely about diagnosis and rollback:

| Change | Rollback on the VM | Rollback if bundled with GKE |
| --- | --- | --- |
| GCS filestore | `ir.config_parameter` back to `file`; re-migrate | plus a workload rollout |
| Redis sessions | config line + restart; everyone re-logs-in | plus a workload rollout |
| Cloud SQL | repoint `db_host`, container Postgres still holds the data | plus a workload rollout |
| GKE | — | four suspects, no independent revert |

Each of the first three is independently provable against real production data
and real user behaviour, on a stack where rollback is a config change and
`docker compose up -d`. If they land together and something breaks, there are
four suspects and no rollback that is not itself four changes.

By the time GKE arrives, the application is already stateless and already
talking to the managed services. The compute move then tests exactly one thing:
whether it runs in a pod.

There is a second benefit. The two code overrides are the only genuinely novel
engineering in this programme — everything else is provisioning. Proving them
first, where the blast radius is one VM that can be snapshot-restored, is also
what makes them reusable for Ops, Sales and Invoicing with confidence rather
than hope.

---

## 4. Target architecture for HRMS

```
                        ┌──────────────── GCLB / Ingress ────────────────┐
                        │  managed cert, Host: hr.cleardeals.xyz         │
                        └───┬───────────────────────────┬────────────────┘
              /websocket    │                           │  everything else
              /longpolling  │                           │
                     ┌──────▼──────┐            ┌───────▼───────┐   ┌──────────┐
                     │ Deployment  │            │  Deployment   │   │Deployment│
                     │    bus      │            │      web      │   │   cron   │
                     │  (gevent)   │            │ workers=N     │   │workers=0 │
                     │   :8072     │            │ cron=0  :8069 │   │ cron=N   │
                     └──────┬──────┘            └───────┬───────┘   └────┬─────┘
                            │        HPA on CPU + connection budget │      │
                            └───────────────┬───────────────────────┴──────┘
                                            │  Workload Identity
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
          ┌─────────▼─────────┐   ┌─────────▼─────────┐   ┌─────────▼─────────┐
          │  Cloud SQL PG 17  │   │   GCS bucket      │   │ Memorystore Redis │
          │  regional HA,PITR │   │  filestore        │   │  sessions, TTL 7d │
          │  via Auth Proxy   │   │  signed-URL reads │   │                   │
          └───────────────────┘   └───────────────────┘   └───────────────────┘
```

New code, as two addons so each can be switched on independently:

- **`cleardeals_gcs_filestore`** — a normal addon. Overrides `_storage`,
  `_get_storage_domain`, `_file_read`, `_file_write`, `_file_delete`,
  `_to_http_stream`, and adds a GCS-aware garbage collector. Inert until
  `ir_attachment.location` is set to `gcs`, so installing it changes nothing.
- **`cleardeals_redis_session`** — a **server-wide** module (§2.6). Patches
  `Application.session_store`. Reads its connection details from `odoo.conf`,
  not from the database, because it loads before any database. Falls back to the
  filesystem store when unconfigured, so it is also inert on install.

Both go in `custom_addons/`, are baked into the image by the existing
`Dockerfile`, and ride the existing Cloud Build pipeline. No change to how
deploys work.

---

## 5. Stages

Each stage states its gate. A stage is not done until its gate passes. Stages
1–3 change nothing about where the application runs.

### Stage 0 — Access (hard gate, blocks everything)

The programme needs strictly more than the last one did: Cloud SQL admin, Redis
admin, `servicenetworking` for the private-services peering that both Cloud SQL
private IP and Memorystore require on the `default` VPC, Workload Identity
bindings, and `container.admin` (already held).

Two things must be resolved first, and neither is a technical task:

1. **The OPEN OS Login finding.** `developer2@` cannot SSH to production. Stages
   2–4 all involve watching a live cutover on that VM and aborting it by hand.
   The fix is one `google_service_account_iam_member` granting
   `roles/iam.serviceAccountUser` to the developer on `hrms-prod-vm@`
   specifically — login only, no sudo. It needs an Owner, and it needs the
   auditor review it is currently being held for.
2. **`resourcemanager.projects.setIamPolicy`.** Every new service account
   binding in this programme is a project-level IAM change. The existing
   recommendation stands: a time-boxed `roles/resourcemanager.projectIamAdmin`
   grant so the Terraform applies as one unit. PAM is already enabled on this
   project with zero entitlements and is the right vehicle; configure it with
   **no approver**, because a sole developer has none and an approval gate with
   no approver is a lockout during the incident it exists for.

**Gate:** `developer2@` can run `terraform plan` to an empty plan **and** can
`gcloud compute ssh odoo-hrms-prod --tunnel-through-iap` successfully.

### Stage 1 — Both overrides written, tested, and switched off

Write both addons. Add `google-cloud-storage` and `redis` to
`requirements.txt`. Extend the existing CI (`cloudbuild.ci.yaml` already has
`config-check`, `image-contents`, `shell-syntax`, `api-docs` and `test` steps) with:

- unit tests for the GCS store against a fake/emulated bucket, covering
  `_file_write` → `_file_read` round-trip, `_file_delete`, the shared-blob
  refcount case from §2.4, and `_to_http_stream` returning a `type='url'`
  stream;
- unit tests for the Redis store that assert the two bugs of §2.5 are **not**
  present: `vacuum(max_lifetime=...)` accepts the kwarg, and
  `get_missing_session_identifiers` correctly matches 42-character prefixes
  against 84-character sids;
- a `rotate(soft=True)` concurrency test, because that is where session bugs
  hide.

Deploy through the normal pipeline. Both modules installed, neither active:
`ir_attachment.location` still absent (so `_storage()` returns `'file'`), and
`cleardeals_redis_session` in `server_wide_modules` but with no Redis host
configured, falling back to the filesystem store.

**Gate:** the modules are live in production, CI is green, and production
behaviour is byte-for-byte unchanged — attachments still on local disk, sessions
still in `$data_dir/sessions`. This is a deliberately boring deploy, and if it
is not boring, something in §2.6 is wrong.

**Plus the memory gate from §2.15**: per-worker VSZ recorded before and after
the two new libraries, and `virtual memory limit reached` still absent from the
container log. There is only ~46 MiB of address space above
`limit_memory_soft`, so if the imports consume it, raise both limits in this
same change with the measurement written down.

### Stage 2 — GCS filestore, still on the VM

Terraform a bucket (uniform access, public access prevention, versioning; the
`storage.tf` house pattern), and grant the VM's `hrms-prod-vm@` **`objectAdmin`
here** — unlike the backups bucket, this one genuinely needs delete for GC. Add
`roles/iam.serviceAccountTokenCreator` on itself if signed URLs are used
(§2.2).

Then, in order: set `ir_attachment.location = gcs`, verify a *new* upload lands
in GCS and downloads, and only then migrate the existing 759 MB with
`force_storage()` — **in batches**, because core's `_migrate` (116) rewrites
every record in one transaction, and 759 MB of `attach.write({'raw': ...})` in a
single transaction on a 4 GB box with a 640 MB hard memory limit will not
finish.

**Reversibility, stated precisely because it is easy to get wrong:** flipping
the parameter back to `file` is instant and affects only *new* writes.
Attachments written to GCS while it was on have no local file, so a real revert
means running the migration in reverse. The flag is not a rollback on its own.

**Gate:** upload, download, and PDF report generation all work; `force_storage`
completes with zero attachments left holding `db_datas`; the count of distinct
`store_fname` values in `ir_attachment` equals the object count in the bucket;
and a delete followed by the new GC actually removes the blob while leaving a
shared blob alone.

### Stage 3 — Memorystore Redis sessions, still on the VM

Memorystore needs private services access peering on the `default` VPC. Point
`cleardeals_redis_session` at it via `odoo.prod.conf` — which means the render
step and the boot-time render unit both carry it, and `terraform.tfvars` gains
the host.

**Gate:** log in, `docker compose restart odoo`, and remain logged in. Then the
harder ones: `res.device` lists the session and revoking it actually logs that
device out (this is the §2.5 bug #2 test, in production); a PDF report still
renders (§2.11 — reports create a session); and the websocket still connects,
since `addons/bus/websocket.py:759` reads the store directly.

Cutting over logs everyone out once. Do it deliberately, announced, out of hours.

### Stage 4 — Cloud SQL, still serving from the VM

The only stage with real downtime, and the only one with a genuine point of no
return once writes land on the new database.

Provision Cloud SQL for PostgreSQL 17, **regional HA**, PITR on, private IP,
`max_connections` set explicitly (§2.10). Run the Cloud SQL Auth Proxy on the VM
and point `db_host` at it. Restore as the Cloud SQL default user, then reassign
ownership to `odoo` (§2.12).

Sequence: pre-cutover dump; stop Odoo; final dump; restore; verify row counts
against `docs/erd/row_counts.csv`; repoint `db_host`; start; health gate; edge
gate.

**Keep the container Postgres and its `./odoo-db-data` bind mount intact for 14
days.** Stopped, not deleted. It is the only rollback that does not involve a
restore.

**Gate:** the full stack on Cloud SQL with container Postgres stopped;
`unaccent` confirmed present via `has_unaccent`; `LISTEN`/`NOTIFY` confirmed
working end-to-end by watching a chat message arrive in a second browser (§2.9);
and a PITR restore to a throwaway instance actually performed, because a backup
nobody has restored is not a backup — the same argument
`infrastructure/terraform/storage.tf` already makes about the empty backups
bucket.

### Stage 5 — GKE

Only now. The application is already stateless and already speaking to the
managed services, so this stage tests one thing.

Three Deployments per §2.7 (`web`, `bus`, `cron`), Workload Identity instead of
node service accounts, `emptyDir` on `/var/lib/odoo` (§2.11), Ingress with a
managed certificate and the `/websocket` + `/longpolling` split, HPA bounded by
the connection budget rather than CPU alone.

Run both stacks in parallel against the same Cloud SQL instance. Cut DNS only
once the GKE stack passes an edge gate equivalent to the one in
`scripts/deploy.sh` — and note that gate's history: on the CRM instance Odoo was
healthy while Traefik served 404 for every request, and the deploy went green.
The Ingress is a new component with the same failure mode.

**Gate:** GKE serves `hr.cleardeals.xyz` correctly before DNS moves; a pod kill
during an active session does not log the user out (this is what Stage 3 bought);
an HPA scale-up to `maxReplicas` does not exhaust `max_connections`; the cron
Deployment is the only thing running crons.

### Stage 6 — Decommission, and codify

Stop the VM. **Do not delete it for 30 days** — `auto_delete = false` and
`deletion_protection = true` are already set, and the boot disk outlives the
instance by design.

Then bring everything into Terraform as a reusable module, because Ops, Sales
and Invoicing are about to instantiate it three more times. Retire the parts of
the old plan that no longer describe reality: the snapshot schedules, the
container-Postgres tuning, the Traefik/Docker version hold.

**Gate:** a `terraform plan` that is empty, against infrastructure that is now
entirely declared.

### Stage 7 — Operations instance (blueprint Phase 2)

Apply the proven modules to the Operations codebase. The blueprint's Phase 2 is
correct as written and needs no restructuring, with one addition: Ops has
dependencies HRMS does not. The CRM instance queries **BigQuery in a different
project** from 22 files across `lead_suggestor` and `leads/models/lead_score.py`,
which means cross-project IAM that HRMS never needed
(`infrastructure/terraform/iam.tf` records exactly this difference). Attaching a
new service account without replicating those grants breaks lead scoring at
runtime, silently.

Also expect the CRM instance to have the **identical OS Login defect** — same
cutover, same attached-service-account pattern, `serviceAccountUser` granted only
to its build account. Untested, and worth testing before it is needed.

### Stage 8 — Sales and Invoicing (blueprint Phase 3)

New applications on a proven platform. Out of scope for this document beyond
one infrastructure note: the bi-directional Operations↔Sales integration and the
Razorpay webhooks into Invoicing are the first **inbound** third-party traffic in
the estate, so they need their own authentication, replay protection and rate
limiting at the Ingress. That is not a detail of the compute migration and should
not be planned as one.

---

## 6. Mapping to the blueprint

| Blueprint | Here | Change |
| --- | --- | --- |
| Phase 1.1 DB migration | Stage 4 | Moved **after** the code refactors, not before |
| Phase 1.2 Filestore refactoring | Stages 1–2 | Split: write/test, then switch on, on the VM |
| Phase 1.3 Session refactoring | Stages 1, 3 | Same split; must be a **server-wide** module |
| Phase 1.4 Environment provisioning | Stages 2–4 | Per-stage, not up front |
| Phase 1.5 PoC validation on GKE | Stage 5 | GKE is the **last** step of the PoC, not the container for it |
| Phase 2 Operations | Stage 7 | Unchanged in substance |
| Phase 3.1–3.3 Sales / Invoicing / Razorpay | Stage 8 | Separated from the IaC work |
| Phase 3.4 Terraform everything | Stage 6 | Moved earlier, and off the product timeline |

Plus Stage 0, which the blueprint does not have and which currently blocks
everything: see §1 on access.

---

## 7. Risks

1. **`_to_http_stream` (§2.2).** The highest-probability way to ship a broken
   PoC. Mitigated by making a download test part of the Stage 1 gate, before
   anything is switched on.
2. **The Redis store patched too late (§2.6).** Fails *silently* into the
   filesystem store. Mitigated by asserting the active store's class at startup
   and logging it, so "did it take effect" is answerable from a log line rather
   than from behaviour.
3. **HPA versus `max_connections` (§2.10).** Manifests as a database-wide outage
   under exactly the load the HPA exists to handle, and on a shared instance it
   takes the other domains with it. Mitigated by deriving `maxReplicas` from the
   connection budget and alerting on Cloud SQL connection utilisation before
   Stage 5.
4. **Orphaned GCS objects (§2.4).** Costs money quietly and forever. Mitigated by
   a GC with its own success metric and a staleness alert, built like
   `monitoring.tf`'s P2b.
5. **The Cloud SQL cutover (Stage 4).** The one irreversible step. Mitigated by
   keeping the container Postgres data dir for 14 days and by rehearsing the
   restore beforehand — the `odoo-prod-migration-check` skill in this repo
   rehearses a deployment against a read-only snapshot of production and should
   be used for the module-upgrade half of this.
6. **Cost (§2.13).** Not a technical risk, but the one most likely to stop the
   programme mid-flight and leave the estate in a half-migrated state, which is
   worse than either end. Price Stages 4 and 5 before starting Stage 2.
7. **Docker/Traefik version hold (§1).** Any host-level work on the VM during
   Stages 2–4 risks an `apt upgrade` that repeats the February outage. Nothing in
   these stages requires one.

---

## 8. What was not verified

Stated explicitly, because the value of the preceding sections rests on the
difference:

- ~~**How to start `GeventServer` standalone.**~~ **RESOLVED 2026-09-10**, by
  reading `ps auxf` on the live VM and then the source. It is `argv[1] == 'gevent'`
  — positional, not merely present (`odoo/_monkeypatches/site.py:29`,
  `odoo/service/server.py:898`). See §2.7 for the container command. This is the
  one open question in these documents that was answered by looking at the
  running system rather than at the code, which is worth noting: the source alone
  did not make the positional requirement obvious.
- **Cloud SQL, Memorystore and GKE behaviour.** Everything in §2 about the Odoo
  source was read from this repository. Everything about GCP service limits,
  quotas, tier defaults and pricing is *not* verified here and must be checked
  against current documentation and this project's actual quota.
- **Whether OCA prior art fits.** `storage_backend` / attachment-object-storage
  and the Camptocamp `session_redis` module solve exactly these two problems and
  should be evaluated in Stage 1 before writing new code. Their current state
  and Odoo 19 support were not checked. If one fits, the §2 findings become the
  review checklist for it rather than a specification — every one of them is a
  question to ask of any candidate module.
- **Current row counts and filestore size.** 119 MB / 759 MB come from a comment
  in `storage.tf` written on 2026-09-09. Re-measure before Stage 2 sizes its
  batches.
