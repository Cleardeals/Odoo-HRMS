# ER Diagram — Odoo HRMS

The ER diagram is **generated from the production database, not drawn**. Table
structure, column types, keys and constraints are introspected from a read-only
snapshot of `odoo_hrms_db`; only scope, grouping and prose are hand-written.

## Files

| File | Hand-edited? | What it is |
|---|---|---|
| `ERD.pdf` | no | The diagram. Single-page vector, 81 × 72 in — zoom freely, text is selectable. |
| `ERD.drawio` | no | draw.io / diagrams.net source, editable by hand. |
| `ERD.svg` / `ERD.png` | no | Web and raster renderings of the same diagram. |
| `erd.dot` | **no — generated** | Graphviz source. Diffable; this is what review should compare. |
| `erd_meta.yaml` | **yes** | The only hand-maintained file: scope, subsystem grouping, colours, prose. |
| `generate_erd.py` | yes | The generator. Emits `erd.dot` and `ERD.drawio` from the snapshot. |
| `columns.csv`, `constraints.csv`, `fields.csv` | **no — captured** | The production schema snapshot. |
| `row_counts.csv` | **no — captured** | Row counts at capture time; the evidence behind "actively used". |
| `capture_schema.sh` | yes | Refreshes the snapshot from production, read-only. |

## Scope, and why

The instance has **116 modules installed**. Drawing all of them would produce a
wall nobody reads, so the diagram covers the four subsystems we actually operate:

| Subsystem | Tables | Why it is in scope |
|---|---|---|
| Employee master & org structure | `hr_employee`, `hr_version`, `hr_department`, `hr_job`, `hr_employee_family` | `hr_employee_cleardeals` is ours and declares **63 of `hr_employee`'s columns** |
| Employee document vault | `hr_employee_document`, `document_type`, `doc_attach_rel` | 134 vault records, 175 attachment links |
| Document template manager | `document_template`, `document_template_variable`, `document_category`, `document_tag` | Ours; 16 templates, 141 variables |
| Recruitment pipeline | `hr_applicant`, `hr_recruitment_stage`, `hr_applicant_refuse_reason` | 2,090 applicants — the busiest data in the instance; `custom_recruitment_fix` patches its refusal mail |
| Odoo framework (boundary) | `res_company`, `res_users`, `res_partner`, `ir_attachment` | Context only — drawn greyed, abbreviated to referenced columns |

Deliberately excluded: payroll, loans, salary advance, leaves, attendance,
timesheets, expenses and the dashboard. Their modules are installed, but the
tables are empty in production — `hr_payslip`, `hr_loan`, `salary_advance`,
`hr_resignation` and `employee_transfer` all hold zero rows. `history_employee`
and `hr_employee_shift` are not installed at all.

If payroll goes live, add the tables to `erd_meta.yaml` and regenerate.

## Reading the diagram

IE (Crow's Foot) notation; the legend is drawn on the diagram itself.

- **`PK` / `FK` / `U` / `N`** — primary key, foreign key, unique constraint, nullable.
- **Column tint** marks the module that *declared* the field, taken from Odoo's
  own `ir_model_data`. Untinted columns are stock Odoo 19. This is what makes
  the extent of our customization visible at a glance.
- **Dashed edges** point at boundary (framework) tables.
- **Two-column entities** — tables above 40 columns are laid out in two column
  lists so the box stays a sane height. `hr_employee` has 106 columns.

### Two suppressions, stated plainly

Some foreign keys are drawn as columns but **not** as edges, because every table
has them and they all point at one node:

- `create_uid`, `write_uid` → `res_users`
- `company_id` → `res_company`, `message_main_attachment_id` → `ir_attachment`

Forty edges converging on a single box hides the relationships that carry
meaning. The columns are still shown, so nothing is concealed. Both suppression
lists live in `erd_meta.yaml` (`audit_columns`, `ubiquitous_columns`) and the
Graphviz and draw.io outputs apply the same list — the two renderings show the
same 45 relationships.

## Regenerating

```bash
./docs/erd/capture_schema.sh && python3 docs/erd/generate_erd.py && dot -Tpdf docs/erd/erd.dot -o docs/erd/ERD.pdf
```

The capture step needs `gcloud` auth and reaches production **read-only** — every
statement is a `SELECT` or `COPY (...) TO STDOUT`. Nothing is written to the VM
or the database. If the schema has not changed, skip the capture and just run the
generator.

Requirements: `graphviz` (`brew install graphviz`) and `pyyaml`.

Adding a table to the diagram requires an entry in `erd_meta.yaml`; the generator
exits with an error naming any table listed there that is missing from the
snapshot, so scope and snapshot cannot silently drift apart.

## Findings worth acting on

Two things surfaced while building this. Neither is fixed here — this directory
is documentation only.

1. **`doc_attachment_ids` is a dead duplicate table.** `oh_employee_documents_expiry`
   has two join tables for the same employee-document ⇄ attachment relation:
   `doc_attach_rel` (175 rows, live) and `doc_attachment_ids` (0 rows). The dead
   one is left out of the diagram.
2. **`hr_employee_family` is empty.** `hr_employee_updation` is installed and the
   table exists, but no family or dependant data has ever been captured. It is
   drawn, flagged `EMPTY IN PRODUCTION`, so the diagram does not imply the data
   lives somewhere else.
