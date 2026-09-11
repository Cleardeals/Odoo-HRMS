# The migration, explained from first principles

A companion to `docs/cloud_native_migration_plan.md`. That document is the
*plan* — terse, gated, written to be executed and audited. This one is the
*teaching*: what the system actually is today, what we want it to become, and
why every decision in the plan is the decision it is.

It assumes you know Python and SQL and have used Docker. It assumes nothing
about Kubernetes, object storage, or Odoo's internals.

Read it with the source open. Every claim here names a file and a line so you
can check it rather than believe it. If something below is wrong, the file wins.

---

## Part 0 — The one idea

Everything in this migration follows from a single question:

> **When a program stops running, what does it forget?**

Whatever it forgets, it never had to share. Whatever it *remembers*, it wrote
down somewhere — and wherever it wrote it down is now a thing that other copies
of the program need to be able to read.

That "somewhere" is called **state**. And the entire migration is one sentence:

> **Move Odoo's state off the machine Odoo runs on, so that we can run many
> Odoos and none of them is special.**

That's it. GKE, Cloud SQL, GCS and Redis are just the four places the state
goes. If you keep that sentence in your head, every decision in the plan stops
being arbitrary.

### Why "none of them is special" is the goal

Right now there is exactly one machine, `odoo-hrms-prod`. It is special. It is
special in a way that is easy to miss because everything works:

- If it dies, HR is down until someone rebuilds it.
- You cannot run a second one, because the second one would have a *different*
  database, *different* uploaded documents, and *different* logged-in users.
- You cannot restart it during working hours, because the restart is visible to
  every user.
- You cannot test a change on an identical copy, because there is no such thing
  as an identical copy.

Each of those is the same problem wearing a different hat: the machine holds
state that only it has.

### Odoo keeps state in exactly four places

This is the most useful fact in the whole document. Odoo is a big program but it
only writes to four kinds of place, and each one becomes one leg of the
migration.

| # | What | Where it lives today | Where it's going |
| --- | --- | --- | --- |
| 1 | **Relational data** — employees, leaves, payslips, every record | Postgres, in a container on the VM | **Cloud SQL** |
| 2 | **Files** — uploaded documents, generated PDFs, compiled CSS/JS | `/var/lib/odoo/filestore/` on the VM's disk | **GCS** |
| 3 | **Sessions** — who is currently logged in | `/var/lib/odoo/sessions/` on the VM's disk | **Redis** |
| 4 | **Scratch** — temp files while rendering a PDF, addon caches | the VM's disk | **stays local, and that's fine** |

Number 4 is the one people forget, and it's why "stateless" is a slightly
misleading word. A stateless pod still writes to disk. It just doesn't write
anything it would *miss*. More on this in Part 4.6.

---

## Part 1 — What we have today, traced end to end

Let's follow one HTTP request from a browser to a rendered page. Not
abstractly — through the actual components in this repository.

### 1.1 The physical picture

```
   browser
      │  https://hr.cleardeals.xyz/odoo/employees
      ▼
   DNS  ──────────────►  a static external IP
                         (google_compute_address.prod, compute.tf:26)
      ▼
   GCP firewall  ───────  default-allow-http / default-allow-https reach this VM
                          because it carries the tags ["http-server","https-server"]
                          (compute.tf, the `tags` block)
      ▼
 ┌──────────────────── odoo-hrms-prod (one e2-medium VM) ─────────────────────┐
 │                                                                            │
 │   Docker network "web"                                                     │
 │                                                                            │
 │   ┌──────────┐        ┌──────────────────┐        ┌──────────────────┐    │
 │   │ traefik  │───────►│  odoo-app        │───────►│  odoo-db         │    │
 │   │ :80 :443 │        │  :8069  :8072    │        │  postgres:17     │    │
 │   └──────────┘        └──────────────────┘        └──────────────────┘    │
 │        │                      │                            │              │
 │   ./letsencrypt        ./odoo-web-data            ./odoo-db-data          │
 │   (the TLS cert)       (filestore + sessions)      (the whole database)   │
 │                                                                            │
 │   All three of those are directories on ONE 30 GB disk.                    │
 └────────────────────────────────────────────────────────────────────────────┘
```

Notice the bottom row. **All the state is on one disk.** That single fact is
what makes the machine special, and undoing it is the migration.

### 1.2 Traefik: what it is and why it's there

Traefik is a **reverse proxy**. A reverse proxy is a receptionist: everything
from the outside world talks to it, and it decides which internal service should
actually answer.

It's doing four jobs here:

1. **TLS termination.** The browser speaks HTTPS to Traefik. Traefik speaks
   plain HTTP to Odoo. Odoo never sees a certificate.
2. **Getting the certificate.** `--certificatesresolvers.myresolver.acme.tlschallenge=true`
   means Traefik talks to Let's Encrypt and proves it controls
   `hr.cleardeals.xyz` — which is why the HTTP firewall rule has to stay open
   even though everything redirects to HTTPS. Take port 80 away and renewal
   breaks silently, 60 days later.
3. **Routing.** It reads Docker labels off the containers themselves. Look at
   `docker-compose.yml`:

   ```
   traefik.http.routers.odoo.rule=Host(`hr.cleardeals.xyz`)
   traefik.http.routers.odoo-chat.rule=Host(`hr.cleardeals.xyz`) && (PathPrefix(`/websocket`) || PathPrefix(`/longpolling`))
   ```

   Two routers, and the second one is not optional — Part 1.4 explains why.
4. **Security headers.** HSTS, nosniff, `X-Frame-Options: SAMEORIGIN`.

**The thing worth learning from Traefik here** is a failure that already
happened, because it teaches you what a health check is actually for.

On 2026-02-16, Docker Engine was upgraded to 29.2.1. That raised the minimum
Docker API version above the 1.24 that Traefik's client spoke. Traefik's
"docker provider" — the bit that reads labels off containers — died. Traefik
itself kept running perfectly and answered every request with **404**, because
its routing table was empty. Odoo behind it was completely healthy.

The site was down for ~2.5 hours. Every check that asked "is Odoo healthy?"
said yes.

Two things came out of that:

- Docker is pinned at 28.5.2 with `apt-mark hold`, and **that hold exists only
  on the VM** — not in this repo, not in Terraform. It is invisible state. Do
  not run `apt upgrade` on that host.
- `scripts/deploy.sh` grew an **edge gate**: after Odoo says it's healthy, the
  deploy makes a real HTTPS request to `hr.cleardeals.xyz` from outside the
  container and refuses to report success unless it gets a 200.

That's the general lesson: **a component can be healthy and useless at the same
time.** Ask the question the user asks, from where the user asks it.

### 1.3 Odoo's process tree, which is stranger than you'd guess

`odoo.prod.conf` sets `workers = 3`. That doesn't mean threads. Odoo in
production runs a **prefork** model: a master process that forks children, each
child a separate OS process with its own memory and its own database
connections.

Per `odoo/service/server.py` (`PreforkServer.process_spawn`, line 975), the
tree is:

```
master (forks, supervises, reaps; serves nothing)
├── WorkerHTTP   ×3     ← workers = 3            serving :8069
├── WorkerCron   ×1     ← max_cron_threads = 1   serving nothing
└── gevent       ×1     ← always exactly one     serving :8072
```

Five processes hold database connections — the master holds none. Remember that
number; Part 6.1 does arithmetic with it.

Here it is on the live box, so you can match each row to the diagram
(`sudo docker exec odoo-app ps auxf`, 2026-09-10):

```
  PID  VSZ(KB)  RSS(KB)  STAT  COMMAND
    1   386236   187124  Ss    python3 /usr/bin/odoo                 ← master
   19   477508   197860  Sl    python3 /usr/bin/odoo                 ← WorkerHTTP
   21   475596   220284  Sl    python3 /usr/bin/odoo                 ← WorkerHTTP
   23   473412   204432  Sl    python3 /usr/bin/odoo                 ← WorkerHTTP
   24   472364   200524  Sl    ... /usr/bin/odoo gevent              ← the bus
   26   455884   171692  SNl   python3 /usr/bin/odoo                 ← WorkerCron
```

Two tells let you identify them without guessing:

- **PID 24 says `gevent` in its command line.** That is not decoration — it is
  the switch. `odoo/_monkeypatches/site.py:29` sets `odoo.evented = True` only
  when `sys.argv[1] == 'gevent'`, and the master spawns it that way at
  `odoo/service/server.py:898`. Part 3.2 uses this.
- **PID 26 has an `N` in its STAT column**, meaning niced. `WorkerCron.start()`
  calls `os.nice(10)` (`odoo/service/server.py:1432`) so that background jobs
  lose CPU races against user requests. That `N` is how you spot the cron worker
  in a list of otherwise identical `python3` processes.

And there's a number in there worth stopping on, because it changes what Stage 1
has to do. `odoo.prod.conf` sets:

```
limit_memory_soft = 536870912   =  524,288 KB  (512 MiB)
```

These are **virtual** memory limits (`RLIMIT_AS`), so compare against VSZ, not
RSS. The busiest worker is at 477,508 KB — **91% of the soft limit**, with about
**46 MiB** spare.

Why that matters: Stage 1 adds `google-cloud-storage` and `redis` to
`requirements.txt`, and every import maps code into **each** worker. Crossing
the soft limit doesn't crash and doesn't log an error — Odoo finishes the current
request and recycles the worker. What you see is latency and cold caches, and you
will naturally blame the new GCS code rather than the ceiling it just touched.

`odoo.prod.conf` deliberately left these limits alone and said why: *"Revisit
once Phase 6 makes real memory metrics exist — which is the first time there will
be data to decide on."* Phase 6 is done. This is that data. Plan §2.15 turns it
into a Stage 1 gate.

Why prefork rather than threads? Python's GIL means threads don't give you
parallel CPU. Separate processes do. The cost is that they share nothing — no
shared cache, no shared connection pool, and (this is the important one) **no
shared memory for sessions or files.** Which is why those had to go to disk even
on a single machine.

### 1.4 The gevent process, and why `/websocket` is load-bearing

That fifth process is the odd one. `gevent` is a cooperative-concurrency library
— instead of one thread per connection, one process juggles thousands of
connections by switching whenever one of them waits on I/O.

You need that for **long-lived connections**. Odoo's chat, activity counters and
"someone else just changed this record" notifications all use a WebSocket that
stays open for as long as the tab is open. If a WebSocket occupied one of the 3
HTTP workers, three open browser tabs would consume your entire web capacity.

So: with `workers > 0`, Odoo serves the bus from a *separate process on a
separate port* (8072). And that's why `docker-compose.yml` needs the second
router. Get it wrong and:

- Nothing errors, and Odoo logs nothing — the request never reaches it.
- **Traefik's access log does show it**: `accesslog=true` is set, so you get a
  404 per `/websocket` attempt. It is the one place the fault is visible, and
  nobody reads a proxy access log unless they already suspect the proxy.
