#!/usr/bin/env bash
# scripts/render_odoo_conf.sh
#
# Assembles the runtime Odoo config from the committed template plus the two
# secrets held in Secret Manager, and writes the result to TMPFS.
#
# Why tmpfs: /dev/shm is memory-backed, so the assembled file — the only place
# where the config and the secrets exist together — never touches the persistent
# disk, and therefore never appears in a disk snapshot. Snapshots of this VM are
# taken daily (moving to 4-hourly in Phase 7) and kept for 14 days.
#
# Why a render step at all, rather than environment variables: Odoo reads its
# config with Python's ConfigParser, which does not interpolate the environment.
# A ${VAR} left in the file reaches Odoo verbatim.
#
# Runs on the HOST, before `docker compose up`. The compose file bind-mounts the
# rendered path in read-only.
#
# REQUIREMENTS ON THE VM. This needs BOTH:
#   * roles/secretmanager.secretAccessor on the attached service account, and
#   * the cloud-platform OAuth scope on the instance.
# Scopes are a hard ceiling above IAM: the role alone is not enough if the
# access token cannot carry it. The HRMS VM has neither until the Phase 4b
# window, so this script is committed before it can succeed — deliberately, so
# that the code is reviewed before it is load-bearing.
#
# Idempotent: safe to re-run at any time, including on every boot.

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TEMPLATE="${TEMPLATE:-$REPO_DIR/odoo.prod.conf}"
RENDERED="${RENDERED:-/dev/shm/odoo.conf}"

die() { echo "render_odoo_conf: $*" >&2; exit 1; }

[[ -r "$TEMPLATE" ]] || die "template not readable: $TEMPLATE"

command -v gcloud >/dev/null 2>&1 || die "gcloud not on PATH"

fetch() {
  local name="$1" value
  value="$(gcloud secrets versions access latest --secret="$name" 2>/dev/null)" \
    || die "cannot read secret '$name' — check secretmanager.secretAccessor on the VM's service account AND that the instance has the cloud-platform scope"
  [[ -n "$value" ]] || die "secret '$name' is empty"
  printf '%s' "$value"
}

ADMIN_PASSWD="$(fetch odoo-admin-passwd)"
DB_PASSWORD="$(fetch odoo-db-password)"

# A '%' in either value would break ConfigParser interpolation at Odoo startup,
# with an error that says nothing about passwords. Escape it as '%%' rather than
# failing, so a rotation that picks an awkward character is survivable.
ADMIN_PASSWD="${ADMIN_PASSWD//%/%%}"
DB_PASSWORD="${DB_PASSWORD//%/%%}"

# Written via a temp file in the same tmpfs and moved into place, so a reader
# never sees a half-written config.
TMP="$(mktemp "${RENDERED}.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
chmod 600 "$TMP"

# Substitution is done in the shell rather than with sed, because the values are
# untrusted-by-construction random strings: sed would interpret &, \ and the
# delimiter inside a replacement.
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line//__ADMIN_PASSWD__/$ADMIN_PASSWD}"
  line="${line//__DB_PASSWORD__/$DB_PASSWORD}"
  printf '%s\n' "$line"
done < "$TEMPLATE" > "$TMP"

grep -q '__ADMIN_PASSWD__\|__DB_PASSWORD__' "$TMP" \
  && die "a placeholder survived substitution — refusing to start with a literal placeholder as a password"

# Odoo runs as uid 101 in the container and must be able to read the mount.
chmod 644 "$TMP"
mv -f "$TMP" "$RENDERED"
trap - EXIT

echo "render_odoo_conf: wrote $RENDERED ($(wc -l < "$RENDERED") lines, secrets injected)"
