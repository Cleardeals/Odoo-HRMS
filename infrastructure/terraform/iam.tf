# infrastructure/terraform/iam.tf
# Service accounts and their bindings.
#
# Creating these changes NOTHING about the running VM: it keeps its current
# identity until the Phase 4b window, because attaching a different service
# account requires the instance to be stopped. So this file is safe to apply
# outside a window, and deliberately is — the identities exist and are reviewable
# before the change that starts using them.

# ── Runtime identity for the production VM ─────────────────────────────────────
#
# Attached to odoo-hrms-prod during Phase 4b (see compute.tf — the field cannot
# be changed while the instance runs).
#
# WHAT IT REPLACES, and why this is the highest-value change in the migration:
# the VM currently runs as the COMPUTE DEFAULT service account, which holds ZERO
# project IAM roles. Verified directly with a filtered get-iam-policy that
# returns nothing at all.
#
# The consequence is measured, not theoretical. The Ops Agent is installed,
# active and enabled, and has never shipped a single byte: agent metrics have
# zero time series, Cloud Logging holds only audit logs, and the collector
# journal carries ~120 PermissionDenied entries per 20 minutes. It has written
# 627 MB of its own failure messages to the disk while failing.
resource "google_service_account" "prod_vm" {
  account_id   = "hrms-prod-vm"
  project      = var.project_id
  display_name = "HRMS production VM runtime"
}