- The browser console shows a failed WebSocket handshake.
- Every realtime update in the UI just... stops.

So not literally invisible — just filed somewhere nobody looks, under a status
code that reads like a missing favicon.

Under the hood, how does one Odoo process tell another that something happened?
Postgres. `addons/bus/models/bus.py:163` calls **`pg_notify`**, and the gevent
process runs **`LISTEN imbus`** (`:242`). Postgres is the message bus — there is
no RabbitMQ, no Kafka, nothing else to run.

One wrinkle worth registering now, because it matters at Stage 4 and is
invisible everywhere else: both sides connect with `db_connect("postgres")` —
the **`postgres` maintenance database**, not `odoo_hrms_db`. The channel is
deliberately server-wide, so one Odoo hosting many databases shares one channel
and filters by payload. Which means the `odoo` role needs `CONNECT` on a
database nothing else in the application ever touches.

Hold onto all of that. It's Part 6.2, and it's the trap most likely to bite you
a year from now.

### 1.5 Where the files actually go, and the clever thing Odoo does

When you attach a payslip PDF to an employee, Odoo creates a row in
`ir_attachment`. The bytes do **not** go in that row (usually). They go to disk,
and the row records where.

Here's the clever part. Odoo doesn't name the file after the document. It names
it after **the SHA-1 of the contents** (`_compute_checksum`,
`ir_attachment.py:324`):

```python
return hashlib.sha1(bin_data or b'').hexdigest()
```

and then (`_get_path`, line 132):

```python
fname = sha[:2] + '/' + sha       # scatter across 256 dirs
```

So a file becomes:

```
/var/lib/odoo/filestore/odoo_hrms_db/a9/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3
```

The `a9/` prefix exists because directories with a hundred thousand entries are
slow; 256 subdirectories keeps each one small.

This is **content-addressed storage**, and it has one consequence that matters
enormously later:

> **If ten employees have the identical company policy PDF attached, there is
> ONE file on disk and TEN rows in `ir_attachment` pointing at it.**

Think of a library that shelves books by a fingerprint of their text rather than
by title. Two copies of the same book are one physical book with two catalogue
cards. Deduplication for free.

**And this is not a thought experiment — it's your data.** Measured on
production, 2026-09-10:

```
attachment rows with a blob : 5,489
distinct blobs              : 4,359
                              ------
shared references           : 1,130   (21% of all attachments)

logical bytes (sum file_size) : 1,107 MB
actual bytes on disk          :   769 MB   → dedup is saving ~30%
```

And grouped by how many attachments share each blob:

| attachments per blob | blobs |
| --- | --- |
| **21** | 2 |
| 11 | 2 |
| **10** | 61 |
| 5 | 25 |
| 4 | 15 |
| 3 | 50 |

I picked "ten employees" as an illustration before measuring. There are
literally sixty-one blobs shared by exactly ten attachments, and two shared by
twenty-one.

So now: **deleting a catalogue card must not burn the book.** On those
twenty-one-reference blobs, twenty other cards still point at it.

Odoo solves this with a two-step dance. Look at `_file_delete`
(`ir_attachment.py:173`):

```python
def _file_delete(self, fname):
    # simply add fname to checklist, it will be garbage-collected later
    self._mark_for_gc(fname)
```

It **deletes nothing**. It writes an empty file into a `checklist/` directory —
a note saying "this blob might be garbage now, check later."

Later, a background job (`_gc_file_store_unsafe`, line 222) does the checking,
and this is the whole algorithm:

```python
# 1. read every note in the checklist
for dirpath, _, filenames in os.walk(self._full_path('checklist')):
    ...

# 2. ask the database which of those are still referenced
self.env.cr.execute(
    "SELECT store_fname FROM ir_attachment WHERE store_fname IN %s", [names])
whitelist = set(row[0] for row in self.env.cr.fetchall())

# 3. delete the ones nobody points at; clear the note either way
for fname in names:
    if fname not in whitelist:
        os.unlink(self._full_path(fname))
    os.unlink(checklist[fname])
```

That's it. Collect candidates, ask the database, delete the unreferenced ones.
It runs under `LOCK ir_attachment IN SHARE MODE` (line 212) so nobody can create
a new reference to a blob while it's being judged.

Understand these fifteen lines and you understand exactly what Part 5.1 has to
rebuild for GCS — and exactly why "just delete the object on unlink" is wrong.

### 1.5b Watching the garbage collector work

Here is the nicest thing in this whole document, because it turns the algorithm
above from a story into arithmetic you can check.

Reading the code gives a prediction. If `_file_delete` only ever *writes a note*,
and the GC deletes only unreferenced blobs, then at any moment:

> every orphaned file on disk should have a pending note in `checklist/`, and the
> notes should split cleanly into "still referenced" (which GC will spare) and
> "unreferenced" (which GC will delete).

Measured on production, 2026-09-10:

```
referenced by an attachment, ABSENT from disk :  0
on disk, referenced by NOTHING (orphans)      :  9
pending notes in checklist/                   : 18
  ├─ note's blob still referenced             :  9   → GC will keep
  └─ note's blob unreferenced                 :  9   → GC will delete
orphans with NO pending note                  :  0
```

**18 = 9 + 9, and the orphan set is entirely inside the note set.** The
prediction held to the number. `ir_cron` id 1, *"Base: Auto-vacuum internal
data"*, is active on a daily schedule and last ran 21 hours earlier — so those
18 notes are simply one day's churn awaiting the next sweep.

Two things worth taking from that:

- **The mechanism is real and healthy.** You are not reading aspirational code;
  it is running, and its bookkeeping balances.
- **Zero missing blobs is the number that matters for Stage 2.** Every
  attachment that claims a file has one. So when the migration runs, a
  `FileNotFoundError` would mean the *new* code is wrong — not that it inherited
  pre-existing damage. Starting from a provably consistent base is what makes
  the migration's own failures interpretable.

That second point is a general habit worth stealing: before you migrate
something, measure whether it is internally consistent. Otherwise the first bug
you hit will be someone else's, and you will spend a day owning it.

You can re-run all of it yourself; the queries are in §1.10.

### 1.6 Where sessions go, and what a session actually is

HTTP has no memory. Every request arrives as a stranger. So how does the server
know you're logged in?

**The cloakroom.** You hand over your coat, they hand you a numbered ticket. The
ticket is meaningless — it's just a number. Your coat is in the cloakroom. Every
time you come back you show the ticket and they fetch your coat.

The ticket is the **cookie**. The coat is the **session** — a small dictionary
holding `{uid: 7, login: ..., context: {...}}`. The cloakroom is
`/var/lib/odoo/sessions/`.

The ticket number is called the **sid**, and it is 84 characters. Why 84?
`generate_key` (`odoo/http.py:1027`) takes a SHA-512 (64 bytes), drops the last
byte to avoid base64 padding (63 bytes), and base64-encodes it — which gives
exactly 84 characters. It's validated by
`^[A-Za-z0-9_-]{84}$` (line 941).

Now the part that trips everyone up. **The sid is two halves.**

```
STORED_SESSION_BYTES = 42          (odoo/http.py:321)

┌─────────────── 42 chars ───────────────┬─────────────── 42 chars ───────────────┐
│  the DEVICE identifier                 │  the SECRET                            │
│  stored in the database (res.device)   │  never stored; proves it's really you  │
└────────────────────────────────────────┴────────────────────────────────────────┘
```

The first half says *which* cloakroom ticket family this is — it's how the
"My Devices / log out everywhere" feature knows you have a session on your phone
and one on your laptop. The second half is the secret.

**Rotation** is why the split exists. Periodically Odoo issues you a fresh
ticket, so that a ticket stolen last month is worthless. Look at `rotate`
(`odoo/http.py:985`):

- **Soft rotation** keeps the first 42 characters and generates a new second 42.
  You're still the same *device*, with a new secret. Your CSRF token survives.
- **Hard rotation** (logout) replaces all 84.

Soft rotation has a genuinely hard problem: your browser has six requests in
flight when rotation happens. If each one rotates independently you get six
sessions and five of them are orphans. Odoo's fix is to write the new sid *into
the old session* as `next_sid`, so a concurrent request finds it and follows
along rather than minting its own. There's a 120-second grace window
(`SESSION_DELETION_TIMER`, line 317) before the old one is reaped.

If you get that read-back wrong when you write the Redis store, users get logged
out at random under load — and everyone will blame Redis.

### 1.7 The disk, laid out

Now you can read the disk and know what everything is:

```
/opt/odoo-hrms/                        ← the checkout (moved here in Phase 4c)
├── docker-compose.yml
├── odoo.prod.conf                     ← template, no secrets
├── .env                               ← ODOO_IMAGE=...:<sha>  (written by deploy.sh)
├── letsencrypt/acme.json              ← THE ONLY COPY of the TLS cert state
├── odoo-db-data/                      ← the ENTIRE database (119 MB)
└── odoo-web-data/                     ← mounted at /var/lib/odoo in the container
    ├── filestore/odoo_hrms_db/        ← 759 MB of HR documents
    │   ├── a9/a94a8f...
    │   └── checklist/                 ← the GC notes from §1.5
    ├── sessions/                      ← the cloakroom from §1.6
    └── addons/                        ← Odoo's own scratch cache

/dev/shm/odoo.conf                     ← the RENDERED config, in RAM, never on disk
```

That last line is worth a moment. `scripts/render_odoo_conf.sh` takes the
committed `odoo.prod.conf`, pulls two secrets from Secret Manager, substitutes
them, and writes the result to `/dev/shm` — which is tmpfs, i.e. RAM.

Why? Because the disk gets snapshotted every 4 hours and those snapshots are
kept 30 days. A config file containing a live database password, on disk, is a
config file containing a live database password in 180 backups. In RAM, it
exists only while the machine is running.

### 1.8 How a deploy works today

Worth understanding, because the migration rides this pipeline and mustn't break
it.

```
you merge a PR to main
      ▼
Cloud Build trigger fires  (infrastructure/terraform/cloudbuild.tf)
      ▼
build the image, run gates: config-check, image-contents, shell-syntax,
                            api-docs, test-db, test       (cloudbuild.yaml)
      ▼
push to Artifact Registry, tagged with the commit SHA — never :latest
      ▼
◆ WAIT FOR A HUMAN TO APPROVE ◆
      ▼
SSH to the VM over an IAP tunnel, under OS Login, as hrms-cloudbuild@
      ▼
sudo bash scripts/deploy.sh <sha>
```

And `deploy.sh` is worth reading in full at some point, because almost every
line is a scar. The shape:

1. `flock` — one deploy at a time.
2. Record what's *actually running* (`docker inspect`) as the rollback target —
   deliberately not `.env`, because `.env` records an intention, not a reality.
3. `git fetch --depth 1` and assert `HEAD == <sha>`. Refuse if the branch moved
   mid-build: the image was tested, the tree must match it.
