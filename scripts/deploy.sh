#!/usr/bin/env bash
# scripts/deploy.sh — the production deploy, run ON the VM.
#
# Invoked by Cloud Build over SSH:
#     sudo bash scripts/deploy.sh <commit-sha>
#
# It lives in the repo rather than inline in cloudbuild.yaml on purpose. A
# heredoc in the build config would pass through three layers of quoting —
# Cloud Build substitution, then bash, then ssh — which is where deploy scripts
# reliably die over a stray quote nobody can see in a diff. Here it is
# reviewable in a pull request, and runnable by hand when something has gone
# wrong at 3am and Cloud Build is not the tool you want.
#
# What it replaces: a GitHub Actions workflow that SSHed in with a long-lived
# key from a repo secret, wrote odoo.conf from another secret, ran
# `docker compose build` ON THIS VM, and reported success whether or not Odoo
# came back up.

set -euo pipefail

# Defined first: the project-id lookup below calls die().
log() { echo "[deploy $(date -u +%H:%M:%S)] $*"; }
die() { echo "[deploy] FATAL: $*" >&2; exit 1; }

SHA="${1:?usage: deploy.sh <commit-sha>}"

# Resolved, not hardcoded, so the Phase 4c move to /opt/odoo-hrms needs no flag
# day. Both this script and the pipeline must keep working on BOTH sides of that
# move: pinning either path means the deploy breaks for the window between the
# directory moving and the code that knows about it being deployed — and the
# only way to deploy that code is the deploy that is broken.
#
# /opt/odoo-hrms wins when it exists. Once the move is done and settled, the
# fallback can be deleted.
if [[ -n "${APP_DIR:-}" ]]; then
  :                                   # explicit override always wins
elif [[ -d /opt/odoo-hrms/.git ]]; then
  APP_DIR=/opt/odoo-hrms
elif [[ -d /home/tech/odoo-project/.git ]]; then
  APP_DIR=/home/tech/odoo-project
else
  echo "[deploy] FATAL: no checkout at /opt/odoo-hrms or /home/tech/odoo-project" >&2
  exit 1
fi
REGISTRY="${REGISTRY:-us-central1-docker.pkg.dev}"

# Project id is read from the instance metadata server rather than hard-coded.
# This repository is PUBLIC: no project identifier belongs in it. It is also
# simply more correct — the VM knows which project it is in, and a copy of this
# script on another host cannot silently deploy to the wrong registry.
GCP_PROJECT="${GCP_PROJECT:-$(curl -fsS -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/project/project-id 2>/dev/null || true)}"
[[ -n "${GCP_PROJECT}" ]] || die "cannot determine GCP project (not on a GCE VM? set GCP_PROJECT)"

IMAGE_BASE="${IMAGE_BASE:-${REGISTRY}/${GCP_PROJECT}/hrms/odoo-hrms}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-300}"   # 5 min: a migration deploy is slow

# Public hostname, used by the edge gate below to prove traffic actually reaches
# Odoo through Traefik. It MUST match the Host(`...`) rule on the odoo router in
# docker-compose.yml — Traefik routes on it, so a value that does not match
# matches no router and returns 404.
#
# That coupling is deliberate rather than clever. Deriving it by parsing the
# compose labels would keep the two in sync automatically, but it would also
# silently follow a typo, and this gate exists precisely to notice when the
# public path is broken. If the domain ever changes, this line should be part of
# that change.
EDGE_HOST="${EDGE_HOST:-hr.cleardeals.xyz}"
EDGE_TIMEOUT="${EDGE_TIMEOUT:-60}"        # Traefik's docker provider is event-driven

cd "$APP_DIR" || die "app dir not found: $APP_DIR"

# git refuses to operate on a repository owned by another user ("detected
# dubious ownership"). This script runs as root; the checkout is owned by
# `tech`. The inline bootstrap in cloudbuild.yaml passes -c safe.directory on
# every call, but this script's own git commands would not — so they would all
# fail and the deploy would die after the checkout.
#
# Set once here, for every git invocation in the script, via environment rather
# than `git config --global`: a deploy should not leave persistent config behind
# on the host.
#
# The real fix is Phase 4c moving the application out of a personal home
# directory to /opt/odoo-hrms.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0="$APP_DIR"

