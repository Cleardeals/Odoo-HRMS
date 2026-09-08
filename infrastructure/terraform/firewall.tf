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

# ── TO BE DELETED IN PHASE 5 ───────────────────────────────────────────────────
# Imported so that the current state is recorded and the deletion is a reviewable
# diff rather than an undocumented console action.

# tcp:22 from 0.0.0.0/0 at the default-ish priority, UNTAGGED, so it applies to
# every VM in the project, present and future.
#
# SUPERSEDED IN PHASE 5 by an allow-iap-ssh rule scoped to 35.235.240.0/20 —
# Google's fixed IAP TCP-forwarding range. That is the whole point: SSH stops
# being reachable from the internet at all, every connection is brokered by IAP
# which authenticates the caller against IAM BEFORE a packet reaches sshd, and
# access is granted and revoked purely through IAM. There is then no key on the
# host to forget to remove when somebody leaves.
#
# Already verified working on this project, which is why the plan can commit to
# it: developer1@ and developer2@ hold roles/iap.tunnelResourceAccessor and
# roles/compute.osLogin, and an IAP-tunnelled session to this VM succeeds today.
resource "google_compute_firewall" "default_allow_ssh" {
  name    = "default-allow-ssh"
  project = var.project_id
  network = "default"

  # Live value. Omitting it plans its removal.
  description = "Allow SSH from anywhere"

  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# tcp:3389 from 0.0.0.0/0. Nothing in this project runs Windows and nothing
# listens on 3389. Deleted outright in Phase 5.
resource "google_compute_firewall" "default_allow_rdp" {
  name    = "default-allow-rdp"
  project = var.project_id
  network = "default"

  # Live value. Omitting it plans its removal.
  description = "Allow RDP from anywhere"

  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["3389"]
  }
}

# ── The two health-check rules: ALL TCP, for a load balancer that never existed ─
#
# These permit EVERY TCP PORT from Google's health-check ranges to any instance
# tagged lb-health-check — and odoo-hrms-prod carries that tag (compute.tf).
#
# Verified before calling them dead: the project has ZERO forwarding rules and
# ZERO target pools. There is no load balancer, so there is nothing performing
# these health checks.
#
# This is not world-open, so it is not an emergency. It is a live, unnecessary
# path to every port on the box — including Postgres and the Traefik admin API —
# and a rule that grants nothing needed is worse than useless: it is read as
# load-bearing by the next person to touch it. Deleted in Phase 5 along with the
# instance tag, in one change.
resource "google_compute_firewall" "default_allow_health_check" {
  name    = "default-allow-health-check"
  project = var.project_id
  network = "default"

  direction = "INGRESS"
  priority  = 1000
  source_ranges = [
    "35.191.0.0/16",
    "130.211.0.0/22",
    "209.85.152.0/22",
    "209.85.204.0/22",
  ]
  target_tags = ["lb-health-check"]

  allow {
    protocol = "tcp"
  }
}

resource "google_compute_firewall" "default_allow_health_check_ipv6" {
  name    = "default-allow-health-check-ipv6"
  project = var.project_id
  network = "default"

  direction = "INGRESS"
  priority  = 1000
  source_ranges = [
    "2600:1901:8001::/48",
    "2600:2d00:1:b029::/64",
  ]
  target_tags = ["lb-health-check"]

  allow {
    protocol = "tcp"
  }
}