4. Render the config from Secret Manager.
5. `docker pull` the exact image by name.
6. Optionally run a module upgrade **on the new image while the old container is
   still serving** — so if the migration fails, the image is never swapped and
   the old code keeps running against the schema it was built for.
7. `docker compose up -d odoo`.
8. **Health gate** — `/web/health?db_server_status=1`, which opens a real cursor.
   The bare `/web/health` returns 200 with Postgres down; the query parameter is
   what makes it a gate.
9. **Edge gate** — real HTTPS to the public hostname (§1.2).
10. On health failure: roll back to the previous image. On *edge* failure:
    deliberately **do not** roll back, because Odoo is provably fine and
    re-pinning an old image while someone diagnoses a proxy fault is just a
    second unplanned change.
11. Prune images by **count, not age** — keeping 3. An age filter would delete
    the rollback target, because the previous image is exactly as old as
    whenever it was built.

### 1.9 What's already protecting you

Don't lose these in the migration. They were expensive:

- 4-hourly disk snapshots, 30-day retention, `KEEP_AUTO_SNAPSHOTS` so they
  outlive the disk.
- Five alert policies with delivery actually proven (an unverified notification
  channel looks healthy and pages nobody).
- SSH only through an IAP tunnel; no SSH port open to the internet.
- OS Login, which replaced **five** unexpiring project-metadata SSH keys that
  were each passwordless root on production, on unknown laptops.
- Secrets in Secret Manager, rendered to tmpfs.
- Traefik's admin API bound to `127.0.0.1` instead of `0.0.0.0`.
- Image tags that mean something, so rollback is real.

### 1.10 Go and look yourself

Don't take my word for any of it.

**First, `cd`.** `docker compose` reads `docker-compose.yml` from the *current
directory*, and your shell starts in your home directory. Every `docker compose`
command below fails with `no configuration file provided: not found` unless you
move to the app directory first — which Phase 4c moved to `/opt/odoo-hrms`:

```bash
cd /opt/odoo-hrms
```

`scripts/deploy.sh` still carries a fallback to the old `/home/tech/odoo-project`
until the move is fully settled, so if `/opt/odoo-hrms` is ever absent, look
there.

**Second, `.env` is root-only, so Compose needs `sudo` even to read.** After the
`cd` you will hit:

```
open /opt/odoo-hrms/.env: permission denied
```

`scripts/deploy.sh` writes `.env` through `mktemp` + `chmod 600` while running as
root under sudo, so it ends up `root:root` mode 600. The Compose *client* reads
that file on your behalf — it has to, in order to resolve
`image: ${ODOO_IMAGE:-odoo-hrms:latest}` — before it ever contacts the daemon. So
this is a plain file-read error, not a Docker permission problem, and belonging
to the `docker` group does not help.

Worth sitting with for a second, because it is a real operational defect rather
than a quirk. `.env` holds exactly one line —
`ODOO_IMAGE=<registry>/hrms/odoo-hrms:<sha>` — which is **not a secret**. The 600
is a reasonable precaution for a file that might one day hold one. But the effect
today is that **read-only diagnostics require root**: `docker compose logs`,
`docker compose ps` and `docker compose exec` all fail without it. That is a bad
property at 3am, when the thing you want is to look without changing anything.

**Third, no human is in the `docker` group, so everything needs `sudo` anyway.**
Skip Compose and you hit the next boundary:

```
permission denied while trying to connect to the Docker daemon socket
at unix:///var/run/docker.sock
```

**This is correct, and must not be "fixed".** Membership of the `docker` group is
equivalent to root: anyone in it can `docker run -v /:/host` and read or rewrite
the entire filesystem, with no sudo and no audit trail. The group is deliberately
empty of humans, and root via `sudo` — which OS Login grants through
`roles/compute.osAdminLogin` and which is logged — is the intended path. It
matches the pipeline: Cloud Build SSHes in and runs `sudo bash
scripts/deploy.sh`, never bare `docker`.

So the working commands all take `sudo`, and the useful choice is *which* tool:

```bash
sudo docker exec odoo-app ps auxf          # no working directory, no .env
sudo docker compose exec odoo ps auxf      # needs the cd, and reads .env
```

Prefer the first in runbooks and scripts. `docker-compose.yml` pins
`container_name:` on all three services (`traefik`, `odoo-db`, `odoo-app`), so
`docker exec` and `docker logs` by name survive both a directory move (Phase 4c
already did one) and a file mode a later deploy might tighten.

**The lesson is bigger than the commands.** Those three failures are three
*separate* permission boundaries — a working directory, a file mode, a group
membership — stacked so that each one hides the next. Fix the first and you
learn about the second; fix the second and you learn about the third. At no point
does an error message mention the boundary behind it.

That is the same shape as the OS Login lockout in Part 7, where five independent
checks all report success because the missing permission sits on a different
resource. It is why every stage in the plan states a **gate** that has to be
demonstrated rather than argued: in access control, "there is no reason this
would fail" is not evidence.

This whole class of friction disappears on GKE: `kubectl logs` has no working
directory to be wrong about, no dotfile to be unable to read, and its permission
model is one RBAC check that says which resource it denied you.

```bash
# the process tree — you should see master + 3 http + 1 cron + 1 gevent
docker exec odoo-app ps auxf

# where the files really are, and the content-addressed names
docker exec odoo-app ls /var/lib/odoo/filestore/odoo_hrms_db | head

# the cloakroom
docker exec odoo-app ls /var/lib/odoo/sessions | head

# how many routers Traefik knows about — a healthy HRMS stack reports 5,
# and ZERO is the signature of the February outage
curl -s http://127.0.0.1:8080/api/rawdata | python3 -c \
  'import json,sys; print(len(json.load(sys.stdin)["routers"]))'

# prove the deduplication of §1.5 — rows vs. distinct blobs.
# If `blobs` is lower than `rows`, the gap IS the content-addressed dedup,
# and it is exactly the number of attachments that would break if a naive
# _file_delete removed a blob on unlink (§4.1).
docker exec odoo-db psql -U odoo -d odoo_hrms_db -c \
  'SELECT count(*) AS rows,
          count(DISTINCT store_fname) AS blobs
     FROM ir_attachment
    WHERE store_fname IS NOT NULL;'

# and the same number from the other side: how many files are actually on disk
docker exec odoo-app find /var/lib/odoo/filestore/odoo_hrms_db \
  -type f -not -path '*/checklist/*' | wc -l
```

Those last two are worth running **before** Stage 2, not just for interest. The
`blobs` count is the number of objects the migration has to create in GCS, and
the disk count should match it. If it does not, something in the filestore is
already inconsistent and Stage 2 would carry that forward.

---

## Part 2 — Why change it? The honest case

The blueprint gives four reasons (§2). Let me grade them **for HRMS
specifically**, because two are strong and two are weaker than they sound, and
knowing which is which stops you from over-engineering.

### "Single point of failure" — STRONG, and the real reason

Postgres is a container on one VM in one zone. If the disk corrupts, if the zone
has an incident, if someone fills the disk, HR is down until a human rebuilds
from a snapshot. And those snapshots are **crash-consistent** — they capture the
disk as if the power were cut. Postgres recovers from that, but a snapshot
cannot give you "the database as it was at 14:19, just before that bad import,"
and it can only be restored *into a disk*.

Cloud SQL gives you a standby in another zone with automatic failover, and
**point-in-time recovery** — replay the write-ahead log to any second you name.

`infrastructure/terraform/storage.tf` already makes this argument against
itself, and it's worth quoting the reasoning: the backups bucket exists, it is
**empty**, and the comment says so plainly. Recovery today rests entirely on
crash-consistent disk snapshots. For 759 MB of payroll and personnel documents —
records whose loss is least recoverable by re-entering them — that is the
weakest part of the current system.

**This is the reason to do the migration.** Everything else is a bonus.

### "Stateful VM lock-in prevents auto-scaling" — REAL, but not about scale

True, and it's the mechanism of the whole plan. But be honest about why it
matters *here*: HRMS is 119 MB with three workers and, per `odoo.prod.conf`,
**zero** "virtual memory limit reached" entries in 30 days of logs. Nobody is
waiting on this system.

The value isn't handling load. It's the four things statelessness gives you that
have nothing to do with traffic:

1. **Zero-downtime deploys.** Start new pods, drain old ones. Today a deploy is
   a visible restart.
2. **Self-healing.** A pod that dies is replaced automatically. A VM that dies
   waits for a human.
3. **A real staging environment.** Once nothing is special about a running copy,
   you can make another one.
4. **Deploys stop being scary**, which changes how often you're willing to ship.

Frame it as *operability*, not performance. If you frame it as performance,
someone will correctly point out that nothing is slow, and they'll be right.

### "Tightly coupled functional domains" — STRONG, but a different project

Combining deal management and invoice generation in one Odoo means one
deployment risks both, one migration blocks both, and every module upgrade is
negotiated between two teams. Splitting them is right.

But notice: **this is not an infrastructure problem.** You could split the
domains onto two VMs tomorrow with no Kubernetes at all. And you can't fix it by
migrating either, because Sales and Invoicing *don't exist yet* — they're new
applications, one of which replaces ROLO and integrates Razorpay.

That's exactly why the plan pulls them out into Stage 8. Bundling "build two new
products" with "migrate the platform" gives you one project that can't ship
until both halves are done.

### "Operational overhead" — PARTLY ALREADY SOLVED

The blueprint says manual backups and server patches eat engineering time. Half
of that is already fixed: snapshots are automated, alerts fire, deploys are a
pipeline with an approval gate.

What's genuinely still manual: Postgres version upgrades, OS patching (made
worse by that `apt-mark hold`), and certificate renewal depending on a single
`acme.json` and a personal mailbox for failure notices.

Managed services do remove those. It's a real benefit — just a smaller one than
it was six months ago, because the previous migration already collected the
cheap wins.

### And the thing the blueprint doesn't say

**It will cost several times more.** One `e2-medium` with a co-located Postgres
becomes a GKE cluster plus a regional-HA Cloud SQL instance plus a Memorystore
instance — and the blueprint applies that four times over.

That's not an argument against doing it. High availability genuinely costs money;
a standby database in another zone is a second database. But it *is* an argument
for pricing Stages 4 and 5 **before** starting Stage 2, because a programme that
runs out of budget halfway leaves the estate half-migrated, which is worse than
either end.

---

## Part 3 — The desired state, one component at a time

### 3.1 Kubernetes, in the only terms you need

Kubernetes has a reputation for complexity. For this migration you need five
nouns.

**A container** you know: a process plus its filesystem, isolated.

**A Pod** is one or more containers that share a network address and are always
scheduled together. Almost always one real container plus sidecars. A pod is
**mortal by design** — it gets killed and replaced, and it does not have a
stable identity. That mortality is the whole point, and it's why state has to
live elsewhere.

