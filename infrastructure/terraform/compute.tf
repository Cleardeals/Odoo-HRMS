# infrastructure/terraform/compute.tf
# The HRMS VM, its disk, and its static address.
#
# Everything here was IMPORTED from infrastructure that already existed and had
# been managed by hand. The HCL was written to match what was already running —
# never the other way round. The gate for this phase is a completely EMPTY first
# plan; any diff means the code is wrong, not production.
#
# That separation is what makes the later phases reviewable. Several things in
# this file are, on the merits, wrong (see auto_delete below). They are imported
# as-is anyway, and changed in a second, deliberate apply. Fixing a resource
# during an import is how an import turns into an outage.

# ── Static address ─────────────────────────────────────────────────────────────
# IN_USE, and the address the public DNS record for var.public_host points at.
# Releasing it means losing it to the regional pool, so it is effectively
# permanent.

resource "google_compute_address" "prod" {
  name         = "odoo-hrms-production"
  project      = var.project_id
  region       = var.region
  address_type = "EXTERNAL"
}

# ── Boot disk ──────────────────────────────────────────────────────────────────
#
# Declared standalone rather than as an inline boot_disk with
# initialize_params, so the disk is a resource with its own identity and can
# outlive the instance. The instance below references it by source.
#
# NOTE the image is Debian 12 bookworm, not the Ubuntu 24.04 the CRM instance
# runs. This matters later: Debian has no snap packages, so the host reports no
# /dev/loopN squashfs mounts — which is the thing that would otherwise poison a
# naive disk-utilisation alert. Confirm the real device labels in Phase 6 rather
# than assuming either shape.

resource "google_compute_disk" "prod" {
  name    = "odoo-hrms-prod"
  project = var.project_id
  zone    = var.zone
  type    = "pd-balanced"
  size    = var.boot_disk_size_gb
  image   = "https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-12-bookworm-v20260210"

  physical_block_size_bytes = 4096

  lifecycle {
    # The image is the one the disk was CREATED from and is pure history — the
    # running system has been patched far past it. Without this, every provider
    # upgrade that changes image handling threatens to recreate the boot disk of
    # production.
    ignore_changes = [image, snapshot]
  }
}

# The snapshot schedule is attached through its OWN resource, not a field on the
# disk, matching the CRM module. Keeping the attachment separate is also what
# makes the Phase 7 swap to a 4-hourly schedule a two-line change rather than a
# disk modification.
#
# PHASE 7: this now points at the 4-hourly policy. A disk accepts only one
# snapshot schedule, so this is a replace — Terraform detaches the old policy
# and attaches the new one. Nothing about the disk or its data is touched, and
# snapshots already taken are unaffected.
resource "google_compute_disk_resource_policy_attachment" "prod_snapshot" {
  name    = google_compute_resource_policy.four_hourly_snapshot.name
  disk    = google_compute_disk.prod.name
  project = var.project_id
  zone    = var.zone
}

# ── Snapshot schedule — as imported ────────────────────────────────────────────
#
# Daily at 12:00 UTC, 14-day retention, attached to the disk and demonstrably
# working: six consecutive daily snapshots were confirmed before this was
# written.
#
# It is REPLACED in Phase 7 by a 4-hourly schedule with 30-day retention. That
# change is not primarily about the recovery point (though it moves worst-case
# data loss from 24 h to 4 h). It is what makes backup alerting possible at all:
# Cloud Monitoring refuses an absence condition longer than 23h30m, so against a
# DAILY schedule there is no usable window — consecutive snapshots are already
# 24 h apart, so any alert able to detect a stopped schedule also fires shortly
# before every healthy one.
resource "google_compute_resource_policy" "daily_snapshot" {
  name    = "default-schedule-1"
  project = var.project_id
  region  = var.region

  snapshot_schedule_policy {
    # Present on the live policy as a populated block. Omitting it plans a
    # change forever.
    #
    # The Phase 7 replacement policy must OMIT this block, for the opposite
    # reason: GCP does not persist it when every value inside is the default, so
    # declaring it on a Terraform-CREATED policy plans a change forever in the
    # other direction. The two are not inconsistent — one is imported, one is
    # created.
    snapshot_properties {
      guest_flush       = false
      labels            = {}
      storage_locations = []
    }

    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "12:00"
      }
    }

    retention_policy {
      max_retention_days    = 14
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }
  }
}

