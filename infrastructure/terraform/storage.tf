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