resource "google_project_iam_member" "prod_vm" {
  for_each = toset([
    # These two are what make the ALREADY-INSTALLED Ops Agent start working.
    # Nothing needs installing on the VM; it has simply never been allowed to
    # write. Without them Phase 6 and Phase 7 are both impossible — there is no
    # point alerting on metrics that never arrive.
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",

    # Pull deploy images built by Cloud Build.
    "roles/artifactregistry.reader",

    # Read odoo-admin-passwd and odoo-db-password in
    # scripts/render_odoo_conf.sh. Granted at the project level rather than
    # per-secret: both secrets have exactly one reader and one purpose, so a
    # per-secret binding would add a second place to look without narrowing
    # anything.
    #
    # NOTE this role is necessary but NOT sufficient. Scopes are a hard ceiling
    # above IAM, and the instance currently carries the restricted default
    # scopes rather than cloud-platform, so the render step cannot succeed until
    # 4b changes both together.
    "roles/secretmanager.secretAccessor",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.prod_vm.email}"
}

# No BigQuery roles, and no cross-project grants. Unlike the CRM instance — where
# 22 files across lead_suggestor and leads/models/lead_score.py query BigQuery in
# a DIFFERENT project, and where attaching a new service account without
# replicating four roles would have silently broken lead scoring at runtime —
# HRMS has no BigQuery dependency at all. requirements.txt contains no
# google-cloud-* package and no custom addon imports bigquery, which is why the
# probe in entrypoint.sh had always printed a failure and has been removed.
#
# That check is the reason this file is short. It was done before assuming.

# ── CI/CD identity ─────────────────────────────────────────────────────────────

resource "google_service_account" "cloudbuild" {
  account_id   = "hrms-cloudbuild"
  project      = var.project_id
  display_name = "HRMS Cloud Build CI/CD"
}

resource "google_project_iam_member" "cloudbuild" {
  for_each = toset([
    "roles/artifactregistry.writer", # push images
    "roles/logging.logWriter",       # required for a custom build service account
    "roles/compute.osAdminLogin",    # SSH to the VM with sudo, via OS Login
    "roles/compute.viewer",          # resolve the instance before connecting
    "roles/iap.tunnelResourceAccessor",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# Deliberately NOT granted roles/storage.objectViewer. Source arrives from the
# GitHub App, not a GCS tarball, so the build never reads a bucket. Add it only
# if a manual `gcloud builds submit` is ever needed.
#
# Deliberately NOT granted compute.instances.setMetadata either, and this one
# matters: setMetadata permits writing `startup-script`, which runs as ROOT at
# next boot. Granting it would hand permanent root on production to anything
# that can trigger a build. It is also why OS Login is REQUIRED rather than
# merely tidy — without it, `gcloud compute ssh` falls back to writing an
# ephemeral key into instance metadata, which needs exactly that permission.

# ── SSH into a VM that has a service account attached ──────────────────────────
# Non-obvious requirement: OS Login roles alone are not enough. The caller must
# also be able to act as the service account the TARGET INSTANCE runs as, or the
# connection is refused after authentication succeeds.
resource "google_service_account_iam_member" "cloudbuild_actas_prod_vm" {
  service_account_id = google_service_account.prod_vm.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# The same grant on the account the instance runs as TODAY.
#
# On the CRM instance this gap cost two failed deploys: granting a permission to
# the identity a resource WILL have is not the same as granting it to the one it
# HAS. Kept here for the same reason, and removable once 4b has attached
# hrms-prod-vm@ — but removed in that same change, not before.
#
# In practice HRMS cannot deploy before 4b anyway: scripts/deploy.sh runs
# render_odoo_conf.sh, which needs Secret Manager and therefore the
# cloud-platform scope. So this binding is belt-and-braces rather than
# load-bearing, and it costs nothing to be certain.
resource "google_service_account_iam_member" "cloudbuild_actas_default_compute" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${data.google_project.this.number}-compute@developer.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# NOTE, deliberately not implemented here: a human also needs
# roles/iam.serviceAccountUser on prod_vm to SSH in under OS Login —
# compute.osLogin alone is not enough on a VM with an attached service account.
# No such grant exists, which is why developer2@ currently cannot log in at all.
# That is an OPEN finding held for auditor review, not an oversight to fix in
# passing: see "FINDING (OPEN)" in docs/infrastructure_migration_plan.md before
# adding one.

# ── Letting Cloud Build USE the custom build service account ───────────────────
#
# A trigger running as a user-managed service account needs Cloud Build's
# SERVICE AGENT to be able to mint tokens for it. The console does this
# silently; the API does not.
#
# The failure is delayed and misleading: creating the trigger SUCCEEDS, because
# the principal running Terraform has actAs via its own role. Only the first
# BUILD fails, with an error that reads like a Cloud Build fault rather than a
# missing binding.
#
# CAREFUL — the project has two Cloud Build identities and they are NOT
# interchangeable:
#
#   <PROJECT_NUMBER>@cloudbuild.gserviceaccount.com
#       LEGACY DEFAULT build account — the identity a build runs as when none is
#       specified.
#
#   service-<PROJECT_NUMBER>@gcp-sa-cloudbuild.iam.gserviceaccount.com
#       SERVICE AGENT — Google's control-plane identity, and the one that
#       impersonates a user-specified service account on the build's behalf.
#
# It is the SERVICE AGENT that needs this. Granting it to the legacy account
# instead leaves the real impersonation path unauthorised while a binding sits
# there looking correct.
#
# The address is composed explicitly rather than read from
# google_project_service_identity, because that resource returns the LEGACY
# account for cloudbuild.googleapis.com, not the service agent. Note also that
# service agents are Google-managed and do NOT appear in
# `gcloud iam service-accounts list`, so their absence from that output is not
# evidence they are missing.
resource "google_service_account_iam_member" "cloudbuild_agent_token_creator" {
  service_account_id = google_service_account.cloudbuild.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

# ── Who may release a queued production deploy ─────────────────────────────────
#
# OPTIONAL, and empty by default — which is a correction to the assumption this
# migration started from.
#
# The CRM module states that roles/editor does not include
# cloudbuild.builds.approve, so an explicit grant is required or the approval
# gate deadlocks. That is NOT true, verified two ways on this project:
#
#   gcloud iam roles describe roles/editor --format="value(includedPermissions)" \
#     | tr ';' '\n' | grep '^cloudbuild.builds.'
#   -> approve, create, get, list, update
#
# and a live testIamPermissions returns cloudbuild.builds.approve as granted for
# an editor principal. (Watch the separator: value() emits a SEMICOLON-delimited
# list, so splitting on a comma yields one long line and an anchored grep
# silently matches nothing — which is how the wrong conclusion is easy to reach.)
#
# So the project's editors can already approve. The reason to set this variable
# anyway is to grant approval to somebody who is NOT an editor, and to make the
# approver list deliberate rather than a side effect of a broad role. Prefer a
# group: an approver list is a rota, not architecture.
resource "google_project_iam_member" "cloudbuild_approvers" {
  for_each = toset(var.cloudbuild_approvers)
  project  = var.project_id
  role     = "roles/cloudbuild.builds.approver"
  member   = each.value
}
