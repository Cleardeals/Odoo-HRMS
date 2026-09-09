#!/usr/bin/env bash
# infrastructure/systemd/render-on-boot.sh
#
# Wrapper that odoo-hrms-config.service runs at boot. It exists only to add
# retries around scripts/render_odoo_conf.sh.
#
# WHY RETRIES. The render reads Secret Manager, which needs the network, the
# metadata server, and a working token. At boot those arrive in that order and
# not instantly, and `network-online.target` means "an interface has an
# address", not "Google's APIs answer". A single attempt at T+0 fails often
# enough to matter, and the cost of that failure is the whole point of this
# unit — Odoo starting with no configuration.
#
# It deliberately does NOT retry forever: docker.service is ordered after this
# unit, so every second spent here is a second production is down. Six attempts
# over roughly a minute is the compromise.

set -uo pipefail

APP_DIR="${APP_DIR:-/opt/odoo-hrms}"
SCRIPT="${SCRIPT:-$APP_DIR/scripts/render_odoo_conf.sh}"
ATTEMPTS="${ATTEMPTS:-6}"
SLEEP="${SLEEP:-10}"

log() { echo "render-on-boot: $*"; }

if [[ ! -x "$SCRIPT" && ! -r "$SCRIPT" ]]; then
  # Not an error. Before the first Cloud Build deploy the VM's checkout predates
  # these scripts, and this unit is installed ahead of that deliberately so the
  # protection is in place BEFORE the deploy that starts relying on tmpfs.
  log "no render script at $SCRIPT yet — nothing to do (expected before the first deploy)"
  exit 0
fi

for i in $(seq 1 "$ATTEMPTS"); do
  if bash "$SCRIPT"; then
    log "config rendered on attempt $i"
    exit 0
  fi
  log "attempt $i/$ATTEMPTS failed"
  [[ "$i" -lt "$ATTEMPTS" ]] && sleep "$SLEEP"
done

# Loud, because the consequence is not obvious from anywhere else. Odoo will
# start on its built-in defaults: db_host empty, so it connects to a local unix
# socket that does not exist in its container and cannot reach Postgres at all.
# The site will be down, and Phase 7's P1 uptime alert is what reports it.
log "FATAL: could not render $APP_DIR config after $ATTEMPTS attempts."
log "Odoo will start WITHOUT a configuration file and will not reach its database."
log "Fix: run '$SCRIPT' by hand, then 'docker compose up -d' in $APP_DIR."
exit 1