# ── Phase 7: the 4-hourly schedule that replaces it ───────────────────────────
#
# Applied 2026-09-09. default-schedule-1 above is left DEFINED but DETACHED —
# the attachment now points here. Keeping it defined preserves the record of
# what production ran on, and detaching rather than deleting means the 14 days
# of snapshots it already took are still governed by their own retention and
# are not orphaned.
#
# Two changes, and the second is the reason for the first:
#
#   1. Recovery point moves from 24 h to 4 h. On its own this would be a
#      judgement call about how much HR data is acceptable to lose.
#
#   2. IT IS WHAT MAKES A "BACKUPS HAVE STOPPED" ALERT POSSIBLE AT ALL. Cloud
#      Monitoring refuses an absence duration above 23h30m. Against a DAILY
#      schedule there is no usable window: consecutive snapshots are 24 h apart
#      to within a second, so every window short enough to be accepted also
#      fires shortly before every healthy snapshot. At 4-hourly, a 5 h window
#      is comfortably inside the limit and tolerates one late run.
#
# Retention goes 14 -> 30 days. Storage is incremental and this disk is 30 GB
# with ~12 GB used, so the cost of the extra fortnight is small against being
# able to recover from a problem noticed three weeks late — which is the
# realistic detection time for silent data corruption in an HR system where
# most records are read rarely.
#
# start_time is 02:00, deliberately offset from the old 12:00 slot, so the first
# new snapshot is visibly distinguishable from the last old one when verifying
# the swap actually took effect.
#
# NOTE: no snapshot_properties block, and that is not an oversight — see the
# comment on the imported policy above. GCP does not persist that block when
# every value in it is the default, so declaring it on a policy Terraform
# CREATES plans a change on every apply, forever.
resource "google_compute_resource_policy" "four_hourly_snapshot" {
  name    = "hrms-prod-4h"
  project = var.project_id
  region  = var.region

  snapshot_schedule_policy {
    schedule {
      hourly_schedule {
        hours_in_cycle = 4
        start_time     = "02:00"
      }
    }

    retention_policy {
      max_retention_days = 30

      # KEEP_AUTO_SNAPSHOTS, not APPLY_RETENTION_POLICY. If the disk is ever
      # deleted, the snapshots must outlive it — deleting the disk is precisely
      # the event that makes them matter.
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }
  }
}

# ── The instance ───────────────────────────────────────────────────────────────

