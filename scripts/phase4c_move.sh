#!/usr/bin/env bash
# scripts/phase4c_move.sh
#
# Moves the application out of a personal home directory.
#
#     /home/tech/odoo-project  ->  /opt/odoo-hrms
#
# Run as root on the VM, with the stack DOWN, inside the Phase 4c window.
#
# ── WHY THIS MOVE EXISTS ─────────────────────────────────────────────────────
#
# The CRM repo records three outage-class problems caused by this location, and
# they were the justification for doing the same thing here. Two of the three
# apply to this host; the first one has already bitten it:
#
#   1. `git` refuses to operate on a repo owned by another user ("detected
#      dubious ownership") and kills a deploy. Live here: every git command in
#      scripts/deploy.sh needs `-c safe.directory='*'` precisely because the
#      checkout is owned by `tech` and the deploy does not run as `tech`.
#   2. The location is why the addons were bind-mounted, which made the image
#      tag a lie and rollback a fiction. Phase 3 removed the mount; this removes
#      the reason it was ever there.
#   3. On CRM the OS Login user could not `cd` into a mode-750 home directory,
#      so a manual command ran silently in the wrong place. THIS DOES NOT APPLY
#      HERE and the plan was wrong to claim it did: /home/tech is mode 755, so
#      tech_cleardeals_in can already traverse it. Verified before the window.
#
# So the honest justification on this host is (1) and (2), not (3). It is still
# worth doing — /opt is the conventional place for site-local application trees
# and root:root 755 makes ownership a deliberate choice rather than an accident
# of who happened to run the installer — but it is a tidiness-and-correctness
# change, not an emergency.
#
# ── WHAT THIS SCRIPT DELIBERATELY DOES NOT DO: chown anything ────────────────
#
# The data directories carry ownership that must survive exactly. On this host:
#
#   odoo-db-data   drwx------  owned by uid 999 (postgres inside the container;
#                              maps to no host name, so `ls -l` shows a number)
#   odoo-web-data  owned by Debian-exim:crontab — host names that happen to
#                  collide with the container's uid/gid. Meaningless, and must
#                  still be preserved byte for byte.
#
# `mv` within one filesystem is an atomic rename and preserves all of it. A
# `cp -a` would rewrite ownership and Postgres would refuse to start with
# "data directory has invalid permissions". The same-filesystem precondition is
# asserted below rather than assumed.
#
# ── COMPOSE PROJECT IDENTITY ──────────────────────────────────────────────────
#
# Compose derives its project name from the DIRECTORY NAME unless pinned. This
# directory is `odoo-project`, so the live project is `odoo-project`; after the
# move it would silently become `odoo-hrms`. The containers set container_name
# explicitly, so compose would then try to create NEW containers using names
# that are already taken and fail with "name is already in use" — mid-window,
# with the stack down, which is the worst possible time to debug an identity
# problem.
#
# So this script REQUIRES the compose file to pin `name: odoo-project` before it
# will move anything. The repo's docker-compose.yml already does; a VM still on
# the old checkout must be patched first. Refusing is deliberate: the failure it
# prevents is confusing and happens after the point of no return.
#
# ROLLBACK: mv /opt/odoo-hrms /home/tech/odoo-project
# scripts/deploy.sh resolves either path, so it keeps working both ways.

set -euo pipefail

OLD="${OLD_DIR:-/home/tech/odoo-project}"
NEW="${NEW_DIR:-/opt/odoo-hrms}"

die() { echo "phase4c: FATAL: $*" >&2; exit 1; }
ok()  { echo "phase4c: $*"; }

[[ "$(id -u)" -eq 0 ]] || die "must run as root"

# ── Preconditions, all of them, before touching anything ──────────────────────
[[ -d "$OLD/.git" ]] || die "no checkout at $OLD"
[[ ! -e "$NEW"    ]] || die "$NEW already exists — refusing to overwrite"

running="$(docker ps -q | wc -l | tr -d ' ')"
[[ "$running" == "0" ]] || die "$running containers still running — run 'docker compose stop' first, or a live Postgres will have its data directory renamed underneath it"

# The compose project name must be pinned, for the reason above.
grep -Eq '^name:[[:space:]]*odoo-project[[:space:]]*$' "$OLD/docker-compose.yml" \
  || die "docker-compose.yml does not pin 'name: odoo-project' — add it BEFORE moving, or compose will rename the project to '$(basename "$NEW")' and collide with the existing container_names"
ok "compose project name is pinned"

