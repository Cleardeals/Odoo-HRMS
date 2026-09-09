# infrastructure/terraform/versions.tf
#
# State lives in a bucket in THIS project. Not in the CRM instance's
# cleardeals-odoo-tfstate, and not in the WhatsApp platform's shared bucket:
# sharing one would tie HRMS's state to the lifecycle and IAM of an unrelated
# project, and force a cross-project grant for the HRMS CI service account. A
# project-level mistake should stop at that project.
#
# The bucket has uniform bucket-level access, public access prevention, and
# object versioning, so a truncated state write is recoverable from a prior
# generation. It is declared in storage.tf and imported like everything else.

terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "cleardeals-hrms-tfstate"
    prefix = "hrms-prod"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
