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
echo "-----------------------------------"
echo "Validating dependencies..."
python3 -c "from google.cloud import bigquery; print('✓ BigQuery import successful')" 2>/dev/null || echo "✗ BigQuery not available"
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
