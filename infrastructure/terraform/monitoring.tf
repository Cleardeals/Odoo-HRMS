# infrastructure/terraform/monitoring.tf
#
# Phase 7 — alerting. Before this file there was NOTHING, verified rather than
# assumed: 0 notification channels, 0 alert policies, 0 uptime checks in the
# project. Production HRMS ran unwatched, and every incident so far has been
# found by a person noticing the site was wrong.
#
# This was blocked until Phase 4b, and not for the reason it looked like. The
# Ops Agent had been installed, `active` and `enabled` for months while shipping
# NOTHING — the attached service account held zero IAM roles, so every batch it
# collected was dropped with a PermissionDenied. Alerting on metrics that were
# never arriving would have produced a console full of "no data" conditions and
# a false sense of coverage. 4b fixed the permission and Phase 6 added container
# logs; these policies are the point of having done both.
#
# ── THRESHOLDS ARE VALIDATED AGAINST REAL DATA, NOT ASSUMED ───────────────────
#
# Every threshold below was checked against what this host is actually
# producing, on 2026-09-09, after the agent started shipping. Measured:
#
#   disk/percent_used   /dev/sda1  used 39.93  free 55.60  reserved 4.47
#                       /dev/sda15 used  9.52  free 90.48  reserved 0.00
#   memory/percent_used used 37.57  free 40.42  cached 19.06  slab 2.47
#
# THE `state` FILTER IS THE LOAD-BEARING ONE, and this measurement is what
# proves it. `state` is a metric label, and `free` is one of its values: an
# unfiltered "disk > 85%" alert matches /dev/sda15 state=free at 90.48% and
# fires immediately, permanently, while the disk is 90% EMPTY. The condition
# would have been exactly inverted.
#
# CRM's host had the analogous trap in a different shape — eleven series, eight
# of them /dev/loopN snap squashfs mounts pinned at 100% forever. Debian 12 has
# no snaps so those are absent here, but assuming that meant "only /dev/sda1"
# was still wrong: /dev/sda15 is the EFI system partition. It is INCLUDED
# deliberately by the starts_with("/dev/sd") filter, at 9.52% and static — a
# filling /boot/efi breaks kernel updates and is worth knowing about.
#
# An alert that is always firing is worse than no alert. It teaches everyone to
# close the notification without reading it, and the one that matters then
# arrives in a mailbox where alerts have already been reclassified as noise.

# ── Where alerts go ────────────────────────────────────────────────────────────
#
# GCP sends a verification email when this channel is created, and the channel
# DELIVERS NOTHING until somebody clicks the link in it. A policy attached to an
# unverified channel looks completely healthy in the console and silently pages
# no one — the worst possible failure mode for the thing whose entire job is to
# tell you about failure. Verify it, and confirm `verificationStatus: VERIFIED`
# rather than trusting that the mail arrived.
resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "Odoo HRMS production alerts"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

locals {
  alert_prefix   = "[hrms-prod]"
  alert_channels = [google_monitoring_notification_channel.email.id]
}

# ── P1: the site is unreachable from the internet ─────────────────────────────
#
# The highest-value alert here, because it is the only one that asks the
# question a user asks. It is indifferent to WHICH layer broke: it catches the
# VM being down, Odoo being down, Postgres unreachable, an expired certificate,
# and — the case that motivates it — Traefik alive but routing nothing.
#
# That last case is not hypothetical on this stack's sibling: in the CRM Phase 4c
# window Traefik's docker provider died on a client/daemon API mismatch, so it
# discovered no containers and served 404 for every request while Odoo sat
# behind it perfectly healthy. Every internal check passed. Only an external
# check sees it.
#
# HRMS has survived the same class of break already — Docker 29.2.1 was
# installed here on 2026-02-16 and removed 90 minutes later, with docker-ce
# pinned at 28.5.2 by `apt-mark hold` ever since. That pin is the only thing
# standing between this host and the identical outage, and nothing was watching.
resource "google_monitoring_uptime_check_config" "site" {
  project      = var.project_id
  display_name = "Odoo HRMS production — /web/login"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path           = "/web/login"
    port           = 443
    use_ssl        = true
    request_method = "GET"

    # validate_ssl makes a certificate problem FAIL the check rather than being
    # silently ignored. Traefik renews via ACME on its own, so a failed renewal
    # has no other route to anybody's attention.
    validate_ssl = true

    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  # /web/login, not /. The root path redirects, and a redirect is served by
  # Traefik's ENTRYPOINT before any routing happens — so a check against /
  # passes even when no router exists, which is exactly the outage above.
  # Confirmed on this host: a port-80 probe returns 301 for a hostname matching
  # no router at all.
  #
  # It is also chosen over /web/health because /web/health without
  # db_server_status=1 returns 200 without touching the database, and
  # /web/database/selector renders unconditionally. Both were in use here as
  # "health checks" before this migration and neither proves anything.
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.public_host
    }
  }
}

