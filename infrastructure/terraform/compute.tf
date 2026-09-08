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
resource "google_compute_disk_resource_policy_attachment" "prod_snapshot" {
  name    = google_compute_resource_policy.daily_snapshot.name
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

  # lb-health-check is REAL and is on the live instance, so it is imported. It
  # should not be: the project has ZERO forwarding rules and zero target pools,
  # while default-allow-health-check permits ALL TCP PORTS from Google's health
  # check ranges to anything carrying this tag. That is a live, unnecessary path
  # to every port on the box — Postgres and the Traefik API included — existing
  # to serve a load balancer that was never built.
  #
  # Removed in Phase 5, together with the two firewall rules that reference it.
  # Not here: this file's job is to record what is, and the tag and the rules
  # must go in one reviewed change rather than leaving one half live.
  tags = ["http-server", "https-server", "lb-health-check"]

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

    # enable-oslogin is DELIBERATELY ABSENT. OS Login is off today, and the five
    # never-expiring keys in project metadata are how everyone reaches this box.
    #
    # It is enabled in the Phase 4b window, not here, because it is a HARD
    # CUTOVER: the moment it is on, those metadata keys stop working on this
    # machine and anyone relying on them loses access until granted
    # roles/compute.osLogin or osAdminLogin.
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
  service_account {
    email = "${data.google_project.this.number}-compute@developer.gserviceaccount.com"
    scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring.write",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/trace.append",
    ]
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