# ── One deploy at a time ──────────────────────────────────────────────────────
# Cloud Build does not serialise approved builds. Two people approving in quick
# succession would otherwise interleave .env writes and leave an image running
# that nobody chose.
exec 9>/var/lock/odoo-hrms-deploy.lock
flock -n 9 || die "another deploy is already running"

# ── Rollback pointer comes from what is RUNNING ───────────────────────────────
# Deliberately NOT from .env. If someone hand-edited that file and never
# restarted, it describes an intention rather than reality — and rollback would
# restore an image that was never actually serving traffic.
CONTAINER="$(docker compose ps -q odoo 2>/dev/null || true)"
if [[ -n "$CONTAINER" ]]; then
  PREV="$(docker inspect --format '{{.Config.Image}}' "$CONTAINER")"
  log "currently running: $PREV"
else
  PREV=""
  log "no running odoo container — this is a cold start, rollback unavailable"
fi

NEW="${IMAGE_BASE}:${SHA}"

# ── Bring the working tree to the exact commit being deployed ─────────────────
# The compose file, odoo.prod.conf and this script must match the image. The
# application code itself is IN the image, not here.
log "checking out ${SHA}"
if [[ "$(git rev-parse HEAD)" != "$SHA" ]]; then
  # HTTPS rather than an ssh remote. This runs under sudo; root has no GitHub
  # key, so an SSH fetch fails with "Host key verification failed". The repo is
  # public, so HTTPS needs no credentials — and the VM needs no deploy key.
  # Idempotent, so a hand-run deploy self-heals a remote someone changed.
  git remote set-url origin "${REPO_URL:-https://github.com/Cleardeals/Odoo-HRMS.git}"

  # --depth 1 is REQUIRED, not an optimisation. The checkout is a shallow clone
  # (confirmed: .git/shallow exists, .git is 228MB), and a plain `git fetch` on a
  # shallow repo UNSHALLOWS it, pulling the whole history of a vendored Odoo
  # fork. Measured on the CRM VM: .git grew from 980MB to 5.3GB before the fetch
  # was killed, and it had not finished.
  #
  # The BRANCH is fetched, not the commit: GitHub refuses to serve an arbitrary
  # SHA here ("couldn't find remote ref"). The assertion below then confirms the
  # tree really is the commit that was built.
  git fetch --depth 1 --quiet origin "${DEPLOY_BRANCH:-main}"
  git reset --hard --quiet FETCH_HEAD
fi
# The checkout must be EXACTLY the commit that was built and tested. The
# pipeline fetches a branch tip, so if someone pushed to the branch between the
# build starting and the deploy running, the tip is no longer what was tested.
# Refuse rather than ship an untested tree alongside a tested image.
ACTUAL="$(git rev-parse HEAD)"
[[ "$ACTUAL" == "$SHA" ]] || die "checkout is $ACTUAL but the built commit is $SHA — the branch moved mid-build; refusing to deploy"

# ── Config from Secret Manager into tmpfs ─────────────────────────────────────
# Needs secretmanager.secretAccessor AND the cloud-platform scope on the
# instance. Both arrive in the Phase 4b window; before that this step is the one
# that will fail, loudly, which is correct — Odoo must never start with a
# missing config, because its built-in defaults include list_db = True.
log "rendering config"
bash scripts/render_odoo_conf.sh || die "config render failed — refusing to start Odoo with no config"

# ── Swap the image ────────────────────────────────────────────────────────────
# Docker needs a credential helper to pull from Artifact Registry. Without it
# the pull fails with "denied: Unauthenticated request" — the daemon does not
# use the VM's service account by itself. Configured here rather than assumed as
# VM state, so a rebuilt or replaced VM works with no manual step. Idempotent.
log "configuring the Artifact Registry credential helper"
gcloud auth configure-docker "${REGISTRY}" --quiet >/dev/null 2>&1 \
  || die "could not configure the docker credential helper for ${REGISTRY}"

log "pulling ${NEW}"
docker compose pull odoo || die "cannot pull $NEW"

