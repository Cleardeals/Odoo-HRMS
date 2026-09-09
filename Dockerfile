# ==============================================================================
# Odoo HRMS - Production Dockerfile
# ==============================================================================
# Based on official Odoo 19.0 image with isolated virtual environment
# Optimized for e2-medium (2 vCPU, 4GB RAM)
# Build time: ~3-5 minutes
# ==============================================================================

FROM odoo:19.0

LABEL vendor="ClearDeals" \
      version="19.0" \
      description="Odoo HRMS Production"

# Switch to root for system modifications
USER root

# Install system dependencies
# Grouped by purpose for maintainability
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools for Python packages with C extensions
    build-essential \
    python3-dev \
    # LDAP/SASL authentication
    libsasl2-dev \
    libldap2-dev \
    # Virtual environment support
    python3-venv \
    python3-full \
    # Version control (if needed for pip installs from git)
    git \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment with access to system packages
# This allows us to install additional packages without breaking system Python
RUN python3 -m venv --system-site-packages /opt/odoo-venv

# Configure environment to use venv by default
ENV VIRTUAL_ENV="/opt/odoo-venv" \
    PATH="/opt/odoo-venv/bin:$PATH"

# Upgrade pip in venv (faster than --upgrade during install)
RUN /opt/odoo-venv/bin/pip install --no-cache-dir --upgrade pip

# Install additional Python dependencies
# Layer caching: requirements.txt changes less frequently than code
COPY ./requirements.txt /tmp/requirements.txt
RUN /opt/odoo-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Set ownership of venv to odoo user
RUN chown -R odoo:odoo /opt/odoo-venv

# Copy custom entrypoint script.
#
# Deliberately NOT `COPY --chmod=755`. That option requires BuildKit, and
# `gcr.io/cloud-builders/docker` — which both cloudbuild.yaml and
# cloudbuild.ci.yaml use — runs the LEGACY builder, where it is a hard error:
#
#   Step 11/18 : COPY --chmod=755 ./entrypoint.sh /usr/local/bin/entrypoint.sh
#   the --chmod option requires BuildKit.
#
# The image built fine by hand on the VM, whose Docker has BuildKit enabled by
# default, so this was invisible until the first CI run — and it would have
# failed the CD build identically, meaning the pipeline could never have built
# an image at all.
#
# Setting DOCKER_BUILDKIT=1 on the build steps would also work, but this way the
# Dockerfile carries no dependency on which builder happens to be in use. Note
# `--chown` below is fine: only `--chmod` is BuildKit-only.
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

# ── Bake the application code INTO the image ──────────────────────────────────
#
# NOT under /mnt/extra-addons. The odoo:19.0 base image declares
#   VOLUME ["/mnt/extra-addons", "/var/lib/odoo"]
# — verified directly with `docker image inspect odoo:19.0`. So at runtime Docker
# mounts an ANONYMOUS EMPTY VOLUME over that path and silently hides anything
# baked beneath it.
#
# This image previously copied to /mnt/extra-addons/custom, which appeared to
# work only because docker-compose.yml bind-mounted ./custom_addons over the
# same path. That mount was the sole thing masking the problem, and on the CRM
# instance the equivalent mistake took production down: the addons vanished, the
# modules never loaded, the UI failed on a view controller and crons died on a
# KeyError.
#
# Removing the bind mount is the point. It is what makes an image tag mean
# something: with the mount, two containers on the same image SHA can run
# different application code depending on what the VM has checked out, and
# re-pinning a previous image leaves the new addons on disk, still mounted — so
# rollback is a fiction.
#
# Nothing was ever wrong with COPY. The path was. /opt is not a declared volume,
# so code baked there survives.
COPY --chown=odoo:odoo ./custom_addons /opt/cleardeals-addons

# Switch back to non-root user for security
USER odoo

# Working directory
WORKDIR /usr/lib/python3/dist-packages/odoo

# Expose ports
EXPOSE 8069 8072

# ── Health check ──────────────────────────────────────────────────────────────
#
# /web/database/selector WAS NOT A HEALTH CHECK. Read the route in
# addons/web/controllers/database.py:59 — it renders its template
# unconditionally and returns 200 without ever touching the database. It was
# answering every 30 seconds in the Odoo log while proving nothing beyond "the
# HTTP worker is alive". A gate like that goes green with Postgres down.
#
# db_server_status=1 makes the route open a real cursor and return HTTP 500 when
# it cannot — confirmed in addons/web/controllers/home.py:177, which sets
# status = 500 on psycopg2.Error. So `curl -f` is a genuine gate here, with no
# need to parse the body.
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f "http://localhost:8069/web/health?db_server_status=1" || exit 1

# Use custom entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["odoo"]
