#!/usr/bin/env bash
# infrastructure/ops-agent/install.sh
#
# Installs infrastructure/ops-agent/config.yaml onto this VM and restarts the
# Ops Agent. Run as root.
#
# This does NOT touch Odoo, Postgres or Traefik. The worst case is that the Ops
# Agent stops, which costs observability and nothing else — so it is safe to run
# outside a maintenance window. Even so, it validates before applying and rolls
# back automatically if the agent does not come back.
#
# ORDERING: run this AFTER Phase 4b has attached hrms-prod-vm@. Before that the
# agent has no permission to write anything, and the final check below will
# correctly refuse.

set -euo pipefail

SRC="${SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/config.yaml}"
DST="${DST:-/etc/google-cloud-ops-agent/config.yaml}"
ENGINE=/opt/google-cloud-ops-agent/libexec/google_cloud_ops_agent_engine

die() { echo "ops-agent: FATAL: $*" >&2; exit 1; }
ok()  { echo "ops-agent: $*"; }

[[ "$(id -u)" -eq 0 ]] || die "must run as root"
[[ -r "$SRC" ]]        || die "config not readable: $SRC"
[[ -x "$ENGINE" ]]     || die "ops agent engine not found at $ENGINE — is the agent installed?"

# ── Validate BEFORE touching the live file ────────────────────────────────────
# The engine renders the merged configuration and runs its startup checks. A
# malformed config fails here rather than after the agent has been stopped.
tmp_out="$(mktemp -d)"
trap 'rm -rf "$tmp_out"' EXIT
"$ENGINE" -in "$SRC" -out "$tmp_out" -logs "$tmp_out" >/dev/null 2>&1 \
  || die "config failed validation — not installing"
ok "candidate config validated"

# ── Install, keeping a timestamped backup ─────────────────────────────────────
backup="${DST}.$(date -u +%Y%m%d-%H%M%S).bak"
if [[ -f "$DST" ]]; then
  cp -a "$DST" "$backup"
  ok "backed up existing config to $backup"
fi
install -m 0644 "$SRC" "$DST"
ok "installed $SRC -> $DST"

# ── Restart, and roll back if it does not come up ────────────────────────────
systemctl restart google-cloud-ops-agent
sleep 8

if ! systemctl is-active --quiet google-cloud-ops-agent; then
  echo "ops-agent: agent did NOT come back — rolling back" >&2
  if [[ -f "$backup" ]]; then
    install -m 0644 "$backup" "$DST"
    systemctl restart google-cloud-ops-agent || true
  fi
  die "rolled back to the previous config"
fi

ok "agent active"

# ── Prove it is actually SHIPPING, not merely running ────────────────────────
#
# This check is the entire point of the script, and it is not paranoia. On this
# VM the agent has been "active" and "enabled" for months while dropping every
# batch it collected, because the attached service account held no IAM roles at
# all. `systemctl is-active` was true the whole time and told nobody anything.
#
# ~120 PermissionDenied entries per 20 minutes was the measured baseline before
# the Phase 4b service-account swap. This must be 0.
errs="$(journalctl -u google-cloud-ops-agent-opentelemetry-collector \
        --since '1 min ago' --no-pager 2>/dev/null \
        | grep -ci 'PermissionDenied' || true)"
[[ "$errs" == "0" ]] || die "agent is running but reporting PermissionDenied ($errs) — the VM service account cannot write. Has Phase 4b attached hrms-prod-vm@, and does the instance have the cloud-platform scope?"

ok "no permission errors; container logs should appear in Cloud Logging shortly"
ok ""
ok "verify from a workstation — both of these returned nothing before this ran:"
ok "  gcloud logging read 'resource.type=\"gce_instance\"' --limit=5"
ok "  and agent.googleapis.com/disk/percent_used should have >0 time series"
ok ""
ok "DO NOT use 'os-inventory describe' as a check on this agent. It fails here"
ok "for an unrelated, project-level reason: VM Manager is on the BASIC feature"
ok "set (patchAndConfigFeatureSet = OSCONFIG_B), which disables OS inventory"
ok "project-wide. The osconfig API says so directly —"
ok "  FAILED_PRECONDITION: OS inventory management has been disabled"
ok "so the command reports nothing however healthy this agent is, and reading it"
ok "as an agent fault sends you looking in the wrong place. Confirm with:"
ok "  curl -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" \\"
ok "    https://osconfig.googleapis.com/v1/projects/<project>/locations/global/projectFeatureSettings"
ok ""
ok "then LIST THE REAL DEVICE LABELS before writing the disk alert in monitoring.tf:"
ok "  the filter must match what this host actually reports, not what was assumed"
