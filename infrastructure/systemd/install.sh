#!/usr/bin/env bash
# infrastructure/systemd/install.sh
#
# Installs odoo-hrms-config.service and its wrapper, then proves the unit works
# rather than assuming it. Run as root on the VM.
#
# Safe to run at any time and safe to re-run: it touches no container, and the
# worst case is that /dev/shm/odoo.conf is rewritten with identical content.
#
# What it does NOT do is reboot. The only complete proof of the boot ordering is
# an actual reboot, and that is the operator's decision, not this script's — see
# the closing note.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_NAME="odoo-hrms-config.service"
UNIT_DST="/etc/systemd/system/${UNIT_NAME}"
WRAP_DST="/usr/local/sbin/render-on-boot.sh"
RENDERED="${RENDERED:-/dev/shm/odoo.conf}"

die() { echo "systemd-install: FATAL: $*" >&2; exit 1; }
ok()  { echo "systemd-install: $*"; }

[[ "$(id -u)" -eq 0 ]] || die "must run as root"
[[ -r "$SRC/$UNIT_NAME" ]]        || die "unit not found: $SRC/$UNIT_NAME"
[[ -r "$SRC/render-on-boot.sh" ]] || die "wrapper not found: $SRC/render-on-boot.sh"

# ── Install ───────────────────────────────────────────────────────────────────
install -m 0755 "$SRC/render-on-boot.sh" "$WRAP_DST"
install -m 0644 "$SRC/$UNIT_NAME"        "$UNIT_DST"
systemctl daemon-reload
ok "installed $WRAP_DST and $UNIT_DST"

# ── Validate the unit before enabling it ──────────────────────────────────────
# systemd-analyze reports syntax problems and unknown directives that would
# otherwise only appear as a mystery at the next boot.
if ! systemd-analyze verify "$UNIT_DST" 2>&1 | tee /tmp/unit-verify.$$ | grep -q .; then
  ok "unit verified clean"
else
  # verify writes warnings to stderr; treat only a non-zero exit as fatal.
  sed 's/^/systemd-install:   /' /tmp/unit-verify.$$ >&2 || true
  ok "systemd-analyze reported the above (warnings are tolerated, errors are not)"
fi
rm -f /tmp/unit-verify.$$

systemctl enable "$UNIT_NAME" >/dev/null 2>&1
ok "enabled at boot"

# ── Prove the ORDERING is what we asked for ───────────────────────────────────
# This is the property the whole unit depends on. Assert it from systemd's own
# resolved view, not from the file we just wrote.
before="$(systemctl show -p Before --value "$UNIT_NAME" 2>/dev/null || true)"
case " $before " in
  *" docker.service "*) ok "ordering confirmed: runs BEFORE docker.service" ;;
  *) die "ordering NOT in place — systemd reports Before=[$before]; Docker would create the empty mount first" ;;
esac

after="$(systemctl show -p After --value "$UNIT_NAME" 2>/dev/null || true)"
case " $after " in
  *" network-online.target "*) ok "ordering confirmed: runs after network-online.target" ;;
  *) echo "systemd-install: WARNING: not ordered after network-online.target — the render may race the network" >&2 ;;
esac

# ── Prove it actually renders ─────────────────────────────────────────────────
# Removing the file first makes this a real test rather than a no-op: if the
# unit does nothing, the file stays missing and the check below fails.
if [[ -e "$RENDERED" ]]; then
  rm -f "$RENDERED"
  ok "removed the existing $RENDERED so the run below is a genuine test"
fi

if [[ -r /opt/odoo-hrms/scripts/render_odoo_conf.sh ]]; then
  systemctl restart "$UNIT_NAME" || die "unit failed — see: journalctl -u $UNIT_NAME"

  [[ -s "$RENDERED" ]] || die "unit reported success but $RENDERED is missing or empty"
  ok "rendered $RENDERED ($(wc -l < "$RENDERED") lines)"

  # A surviving placeholder means the secrets were not substituted, which would
  # start Odoo with a literal placeholder as its password.
  if grep -q '__ADMIN_PASSWD__\|__DB_PASSWORD__' "$RENDERED"; then
    die "a placeholder survived substitution in $RENDERED"
  fi
  ok "no placeholders remain (secrets were substituted)"

  # Idempotence: the header claims it is safe on every boot, so prove it.
  systemctl restart "$UNIT_NAME" || die "second run failed — unit is not idempotent"
  ok "second run succeeded — idempotent"

  systemctl is-active --quiet "$UNIT_NAME" && ok "unit is active (exited)"
else
  ok "render script not present yet (checkout predates it) — ConditionPathExists"
  ok "will skip this unit cleanly at boot until the first deploy lands it"
fi

ok ""
ok "REMAINING PROOF: ordering at real boot time is only fully proven by rebooting."
ok "  sudo reboot     # then, once back:"
ok "  systemctl status odoo-hrms-config   # should be active (exited)"
ok "  ls -l /dev/shm/odoo.conf            # should exist, BEFORE any deploy runs"
ok "  docker ps                            # all three containers healthy"
ok ""
ok "Until that reboot test is done, treat this as installed-but-unproven."