**A Deployment** is a statement of desire: *"I want 4 pods that look like
this."* You don't create pods; you tell the Deployment a number and it makes
reality match. Change the image and it replaces them a few at a time — new one
up and healthy, old one drained, repeat. That's your zero-downtime deploy, and
it's a property of the Deployment, not something you build.

**A Service** is a stable name and IP in front of a set of mortal pods. Pods
come and go; the Service name doesn't. Analogy: a department's phone extension
versus the individual people who answer it.

**An Ingress** is Traefik's replacement — the thing that owns the public IP,
terminates TLS, and routes by hostname and path to Services.

And one more:

**An HPA** (Horizontal Pod Autoscaler) watches a metric and changes the
Deployment's replica count. "If average CPU is over 60%, add a pod, up to 10."

That's the whole vocabulary.

### 3.2 Why three Deployments, not one

The obvious design is one Deployment where each pod runs the full prefork tree
from §1.3. It works. It's also wrong, and it's worth understanding why, because
it's the single most instructive design decision in the plan.

Recall the tree: 3 HTTP workers, 1 cron worker, 1 gevent process. Those three
things have completely different scaling shapes:

| | scales with | wants |
| --- | --- | --- |
| **HTTP** | requests per second | many replicas, short-lived, killable |
| **WebSocket** | *concurrent open tabs* | few replicas, long-lived connections |
| **Cron** | nothing at all | exactly one or two, ever |

Put them in one pod and the HPA — which is watching HTTP CPU — scales all three
together. Scale to 10 pods for a busy morning and you now have 10 cron workers
politely fighting over the same job queue, and you've severed 10 pods' worth of
WebSockets every time it scales *down*, because killing a pod kills its open
connections.

So: three Deployments.

```
Deployment "web"    workers=N, max_cron_threads=0     :8069   HPA'd
Deployment "bus"    evented (gevent)                  :8072   1–2, rarely changed
Deployment "cron"   workers=0, max_cron_threads=N     no port  replicas: 1
```

And the Ingress routes `/websocket` and `/longpolling` to `bus`, everything else
to `web` — **exactly the split the Traefik labels already encode.** You're not
inventing a topology. You're taking the one that already exists inside one
container and giving each part its own scaling knob.

On cron, one nice surprise. You might fear two cron pods running the same job
twice. They won't. `odoo/addons/base/models/ir_cron.py:365` claims jobs with:

```sql
FOR NO KEY UPDATE SKIP LOCKED
```

which is Postgres for "give me a row nobody else has locked, and don't wait."
Two pods asking simultaneously get *different* jobs. So the separation is about
resource waste, not correctness — good to know, because it means a mistake here
is expensive rather than dangerous.

**How do you start just the bus?** This was an open question when the plan was
written — `odoo/cli/` has no `gevent` subcommand, so there appeared to be no
supported way to run `GeventServer` alone. It was answered by looking at the
running system rather than at the code. `ps` on the live VM shows the master
spawning:

```
/opt/odoo-venv/bin/python3 /usr/bin/odoo gevent
```

There *is* a switch. It just isn't a CLI subcommand — it's the first positional
argument, checked at `odoo/_monkeypatches/site.py:29`:

```python
if odoo.evented or not (len(sys.argv) > 1 and sys.argv[1] == 'gevent'):
    return
sys.argv.remove('gevent')
...
odoo.evented = True
```

Read that condition carefully, because the trap is in it. **`gevent` must be
`argv[1]`** — position, not presence. So:

```yaml
command: ["odoo", "gevent", "-c", "/etc/odoo/odoo.conf"]   # ✅ bus
command: ["odoo", "-c", "/etc/odoo/odoo.conf", "gevent"]   # ❌ silently a web server
```

The second one starts a perfectly healthy **prefork** server that serves no
websockets. The pod goes ready, the Service gets endpoints, the Ingress routes
`/websocket` to it, and every realtime update in the UI dies — with nothing in
any log. It is the §1.4 failure mode all over again, one YAML list away.

(The first form works through `entrypoint.sh`, which rewrites `odoo ...` to
`python3 /usr/bin/odoo ...` and preserves argument order, keeping `gevent` in
position 1.)

Two config options exist specifically for this Deployment, and you should use
them: `limit_memory_soft_gevent` and `limit_memory_hard_gevent`
(`odoo/tools/config.py:467,477`). A process juggling thousands of idle
connections has a different memory shape from one rendering a payslip, and these
let you say so instead of sharing one ceiling. Both fall back to the ordinary
limits when unset.

**The general lesson is the better souvenir.** The source did not make the
positional requirement obvious; `ps` did. When you want to know how a system is
*actually* invoked, read the running process table, not just the code that might
invoke it.

### 3.3 Cloud SQL, and what "managed" buys

Same Postgres. Somebody else runs it. Concretely:

- **Regional HA** — a synchronous standby in a second zone, automatic failover.
  The application reconnects; it doesn't participate.
- **PITR** — continuous WAL archiving, so you can restore to any second in the
  retention window. This is the capability the current setup completely lacks
  (§2).
- **Automated backups and patches** in a window you choose.
- **Vertical scaling** by changing a number.

**How the pods reach it**, and this is the part worth understanding: not over the
public internet. You run the **Cloud SQL Auth Proxy** as a sidecar — a second
container in the same pod. Odoo connects to `127.0.0.1:5432` as if Postgres were
local; the proxy holds an encrypted authenticated tunnel to the instance.

Two things fall out:

1. **`db_host` barely changes.** It's `db` today and `127.0.0.1` tomorrow. Odoo
   doesn't know anything moved.
2. **No public database endpoint exists**, and no password sits in the
   connection path — the proxy authenticates with the pod's IAM identity.

And a crucial property: **the Auth Proxy is a TCP proxy.** It moves bytes. It
does not understand the Postgres protocol, so `LISTEN`/`NOTIFY` passes straight
through and the bus from §1.4 keeps working. Part 6.2 is about what happens if
you put something smarter in that position.

### 3.4 GCS, and the mental shift it demands

A filesystem gives you directories, renames, appends, partial writes, `stat`,
locks. **Object storage gives you almost none of that.** You `PUT` a whole
object under a key, you `GET` a whole object, you `DELETE` it, you `LIST` keys
by prefix. That's it.

The names *look* like paths — `filestore/odoo_hrms_db/a9/a94a8f...` — but the
slashes are just characters in a flat key. There are no directories.

Odoo's filestore turns out to be a beautiful fit, and you already know why:
content-addressed, write-once, read-many, never appended to, never renamed
(§1.5). It was practically designed for object storage. Which is why this
override is ~200 lines and not a rewrite.

What you lose is `os.stat` and `open()`. Which is exactly the finding in Part
5.1 — the download path uses both.

### 3.5 Memorystore / Redis, the shared cloakroom

Redis is an in-memory key-value store. Sessions are the textbook use: small,
short-lived, read on every request, and you genuinely don't mind losing them in
a catastrophe (everyone logs in again).

The mental model is unchanged from §1.6 — it's still a cloakroom. It's just that
now **every front desk shares one cloakroom** instead of each keeping its own.

Two features do real work for us:

- **TTL.** Set a key to expire in 604800 seconds (`SESSION_LIFETIME`,
  `odoo/http.py:308`) and Redis deletes it for you. That's the entire
  implementation of `vacuum()` — expiry becomes the storage engine's job instead
  of a cron walking a directory.
- **Sets**, which give us the device index in Part 5.2.

### 3.6 "Stateless" doesn't mean "no disk"

The word oversells it. After all four changes, a pod *still writes locally*:

- `config.addons_data_dir` = `$data_dir/addons` (`odoo/tools/config.py:989`),
  used by `odoo/modules/module.py:147`
- temp files while wkhtmltopdf renders a PDF
- Python bytecode caches

None of it needs to survive a restart. So the pod gets an **`emptyDir`** — a
scratch directory that lives and dies with the pod — mounted at `/var/lib/odoo`.
Not a PersistentVolumeClaim; the whole point is that it's disposable.

The precise definition to carry: **stateless means nothing *durable* on local
disk.** A pod with a read-only root filesystem and no writable data dir will not
boot.

---

## Part 4 — The two pieces of code we actually write

Everything so far is provisioning — clicking things into existence. This part is
the only genuinely novel engineering, and it's where the blueprint is wrong.

### 4.1 The filestore override

#### The upload path — the easy half

Trace what happens when someone attaches a PDF. Odoo's ORM does:

```
create({'raw': <bytes>})
   → _inverse_raw / _inverse_datas          (ir_attachment.py:276)
   → _set_attachment_data                   (line 279)
       → _get_datas_related_values          (line 306)
            computes checksum = sha1(bytes)  (line 324)
            → _file_write(bin_data, checksum)  ◀── OUR HOOK
       → super().write({'store_fname': fname, ...})
```

`_file_write` is a **three-line seam**. Give it bytes and a checksum, return the
key you stored them under. That's the whole contract:

```python
@api.model
def _file_write(self, bin_value, checksum):
    fname = checksum[:2] + '/' + checksum       # keep Odoo's own layout
    bucket.blob(prefix + fname).upload_from_string(bin_value)
    return fname
```

Note we keep the same `sha[:2]/sha` key shape. Nothing requires it — GCS has no
directories — but keeping it means `store_fname` values are identical whether a
blob is on disk or in GCS, which makes the migration reversible and makes SQL
you write against `ir_attachment` valid in both worlds. Free property; take it.

**This is the part the blueprint gets right.** §4.3 says to override
`write`/`create`/`unlink`/`read` — those are ORM methods, and overriding them
means reimplementing checksum, mimetype, `res_field` and index-content handling
that already works. The real seam is three `@api.model` methods, deliberately
narrow:

| method | line |
| --- | --- |
| `_file_read(fname, size=None)` | 147 |
| `_file_write(bin_value, checksum)` | 158 |
| `_file_delete(fname)` | 173 |

Plus `_storage()` (88) and `_get_storage_domain()` (96).

And here's a small gift. `_storage()` is:

```python
return self.env['ir.config_parameter'].sudo().get_param('ir_attachment.location', 'file')
```

The switch between local disk and GCS is **a row in a database table.** Settings
→ Technical → System Parameters. No deploy, no restart, and revertible in one UI
action. That's not an accident of Odoo's design; it's what makes Stage 2 safe
enough to do on a Tuesday.

#### The download path — where the blueprint breaks

Now, the reason this section exists.

You'd assume downloads call `_file_read`. **They don't.** Look at
`_to_http_stream` (`ir_attachment.py:896`):

```python
if self.store_fname:
    stream.type = 'path'
    stream.path = werkzeug.security.safe_join(
        os.path.abspath(config.filestore(request.db)),
        self.store_fname
    )
    stat = os.stat(stream.path)          # ◀── FileNotFoundError
    stream.last_modified = stat.st_mtime
    stream.size = stat.st_size
```

It builds a **local filesystem path** and calls `os.stat` on it. There is no
local file. The request raises.

So if you implement §4.3 exactly as written, you get a system where:

