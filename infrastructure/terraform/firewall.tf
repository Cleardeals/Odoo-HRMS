# infrastructure/terraform/firewall.tf
#
# All eight live rules, imported EXACTLY as they are — including the four that
# should not exist. Phase 5 removes those, and does it after IAP has been proven
# for both callers, not before.
#
# The order matters and is not caution for its own sake. On the CRM instance the
# auth log showed real, recent, successful logins arriving DIRECTLY on the public
# address under legacy metadata keys, not through the tunnel. Deleting the
# world-open SSH rule first would have cut the only path anyone was using.
#
# HRMS has five never-expiring keys in project metadata and five human home
# directories on the box, so the same check applies here with more force: read
# /var/log/auth.log and find out who is actually connecting, and how, before
# deleting default-allow-ssh.

# ── What actually serves production ────────────────────────────────────────────
# These two are correct and stay. They work via the http-server / https-server
# tags on the instance in compute.tf, so do not remove those tags without
# revisiting this file.

resource "google_compute_firewall" "default_allow_http" {
  name    = "default-allow-http"
  project = var.project_id
  network = "default"

  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
}

# Port 80 is not redundant with 443 here, and should not be "tidied away":
# Traefik's ACME tlsChallenge resolver needs it reachable from the internet to
# renew the certificate. Closing it turns a working renewal into a silent
# expiry, which is what Phase 7's P4 alert exists to catch.
resource "google_compute_firewall" "default_allow_https" {
  name    = "default-allow-https"
  project = var.project_id
  network = "default"

  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["https-server"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

# ── Project defaults that stay ─────────────────────────────────────────────────

resource "google_compute_firewall" "default_allow_icmp" {
  name    = "default-allow-icmp"
  project = var.project_id
  network = "default"

  # Live value. Omitting it plans its removal.
  description = "Allow ICMP from anywhere"

  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "icmp"
  }
}

# Kept, but note what it permits: ALL TCP and UDP between instances in the VPC.
# On the CRM project this is what made an unauthenticated Traefik admin API,
# published on 0.0.0.0:8080, readable from another VM — confirmed by fetching the
# full routing configuration across instances. HRMS publishes that same
# dashboard the same way (docker-compose.yml), which Phase 3 narrows to
# loopback. This rule is the reason that narrowing matters even with no firewall
# rule admitting 8080 from the internet.
resource "google_compute_firewall" "default_allow_internal" {
  name    = "default-allow-internal"
  project = var.project_id
  network = "default"

  # Live value. Omitting it plans its removal.
  description = "Allow internal traffic on the default network"

  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["10.128.0.0/9"]

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }
}

# ── PHASE 5: THE REPLACEMENT PATH ─────────────────────────────────────────────
#
# Applied FIRST, on its own, and verified before anything is deleted. Adding the
# new path and removing the old one in a single apply would mean discovering any
# mistake with no way back in — so this is deliberately two applies.
#
# 35.235.240.0/20 is Google's fixed IAP TCP-forwarding range. It is not a range
# an attacker can source from: traffic only leaves it after IAP has authenticated
# the caller against IAM, so reaching sshd at all now requires
# roles/iap.tunnelResourceAccessor plus an OS Login role. Authorisation happens
# before the first packet, rather than being sshd's problem.
#
# EVIDENCE THIS IS SAFE, gathered from /var/log/auth.log before the change
# (74 real successful logins across ~3 weeks of retained logs):
#
#   * 59 arrived from the IAP range — all recent and ongoing.
#   * 15 arrived directly, from one ISP address, ALL within a 15-minute window on
#     2026-08-20, and nothing since. Direct SSH has been unused for 20 days.
#   * 45,540 failed attempts from 1,291 distinct source addresses. That is what
#     the world-open rule was actually serving.
#
# The count above needed a second pass to be trustworthy: grepping for
# "Accepted" also matches "PubkeyAcceptedAlgorithms", which inflated the
# non-IAP figure roughly tenfold and would have made direct SSH look actively
# used. Anchor on "Accepted publickey for ".
#
# Both consumers were proven over IAP before the deletion, not assumed:
#   * the operator, interactively, throughout this migration;
#   * hrms-cloudbuild@, by impersonation — it lands as POSIX user
#     sa_115156691799848533571 and has working sudo. Worth knowing for that
#     test: roles/owner does NOT include iam.serviceAccounts.getAccessToken
#     (actAs yes; getAccessToken, signBlob and implicitDelegation are all
#     absent from the basic roles), so a temporary resource-scoped
#     serviceAccountTokenCreator binding was needed, and IAM took 60 seconds to
#     propagate — the first three attempts failed misleadingly.
resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "allow-iap-ssh"
  project = var.project_id
  network = "default"

  description = "Allow SSH only from Google's IAP TCP forwarding range"

  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["35.235.240.0/20"]

  # Untagged, matching the rule it replaces, so a future instance in this
  # project is reachable by the operator without remembering to tag it. The
  # range itself is the restriction.

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# ── DELETED IN PHASE 5, 2026-09-09 ────────────────────────────────────────────
#
# Four rules removed. They are recorded here rather than silently dropped,
# because "why is there no SSH rule" is a question someone will ask, and the
# answer is above: allow-iap-ssh replaced it.
#
#   default-allow-ssh               tcp:22   from 0.0.0.0/0, UNTAGGED
#   default-allow-rdp               tcp:3389 from 0.0.0.0/0, UNTAGGED
#   default-allow-health-check      ALL TCP  from Google LB ranges, tag lb-health-check
#   default-allow-health-check-ipv6 ALL TCP  from Google LB v6 ranges, same tag
#
# WHY EACH ONE WENT.
#
# default-allow-ssh — replaced by allow-iap-ssh. It was untagged, so it applied
# to every VM in the project, present and future, and it was carrying 45,540
# failed authentication attempts from 1,291 distinct addresses. Removing it does
# not remove access; it moves access from "anyone who can reach port 22 and
# holds a key" to "anyone IAM says may connect".
#
# default-allow-rdp — nothing in this project runs Windows and `ss -tlnp`
# confirmed nothing listens on 3389. A rule that admits traffic to a port
# nothing serves is pure attack surface with no compensating function.
#
# The two health-check rules — these permitted EVERY TCP PORT from Google's
# health-check ranges to anything tagged lb-health-check, and odoo-hrms-prod
# carried that tag. Every port includes Postgres on 5432 and Traefik's admin API
# on 8080, both of which are otherwise bound to loopback or the internal network.
#
# Verified dead before deleting, not assumed: the project has ZERO forwarding
# rules and ZERO target pools. There is no load balancer, so nothing was
# performing these checks and nothing depended on them.
#
# A rule that grants nothing needed is worse than useless, because the next
# person to look at it reads it as load-bearing and leaves it alone. The
# lb-health-check tag was removed from the instance in compute.tf in the same
# change, so no orphan tag is left implying a load balancer exists.
#
# ROLLBACK: firewall rules are Compute API calls with no state of their own. Any
# of these can be recreated from an authenticated machine in under a minute, and
# losing SSH does not mean losing the instance.
