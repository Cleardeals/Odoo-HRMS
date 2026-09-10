# infrastructure/terraform/variables.tf

variable "project_id" {
  type        = string
  description = "GCP project ID hosting the HRMS VM"
  # No default — supplied via terraform.tfvars (gitignored). This repo is PUBLIC.
}

variable "region" {
  type        = string
  description = "Default region for regional resources"
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = <<-EOT
    Zone of odoo-hrms-prod.

    Moving a zonal VM means recreating it, so this records where the instance
    actually is rather than expressing a preference. Note it differs from the
    CRM production VM's zone (us-central1-f) — do not "tidy" them to match.
  EOT
  default     = "us-central1-c"
}

variable "machine_type" {
  type        = string
  description = <<-EOT
    Machine type for odoo-hrms-prod.

    e2-medium: 2 SHARED vCPUs and 4 GB, running Odoo in prefork mode with
    workers = 3 and max_cron_threads = 1.

    A change here is EXPLICITLY OUT OF SCOPE for the migration, and there is no
    evidence it is needed: 30 days of container logs contain zero
    "virtual memory limit reached", so workers are not being recycled. Revisit
    only once the Ops Agent is actually shipping metrics (Phase 6), which is the
    honest order for that decision.

    Changing this REQUIRES THE INSTANCE TO BE STOPPED. Terraform will stop it,
    change it, and start it again.
  EOT
  default     = "e2-medium"
}

variable "boot_disk_size_gb" {
  type        = number
  description = <<-EOT
    Boot disk size for odoo-hrms-prod.

    30 GB, and EXPLICITLY OUT OF SCOPE for the migration. It was 74% full when
    this work began; Phase 0c reclaimed ~8 GB of uncapped journal, a stale
    containerd image store and agent logs, taking it to 44% with 16 GB free. The
    disk needed cleaning, not growing.

    Growing a disk is safe and online. SHRINKING IS IMPOSSIBLE — lowering this
    number produces an apply error, not a smaller disk.
  EOT
  default     = 30
}

# ── Cloud Build ────────────────────────────────────────────────────────────────

variable "github_repo" {
  type        = string
  description = "owner/repo that Cloud Build connects to (set up via the GitHub App)"
  # No default — supplied via terraform.tfvars, kept out of this public repo.
}

variable "cloudbuild_github_connected" {
  type        = bool
  description = <<-EOT
    Whether the Cloud Build GitHub App has been installed and granted access to
    var.github_repo. Terraform cannot do this itself — it is a one-time console
    step by a GitHub org admin.

    False skips the trigger resources; the rest of the module still applies.
  EOT
  default     = false
}

variable "cloudbuild_cd_enabled" {
  type        = bool
  description = <<-EOT
    Whether the push-to-main DEPLOY trigger exists. Separate from
    cloudbuild_github_connected because the two carry very different risk: the
    CI trigger runs gates only, this one deploys to production.

    Enable it only after a green cloudbuild.ci.yaml run on a real pull request.
  EOT
  default     = false
}

variable "cloudbuild_approvers" {
  type        = list(string)
  description = <<-EOT
    IAM members who may release a queued production deploy, as fully-qualified
    principals (e.g. "user:someone@example.com", "group:oncall@example.com").

    OPTIONAL, and not a prerequisite. roles/editor DOES include
    cloudbuild.builds.approve — verified against the live role and by
    testIamPermissions on this project, contrary to the note in the CRM repo's
    cloudbuild.tf. So the project's editors can already release a deploy.

    The reason to set this anyway is to grant approval to somebody who is NOT an
    editor, and to make the approver list deliberate rather than a side effect
    of a broad role. Prefer a group over individuals: an approver list is a
    rota, not architecture, and it should change without a Terraform apply.
  EOT
  default     = []
}

# ── Monitoring / alerting ──────────────────────────────────────────────────────

variable "alert_email" {
  type        = string
  description = <<-EOT
    Address the alert notification channel delivers to.

    No default, and supplied via terraform.tfvars (gitignored) rather than
    committed: this repository is PUBLIC, and an address in it is an address
    that gets scraped.

    GCP sends a verification email when the channel is created and DELIVERS
    NOTHING until the link in it is clicked. A policy attached to an unverified
    channel looks perfectly healthy in the console and pages nobody.
  EOT
}

variable "public_host" {
  type        = string
  description = <<-EOT
    Public hostname the uptime check probes. Must match the Host() rule on the
    odoo router in docker-compose.yml and EDGE_HOST in scripts/deploy.sh —
    Traefik routes on it, so a value that matches no router returns 404.
  EOT
  default     = "hr.cleardeals.xyz"
}

# Human principals who must be able to SSH into the production VM.
#
# roles/compute.osLogin alone does NOT grant login on a VM with an attached
# service account — iam.serviceAccounts.actAs on that service account is also
# required. See the long comment on humans_actas_prod_vm in iam.tf; Phase 4b
# missed this and locked out the accounts it was documented as keeping.
#
# Fully-qualified members ("user:someone@example.com" or "group:..."), because
# this repository is PUBLIC and no address belongs in it — the real values live
# in the gitignored terraform.tfvars.
#
# A GROUP is the better long-term answer: membership then changes without a
# Terraform apply. Listed as users here because no suitable group exists yet.
#
# NOTE this grants LOGIN only. Sudo is roles/compute.osAdminLogin and is
# deliberately not included.
variable "vm_ssh_users" {
  description = "Members granted actAs on the VM service account so OS Login works. Login only, not sudo."
  type        = list(string)
  default     = []
}