- uploading works — the object appears in GCS, correctly
- the attachment shows in the UI with the right name and size
- **every single download returns HTTP 500**

You would demo the upload, declare the PoC a success, and discover this in
production. That's why this is the first finding in the plan.

Why does Odoo build a path instead of reading bytes? Efficiency. If you have a
real file, the kernel can send it with `sendfile()` and the bytes never enter
Python. Look a little further and you'll see `config['x_sendfile']` handling —
it can even hand the path to nginx and let *that* serve it. It's a good
optimisation. It just assumes a local filesystem.

#### The fix, and the pleasant surprise

`Stream` supports a third type (`odoo/http.py:492`):

```python
type: str = ''  # 'data' or 'path' or 'url'
```

and `get_response()` (line 591):

```python
if self.type == 'url':
    if self.max_age is not None:
        res = request.redirect(self.url, code=302, local=False)
        res.headers['Cache-Control'] = f'max-age={self.max_age}'
        return res
    return request.redirect(self.url, code=301, local=False)
```

So we can return a **signed URL** and Odoo redirects the browser to it.

A signed URL is a plain HTTPS URL to a private GCS object with a cryptographic
signature and an expiry baked into the query string. GCS validates it. It's a
time-limited bearer token in URL form — like a hotel key card that only works
until Friday.

The consequence is lovely: **the bytes never pass through a pod.** The browser
talks to GCS directly. Serving a 40 MB scanned document costs your pod one
redirect. On 759 MB of documents behind an autoscaler, that's the difference
between memory pressure and none.

**Two traps.**

**(a) Always set `max_age`.** Read the branch again. Without `max_age`, Odoo
emits a **301 — Moved Permanently** — pointing at a URL that expires in an hour.
Browsers and intermediate caches are entitled to keep a 301 forever. So the user
gets a cached permanent redirect to a dead signed URL, and it is unfixable from
the server side. Set `max_age` well under the signature lifetime and you get a
302 with an explicit `Cache-Control`.

**(b) Signing needs a key, and Workload Identity doesn't give you one.**
Signing is a private-key operation. Workload Identity's whole selling point is
that there's no key file anywhere. So `generate_signed_url` can't sign locally;
it has to call the IAM **`signBlob`** API — which requires the pod's service
account to hold `roles/iam.serviceAccountTokenCreator` **on itself**. That
self-referential grant looks like a mistake in a code review, and without it
every download fails on the first try.

**(c) Scope the override precisely.** `ir.attachment` already has a
`type = 'url'` kind — an external *link*, not stored content, with its own
handling (`_is_remote_source`, 944). Only intervene when
`self.store_fname and self._storage() == 'gcs'`. Fire on everything and you'll
break link attachments and the `db_datas` path, neither of which involves GCS.

If policy forbids signed URLs, the fallback is `stream.type = 'data'` with bytes
fetched from GCS. Correct, but it loads each file fully into worker memory
against `limit_memory_hard = 640 MB`.

**I overstated this, and the data says so.** An earlier draft warned that "a
200 MB attachment kills the worker." True in principle; irrelevant here.
Measured:

```
largest attachment  6,551 kB      mean  206 kB
over 10 MB: 0        over 50 MB: 0
```

The biggest thing in the corpus is 6.4 MB. The fallback is **safe on today's
data**, and I should have checked before reaching for a scary number.

Signed URLs are still the better design — bytes never traverse a pod, no memory
churn, no cluster egress — so the recommendation doesn't change. But the honest
argument for them is *architectural*, not "otherwise it falls over." The memory
case becomes real only if large files start arriving, which is a reason to alert
on `max(file_size)` rather than to assume either way.

Worth noticing as a habit: a plausible mechanism plus an invented magnitude
reads exactly like a measured finding. The mechanism was right. The magnitude
was decoration.

#### The `KeyError` in the migration tool

`_get_storage_domain()` (line 96):

```python
return {
    'db':   [('store_fname', '!=', False)],
    'file': [('db_datas',    '!=', False)],
}[self._storage()]
```

Two keys. Set `ir_attachment.location = gcs` and this raises `KeyError: 'gcs'`.

The joke is that the caller is `force_storage()` (line 104) — the tool for
migrating the existing 769 MB. So the migration tool breaks *first*, before
anything user-facing does.

#### And the obvious fix is also wrong

An earlier draft of this said: *"Override `_get_storage_domain` and return the
same domain as `'file'`."* That sounds right. We're moving off files, so use the
file domain.

It is wrong, and it fails in the worst possible way — **silently, reporting
success.** Measured:

```sql
SELECT count(*) FROM ir_attachment WHERE db_datas IS NOT NULL;  -->  0
```

The `'file'` domain is `[('db_datas', '!=', False)]`, and **nothing** on this
system has `db_datas`. Every attachment is already on disk. So `force_storage()`
would search, match zero rows, migrate nothing, and return cleanly. You'd flip
the parameter, run the migration, see no error, and believe 769 MB had moved.

Read the dict once more and the actual semantics appear:

```python
'db':   [('store_fname', '!=', False)],   # target is the DB → find the ones in FILES
'file': [('db_datas',    '!=', False)],   # target is files  → find the ones in the DB
```

The domain answers **"what is not yet in the target?"** — so each key names the
*other* backend's column. For `'gcs'`, the target is GCS, and what isn't in GCS
is what's on local disk, identified by `store_fname`. So the correct answer is
the **`'db'` key's domain**:

```python
'gcs': [('store_fname', '!=', False)],
```

I had the direction of the question backwards. Worth dwelling on for a second,
because the mistake is instructive: I read the dict as *"where the data is"* when
it means *"where the data isn't yet."* Both readings produce sensible-looking
code, and only one of them migrates your files.

#### A consequence that only shows up at 60%

`'db'` and `'file'` work as a pair because they use **different columns**, so the
domain itself tells you what's already done.

GCS breaks that. It **reuses `store_fname`** — deliberately, so that a key means
the same thing whether the blob is on disk or in a bucket. That's a property
worth having (revert paths and ad-hoc SQL stay honest), but it costs you
something: after a blob moves to GCS, `store_fname` is *still set*, so the domain
**still matches it.** There is no column that distinguishes a disk blob from a
GCS blob.

Which means `force_storage()` under `'gcs'` is **"rewrite everything"**, not
"migrate what's left." Re-running re-uploads all 4,359 blobs. And if it dies
partway, it cannot tell you where.

For 769 MB that's survivable, but it isn't an operational procedure. **Stage 2
needs its own batched, resumable script with an explicit progress marker** —
tracked by attachment `id` range or in a small state table. Anywhere except
`store_fname`.

#### The garbage collector, which stops silently

`_gc_file_store` (line 191) begins:

```python
if self._storage() != 'file':
    return
```

It's an `@api.autovacuum`. With `location = gcs`, GC never runs. Nothing logs a
warning, because that early return is *correct* for the `db` case.

Result: every deleted attachment leaves its object in GCS forever, and you pay
for all of it, and nothing tells you. In a system that has been running for
years, that bill grows monotonically.

You have to write your own. But re-read §1.5 first, because the naive version is
wrong:

```python
# WRONG
def _file_delete(self, fname):
    bucket.blob(prefix + fname).delete()
```

Content-addressing (§1.5) means nine other attachments may point at that blob.
This is data loss, and it's *quiet* data loss — it shows up weeks later as one
employee's document 404ing while the others are fine.

Port Odoo's algorithm instead. Three steps, exactly as in `_gc_file_store_unsafe`
(line 222): collect candidates, `SELECT store_fname FROM ir_attachment WHERE
store_fname IN (...)` to get the whitelist, delete only what nobody references.

One change is forced. Odoo's "checklist" is a directory of empty files on local
disk, written by `_mark_for_gc`. **A pod cannot use that** — the pod that writes
the note may not be the pod that collects, and both may be gone by then. Options:

- a small Odoo model (`cleardeals.gcs.gc.queue`) — a database table as the
  checklist. Simple, transactional, visible, and the DB is already shared.
- or `LIST` the bucket by prefix and diff against
  `SELECT DISTINCT store_fname` — no checklist at all. Fine at 759 MB; gets
  expensive as an object count grows.

Start with the queue table. And keep Odoo's `LOCK ir_attachment IN SHARE MODE`
(line 212) around the judging step, so nobody can create a reference to a blob
between the whitelist query and the delete.

Give the GC a **success metric and a staleness alert**, built like
`monitoring.tf`'s P2b. A GC that silently stops is the same failure class as a
snapshot schedule that silently stops — and this repo already learned that
lesson once.

### 4.2 The session store override

#### There is a reference implementation, and it has two bugs

Odoo ships a non-filesystem session store: `MemorySessionStore(SessionStore)` at
`odoo/addons/test_http/utils.py:53`. It's the canonical statement of the minimum
surface — ten methods.

Read it. Then **don't copy it**, because two of those methods are wrong in ways
that don't show up in the test suite.

**Bug 1 — the `vacuum` signature.** The test store has:

```python
def vacuum(self):
    return
```

But `odoo/addons/base/models/ir_http.py:410` calls:

```python
http.root.session_store.vacuum(max_lifetime=http.get_session_max_inactivity(self.env))
```

`TypeError`, in the daily autovacuum. It never fires in the test suite because
the tests never run autovacuum. Correct signature:
`vacuum(self, max_lifetime=SESSION_LIFETIME)` — and with a Redis TTL the body
really is `return`, which is the one place a stub is the right answer.

**Bug 2 — comparing the wrong lengths.** This one is genuinely subtle and it's
worth slowing down for.

```python
def get_missing_session_identifiers(self, identifiers):
    return set(identifiers).difference(self.store)
```

Recall §1.6: **identifiers are the 42-character prefixes; store keys are the
84-character sids.** A 42-character string is never equal to an 84-character
one. So `difference` removes nothing and **every identifier is reported
missing.**

The filesystem store gets it right, and the fix is visible in one line
(`odoo/http.py:1068`):

```python
identifiers.difference_update(sf.name[:42] for sf in session_files)
#                                     ^^^^^  truncate before comparing
```

Now, *who cares?* `odoo/addons/base/models/res_device.py:157` and `:184`. That's
the "My Devices / log out everywhere" feature. "Missing identifier" means "that
session no longer exists", i.e. **revoked**. So the buggy version reports every
device on every user's account as revoked, forever.

That is a security feature silently reporting a false state. Copy the reference
implementation verbatim and you ship it.

The general lesson is bigger than this bug: **a reference implementation written
for tests is optimised for passing tests.** Read it to learn the *contract*, not
to copy the *code*.

#### Mapping sessions onto Redis

```
session:<sid>              → the pickled session dict, TTL 604800s
sessidx:<sid[:42]>         → a Redis SET of full sids sharing this device prefix
```

The second key is the whole design. Without it, `delete_from_identifiers` and
`get_missing_session_identifiers` would have to `SCAN` the keyspace — which is
O(number of sessions) on a request path. It'll be instant in staging with four
sessions and fall over at 200 concurrent users.

