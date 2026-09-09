# infrastructure/terraform/secrets.tf
#
# The two secrets scripts/render_odoo_conf.sh injects into odoo.prod.conf.
#
# ── ONLY THE CONTAINERS ARE DECLARED, NEVER THE VERSIONS ──────────────────────
#
# There is no google_secret_manager_secret_version here, and there must never
# be. Terraform state records every attribute of every resource it manages, so a
# version resource would write the secret value into
# gs://cleardeals-hrms-tfstate in cleartext — turning the state bucket into the
# thing the secret was meant to avoid being. Values are created and rotated with
# `gcloud secrets versions add`, which leaves no copy behind.
#
# What IS in state is metadata: the name, the replication policy, labels. None of
# it is sensitive, and declaring it means the replication policy and the secrets'
# existence are reviewable and drift is visible.
#
# NOTE this differs from the CRM module, which does not declare its secrets in
# Terraform at all. That looks like an omission rather than a decision — there is
# no comment defending it — and the containers are safe to manage, so they are
# managed here.
#
# ── ACCESS ────────────────────────────────────────────────────────────────────
#
# Read access is granted at the PROJECT level in iam.tf
# (roles/secretmanager.secretAccessor on the VM's runtime service account)
# rather than per-secret here. Both secrets have exactly one reader and exactly
# one purpose, so a per-secret binding would add a second place to look without
# narrowing anything.

resource "google_secret_manager_secret" "admin_passwd" {
  project   = var.project_id
  secret_id = "odoo-admin-passwd"

  # The Odoo master password, which gates the database manager
  # (backup / duplicate / restore / drop). It was COMMENTED OUT in the live
  # config, so Odoo was falling back to its built-in default. list_db = False
  # gates the manager UI, so this was not an open door — but it was one config
  # change away from being one.
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "odoo-db-password"

  # The Postgres role password. Seeded with the live value — FOUR CHARACTERS,
  # the `odoo` default that docker-compose.yml published as
  # `${DB_PASSWORD:-odoo}` in this PUBLIC repository, and which is in git
  # history forever.
  #
  # Seeded as-is on purpose, so odoo.prod.conf renders a WORKING config from the
  # first attempt and the render step can be proven separately from the
  # rotation. Rotation is infrastructure/rotate_db_password.sh, and it cannot run
  # until the VM has both secretAccessor and the cloud-platform scope (Phase 4b).
  replication {
    auto {}
  }
}
