# infrastructure/terraform/storage.tf
# Until this module existed the project had NO buckets at all.

# Chicken-and-egg: this bucket holds the state that describes it, so it cannot
# be created by the run that uses it as a backend. It is created once with
# gcloud, then imported here, so that from then on its settings are reviewable
# and drift is visible.
resource "google_storage_bucket" "tfstate" {
  name     = "cleardeals-hrms-tfstate"
  project  = var.project_id
  location = "US-CENTRAL1"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  # The point of versioning on a state bucket: a truncated or corrupted state
  # write is recoverable from the previous generation.
  versioning {
    enabled = true
  }

  # Terraform can create this bucket but must never be allowed to destroy it.
  lifecycle {
    prevent_destroy = true
  }
}

# ── Phase 8: somewhere for logical backups to live ────────────────────────────
#
# WHY THIS EXISTS WHEN SNAPSHOTS ALREADY DO. Disk snapshots (compute.tf,
# 4-hourly since Phase 7) are CRASH-CONSISTENT: they capture the disk as if the
# power had been cut. Postgres recovers from that, but a snapshot cannot give you
# "the database as it was before that bad import at 14:20", and it cannot be
# restored into anything but a disk. A logical `pg_dump` can be inspected,
# diffed, partially restored, and loaded into a different Postgres entirely.
#
# It matters more here than on the CRM instance: alongside the 119 MB database
# there is a 759 MB filestore of HR documents — payroll and personnel
# attachments, which are exactly the records whose loss is least recoverable by
# re-entering them.
resource "google_storage_bucket" "backups" {
  name     = "cleardeals-hrms-backups"
  project  = var.project_id
  location = "US-CENTRAL1"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  # No deletion lifecycle rule, on purpose. Backups ageing out silently is a
  # worse failure than paying for storage — and the failure is invisible until
  # the restore, which is the one moment it cannot be tolerated. If a retention
  # rule is ever added, it needs the same treatment as the snapshot schedule:
  # something that alerts when the newest object gets too old.
  lifecycle {
    prevent_destroy = true
  }
}

# ── Write and read, but NOT delete ────────────────────────────────────────────
#
# objectCreator alone is not enough, and this is the trap worth recording:
# `gcloud storage cp` issues a GET before writing and returns 403 without
# objectViewer. The obvious fix at that point is objectAdmin — which also grants
# storage.objects.delete.
#
# creator + viewer instead means the VM can write its backups and verify them,
# and cannot delete them. If the host is ever compromised, an attacker with full
# root on it still cannot destroy the backups from there. That property is the
# entire point of the pair, and objectAdmin would silently give it away.
#
# Unlike the CRM module, this needs no for_each/locals/depends_on construction.
# That existed there because two service accounts were involved and one did not
# yet exist, so a for_each over their emails could not be evaluated during
# `terraform import` — it failed the whole import run with "Invalid for_each
# argument", including for unrelated resources. Here there is one writer and it
# already exists, so referencing the resource attribute directly is both simpler
# and gives a real dependency edge instead of a hand-declared one.
resource "google_storage_bucket_iam_member" "backup_create" {
  bucket = google_storage_bucket.backups.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.prod_vm.email}"
}

resource "google_storage_bucket_iam_member" "backup_read" {
  bucket = google_storage_bucket.backups.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.prod_vm.email}"
}

# ── TWO GAPS, RECORDED SO THEY ARE NOT MISTAKEN FOR DONE ─────────────────────
#
# 1. NOTHING WRITES TO THIS BUCKET, AND THAT IS A DECISION, NOT AN OVERSIGHT.
#
#    DEFERRED 2026-09-09, pending an organisation-level DR plan that was under
#    discussion when this was written. Do not "fix" this by adding a dump
#    schedule without checking where that landed.
#
#    The state to be aware of meanwhile: creating this bucket did not create any
#    backups. It is EMPTY. The only logical dump that exists was taken by hand
#    before the Phase 4b window. Recovery today rests entirely on the 4-hourly
#    disk snapshots, which are crash-consistent — so there is no point-in-time
#    restore, no partial restore, and no way to load the data into a different
#    Postgres.
#
#    WHY DEFERRING IS THE RIGHT ORDER, rather than building the pipeline now and
#    adjusting later: this bucket is single-region US-CENTRAL1, the same region
#    as the disk it backs up. If the DR plan requires geographic separation — and
#    a same-region backup of a same-region disk is the first thing such a review
#    tends to reject — then the LOCATION has to change, and a GCS bucket's
#    location is IMMUTABLE. That means a new bucket, and anything already
#    written here would have to be migrated. Cadence, retention, whether the
#    759 MB filestore is included, and whether backups belong in this project at
#    all are all the same kind of question.
#
#    When it is unblocked, the shape is: a dump-and-upload script, a systemd
#    timer, a log-based metric on successful uploads, and a staleness alert built
#    exactly like monitoring.tf's P2b — because a backup job that silently stops
#    is the same failure as a snapshot schedule that silently stops.
#
# 2. Legacy GCS bindings still give any project Editor `legacyObjectOwner` on
#    this bucket, which includes delete. So the no-delete property above holds
#    against a compromised VM, but NOT against a project-level principal.
#    Closing that means removing the legacy bindings, which is separate work.