**Never `SCAN` or `KEYS` in a request path.** If you take one Redis rule away
from this document, take that one.

With the index, both operations are set lookups. And Redis TTL means `vacuum` is
genuinely nothing — expiry is the storage engine's job.

Two things to get right or users will be logged out at random:

- **`rotate(soft=True)`** (`odoo/http.py:985`) — the `next_sid` read-back dance
  from §1.6. Both keys must be written, and a concurrent request must be able to
  find `next_sid` in the old session.
- **`delete_old_sessions`** (line 964) — the 120-second grace window before the
  old sid is reaped.

Both will be blamed on Redis when they go wrong. Test them under concurrency in
Stage 1, not in production in Stage 3.

#### Why this cannot be a normal addon

This is the subtlest thing in the migration, and the failure mode is the worst
kind: it *looks like it worked*.

Here's the store today (`odoo/http.py:2716`):

```python
@functools.cached_property
def session_store(self):
    path = odoo.tools.config.session_dir
    return FilesystemSessionStore(path, session_class=Session, renew_missing=True)
```

Two things about that.

**First, `root` is a singleton created when `odoo.http` is imported**, and the
session store is consulted **before any database exists as far as the request is
concerned**. Look at `odoo/http.py:1767` — every request, including requests to
`/web/database/selector` where no database is selected yet, goes through the
store. There's a whole "nodb routing map" for exactly this.

A normal Odoo addon is loaded *per database*, when a registry is built. That is
far too late. Sessions are needed to figure out *which* database you're even
talking about.

So it has to be a **server-wide module**. `odoo/service/server.py:1546`:

```python
load_server_wide_modules()
import odoo.http                     # ◀── only NOW is odoo.http imported
```

That's the window. `odoo.prod.conf` currently has
`server_wide_modules = base,web`; we add ours.

**Second, `functools.cached_property`.** It computes once and writes the result
into the instance's `__dict__`, so subsequent accesses skip the property
entirely. Which means if *anything* touches `root.session_store` before your
patch lands, your patch is inert — the filesystem store is already cached and
will be returned forever.

Belt and braces:

```python
odoo.http.Application.session_store = <our cached_property>
odoo.http.root.__dict__.pop('session_store', None)      # evict any cached value
```

And then — because this is the failure mode that looks like success — **log which
store is active at startup, and assert its class in a test.** Not "did the module
install" (it will) but "is the object actually ours." Otherwise you get a module
that installs cleanly, logs nothing, stores sessions on local disk, works
perfectly on one pod, and breaks the moment there are two.

---

## Part 5 — Why the order is the order

This is the highest-value decision in the plan, so let me argue it properly.

### What the blueprint says

Blueprint §5, Phase 1, does all of this as one PoC:

1. migrate the database to Cloud SQL
2. refactor the filestore to GCS
3. refactor sessions to Redis
4. provision the environment
5. deploy to GKE and validate

Four changes, validated at the end. Everything moves at once.

### Why that's a trap

Imagine it. Stage everything, deploy to GKE, and a user reports: *"I uploaded a
document and now I can't download it."*

What broke?

