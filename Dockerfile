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
      description="Odoo HRMS Production with BigQuery support"

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

# Copy custom entrypoint script
COPY --chmod=755 ./entrypoint.sh /usr/local/bin/entrypoint.sh

# Copy custom addons
# Note: In docker-compose, this is mounted as volume for development
# But we copy here for standalone image builds
COPY --chown=odoo:odoo ./custom_addons /mnt/extra-addons/custom

# Switch back to non-root user for security
USER odoo

# Working directory
WORKDIR /usr/lib/python3/dist-packages/odoo

# Expose ports
EXPOSE 8069 8072

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8069/web/database/selector || exit 1

# Use custom entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["odoo"]
