#!/bin/bash
# ==============================================================================
# Odoo HRMS - Custom Entrypoint Script
# ==============================================================================
# This script:
# 1. Activates the Python virtual environment
# 2. Validates critical imports (BigQuery, Odoo)
# 3. Waits for PostgreSQL to be ready
# 4. Launches Odoo with proper Python interpreter
# ==============================================================================

set -e

# ------------------------------------------------------------------------------
# Activate Virtual Environment
# ------------------------------------------------------------------------------
export VIRTUAL_ENV="/opt/odoo-venv"
export PATH="/opt/odoo-venv/bin:$PATH"

# ------------------------------------------------------------------------------
# Startup Diagnostics (helpful for debugging)
# ------------------------------------------------------------------------------
echo "==================================="
echo "Odoo HRMS Container Starting"
echo "==================================="
echo "Python: $(which python3)"
echo "Python Version: $(python3 --version)"

# Validate critical imports
#
# The BigQuery probe that used to sit here has been removed. It has ALWAYS
# printed "✗ BigQuery not available" on this image and always will: there is no
# google-cloud-* package in requirements.txt and no custom addon imports
# bigquery. It was harmless — `|| echo` rather than a failure — but a startup
# banner that reports a missing dependency nobody needs teaches whoever reads
# the logs to ignore the banner.
#
# HRMS genuinely has no BigQuery dependency, unlike the CRM instance where 22
# files across lead_suggestor and leads/models/lead_score.py query it. That is
# why no BigQuery service account or cross-project IAM grant appears anywhere in
# infrastructure/terraform.
echo "-----------------------------------"
echo "Validating dependencies..."
python3 -c "import odoo; print('✓ Odoo import successful')" 2>/dev/null || echo "✗ Odoo not available"
echo "-----------------------------------"

# ------------------------------------------------------------------------------
# Wait for Database (if DB_HOST is set)
# ------------------------------------------------------------------------------
if [ -n "$DB_HOST" ]; then
    echo "Waiting for PostgreSQL at $DB_HOST:${DB_PORT:-5432}..."
    until pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "${DB_USER:-odoo}" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping 1s"
        sleep 1
    done
    echo "✓ PostgreSQL is ready"
fi

# ------------------------------------------------------------------------------
# Execute Odoo Command
# ------------------------------------------------------------------------------
# If first argument is 'odoo', transform it to use venv's Python
if [ "$1" = "odoo" ]; then
    shift  # Remove 'odoo' from arguments
    set -- python3 /usr/bin/odoo "$@"  # Prepend Python interpreter
fi

echo "==================================="
echo "Executing: $*"
echo "==================================="

# Execute the final command (use 'exec' to replace shell with process)
exec "$@"