- the GCS `_file_write`?
- the GCS `_file_read`?
- `_to_http_stream` (Part 4.1 — most likely, and you don't know that yet)?
- the pod's Workload Identity permissions on the bucket?
- the Ingress mangling the redirect?
- the Cloud SQL connection dropping mid-transaction so the row was never
  committed?

**Six suspects, and no way to remove one without removing all of them.** Your
only rollback is "go back to the VM," which reverts four changes and teaches you
nothing about which one was wrong. So you try again — and you're debugging four
simultaneous changes on a platform you've never operated, while HR waits.

### What we do instead

Run the first three **on the existing VM, one at a time.** GKE last.

| Stage | Change | If it goes wrong |
| --- | --- | --- |
| 2 | GCS filestore | flip an `ir.config_parameter` back to `file` |
| 3 | Redis sessions | one config line + `docker compose up -d`; everyone re-logs-in |
| 4 | Cloud SQL | repoint `db_host`; the container Postgres still holds the data |
| 5 | GKE | the app is already proven stateless — this tests one thing |

Now the same bug report is trivial. You're in Stage 2. **Only the filestore
changed.** Everything else — the database, sessions, the proxy, the runtime — is
byte-for-byte what it was yesterday, and it was working yesterday. There is
exactly one suspect.

And the rollback is a *config parameter*, not a platform migration.

By the time you reach Stage 5, the application is already stateless and already
talking to Cloud SQL, GCS and Redis. The compute move tests exactly one
question: *does it run in a pod?*

### There's a second reason, and it's about reuse

The two overrides are the only novel code in this whole programme. Everything
else is provisioning.

Prove them on one VM you can snapshot-restore, against real production data and
real user behaviour, and they become **assets** — modules you install on Ops,
Sales and Invoicing with confidence. Prove them inside a simultaneous
Kubernetes migration and you'll never quite know whether they work or whether
the platform is hiding something.

### One thing to be precise about: "reversible" has limits

Stage 2's rollback deserves care, because the obvious reading is wrong.

Flipping `ir_attachment.location` back to `file` is instant, and it affects
**only new writes**. Attachments written to GCS while it was on have no local
file. So a real revert means running the migration *backwards*.

**The flag flip is a stop-the-bleeding move, not a rollback.** It stops making
the problem bigger. Undoing it is a data migration. Say that out loud before
Stage 2, so nobody plans around a rollback that doesn't exist.

Stage 4 is the genuine one-way door. Once writes land on Cloud SQL, the
container Postgres is stale by however long you've been live. Which is why the
plan keeps that data directory — stopped, not deleted — for 14 days: it's the
only rollback that isn't a restore.

---

## Part 6 — The traps, and how to recognise them

Four things that will not appear in a code review but will appear in an incident.

### 6.1 The connection arithmetic, which is how an autoscaler kills a database

Start with something surprising. Odoo keeps **two** connection pools, not one
(`odoo/sql_db.py:811`):

```python
_Pool_readonly: ConnectionPool | None = None
```

`http.py` takes a *readonly* cursor on every request. If you'd configured a read
replica, those would go to the replica. We haven't, so `connection_info_for`
(line 769) falls back to the primary — meaning they're **separate physical
connections to the same server.**

So the multiplier is 2, not 1. Today (`odoo.prod.conf` documents this):

```
5 processes × 2 pools × db_maxconn 5  =  50    against max_connections 60
```

Comfortable. And notice how careful that number is: Postgres reserves 3
connections for superusers, so the usable ceiling is 57, and 50 leaves real
headroom rather than an exact fit.

Now put it on Kubernetes. **The process count is no longer fixed — the HPA owns
it.** Say `web` pods run `workers=2`:

```
4 pods  →  8 worker processes × 2 × 5  =   80
10 pods →  20 worker processes × 2 × 5 =  200
```

plus the `bus` pod, plus the `cron` pod.

At 10 replicas you need 200+ connections. If the Cloud SQL instance is at a
tier default of, say, 100, then **the autoscaler takes the database down under
exactly the load it exists to absorb** — and on a shared instance (§6.5) it
takes Ops, Sales and Invoicing with it.

This is a beautiful failure because it's *caused* by the thing meant to prevent
failure, and it only fires under load, which is when you're least able to think.

The fix is arithmetic, done in advance:

1. Set `max_connections` on Cloud SQL **explicitly**. Never inherit a tier
   default.
2. Derive `maxReplicas` from the connection budget:

   ```
   maxReplicas ≤ (max_connections - reserved - bus - cron) / (workers × 2 × db_maxconn)
   ```

3. Alert on Cloud SQL connection utilisation **before** Stage 5, so you see it
   climbing rather than discovering the ceiling by hitting it.

And when you do the sum, remember which side has slack. `db_maxconn = 5` is
already tight; the honest lever is `maxReplicas`.

### 6.2 Never put a transaction-pooling PgBouncer in front of Cloud SQL

§6.1 makes you want a connection pooler. It's the standard answer, and PgBouncer
is the standard tool.

Do not put it in transaction-pooling mode in front of this application. Here's
why, and it's a lovely illustration of leaky abstractions.

Recall §1.4: the bus is Postgres. `pg_notify` to publish
(`addons/bus/models/bus.py:163`), `LISTEN imbus` to subscribe (`:242`).

`LISTEN` is a **session-scoped** thing. You say "notify me on this channel" and
that subscription belongs to *that connection*, indefinitely.

Transaction pooling means PgBouncer hands you a connection for the duration of
one transaction, then gives it to someone else. Your `LISTEN` was registered on
a connection you no longer have. The notification arrives at whichever process
happens to be holding that connection now — or nowhere.

**The desk analogy.** Picture the database as an office with a bank of desks,
each with a phone.

*With your own desk* (session pooling, or no pooler): you get desk 7 for your
whole visit. You tell reception *"ring desk 7 if a package arrives for me."* An
hour later the package comes, reception rings desk 7, you're sitting there, you
get it.

*With transaction pooling*: you get whatever desk is free, and only while you do
one task. Then you hand it back and return to the waiting room. So you sit at
desk 7, tell reception *"ring desk 7 for my package"* — and your task ends, and
the desk goes to Bob. The package arrives. Reception rings desk 7. **Bob
answers**, has no idea what it's about, and hangs up. You wait forever.

The bug is in the sentence: **you registered the subscription against the desk,
not against yourself.** `LISTEN` puts state on a *connection*; transaction
pooling is built on the premise that connections carry no state. Both cannot be
true.

That premise is correct for nearly everything an app does, which is why the
abstraction is usually watertight. It leaks at exactly the handful of Postgres
features whose state lives on the connection: `LISTEN`/`NOTIFY`, prepared
statements, temp tables, `SET` variables, session-level advisory locks. Nowhere
else.

#### Odoo's bus isn't just incompatible — it's the textbook worst case

Here's the real listener, `addons/bus/models/bus.py:237`:

```python
def loop(self):
    _logger.info("Bus.loop listen imbus on db postgres")
    with odoo.sql_db.db_connect('postgres').cursor() as cr, \
         selectors.DefaultSelector() as sel:
        cr.execute("listen imbus")
        cr.commit()                       # ← 1
        conn = cr._cnx
        sel.register(conn, selectors.EVENT_READ)
        while not stop_event.is_set():    # ← 3
            if sel.select(TIMEOUT):       # ← 2
                conn.poll()
```

1. **It commits immediately after `LISTEN`.** `COMMIT` is precisely the signal a
   transaction-mode pooler uses to reclaim the connection. The subscription is
   registered, and the desk goes to Bob on the very next line.
2. **Then it blocks on the raw socket**, waiting for Postgres to spontaneously
   push bytes down that specific TCP connection. A transaction-mode pooler holds
   no client↔server mapping at that instant, so there is nothing to route the
   notification along.
3. **Then it loops forever** — one connection, held open indefinitely, *with no
   transaction open*. That is the exact state transaction pooling was invented to
   eliminate. The pooler sees an idle connection that ought to be reclaimed, and
   reclaiming it is the bug.

#### The log doesn't stay silent. It lies to you comfortingly.

An earlier version of this section said "nothing in any log." **That was wrong,
and the reality is nastier.** Look at the first line of `loop()`:

```
INFO … Bus.loop listen imbus on db postgres
```

That appears every time, and **it is true.** `LISTEN imbus` really did execute
and really did succeed. The connection just never receives anything afterwards.

So the log doesn't omit the failure — it asserts, accurately, that the broken
component started correctly. And `run()` catches `InterfaceError`/`PoolError`
and restarts `loop()`, so a pooler that keeps reclaiming the connection gives
you an endless cycle of reconnects and cheerful log lines.

That's the worst shape a fault can take: the component reports healthy, the
symptom shows up in a different subsystem (the UI), and the cause is a middlebox
nobody thinks of as a participant.

**Which is why someone will spend two days on Redis.** In this plan you move
sessions to Redis at Stage 3. Then at Stage 5 somebody adds a pooler to fix
connection limits, and chat breaks. What's the nearest suspicious recent change?
*"We put sessions in Redis."* Chat feels session-shaped. It is the obvious
suspect, it is completely innocent, and you can lose two days there before
anyone suspects a component they never thought of as part of the system.

#### One more thing the code told me: the bus lives in a different database

Both halves call `db_connect("postgres")` — the publisher at `bus.py:159`, the
listener at `:240`. Not `odoo_hrms_db`. The `imbus` channel is deliberately
**server-wide** rather than per-database, so one Odoo server hosting many
databases shares one channel and filters by payload.

Consequence for Stage 4: **the `odoo` role must be able to `CONNECT` to the
`postgres` database on Cloud SQL.** It can by default — but

```sql
REVOKE CONNECT ON DATABASE postgres FROM PUBLIC;
```

kills every realtime feature, with the identical reassuring log line.

And that is a completely reasonable thing for a security reviewer to ask for —
*more* likely under the shared-instance model of Part 6.5, where restricting
cross-database access is the entire point of one role per domain. So the two
good ideas collide, and you have to resolve it deliberately: every domain's role
needs `CONNECT` on `postgres`, documented as load-bearing rather than looking
like a default nobody got around to tightening.

#### Why the Auth Proxy is safe

Because it is **stupid**, and that is the point.

An encrypted TCP tunnel with IAM authentication. One connection in, one
connection out. It copies bytes. **It does not parse the Postgres protocol** — it
cannot tell a `SELECT` from a `BEGIN` from a `LISTEN`.

Something that doesn't understand your semantics cannot break them. PgBouncer
breaks `LISTEN` *because* it understands transactions well enough to act on them
and not well enough to know about the exception.

**For a middlebox, less intelligence means fewer semantics it can violate.**
Every bit of protocol awareness is a new chance to be subtly wrong.

#### So what do you actually do about §6.1?

In order of preference:

1. **Cap `maxReplicas` from the connection budget.** The real lever, and it adds
   no components. This is the whole recommendation.
2. **Set Cloud SQL's `max_connections` explicitly** instead of inheriting a tier
   default nobody has looked at.
3. **If you genuinely need a pooler** — session-pooling mode preserves `LISTEN`.
   Smaller saving, no breakage.
4. **Best structural answer: pool the `web` pods and let the `bus` pod connect
   direct.** It is one pod holding one long-lived connection; pooling buys it
   nothing. Part 3.2's three-way split makes this trivial — the bus is already
   its own Deployment, so it just gets a different `db_host`. **The component
   that breaks under pooling is exactly the component that doesn't need it**,
   which is a good sign the split was the right shape.

A footnote for the arithmetic in §6.1: that listener connection comes from
Odoo's own pool and is held for the process's lifetime. With `db_maxconn = 5`,
the gevent process has **4** usable slots, not 5.

### 6.3 The 301 that poisons caches

Covered in Part 4.1, restated because it's the kind of thing that gets lost.

`Stream.get_response()` with `type='url'` and no `max_age` emits **301 Moved
Permanently** to a signed URL that expires. A 301 is cacheable indefinitely by
browsers and by every proxy in between.

So: the URL dies in an hour, and the redirect to it lives forever. The user's
browser doesn't even ask your server. **You cannot fix it server-side.**

Always set `max_age`, well under the signature lifetime.

### 6.4 `unaccent`, and a restore that fails halfway

`odoo.prod.conf` has `unaccent = True`. Read what that flag actually does
(`odoo/tools/config.py:449`):

> "Try to enable the unaccent extension **when creating new databases**."

So it's a **database-creation** instruction, not a runtime setting — and it
already ran, years ago. It's history.

Worth noticing the word *"Try"*. That's honest documentation of a best-effort
operation, and it's easy to read past. Here's the only place the flag is read
(`odoo/service/db.py:154`):

```python
try:
    with db.cursor() as cr:
        cr.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        if odoo.tools.config['unaccent']:
            cr.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
            cr.execute("ALTER FUNCTION unaccent(text) IMMUTABLE")
except psycopg2.Error as e:
    _logger.warning("Unable to create PostgreSQL extensions : %s", e)
```

Look at that `except`. **Odoo swallows the failure and carries on.** No
permission? One `WARNING` line in a wall of startup output, a database with no
`unaccent`, and an application that boots perfectly and searches wrongly.

#### So what does matter? Odoo asks the database, every startup

Every registry load, Odoo runs a query: *is the `unaccent` function actually
here?* That's `has_unaccent` (`odoo/modules/db.py:166`). It doesn't trust the
config flag — it looks.

Sensible. But it asks a **second, stranger question** too, and to see why we
need to talk about why Odoo wants the function at all.

#### Why "is it here?" isn't enough — the phone book

Odoo wants accent-insensitive search to be **fast**. Fast search means an
**index**.

An index is a precomputed answer book. Think of a phone book: names sorted
alphabetically so you can find "Patel" without reading every page.

But Odoo isn't searching the raw name — it's searching the *accent-stripped*
name, because it wants `cafe` to find `café`. A phone book sorted by raw surname
is no help there: `Müller`, `Muller` and `Mueller` land on different pages.

What Odoo needs is a **second phone book, sorted by the stripped version**.
Postgres can do that — an *expression index*:

```sql
CREATE INDEX ... ON res_partner (unaccent(name))
```

Building it means walking every row once, calling `unaccent()`, and writing the
answers down in sorted order.

**And there's the problem.** That book is only useful if `unaccent('Müller')`
returns the same thing *forever*. If the accent-stripping rules ever changed,
your book would be sorted by the old rules — and lookups using the new rules
would silently miss people. The book would be quietly wrong, and nothing would
say so.

#### So Postgres makes you promise

Postgres won't index a function unless you promise its answer never changes.
Three levels of promise:

| label | the promise | example |
| --- | --- | --- |
| `VOLATILE` | could return anything, any time | `random()`, `now()` |
| `STABLE` | same answer within one query; may differ between queries | anything reading settings |
| `IMMUTABLE` | **same input → same answer, forever** | `lower()`, `abs()` |

**Only `IMMUTABLE` can be indexed.** The phone book is why.

And how does Postgres label `unaccent`? **`STABLE`** — because it reads its
accent rules from dictionary files on disk, and somebody could edit those files.
By Postgres's own reasoning, it is not safe to index.

#### Odoo overrides Postgres, deliberately

That's what the second line above is:

```sql
ALTER FUNCTION unaccent(text) IMMUTABLE     -- "trust me, Postgres"
```

It forcibly relabels the function to unlock indexing. Odoo's own comment
concedes the point:

> From PostgreSQL's point of view, making 'unaccent' immutable is **incorrect**
> because it depends on external data […] But in the case of Odoo, we consider
> that those data don't change in the lifetime of a database. **If they do
> change, all indexes created with this function become corrupted!**

A documented, accepted trade. But notice the consequence: **the good state is not
"the extension is installed." It's "installed AND somebody ran that second
line."** Two separate facts. Installing gets you `STABLE`. Only the `ALTER` gets
you `IMMUTABLE`.

That second fact is the stranger question `has_unaccent` asks.

#### Now the three states make sense

```python
MISSING   = 0   # the function isn't there
PRESENT   = 1   # there, but STABLE    — can't be indexed
INDEXABLE = 2   # there, and IMMUTABLE — can be indexed
```

And Odoo behaves differently in each, because its two consumers test
differently — `registry.py:305` is a **truthy** test, while `registry.py:844` is
`== FunctionStatus.INDEXABLE`:

**`MISSING`** — Odoo gives up on accents. `registry.py:305` swaps the function
for `lambda x: x`, so searches stop wrapping in `unaccent()` at all. Search turns
accent-*sensitive*: `cafe` no longer finds `café`. **Your answers change.** No
error.

**`PRESENT`** — Odoo still wraps searches in `unaccent()`, so answers are
correct. But it won't build the stripped phone book. You're asking *"find
everyone whose stripped name is muller"* holding only the raw-sorted book — it
can't help, so Postgres reads every row. **Correct but slow.** No error.

**`INDEXABLE`** — searches use `unaccent()`, the matching index exists, lookups
are fast. Correct *and* fast.

**Two entirely different silent failures.** One changes what comes back. The
other changes how long it takes. Neither says a word.

#### Your database is in the best state — measured

```
extname   | schema | version        proname  | pronargs | provolatile
pg_trgm   | public | 1.6            unaccent |        1 | i   ← IMMUTABLE
unaccent  | public | 1.1            unaccent |        2 | s   (ignored, pronargs=1)
```

`INDEXABLE`. Somebody ran that `ALTER` — which tells us the database was
originally created by Odoo with `unaccent = True`, and it worked.

**Which means the migration can only make this worse**, in one of the two silent
ways above. That asymmetry is the whole reason this section exists.

Two more traps in the query, while we're here. It requires
`pronamespace = current_schema` — so installing extensions into a separate
`extensions` schema (a common hardening pattern) leaves `\dx` looking perfect
and Odoo reporting `MISSING`. And `pronargs = 1`, so only the one-argument
overload counts.

---

#### Now: why Cloud SQL threatens all of this

Here's the thing I didn't expect to find:

```
rolname | rolsuper
odoo    | t          ← your odoo role is a Postgres SUPERUSER
```

Of course it is. Postgres runs in a container, `odoo` is the account it was set
up with, so it owns everything and can do anything — `CREATE EXTENSION` and
`ALTER FUNCTION` included.

**On Cloud SQL, nobody can ever be a superuser.** Google doesn't offer it; that's
how instances stay manageable. The ceiling is membership of a role called
`cloudsqlsuperuser` — which can create extensions, but is not a true superuser.

So the migration isn't "copy the data across." It's: **take a database built by
a superuser, and rebuild it somewhere no superuser exists.**

#### Why the restore "fails halfway"

This is the bit that's easy to miss. **A `pg_dump` file is not data. It's a
script of SQL commands.** Open one:

```sql
CREATE EXTENSION unaccent;                    -- ← needs superuser
ALTER FUNCTION unaccent(text) IMMUTABLE;
CREATE TABLE res_partner (...);
COPY res_partner FROM stdin; ...
CREATE INDEX ...;
```

Restoring means **running** every line, as whoever you logged in as.

Connect as `odoo` on Cloud SQL and it hits `CREATE EXTENSION` and is refused —
*and that line is near the top, before your data.* So you don't get a clean "no"
up front. You get a few objects created, then a permission error, then either a
halt or a cascade of follow-on failures against a half-built schema.

Mid-maintenance-window. On a partly-loaded database. The worst moment for a
surprise.

#### So it's three steps, not two

1. **Restore as the Cloud SQL admin user** (the one with `cloudsqlsuperuser`),
   so `CREATE EXTENSION` is allowed.
2. **Hand ownership of the objects to `odoo`**, so the application owns its own
   schema.
3. **Re-run `ALTER FUNCTION unaccent(text) IMMUTABLE` — as the admin user.**

Step 3 is the sneaky one, and it's **unfixable from inside the application**.
`ALTER FUNCTION` requires *owning* that function, and in step 1 the *admin user*
created the extension — so the admin owns those functions, not `odoo`. Even if
`odoo` noticed the problem, it could not correct it. Somebody has to do it
deliberately, as the right role.

Skip step 3 and you land in `PRESENT`: right answers, indexes quietly unused,
and no bug report — because nobody ever files *"search feels a bit slower than
last month."*

#### What to check afterwards

Restore into a **throwaway** instance and ask exactly what Odoo asks:

```sql
SELECT current_schema, p.provolatile
  FROM pg_proc p
 WHERE p.proname = 'unaccent'
   AND p.pronamespace = current_schema::regnamespace
   AND p.pronargs = 1;
```

- `i` → immutable, you match production
- `s` → step 3 was needed, and you just caught it before the real cutover
- no rows → the extension didn't survive, or it's in the wrong schema

**Being honest about a gap:** I don't know whether `pg_dump` actually preserves
that `ALTER FUNCTION`. `pg_dump` deliberately doesn't dump an extension's
internal objects — it writes `CREATE EXTENSION` and lets the extension rebuild
itself. Whether a volatility change to one of those functions survives, I can't
tell you from here. But the query above settles it in ten seconds on a scratch
instance, which is why step 3 is written as *re-assert* rather than *must*.

#### The general lesson

Your database holds state that isn't tables and isn't rows — which extensions
exist, how their functions are labelled, who owns what, which roles hold which
privileges. `pg_dump` preserves most of it, silently drops some of it, and Odoo
checks what survived at startup and quietly does **less** when something's
missing.

So the test after migrating can't be *"is the data there?"* It has to be
**"does the database still answer Odoo's questions the same way?"**

### 6.5 One shared Cloud SQL, or four?

A design question, not a bug, and worth deciding deliberately because it's
expensive to reverse.

The blueprint says "a centralized, fully managed Cloud SQL cluster" (§4.2) —
i.e. one instance, four databases. On cost that's almost certainly right; HRMS is
**119 MB**, and four HA instances to hold a few gigabytes total is hard to
defend.

But notice the tension. Blueprint §3 is all about **decoupling** the domains, and
a shared instance re-couples them at two levels:

- **capacity** — the §6.1 connection budget is now shared, so Sales' autoscaler
  can starve payroll
- **maintenance** — one upgrade window for all four domains, which is exactly
  the coupling §3 complains about

That's a real trade, and either answer can be right. Just make it a decision
rather than a default. If shared:

- a **separate Postgres role per domain**, no cross-database grants, so Sales
  cannot read payroll — this is not optional for HR data
- budget `max_connections` across **all four** HPAs together, not per instance

For Redis the call is easier. Sessions are small and uniform, so one instance
with a key prefix or logical DB per domain is fine.

---

## Part 7 — The part that isn't technical

Everything above is solvable with a keyboard. This isn't, and it's the actual
critical path.

### Stage 0 exists because of two access problems

**The developer cannot log into production.**

Not "cannot sudo" — that was the documented, accepted outcome of the OS Login
cutover. **Cannot log in at all.** Recorded as an OPEN finding in
`docs/infrastructure_migration_plan.md`.

The cause is worth learning because it's a genuinely non-obvious IAM shape.
`roles/compute.osLogin` is not sufficient on a VM that has a service account
attached. You *also* need `iam.serviceAccounts.actAs` **on that service
account** — because logging in means the session can use the VM's identity, and
IAM makes you prove you're allowed to borrow it.

Phase 4b did both halves of the change that creates this requirement (enabled OS
Login, attached `hrms-prod-vm@`) and granted `actAs` only to the Cloud Build
account. Humans were locked out as a side effect.

And here's the part that makes it a good lesson: **every obvious check says
access is fine.**

| check | says |
| --- | --- |
| `testIamPermissions` on the instance | `compute.instances.osLogin` **GRANTED** |
| OS Login POSIX profile | exists |
| registered SSH key | present, no expiry |
| `getent passwd` on the host | resolves the user |
| IAP tunnel | connects |

Every one of them green. The missing permission is on a **different resource** —
the service account, not the instance — so an instance-scoped check structurally
cannot see it. And the client-side error is `Permission denied (publickey)`,
which blames a key that is perfectly fine.

The authoritative check is the metadata endpoint the guest agent actually
consults:

```bash
curl -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/oslogin/authorize?email=<user>&policy=login'
# → {"success":false}
```

**Why this blocks the migration:** Stages 2, 3 and 4 each involve watching a
live cutover and being able to abort it by hand. A Cloud SQL cutover you cannot
SSH into is not a cutover you can abort. Right now the only way in is borrowing
`tech@` — an Owner account scheduled to be retired.

**Second problem:** `resourcemanager.projects.setIamPolicy` is denied, so every
project-level IAM binding needs an Owner. This migration adds several (Workload
Identity, Cloud SQL client, GCS access, the `signBlob` self-grant from Part 4.1).

The recommendation stands: a **time-boxed** `roles/resourcemanager.projectIamAdmin`
grant so the Terraform applies as one unit. PAM (Privileged Access Manager) is
already enabled on this project with zero entitlements and is the right vehicle
— configured with **no approver**, because a sole developer has none, and an
approval gate with no approver is a lockout during the exact incident it exists
for.

### Why the plan grants nothing

`docs/cloud_native_migration_plan.md` describes the fix — one
`google_service_account_iam_member` giving the developer
`roles/iam.serviceAccountUser` on `hrms-prod-vm@`, login only, no sudo — and
**does not implement it.** A draft was written and removed at the operator's
direction, so nothing in this repository grants a human access to production and
nothing is one flag away from doing so.

That's deliberate. The finding is more useful to an auditor intact than quietly
patched, and it's the sharpest available illustration of the standing problem:
the only technical operator cannot reach production without borrowing an account
that is being retired.

---

## Part 8 — What I don't know

The value of everything above depends on being clear about this.

**Verified** — read from this repository, with file and line numbers:
everything about Odoo's internals. The five bugs and gaps in Part 4 are all
readable in `odoo/`. Go check them; that's what the line numbers are for.

**Not verified:**

- ~~**How to start `GeventServer` standalone.**~~ **Resolved 2026-09-10** — see
  Part 3.2. It is `argv[1] == 'gevent'`, positionally. Found by reading `ps auxf`
  on the live VM, not by reading the code, which is itself the lesson.
- **All GCP behaviour.** Quotas, tier defaults, `max_connections` limits,
  Memorystore sizes, pricing. Check current documentation and this project's
  actual quota. Every GCP number in these documents is illustrative.
- **Whether the OCA prior art fits.** `storage_backend` /
  attachment-object-storage and Camptocamp's `session_redis` solve exactly these
  two problems. If one supports Odoo 19 well, use it — and then **Part 4 becomes
  your review checklist** rather than a specification. Ask any candidate module:
  does it override `_to_http_stream`? does it handle `_get_storage_domain`? does
  it have a GC that respects shared blobs? does its `vacuum` accept
  `max_lifetime`? does `get_missing_session_identifiers` truncate to 42? Five
  questions, and they'll tell you a lot fast.
- **Current data sizes.** 119 MB / 759 MB come from a comment in `storage.tf`
  dated 2026-09-09. Re-measure before Stage 2 sizes its batches.

---

## Appendix — The ten things worth remembering

1. **The migration is one sentence:** move Odoo's state off the machine Odoo
   runs on. Everything else is detail.
2. **Odoo keeps state in four places** — database, filestore, sessions, scratch
   — and each is one leg of the plan. The fourth stays local, and that's fine.
3. **The filestore is content-addressed** (SHA-1 of the bytes), so blobs are
   shared between attachments. This is why deletion needs a garbage collector
   and not a `delete`.
4. **The sid is two halves** — 42 characters of device identity, 42 of secret.
   Everything about sessions and device revocation follows from that split.
5. **Downloads don't call `_file_read`.** `_to_http_stream` builds a local path
   and `os.stat`s it. This is the finding that would have sunk the PoC.
6. **The session store must be server-wide**, and it fails *silently* into the
   filesystem store if it's patched too late. Log the active class; assert it in
   a test.
7. **A component can be healthy and useless.** Traefik proved it for 2.5 hours.
   Ask the user's question from where the user asks it.
8. **The HPA is a connection multiplier.** Two pools per process × workers ×
   pods. Derive `maxReplicas` from the connection budget, not from CPU.
9. **The bus is Postgres `LISTEN`/`NOTIFY`, in the `postgres` database.** The
   dumb TCP proxy is safe; transaction pooling kills every realtime feature —
   and not silently, which is worse: the log asserts the bus started fine,
   because it did. Revoking `CONNECT` on `postgres` breaks it the same way.
10. **Do one thing at a time.** Four changes at once means four suspects and no
    rollback that isn't also four changes. Prove GCS, Redis and Cloud SQL on the
    VM. GKE last.
11. **Measure the running system, don't reason about it.** Reading the source got
    the mechanisms right and three quantities wrong. `ps auxf` answered a
    question the code didn't (`argv[1] == 'gevent'`) and found workers sitting at
    91% of `limit_memory_soft` just as Stage 1 was about to add two libraries.
    Six SQL queries then corrected a wrong prescription (the storage domain
    asks *"what isn't in the target yet"*, so `'gcs'` needs the `'db'` domain,
    not the `'file'` one — the obvious choice matches zero rows and reports
    success), deflated an invented magnitude (largest attachment 6.4 MB, not the
    "200 MB" I reached for), and turned the shared-blob hazard from a caveat into
    61 blobs with ten references and two with twenty-one. None of it was
    derivable from reading, and the plan was wrong in a load-bearing way until
    somebody ran a query.