# Same filesystem means mv is a rename. Across filesystems it becomes a
# copy+delete: slow, and it rewrites ownership on the data directories.
src_fs="$(df --output=source "$OLD" | tail -1)"
dst_fs="$(df --output=source "$(dirname "$NEW")" | tail -1)"
[[ "$src_fs" == "$dst_fs" ]] || die "$OLD ($src_fs) and $(dirname "$NEW") ($dst_fs) are different filesystems; mv would copy and rewrite ownership"

ok "preconditions OK: checkout present, target free, 0 containers, same filesystem ($src_fs)"

# ── Record what must survive, so the move can be proven rather than assumed ───
# Numeric owner (%u:%g), not names: odoo-db-data is uid 999 with no host name,
# and %U:%G would render it as the number anyway while hiding real changes on
# the directory that DOES have names.
before_db_own="$(stat -c '%u:%g' "$OLD/odoo-db-data")"
before_db_mode="$(stat -c '%a'  "$OLD/odoo-db-data")"
before_web_own="$(stat -c '%u:%g' "$OLD/odoo-web-data")"
before_web_mode="$(stat -c '%a'  "$OLD/odoo-web-data")"
before_head="$(git -c safe.directory='*' -C "$OLD" rev-parse HEAD)"
before_du="$(du -s "$OLD" | cut -f1)"
before_files="$(find "$OLD" | wc -l | tr -d ' ')"

ok "before: db-data ${before_db_own} mode ${before_db_mode}; web-data ${before_web_own} mode ${before_web_mode}"
ok "before: HEAD ${before_head:0:11}, ${before_du} blocks, ${before_files} paths"

# ── The move ─────────────────────────────────────────────────────────────────
mv "$OLD" "$NEW"
ok "moved $OLD -> $NEW"

# ── Prove nothing changed but the path ───────────────────────────────────────
after_db_own="$(stat -c '%u:%g' "$NEW/odoo-db-data")"
after_db_mode="$(stat -c '%a'  "$NEW/odoo-db-data")"
after_web_own="$(stat -c '%u:%g' "$NEW/odoo-web-data")"
after_web_mode="$(stat -c '%a'  "$NEW/odoo-web-data")"
after_head="$(git -c safe.directory='*' -C "$NEW" rev-parse HEAD)"
after_du="$(du -s "$NEW" | cut -f1)"
after_files="$(find "$NEW" | wc -l | tr -d ' ')"

[[ "$after_db_own"   == "$before_db_own"   ]] || die "odoo-db-data ownership changed: $before_db_own -> $after_db_own"
[[ "$after_db_mode"  == "$before_db_mode"  ]] || die "odoo-db-data mode changed: $before_db_mode -> $after_db_mode"
[[ "$after_web_own"  == "$before_web_own"  ]] || die "odoo-web-data ownership changed: $before_web_own -> $after_web_own"
[[ "$after_web_mode" == "$before_web_mode" ]] || die "odoo-web-data mode changed: $before_web_mode -> $after_web_mode"
[[ "$after_head"     == "$before_head"     ]] || die "git HEAD changed: $before_head -> $after_head"
[[ "$after_du"       == "$before_du"       ]] || die "size changed: $before_du -> $after_du blocks"
[[ "$after_files"    == "$before_files"    ]] || die "path count changed: $before_files -> $after_files"

ok "verified: ownership, modes, git HEAD, size and path count all identical"
ok ""
ok "NOW RECREATE THE CONTAINERS — DO NOT 'docker compose start':"
ok "  cd $NEW && docker compose up -d --force-recreate"
ok ""
# WHY --force-recreate AND NOT start. Docker resolves bind mounts to ABSOLUTE
# paths and records them in the container's config at creation time. The stopped
# containers still point at $OLD:
#
#   odoo-db   $OLD/odoo-db-data  -> /var/lib/postgresql/data
#   odoo-app  $OLD/odoo.conf, $OLD/odoo-web-data, $OLD/custom_addons
#   traefik   $OLD/letsencrypt
#
# `docker compose start` reuses those containers, and Docker CREATES A MISSING
# BIND SOURCE AS AN EMPTY ROOT-OWNED DIRECTORY rather than failing. Postgres
# would then find an empty PGDATA and initdb a fresh, empty cluster — while the
# real data sat untouched at $NEW/odoo-db-data. Odoo would come up with no
# database, and the obvious "fix" of restoring a backup would be the wrong move.
#
# Recreating rebuilds the mount table from the compose file in the new location.
# It is safe: all state is in the bind mounts, which is the whole point of them.