# Rewrite ONLY the ODOO_IMAGE line, preserving every other key.
#
# This must never become `echo "ODOO_IMAGE=..." > .env`, which truncates the
# file and silently deletes every other variable on every deploy. On the CRM
# instance that made .env unusable for per-host runtime configuration and nobody
# could tell why their setting kept vanishing.
set_env_image() {
  local image="$1" tmp
  tmp="$(mktemp "${APP_DIR}/.env.XXXXXX")" || die "cannot create temp .env"
  if [[ -f .env ]]; then
    grep -v '^ODOO_IMAGE=' .env >> "${tmp}" || true
  fi
  echo "ODOO_IMAGE=${image}" >> "${tmp}"
  chmod 600 "${tmp}"
  mv -f "${tmp}" .env || die "cannot update .env"
}

set_env_image "${NEW}"

# ── Optional module upgrade ───────────────────────────────────────────────────
# A release that changes a module's schema has to run Odoo's own upgrade before
# the new code starts serving. Without it the container comes up with new Python
# against an old schema, and the failure surfaces later as a missing column in
# somebody's request rather than here, where it can still be stopped.
#
# Deliberately opt-in. Every ordinary deploy must stay exactly as fast and as
# boring as it is today, so this does nothing at all unless asked:
#
#   * ODOO_UPGRADE_MODULES=hr_employee_shift  — for a hand-run deploy;
#   * a one-shot request file (.deploy-upgrade in the app dir) — for a deploy
#     driven by Cloud Build, which has no way to pass an environment variable
#     through the trigger. The operator writes the file before approving the
#     build, and it is consumed on success so the next deploy is ordinary again.
#
# Ordering matters: this runs while the OLD container is still serving, using
# the NEW image (already pulled). If it fails we die here, the image is never
# swapped, and the old container keeps running against the schema it was built
# for — the one combination that is definitely consistent.
#
# `run --rm --no-deps` starts a throwaway container on the new image. --no-deps
# so it cannot restart the db container underneath a live Odoo.
UPGRADE_FILE="${UPGRADE_FILE:-${APP_DIR}/.deploy-upgrade}"
UPGRADE_MODULES="${ODOO_UPGRADE_MODULES:-}"
if [[ -z "${UPGRADE_MODULES}" && -f "${UPGRADE_FILE}" ]]; then
  UPGRADE_MODULES="$(tr -d '[:space:]' < "${UPGRADE_FILE}" || true)"
  [[ -n "${UPGRADE_MODULES}" ]] && log "upgrade requested by ${UPGRADE_FILE}"
fi

if [[ -n "${UPGRADE_MODULES}" ]]; then
  log "upgrading modules on ${NEW}: ${UPGRADE_MODULES}"
  # No timeout wrapper: an upgrade over a large table can legitimately take
  # many minutes, and killing one halfway is far worse than waiting.
  docker compose run --rm --no-deps odoo \
      odoo -c /etc/odoo/odoo.conf \
           -u "${UPGRADE_MODULES}" \
           --stop-after-init \
    || die "module upgrade failed; image NOT swapped, ${PREV:-current} still serving"
  log "module upgrade finished"
  # Consumed only on success, so a failed deploy can simply be retried.
  rm -f "${UPGRADE_FILE}"
fi

log "starting"
docker compose up -d odoo

# ── Health gate ───────────────────────────────────────────────────────────────
# A BARE /web/health IS NOT A HEALTH CHECK. Read the route in
# addons/web/controllers/home.py:177: it returns 200 {"status":"pass"} without
# touching the database unless db_server_status is passed. A gate polling the
# bare path goes green with Postgres down and then reports a successful deploy.
#
# db_server_status=1 makes the route open a real cursor and return HTTP 500 on
# psycopg2.Error; /web/login additionally proves the registry loaded and the
# modules initialised.
healthy() {
  docker compose exec -T odoo curl -fsS \
      "http://localhost:8069/web/health?db_server_status=1" 2>/dev/null \
    | grep -q '"status": *"pass"' \
  && docker compose exec -T odoo curl -fsS -o /dev/null \
      "http://localhost:8069/web/login" 2>/dev/null
}

