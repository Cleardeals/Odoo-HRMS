# infrastructure/terraform/cloudbuild.tf
# The CI/CD entry points.
#
# ── ONE-TIME MANUAL STEP ──────────────────────────────────────────────────────
# Terraform cannot create the GitHub App connection. A GitHub org admin installs
# the Cloud Build GitHub App and grants it this repository, once, at
# https://console.cloud.google.com/cloud-build/triggers/connect
#
# Until then keep cloudbuild_github_connected = false: these resources are
# skipped and the rest of the module still applies cleanly.

locals {
  gh_owner = split("/", var.github_repo)[0]
  gh_name  = split("/", var.github_repo)[1]

  # Two switches, deliberately independent. The CI trigger builds no production
  # image and touches no VM. The CD trigger deploys to production. Tying them to
  # one flag would force that blast-radius increase to be accepted just to get
  # pull-request checks.
  ci_count = var.cloudbuild_github_connected ? 1 : 0
  cd_count = var.cloudbuild_github_connected && var.cloudbuild_cd_enabled ? 1 : 0
}

# ── CI: pull requests ──────────────────────────────────────────────────────────
resource "google_cloudbuild_trigger" "ci" {
  count       = local.ci_count
  project     = var.project_id
  location    = "global"
  name        = "hrms-ci-pull-request"
  description = "Tests, config checks, OpenAPI parity, and image-contents verification. Builds no production image, deploys nothing."

  github {
    owner = local.gh_owner
    name  = local.gh_name
    pull_request {
      # Both branches that can reach production: main directly, and development
      # which is merged into it.
      branch = "^(main|development)$"
      # comment_control is deliberately omitted. Its API default is stored as
      # UNSET, so setting it explicitly produces a permanent one-line diff on
      # every plan — which trains people to skim plans instead of read them.
    }
  }

  filename        = "cloudbuild.ci.yaml"
  service_account = google_service_account.cloudbuild.id
}

# ── CD: push to main ───────────────────────────────────────────────────────────
#
# A merge STARTS this pipeline; it does not reach production unattended.
# approval_required holds every run until a human releases it.
#
# ── DO NOT ENABLE BEFORE THE PHASE 4B WINDOW ─────────────────────────────────
#
# scripts/deploy.sh runs render_odoo_conf.sh, which reads Secret Manager from
# the VM. That needs roles/secretmanager.secretAccessor on the attached service
# account AND the cloud-platform scope on the instance. The VM has neither until
# 4b attaches hrms-prod-vm@ and widens the scopes — both of which require the
# instance to be stopped.
#
# So a CD run before that window fails at the render step. It fails SAFELY —
# deploy.sh dies before swapping the image, and the old container keeps serving —
# but it is a wasted approval and a misleading red build. Keep
# cloudbuild_cd_enabled = false until 4b is done and a hand-run
# render_odoo_conf.sh has been seen to succeed on the VM.
resource "google_cloudbuild_trigger" "cd" {
  count       = local.cd_count
  project     = var.project_id
  location    = "global"
  name        = "hrms-cd-main"
  description = "Gate, build, push to Artifact Registry, and deploy to odoo-hrms-prod. Requires human approval."

  github {
    owner = local.gh_owner
    name  = local.gh_name
    push {
      branch = "^main$"
    }
  }

  filename        = "cloudbuild.yaml"
  service_account = google_service_account.cloudbuild.id

  substitutions = {
    _ZONE     = var.zone
    _INSTANCE = google_compute_instance.prod.name
    _REGION   = var.region
  }

  approval_config {
    approval_required = true
  }

  # Deliberately NO included_files filter. A deploy trigger that skips files is
  # a deploy trigger that silently does not deploy something.
}