resource "google_monitoring_alert_policy" "site_down" {
  project      = var.project_id
  display_name = "${local.alert_prefix} P1 Site unreachable from the internet"
  combiner     = "OR"

  documentation {
    content   = <<-EOT
      ${var.public_host}/web/login is not returning 2xx to Google's external
      uptime checkers.

      This alert is deliberately layer-agnostic — it says users cannot reach the
      site, not which component failed. Work outwards:

        1. Is the instance running?
        2. Is Odoo healthy from inside its own container?
             sudo docker exec odoo-app curl -fsS \
               "http://localhost:8069/web/health?db_server_status=1"
           Note the query parameter. Without it this route returns 200 without
           touching the database.
        3. If Odoo is healthy but the site is not, it is the proxy or the
           routing. Count Traefik's routers:
             curl -s http://127.0.0.1:8080/api/http/routers | \
               python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'
           A healthy stack reports 5. ZERO ROUTERS is the signature of the
           docker-provider failure: Traefik alive and answering, its provider
           dead, nothing routed anywhere.
        4. A certificate failure also trips this check, because validate_ssl is
           on. See P4.

      Access is IAP-only since Phase 5 — there is no longer any route to port 22
      from the internet:

        gcloud compute ssh tech@odoo-hrms-prod --project=<project> \
          --zone=us-central1-c --tunnel-through-iap

      DO NOT run `apt upgrade` while debugging. docker-ce and docker-ce-cli are
      held at 28.5.2 deliberately; containerd.io is NOT held, so a blanket
      upgrade moves it underneath a pinned Docker.
    EOT
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "uptime check failing from multiple regions"

    condition_threshold {
      filter = join(" AND ", [
        "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\"",
        "resource.type=\"uptime_url\"",
        "metric.label.check_id=\"${google_monitoring_uptime_check_config.site.uptime_check_id}\"",
      ])

      # REDUCE_COUNT_FALSE counts how many of Google's geographically separate
      # checkers are currently failing. Requiring more than one means a single
      # checker having a bad minute does not page anybody, while a real outage —
      # which every checker sees — still does. Alerting on one failed check
      # produces false pages; requiring all of them delays a real one.
      aggregations {
        alignment_period     = "1200s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.host"]
      }

      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "60s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = local.alert_channels

  alert_strategy {
    auto_close = "3600s"
  }
}

# ── P2: the root filesystem is filling ────────────────────────────────────────
#
# Measured at 39.93% used on /dev/sda1. That is comfortable now and was NOT
# comfortable three weeks ago: this disk was at 74% when the migration began and
# was brought down to 42% by reclaiming containerd leases — without growing it,
# because a disk upgrade was explicitly out of scope.
#
# It will climb again, and faster than before, because the Cloud Build pipeline
# retains up to 3 tagged images (IMAGE_KEEP in scripts/deploy.sh) and this
# image is around 3 GB. `docker image prune -f` does NOT reclaim them: it removes
# DANGLING images only, and a tagged image is not dangling.
#
# A full disk on this host is not a degraded service, it is a stopped one:
# Postgres cannot write, Odoo cannot write, and the deploy that would fix it
# cannot pull an image. On 30 GB, with Postgres data, the filestore and every
# Docker image sharing one partition, that is not a distant prospect.
resource "google_monitoring_alert_policy" "disk_filling" {
  project      = var.project_id
  display_name = "${local.alert_prefix} P2 Root filesystem above 85%"
  combiner     = "OR"

  documentation {
    content   = <<-EOT
      A real block device on odoo-hrms-prod is over 85% full.

      A full disk here stops the service outright — Postgres cannot write, Odoo
      cannot write, and the deploy that would fix it cannot pull an image. It
      does not resolve itself.

      Usual consumers, in the order they are usually guilty:

        docker system df                      # retained deploy images, ~3GB each
        sudo du -sh /var/lib/containerd       # leases pinning dead snapshots
        journalctl --disk-usage
        sudo du -sh /var/log/google-cloud-ops-agent
        sudo du -sh /opt/odoo-hrms/odoo-web-data   # filestore, ~759MB

      Reclaiming space, least destructive first:

        docker image prune -a --filter "until=336h"   # untagged AND old tagged
        docker builder prune                          # build cache

      THE LEASES ARE THE USUAL SURPRISE. When this was at 74%, the images were
      not the problem — buildkit held `buildkit/lease.temporary` leases that
      pinned containerd snapshots and blocked garbage collection, so the space
      did not come back until the leases were released. `docker system df` does
      not show this.

      Note /dev/sda15 is the EFI system partition and is matched by this alert
      on purpose. It sits at ~9.5% and is static; if it is the device that
      tripped, the cause is accumulated kernels, not application data.
    EOT
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "disk used > 85% on a real block device"

    condition_threshold {
      filter = join(" AND ", [
        "metric.type=\"agent.googleapis.com/disk/percent_used\"",
        "resource.type=\"gce_instance\"",
        # Both labels are required. state="used" is what stops this matching
        # state="free", which reads 90.48% on /dev/sda15 right now and would
        # invert the alert. See the header.
        "metric.label.state=\"used\"",
        "metric.label.device=starts_with(\"/dev/sd\")",
      ])

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }

      comparison      = "COMPARISON_GT"
      threshold_value = 85

      # Five minutes, not instant. Disk usage does not spike and self-correct,
      # so a sustained reading is the honest signal; this only suppresses a
      # transient blip while an image is being pulled.
      duration = "300s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = local.alert_channels

  alert_strategy {
    auto_close = "86400s"
  }
}

# ── P2b: automated snapshots have stopped ─────────────────────────────────────
#
# Everything else here watches whether the system is RUNNING. Nothing watched
# whether it is RECOVERABLE. If the snapshot schedule silently stops, the first
# anyone learns of it is during a restore — the single worst moment to find out,
# and precisely the failure this closes.
#
# ── THE OBVIOUS IMPLEMENTATION DOES NOT WORK ─────────────────────────────────
#
# The natural approach is a log-based metric on the `createSnapshot` audit log.
# It would never fire. On the CRM project the only
# v1.compute.disks.createSnapshot entries were MANUAL snapshots taken by a human
# during the migration; the daily scheduled snapshots — which demonstrably
# existed, one per day — produced no createSnapshot audit entry at all.
#
# A metric built on that filter sits permanently at zero while snapshots run
# perfectly, so an absence alert on it fires forever and is muted within a week.
# Scheduled snapshots are logged instead as a SYSTEM EVENT with methodName
# "ScheduledSnapshots", which is what this matches.
#
# There is no built-in snapshot-age metric to use instead. The only
# snapshot-related metrics Cloud Monitoring exposes for Compute are quota
# counters, which say nothing about whether a snapshot was actually taken.
resource "google_logging_metric" "scheduled_snapshot" {
  project     = var.project_id
  name        = "hrms/scheduled_snapshot_taken"
  description = "Counts scheduled snapshot events on the production disk. Drives the snapshot-stopped alert."

  # Scoped by ZONE rather than by disk id, deliberately. A disk id changes when
  # the disk is recreated — which is exactly what a whole-VM recovery does — so
  # a filter pinned to the current id would go silent immediately after a
  # restore and alert about the machine that had just been rescued.
  #
  # It is scoped at all, rather than matching any disk, so that a snapshot of
  # some unrelated disk elsewhere cannot satisfy the alert while production's
  # schedule is dead.
  filter = join(" AND ", [
    "logName=\"projects/${var.project_id}/logs/cloudaudit.googleapis.com%2Fsystem_event\"",
    "resource.type=\"gce_disk\"",
    "resource.labels.zone=\"${var.zone}\"",
    "protoPayload.methodName=\"ScheduledSnapshots\"",
    "severity=\"INFO\"",
  ])

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_monitoring_alert_policy" "snapshots_stopped" {
  project      = var.project_id
  display_name = "${local.alert_prefix} P2b Automated snapshots have stopped (>5h)"
  combiner     = "OR"

  documentation {
    content   = <<-EOT
      No scheduled snapshot has been recorded on the production disk for over
      five hours. Backups have stopped, and nothing else here would have told
      you.

      Check, in order:

        1. Is the schedule still attached to the disk?
             gcloud compute disks describe odoo-hrms-prod \
               --zone=us-central1-c --format="value(resourcePolicies)"
        2. Do the snapshots actually exist?
             gcloud compute snapshots list \
               --filter="sourceDisk~odoo-hrms-prod" \
               --sort-by=~creationTimestamp --limit=5
        3. Has the policy itself been changed or deleted?
             gcloud compute resource-policies list --region=us-central1

      A detached policy is the common cause and it is completely silent: the
      disk keeps working perfectly and simply stops being backed up.

      REMEMBER WHAT A SNAPSHOT IS NOT. These are crash-consistent, not
      application-consistent. For a restore you actually trust, take a logical
      dump:

        sudo docker exec odoo-db pg_dump -U odoo odoo_hrms_db | gzip > dump.sql.gz

      The boot disk has auto_delete = false, so it survives deletion of the
      instance and a whole-VM recovery is a matter of attaching it to a new one.

      WINDOW: snapshots run every 4 hours, so this fires after roughly one
      missed run plus an hour of slack. A single late run should not trip it;
      two consecutive misses will.
    EOT
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "no scheduled snapshot event in over 5 hours"

    # ABSENCE, not a threshold. A log-based counter metric emits nothing at all
    # when no matching log arrives — it does not emit a zero. A threshold
    # condition like "count < 1" therefore has no data to evaluate and stays
    # silent through the very outage it was written for.
    condition_absent {
      filter = join(" AND ", [
        "metric.type=\"logging.googleapis.com/user/${google_logging_metric.scheduled_snapshot.name}\"",
        "resource.type=\"gce_disk\"",
      ])

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_COUNT"
      }

      # 5 h — the 4-hourly schedule (compute.tf) plus an hour of slack.
      #
      # This number is why that schedule changed. Cloud Monitoring refuses an
      # absence duration above 23h30m, so against the previous DAILY schedule
      # there was no usable window at all: consecutive snapshots were 24 h apart
      # to within a second, and any window short enough to be accepted also
      # fired shortly before every healthy snapshot.
      duration = "18000s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = local.alert_channels

  alert_strategy {
    auto_close = "86400s"
  }
}

# ── P3: memory pressure ────────────────────────────────────────────────────────
#
# Measured at 37.57% used with the prefork workers running, so 85% is a genuine
# anomaly rather than a round number. Note this baseline is meaningfully higher
# than CRM's ~20%: this is an e2-medium with 4 GB running 3 HTTP workers plus
# cron and gevent, and a machine upgrade was explicitly out of scope, so the
# headroom here is real but thinner.
#
# Worth alerting on separately from the site check because Odoo's own worker
# recycling hides it for a while: limit_memory_hard kills and restarts a worker
# rather than letting it exhaust the host, so the site keeps answering while
# requests are dropped underneath. The symptom is slowness, not an outage, and
# nothing else here would report it.
#
# NOTE those Odoo limits are VIRTUAL memory (RLIMIT_AS), which is why
# limit_memory_hard = 671088640 reads oddly against this metric. This alert
# watches the host's real memory. The two measure different things; do not try
# to reconcile the numbers.
resource "google_monitoring_alert_policy" "memory_pressure" {
  project      = var.project_id
  display_name = "${local.alert_prefix} P3 Host memory above 85%"
  combiner     = "OR"

  documentation {
    content   = <<-EOT
      Host memory is above 85%. Baseline with the prefork workers running is
      about 38%, so this is a real change, not normal variation.

      Check for a worker leaking rather than assuming load:

        sudo docker exec odoo-app ps -o pid,rss,vsz,etime,cmd -C odoo

      Odoo recycles a worker that exceeds limit_memory_hard, so the site may
      still be answering while requests are being dropped. Repeated "virtual
      memory limit reached" in the Odoo log is worker recycling, and means the
      limits need review rather than the host.

      Remember Postgres is on the same 4 GB host with max_connections = 60.
      db_maxconn = 5 is per PROCESS and Odoo keeps TWO pools per process, giving
      a ceiling of 5 x 2 x 5 = 50. Raising db_maxconn without redoing that
      arithmetic is a way to turn memory pressure into connection exhaustion.
    EOT
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "memory used > 85%"

    condition_threshold {
      filter = join(" AND ", [
        "metric.type=\"agent.googleapis.com/memory/percent_used\"",
        "resource.type=\"gce_instance\"",
        # As with disk: state="free" reads 40.42% and state="cached" 19.06%.
        # Without this label the condition is meaningless.
        "metric.label.state=\"used\"",
      ])

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }

      comparison      = "COMPARISON_GT"
      threshold_value = 85
      duration        = "600s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = local.alert_channels

  alert_strategy {
    auto_close = "86400s"
  }
}

# ── P4: the TLS certificate is close to expiring ──────────────────────────────
#
# Traefik renews via ACME automatically, so this should never fire. It exists
# because of where the failure notice would otherwise go — Let's Encrypt's
# warnings go to the ACME contact address configured on the resolver, not to
# anyone watching this project. If renewal breaks, they land somewhere nobody
# monitors and the first anyone hears of it is the site failing.
#
# P1 already catches an EXPIRED certificate, because validate_ssl is on. This
# one is deliberately earlier: fifteen days is enough to debug an ACME problem
# calmly instead of during an outage.
resource "google_monitoring_alert_policy" "ssl_expiring" {
  project      = var.project_id
  display_name = "${local.alert_prefix} P4 TLS certificate expires in under 15 days"
  combiner     = "OR"

  documentation {
    content   = <<-EOT
      The certificate for ${var.public_host} expires in under 15 days and has
      not been renewed.

      Traefik renews automatically via ACME, so this firing means renewal is
      broken. It is a warning, not yet an outage — but it becomes an outage on a
      known date.

        sudo docker logs traefik 2>&1 | grep -i acme

      The certificate lives in ./letsencrypt/acme.json under /opt/odoo-hrms. The
      tlsChallenge resolver needs PORT 80 reachable from the internet to
      complete a renewal, so confirm the firewall still permits it —
      default-allow-http covers this via the http-server tag on the instance.
      Phase 5 deleted four firewall rules but deliberately kept port 80 open for
      exactly this reason: closing it turns a working renewal into a silent
      expiry.
    EOT
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "time until certificate expiry < 15 days"

    condition_threshold {
      filter = join(" AND ", [
        "metric.type=\"monitoring.googleapis.com/uptime_check/time_until_ssl_cert_expires\"",
        "resource.type=\"uptime_url\"",
        "metric.label.check_id=\"${google_monitoring_uptime_check_config.site.uptime_check_id}\"",
      ])

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_MEAN"
      }

      comparison      = "COMPARISON_LT"
      threshold_value = 15
      duration        = "3600s"

      trigger {
        count = 1
      }
    }
  }

  notification_channels = local.alert_channels

  alert_strategy {
    auto_close = "86400s"
  }
}