log "waiting for health (up to ${HEALTH_TIMEOUT}s)"
deadline=$(( SECONDS + HEALTH_TIMEOUT ))
odoo_ok=false
while (( SECONDS < deadline )); do
  if healthy; then odoo_ok=true; break; fi
  sleep 5
done

# ── Rollback ──────────────────────────────────────────────────────────────────
if [[ "$odoo_ok" != true ]]; then
  log "health check FAILED after ${HEALTH_TIMEOUT}s"
  docker compose logs --tail=50 odoo 2>&1 | sed 's/^/    /' >&2

  if [[ -z "$PREV" ]]; then
    die "no previous image to roll back to — leaving the failed container for inspection"
  fi

  log "rolling back to ${PREV}"
  set_env_image "${PREV}"
  docker compose up -d odoo

  # NOTE: this restores the IMAGE. It does not undo a schema migration — those
  # are not reversible by re-pinning a tag. A deploy that ran migrations and then
  # failed its health check needs the pre-deploy dump, not this path.
  die "deploy of ${SHA} failed health check; rolled back to ${PREV}"
fi

log "Odoo is healthy on ${SHA}; checking the public path"

# ── Edge gate ─────────────────────────────────────────────────────────────────
# EVERY CHECK ABOVE THIS LINE ASKS ODOO ABOUT ITSELF, FROM INSIDE ITS OWN
# CONTAINER. That is a real gate for "did the image boot and load the registry",
# and a complete blind spot for "can a user reach the site".
#
# The blind spot is not hypothetical. On the CRM instance, Traefik's docker
# provider died on a client/daemon API mismatch, so it discovered no containers
# and served 404 for every request — while Odoo sat behind it perfectly healthy,
# answering the checks above. The deploy went green and the site was down.
#
# So this asks the question from the outside in, over the same path a browser
# takes: TLS on 443, SNI and Host set to the public name, routed by Traefik,
# proxied to Odoo, 200 back.
#
# --resolve pins that hostname to the loopback address instead of using DNS.
# Two reasons: the check must test THIS host rather than whatever the public
# record currently points at, and it must not depend on the VM being able to
# reach its own external address. The Host header and SNI still carry the real
# name, so Traefik's router matches and the certificate validates normally.
#
# IT MUST SPEAK TLS. The http->https redirect is configured on the ENTRYPOINT
# and runs BEFORE routing, so a probe on port 80 returns 301 even for a hostname
# that matches no router — it would pass straight through a total routing
# outage. Verified on the CRM stack: port 80 returned 301 for an unmatched host
# while the TLS path correctly returned 404.
edge_healthy() {
  curl -fsS -o /dev/null --max-time 10 \
    --resolve "${EDGE_HOST}:443:127.0.0.1" \
    "https://${EDGE_HOST}/web/login" 2>/dev/null
}

edge_ok=false
edge_deadline=$(( SECONDS + EDGE_TIMEOUT ))
while (( SECONDS < edge_deadline )); do
  if edge_healthy; then edge_ok=true; break; fi
  sleep 3
done

if [[ "$edge_ok" != true ]]; then
  # DELIBERATELY NO ROLLBACK HERE.
  #
  # Odoo has already proven itself healthy on the new image, so re-pinning the
  # previous tag cannot fix a broken edge — it would just be a second unplanned
  # change made while somebody is trying to diagnose the first, and it would
  # leave production running older code for a fault that has nothing to do with
  # the code. The right response is to fail loudly and hand over the evidence.
  log "EDGE CHECK FAILED: Odoo is healthy, but ${EDGE_HOST} does not serve through Traefik"
  log "the image is fine — do NOT roll it back; this is the proxy or the routing"
  log ""
  log "check, in order:"
  log "  1. is the odoo container attached to the 'web' network"
  log "  2. is Traefik running, and is its docker provider alive"
  log "  3. does EDGE_HOST still match the Host() rule in docker-compose.yml"
  log ""
  # Diagnostics stay on STDOUT, unlike the rollback path above which sends
  # container logs to stderr. Both streams end up in the same Cloud Build log,
  # but they are flushed independently, so mixing them reorders the output. When
  # the whole point is to hand a human a readable trail, ordering is part of the
  # diagnostic.
  log "--- traefik logs ---"
  docker compose logs --tail=50 traefik 2>&1 | sed 's/^/    /' || true
  log "--- routers Traefik currently knows about ---"
  # ZERO routers here is the signature of the provider-death failure: Traefik
  # alive and answering, but its docker provider dead, so nothing is routed
  # anywhere. A healthy HRMS stack reports 5.
  curl -fsS --max-time 5 http://127.0.0.1:8080/api/rawdata 2>/dev/null \
    | python3 -c 'import json,sys; print("    routers:", len(json.load(sys.stdin).get("routers",{})))' 2>/dev/null \
    || log "    (dashboard unreachable — Traefik itself is likely the problem)"
  die "deploy of ${SHA} is live on Odoo but not reachable at ${EDGE_HOST}"
