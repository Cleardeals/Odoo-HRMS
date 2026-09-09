#!/usr/bin/env bash
#
# Refresh the ERD schema snapshot from production.
#
# READ-ONLY. Every statement below is a SELECT or a COPY (... ) TO STDOUT.
# Nothing is written to the production VM or database.
#
#   ./docs/erd/capture_schema.sh
#   python3 docs/erd/generate_erd.py
#   dot -Tpdf docs/erd/erd.dot -o docs/erd/ERD.pdf
#
set -euo pipefail

ZONE="us-central1-c"

# The project id is deliberately NOT hardcoded: this repository is public.
# Supply it from the environment, or let gcloud's active configuration provide
# it:
#
#   PROJECT=my-project ./docs/erd/capture_schema.sh
#
PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
[[ -n "${PROJECT}" && "${PROJECT}" != "(unset)" ]] || {
  echo "capture_schema: set PROJECT, or run 'gcloud config set project <id>'" >&2
  exit 1
}

INSTANCE="odoo-hrms-prod"

# Resolved by OS Login now rather than being a fixed local account. Note that
# since Phase 5 the ONLY route to this VM is IAP, so the gcloud ssh calls below
# need --tunnel-through-iap; a plain SSH to the public address is refused.
SSH_USER="${SSH_USER:-tech}"
CONTAINER="odoo-db"
DB="odoo_hrms_db"

OUT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_sql() {
  # --tunnel-through-iap is REQUIRED since Phase 5 of the infrastructure
  # migration. default-allow-ssh was deleted, so there is no route to port 22
  # from the internet at all and a plain gcloud compute ssh now times out.
  #
  # sudo, because Docker is not accessible to the login user under OS Login.
  gcloud compute ssh "${SSH_USER}@${INSTANCE}" \
    --zone "$ZONE" --project "$PROJECT" --tunnel-through-iap \
    --command "sudo docker exec -i ${CONTAINER} psql -U odoo -d ${DB} -c \"$1\""
}

echo "==> columns.csv"
run_sql "COPY (
  select c.table_name, c.ordinal_position, c.column_name, c.data_type,
         c.character_maximum_length, c.numeric_precision, c.numeric_scale, c.is_nullable
  from information_schema.columns c
  where c.table_schema='public'
  order by c.table_name, c.ordinal_position
) TO STDOUT WITH CSV HEADER" > "$OUT/columns.csv"

echo "==> constraints.csv"
run_sql "COPY (
  select con.conname, con.contype, src.relname as src_table,
         (select string_agg(a.attname, ',' order by k.ord)
            from unnest(con.conkey) with ordinality k(attnum,ord)
            join pg_attribute a on a.attrelid=con.conrelid and a.attnum=k.attnum) as src_cols,
         tgt.relname as tgt_table,
         (select string_agg(a.attname, ',' order by k.ord)
            from unnest(con.confkey) with ordinality k(attnum,ord)
            join pg_attribute a on a.attrelid=con.confrelid and a.attnum=k.attnum) as tgt_cols,
         con.confdeltype
  from pg_constraint con
  join pg_class src on src.oid=con.conrelid
  left join pg_class tgt on tgt.oid=con.confrelid
  join pg_namespace n on n.oid=src.relnamespace and n.nspname='public'
  where con.contype in ('p','f','u')
  order by src.relname, con.contype, con.conname
) TO STDOUT WITH CSV HEADER" > "$OUT/constraints.csv"

echo "==> fields.csv (Odoo field -> declaring module)"
run_sql "COPY (
  select m.model as odoo_model, m.name as table_hint, f.name as field_name,
         f.ttype, f.relation, f.required, f.store, d.module
  from ir_model_fields f
  join ir_model m on m.id = f.model_id
  left join ir_model_data d on d.model='ir.model.fields' and d.res_id=f.id
  order by m.model, f.name
) TO STDOUT WITH CSV HEADER" > "$OUT/fields.csv"

echo
echo "Snapshot refreshed. Next:"
echo "  python3 docs/erd/generate_erd.py"
echo "  dot -Tpdf docs/erd/erd.dot -o docs/erd/ERD.pdf"
echo "  dot -Tsvg docs/erd/erd.dot -o docs/erd/ERD.svg"
echo "  dot -Tpng -Gdpi=150 docs/erd/erd.dot -o docs/erd/ERD.png"