resource "google_compute_instance" "prod" {
  name         = "odoo-hrms-prod"
  project      = var.project_id
  zone         = var.zone
  machine_type = var.machine_type

  # Already enabled before this module existed. Terraform respects it: an apply
  # that would delete this instance fails instead, which is the intent.
  deletion_protection = true
  description         = ""

  # lb-health-check was REMOVED here in Phase 5 (2026-09-09), in the same change
  # as the two firewall rules that referenced it — the tag and the rules had to
  # go together rather than leaving one half live.
  #
  # What it was: the project has ZERO forwarding rules and zero target pools,
  # while default-allow-health-check permitted ALL TCP PORTS from Google's
  # health-check ranges to anything carrying this tag. A live, unnecessary path
  # to every port on the box — Postgres on 5432 and the Traefik admin API on
  # 8080 included — existing to serve a load balancer that was never built.
  #
  # The two that remain are load-bearing: they are how default-allow-http and
  # default-allow-https reach this instance. Removing either closes the site,
  # and removing http-server also breaks Traefik's ACME renewal.
  tags = ["http-server", "https-server"]

  # No `labels` block, deliberately — the same call the CRM module makes, and for
  # the same reason.
  #
  # `gcloud compute instances describe` DOES report
  # goog-ops-agent-policy = v2-x86-template-1-4-0, which is why declaring it
  # looks obviously right. It is not: the provider splits labels into `labels`
  # (what the configuration manages), `terraform_labels`, and `effective_labels`
  # (everything actually on the resource). Import populated only the last, so
  # declaring the label planned an ADD — proof that Terraform does not currently
  # own it.
  #
  # The label is applied by the OS Config Ops Agent policy. `labels` is
  # non-authoritative and manages only the keys it names, so omitting it leaves
  # the live label untouched. Declaring it would make Terraform claim ownership
  # of a label it does not control and fight the policy that sets it — every
  # time that policy bumps its template version.
  #
  # The empty-plan gate is what surfaced this. It was caught, not reasoned out
  # in advance.

  metadata = {
    # Set by the Ops Agent policy. Omitting it plans its REMOVAL, which would
    # quietly detach the VM from that policy.
    enable-osconfig = "TRUE"

    # ── PHASE 4B: OS LOGIN, ENABLED ───────────────────────────────────────────
    #
    # Set on the INSTANCE, not project-wide, so the blast radius is this one VM.
    #
    # This is a hard cutover, and what it revoked is worth recording precisely,
    # because it is the security result of the whole phase. Before it, SSH keys
    # lived in PROJECT metadata with `block-project-ssh-keys` unset, so they
    # applied to every VM in the project:
    #
    #   two named for individual people, one for a shared laptop, tech (twice)
    #
    # The usernames themselves are not reproduced here: this repository is
    # public, and naming whose laptop holds a production root key in a public
    # file is its own disclosure. `gcloud compute project-info describe` has
    # them.
    #
    # Five entries, no expiry on any of them. The guest agent adds
    # metadata-key users to google-sudoers, so each of those keys was
    # PASSWORDLESS ROOT on production, held on unknown laptops, revocable only
    # by editing project metadata. Two are named for people, not roles.
    #
    # After this flag, none of them can log in here. Access is IAM: tech@ holds
    # osAdminLogin (via roles/owner, confirmed by testIamPermissions before the
    # window, not assumed); developer1@, developer2@ and solutionanalysts@ hold
    # roles/compute.osLogin, which is login WITHOUT sudo.
    #
    # ROLLBACK, if someone is locked out: remove this one line and apply. It is
    # a setMetadata call and does NOT require a stop — which is why the serial
    # console was not enabled as a backstop. A lockout here is a two-minute
    # metadata edit, and enabling the console would have added a second
    # permanent root path to close later.
    enable-oslogin = "TRUE"
  }

  boot_disk {
    source      = google_compute_disk.prod.id
    device_name = "odoo-hrms-prod"

    # FALSE — changed from the imported `true` in the second apply, once the
    # first plan was empty.
    #
    # As imported this was TRUE, which meant deleting the instance would DESTROY
    # the boot disk with it: the one operation that would destroy production
    # data, with deletion_protection as the only thing standing in the way. Two
    # safety properties are better than one, and this one is free.
    #
    # The disk now outlives its instance, which is also what makes a whole-VM
    # recovery a matter of attaching the disk to a new instance rather than
    # restoring from a snapshot and losing everything since the last one.
    #
    # Safe and online: this is a setDiskAutoDelete call on the attachment, not a
    # disk or instance modification. No stop, no data movement.
    auto_delete = false
  }

  network_interface {
    network    = "default"
    subnetwork = "default"
    stack_type = "IPV4_ONLY"

    access_config {
      nat_ip       = google_compute_address.prod.address
      network_tier = "PREMIUM"
    }
  }

  # ── The service account swap happens HERE, and only while stopped ───────────
  #
  # Today: the COMPUTE DEFAULT service account, holding ZERO project IAM roles.
  # Verified directly — a get-iam-policy filtered to this member returns nothing
  # at all.
  #
  # The consequence is not theoretical. The Ops Agent is installed, active and
  # enabled on this VM, and has never shipped anything: agent metrics have zero
  # time series, Cloud Logging holds only audit logs, and the collector journal
  # carries ~120 PermissionDenied entries per 20 minutes with dropped_items in
  # the hundreds per batch. It has written 627 MB of its own failure messages to
  # the disk while doing so.
  #
  # The scopes are the second half of the problem, and are why this is harder
  # than the equivalent CRM change. Scopes are a hard ceiling ABOVE IAM: a role
  # grant changes nothing if the access token cannot carry it. These are the
  # restricted defaults, NOT cloud-platform, and Secret Manager — which
  # scripts/render_odoo_conf.sh needs — unambiguously requires cloud-platform.
  #
  # CHANGING EITHER FIELD REQUIRES THE INSTANCE TO BE STOPPED. Terraform will
  # stop it, change it, and start it again. This is the one unavoidable stop in
  # the migration, and the reason Phase 4b is a maintenance window even though
  # no machine-type or disk change is wanted.
  #
  # ── APPLIED IN THE PHASE 4B WINDOW ─────────────────────────────────────────
  #
  # hrms-prod-vm@ replaces the compute default, and the scopes become
  # cloud-platform. Both in the same stop, because both need one.
  #
  # WHY cloud-platform IS NOT AN OVER-GRANT HERE. It looks like the widest
  # possible setting, and in isolation it is — but scopes are a CEILING, not a
  # grant. The effective access is the intersection of scope and IAM, and
  # hrms-prod-vm@ holds exactly four roles: logging.logWriter,
  # monitoring.metricWriter, artifactregistry.reader,
  # secretmanager.secretAccessor. The alternative — enumerating a narrower scope
  # list — buys nothing, because there is no scope that admits Secret Manager
  # but not the rest, and it costs a second stopped-instance window every time a
  # later phase needs one more API. The restriction that matters is the IAM
  # policy, and that is where it is expressed.
  #
  # Proven permission-additive before the window: the compute default held ZERO
  # project roles, and also no resource-level grants — checked individually
  # against the state bucket, both secrets, and the Artifact Registry repo. So
  # this is a strict superset and nothing can regress.
  service_account {
    email  = google_service_account.prod_vm.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  shielded_instance_config {
    enable_secure_boot          = false
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  # Live value is "NONE". Omitting it makes the provider plan a change to null,
  # and this field FORCES REPLACEMENT — on the CRM instance the first plan wanted
  # to destroy and recreate production over an attribute nobody set on purpose.
  key_revocation_action_type = "NONE"

  allow_stopping_for_update = true

  lifecycle {
    # ssh-keys metadata is REWRITTEN CONTINUOUSLY by whoever runs
    # `gcloud compute ssh` — this project's instance metadata already carries
    # google-ssh entries with expiry stamps that have since passed, alongside
    # permanent ones. Terraform must not fight that churn, and must never be the
    # thing that revokes someone's access mid-session.
    #
    # The churn is itself the argument for OS Login: after that cutover this
    # field stops moving, because access stops living in metadata at all.
    ignore_changes = [metadata["ssh-keys"]]
  }
}

data "google_project" "this" {
  project_id = var.project_id
}