fi

log "HEALTHY on ${SHA} (odoo + edge)"

# ── Reclaim disk ──────────────────────────────────────────────────────────────
# `docker image prune -f` removes DANGLING images only, and an image this
# pipeline pushed is never dangling: every build tags it twice, with the short
# and the full commit SHA. So each deploy would otherwise leave another ~1GB
# tagged image behind forever, and nothing would remove it.
#
# That is not a tidiness problem on this host. The disk is 30GB and was 74% full
# before Phase 0c reclaimed ~8GB of uncapped journal, a stale containerd image
# store and agent logs. A full disk here is not a degraded service but a stopped
# one — Postgres cannot write, Odoo cannot write, and the deploy that would fix
# it cannot pull an image.
#
# ── WHY NOT `docker image prune -a --filter until=...` ───────────────────────
#
# Because it would delete the rollback target. That command removes every image
# not currently used by a container, and the moment the new image is running,
# PREV is used by nothing. An age filter does not save it either: the previous
# image is exactly as old as whenever it was built, which on a quiet month is
# older than any sensible window. The obvious one-liner silently destroys the
# ability to roll back, and does it on the deploy where nothing appeared wrong.
#
# So retention is by COUNT, not age. `docker images` lists newest first; keep
# that many distinct image IDs and delete the rest. Deduplication is on the
# image ID rather than the tag, because the two tags per build point at ONE
# image and counting tags would silently halve the depth.
#
# 3 rather than the CRM's 5: this disk is 30GB, not 60GB. Measured, a freshly
# built HRMS image is ~1.0GB (the 3.12GB odoo-hrms:latest currently on the VM
# accumulated from somewhere else), so 3 keeps the running image, the rollback
# target, and one more to fall further back to.
#
# Docker refuses to delete an image that a RUNNING container uses, even with -f,
# so the live image is protected by the daemon regardless of what this computes.
IMAGE_KEEP="${IMAGE_KEEP:-3}"
prune_images() {
  local ids=() id
  # Dedupe while preserving docker's newest-first ordering.
  while read -r id; do
    [[ -n "$id" ]] && ! printf '%s\n' "${ids[@]:-}" | grep -qx "$id" && ids+=("$id")
  done < <(docker images "${IMAGE_BASE}" --format '{{.ID}}' 2>/dev/null)

  (( ${#ids[@]} > IMAGE_KEEP )) || { log "images: ${#ids[@]} resident, keeping ${IMAGE_KEEP} — nothing to prune"; return 0; }

  local removed=0
  for id in "${ids[@]:$IMAGE_KEEP}"; do
    if docker rmi -f "$id" >/dev/null 2>&1; then
      removed=$((removed + 1))
    else
      # Almost always "image is being used by running container", which is the
      # daemon protecting something this should not have selected. Worth a line
      # in the log rather than silence.
      log "images: could not remove ${id} (in use?) — left in place"
    fi
  done
  log "images: ${#ids[@]} resident, kept ${IMAGE_KEEP}, removed ${removed}"
}

prune_images || true
docker image prune -f >/dev/null 2>&1 || true      # dangling leftovers
docker builder prune -f --filter "until=168h" >/dev/null 2>&1 || true
log "disk: $(df -h / | awk 'NR==2 {print $5" used, "$4" free"}')"

exit 0
