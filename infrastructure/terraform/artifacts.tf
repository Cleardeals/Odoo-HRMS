# infrastructure/terraform/artifacts.tf
#
# Images move OFF the VM.
#
# Today the deploy runs `docker compose build odoo` ON the production host, via
# a GitHub Actions workflow that SSHes in with a long-lived private key from a
# repository secret. That build competes with Odoo and Postgres for two shared
# vCPUs and for a disk that was 74% full before Phase 0c reclaimed ~8 GB — and
# the workflow reports success whether or not Odoo comes back up.
#
# It also makes the running image unidentifiable. The live container runs
# `odoo-hrms:latest`, a floating tag built locally, with no .env pinning
# anything. "What is in production" has no answer, and rollback has no target.
#
# Cloud Build pushes here instead, tagged by commit SHA (both short and full),
# and scripts/deploy.sh pins the tag into .env. That is what makes the tag an
# honest answer and rollback a real operation.

resource "google_artifact_registry_repository" "hrms" {
  repository_id = "hrms"
  project       = var.project_id
  location      = var.region
  format        = "DOCKER"
  description   = "Odoo HRMS production images, tagged by commit SHA"

  # No cleanup_policies block, deliberately. Retention is handled on the VM by
  # scripts/deploy.sh, which keeps a fixed COUNT of recent images rather than
  # deleting by age — because the rollback target is exactly as old as whenever
  # it was built, so any age filter eventually deletes the thing you need.
  #
  # A registry-side age policy would have the same flaw and would be harder to
  # reason about, since it cannot see which image is currently running.
}
