#!/usr/bin/env python3
"""
Generate the Odoo HRMS ER diagram from a production schema snapshot.

Structure (tables, columns, types, keys, constraints) is read from the CSV
snapshot in this directory; presentation (scope, grouping, colours, prose) comes
from erd_meta.yaml.  Nothing structural is typed by hand.

Outputs
    erd.dot      Graphviz source  -> rendered to ERD.pdf / ERD.svg / ERD.png
    ERD.drawio   draw.io / diagrams.net XML, editable by hand

Usage
    python3 docs/erd/generate_erd.py
    dot -Tpdf docs/erd/erd.dot -o docs/erd/ERD.pdf

Refreshing the snapshot from production (read-only) is documented in README.md.
"""

from __future__ import annotations

import csv
import html
import sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Snapshot loading
# ---------------------------------------------------------------------------


def load_csv(name: str) -> list[dict]:
    with (HERE / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def short_type(row: dict) -> str:
    """Compress an information_schema type into something readable."""
    t = row["data_type"]
    aliases = {
        "character varying": "varchar",
        "timestamp without time zone": "timestamp",
        "timestamp with time zone": "timestamptz",
        "double precision": "float8",
        "character": "char",
    }
    t = aliases.get(t, t)
    if t == "varchar" and row.get("character_maximum_length"):
        t = f"varchar({row['character_maximum_length']})"
    if t == "numeric" and row.get("numeric_precision"):
        scale = row.get("numeric_scale") or "0"
        t = f"numeric({row['numeric_precision']},{scale})"
    return t


class Schema:
    """The introspected schema, indexed for lookup."""

    def __init__(self) -> None:
        cols = load_csv("columns.csv")
        cons = load_csv("constraints.csv")
        fields = load_csv("fields.csv")

        self.columns: dict[str, list[dict]] = defaultdict(list)
        for r in cols:
            self.columns[r["table_name"]].append(r)

        self.pk: dict[str, set[str]] = defaultdict(set)
        self.unique: dict[str, list[str]] = defaultdict(list)
        self.fks: list[dict] = []
        self.fk_cols: dict[str, set[str]] = defaultdict(set)

        for r in cons:
            src, kind = r["src_table"], r["contype"]
            src_cols = [c for c in (r["src_cols"] or "").split(",") if c]
            if kind == "p":
                self.pk[src].update(src_cols)
            elif kind == "u":
                self.unique[src].append(", ".join(src_cols))
            elif kind == "f":
                self.fks.append(
                    {
                        "src": src,
                        "src_col": src_cols[0] if src_cols else "",
                        "tgt": r["tgt_table"],
                        "tgt_col": (r["tgt_cols"] or "id").split(",")[0],
                        "on_delete": r["confdeltype"],
                    },
                )
                self.fk_cols[src].update(src_cols)

        # field name -> declaring module, per Odoo model, mapped onto tables
        self.field_module: dict[tuple[str, str], str] = {}
        for r in fields:
            table = r["odoo_model"].replace(".", "_")
            if r.get("module"):
                self.field_module[(table, r["field_name"])] = r["module"]

    def module_of(self, table: str, column: str) -> str | None:
        return self.field_module.get((table, column))


# ---------------------------------------------------------------------------
# Graphviz emitter
# ---------------------------------------------------------------------------

BORDER = "#94a3b8"
PK_BG = "#eef4fb"
FK_BG = "#fdf6e8"
NOTE_BG = "#f6f8fa"


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def cell_group(schema: Schema, table: str, meta: dict, c: dict | None) -> str:
    """Render one column as three <TD>s, or three empty padding cells."""
    if c is None:
        return '<TD></TD><TD></TD><TD></TD>'

    module_colors = meta["module_colors"]
    name = c["column_name"]
    is_pk, is_fk = name in schema.pk[table], name in schema.fk_cols[table]
    marker = "<B>PK</B>" if is_pk else ("<B>FK</B>" if is_fk else "")

    owner = schema.module_of(table, name)
    bg = PK_BG if is_pk else (FK_BG if is_fk else module_colors.get(owner or "", ""))
    bg_attr = f' BGCOLOR="{bg}"' if bg else ""

    label = f"<B>{esc(name)}</B>" if is_pk else esc(name)
    typ = short_type(c)
    if c["is_nullable"] == "YES":
        typ += " N"

    return (
        f'<TD ALIGN="LEFT" PORT="l_{esc(name)}"{bg_attr}>{marker}</TD>'
        f'<TD ALIGN="LEFT"{bg_attr}>{label}</TD>'
        f'<TD ALIGN="LEFT" PORT="r_{esc(name)}"{bg_attr}>{esc(typ)}</TD>'
    )


def entity_rows(
    schema: Schema, table: str, meta: dict, only: list[str] | None,
) -> tuple[list[str], int]:
    """Build the <TR> rows for one entity table, and the table's column span."""
    cols = schema.columns[table]
    if only:
        index = {c["column_name"]: c for c in cols}
        cols = [index[c] for c in only if c in index]

    # Wide tables are split into two side-by-side column lists so the entity
    # box does not become a 106-row ribbon that dictates the whole canvas.
    threshold = meta.get("wide_table_threshold", 40)
    lanes = 2 if len(cols) > threshold else 1
    span = 3 * lanes

    rows: list[str] = []
    if lanes == 1:
        for c in cols:
            rows.append(f'        <TR>{cell_group(schema, table, meta, c)}</TR>')
    else:
        half = (len(cols) + 1) // 2
        left, right = cols[:half], cols[half:]
        right += [None] * (len(left) - len(right))
        for a, b in zip(left, right):
            rows.append(
                "        <TR>"
                + cell_group(schema, table, meta, a)
                + cell_group(schema, table, meta, b)
                + "</TR>",
            )

    uniques = schema.unique.get(table, [])
    if uniques:
        body = "".join(f'U ({esc(u)})<BR ALIGN="LEFT"/>' for u in sorted(uniques))
        rows.append(
            f'        <TR><TD ALIGN="LEFT" COLSPAN="{span}" BGCOLOR="{NOTE_BG}">'
            f'<FONT POINT-SIZE="9" COLOR="#444444">{body}</FONT></TD></TR>',
        )
    return rows, span


def entity_node(
    schema: Schema, table: str, spec: dict, meta: dict, only: list[str] | None = None,
) -> str:
    group = meta["groups"][spec["group"]]
    subtitle = spec.get("subtitle", "")
    if spec.get("empty"):
        subtitle += " · EMPTY IN PRODUCTION"
    if only:
        subtitle += f" · {len(only)} of {len(schema.columns[table])} columns shown"

    rows, span = entity_rows(schema, table, meta, only)
    header = (
        f'        <TR><TD BGCOLOR="{group["color"]}" COLSPAN="{span}">'
        f'<FONT COLOR="#ffffff" POINT-SIZE="14"><B>{esc(table)}</B></FONT><BR/>'
        f'<FONT COLOR="{group["accent"]}" POINT-SIZE="9">{esc(subtitle)}</FONT></TD></TR>'
    )
    return (
        f"    {table} [label=<\n"
        f'      <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5" COLOR="{BORDER}">\n'
        f"{header}\n" + "\n".join(rows) + "\n      </TABLE>>];\n"
    )


def legend_node(meta: dict) -> str:
    swatches = "".join(
        f'        <TR><TD BGCOLOR="{c}" WIDTH="18"></TD>'
        f'<TD ALIGN="LEFT">column declared by <B>{esc(m)}</B></TD></TR>\n'
        for m, c in meta["module_colors"].items()
    )
    groups = "".join(
        f'        <TR><TD BGCOLOR="{g["color"]}" WIDTH="18"></TD>'
        f'<TD ALIGN="LEFT">{esc(g["label"])}</TD></TR>\n'
        for g in meta["groups"].values()
    )
    notes = "".join(
        f'        <TR><TD COLSPAN="2" ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#444444">'
        f'• {esc(n)}</FONT></TD></TR>\n'
        for n in meta.get("diagram_notes", [])
    )
    return (
        "    legend [label=<\n"
        f'      <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5" COLOR="{BORDER}">\n'
        '        <TR><TD BGCOLOR="#f1f4f8" COLSPAN="2"><B>Legend &#8212; IE (Crow&#8217;s Foot) notation</B></TD></TR>\n'
        '        <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">primary key</TD></TR>\n'
        '        <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">foreign key (enforced by the database)</TD></TR>\n'
        '        <TR><TD ALIGN="LEFT">U</TD><TD ALIGN="LEFT">unique constraint</TD></TR>\n'
        '        <TR><TD ALIGN="LEFT">N</TD><TD ALIGN="LEFT">nullable</TD></TR>\n'
        '        <TR><TD ALIGN="LEFT">&#9553;&#9472;</TD><TD ALIGN="LEFT">exactly one &#8594; many (mandatory FK)</TD></TR>\n'
        '        <TR><TD ALIGN="LEFT">&#9675;&#9472;</TD><TD ALIGN="LEFT">zero or one &#8594; many (nullable FK)</TD></TR>\n'
        '        <TR><TD BGCOLOR="#f1f4f8" COLSPAN="2"><B>Subsystems</B></TD></TR>\n'
        f"{groups}"
        '        <TR><TD BGCOLOR="#f1f4f8" COLSPAN="2"><B>Column ownership</B></TD></TR>\n'
        f"{swatches}"
        '        <TR><TD BGCOLOR="#f1f4f8" COLSPAN="2"><B>Notes</B></TD></TR>\n'
        f"{notes}"
        "      </TABLE>>];\n"
    )


def build_dot(schema: Schema, meta: dict) -> str:
    detail = meta["tables"]
    links = meta.get("link_tables", {}) or {}
    boundary = meta.get("boundary_tables", {}) or {}
    in_scope = set(detail) | set(links) | set(boundary)

    total_cols = sum(len(schema.columns[t]) for t in in_scope)
    title = meta["title"]
    subtitle = " ".join(meta["subtitle"].split())

    out: list[str] = []
    out.append(
        "/* " + "=" * 75 + "\n"
        f"   {title}\n"
        "   Notation: IE / Crow's Foot   |   Engine: Graphviz (dot)\n\n"
        "   GENERATED FILE - DO NOT EDIT BY HAND.\n"
        "   Structure is introspected from the production schema snapshot in\n"
        "   docs/erd/*.csv; presentation comes from docs/erd/erd_meta.yaml.\n"
        "   Regenerate with:  python3 docs/erd/generate_erd.py\n\n"
        f"   Source: {meta['source']['database']} on {meta['source']['host']}\n"
        f"   Access: {meta['source']['access']}\n"
        "   " + "=" * 75 + " */\n",
    )
    out.append("digraph odoo_hrms_erd {\n")
    out.append(
        "    graph [\n"
        "        rankdir    = LR,\n"
        "        splines    = spline,\n"
        "        newrank    = false,\n"
        "        compound   = true,\n"
        "        nodesep    = 0.55,\n"
        '        ranksep    = "1.9 equally",\n'
        "        pad        = 0.5,\n"
        '        bgcolor    = "#ffffff",\n'
        '        fontname   = "Helvetica",\n'
        "        labelloc   = t,\n"
        "        labeljust  = l,\n"
        f'        label      = <<FONT POINT-SIZE="26"><B>{esc(title)}</B></FONT><BR/><BR/>'
        f'<FONT POINT-SIZE="13" COLOR="#555555">{esc(subtitle)} &#183; '
        f"{len(in_scope)} tables &#183; {total_cols} columns &#183; IE (Crow&#8217;s Foot) notation"
        '<BR ALIGN="LEFT"/>'
        "Generated from the live production schema &#183; "
        "PK = primary key, FK = foreign key, U = unique, N = nullable"
        '<BR ALIGN="LEFT"/></FONT><BR/>>\n'
        "    ];\n",
    )
    out.append('    node [shape = plaintext, fontname = "Helvetica"];\n')
    out.append(
        '    edge [fontname = "Helvetica", fontsize = 9.5, color = "#5b6470", penwidth = 1.4,\n'
        "          dir = both, arrowhead = crowodot];\n\n",
    )

    out.append("    /* --- Entities, clustered by subsystem ------------------------ */\n\n")
    all_specs: dict[str, dict] = {}
    for table, spec in detail.items():
        all_specs[table] = spec
    for table, spec in links.items():
        all_specs[table] = spec
    for table, spec in boundary.items():
        all_specs[table] = spec

    by_group: dict[str, list[str]] = defaultdict(list)
    for table, spec in all_specs.items():
        by_group[spec["group"]].append(table)

    for gname, group in meta["groups"].items():
        members = by_group.get(gname, [])
        if not members:
            continue
        out.append(
            f"    subgraph cluster_{gname} {{\n"
            f'        label = <<FONT POINT-SIZE="15" COLOR="{group["color"]}">'
            f'<B>{esc(group["label"])}</B></FONT>>;\n'
            f'        labelloc = t; labeljust = l;\n'
            f'        style = "rounded"; color = "{group["color"]}"; penwidth = 1.6;\n'
            f'        bgcolor = "#fbfcfd"; margin = 22;\n',
        )
        for table in members:
            spec = all_specs[table]
            only = spec.get("columns") if table in boundary else None
            out.append("    " + entity_node(schema, table, spec, meta, only=only))
        out.append("    }\n\n")

    out.append("\n    /* --- Relationships (IE / Crow's Foot) ------------------------ */\n")
    out.append(
        "    /* Audit-column edges (create_uid / write_uid -> res_users) are\n"
        "       suppressed: every table has them, and drawing 40 edges into one\n"
        "       node hides the relationships that carry meaning. */\n\n",
    )
    audit = set(meta.get("audit_columns") or []) | set(meta.get("ubiquitous_columns") or [])
    seen: set[tuple[str, str, str]] = set()
    for fk in sorted(schema.fks, key=lambda f: (f["tgt"] or "", f["src"], f["src_col"])):
        src, tgt, col = fk["src"], fk["tgt"], fk["src_col"]
        if src not in in_scope or tgt not in in_scope:
            continue
        if col in audit:
            continue
        key = (src, tgt, col)
        if key in seen:
            continue
        seen.add(key)

        spec = detail.get(src) or links.get(src) or boundary.get(src) or {}
        group = meta["groups"].get(spec.get("group", "core"), meta["groups"]["core"])

        col_row = next(
            (c for c in schema.columns[src] if c["column_name"] == col), None,
        )
        nullable = col_row is None or col_row["is_nullable"] == "YES"
        tail = "teeodot" if nullable else "tee"

        # boundary tables are drawn abbreviated; skip edges into hidden columns
        if src in boundary and col not in (boundary[src].get("columns") or []):
            continue
        if tgt in boundary and fk["tgt_col"] not in (boundary[tgt].get("columns") or []):
            continue

        # Edges touching a boundary table are drawn but excluded from rank
        # computation: res_company / res_partner / ir_attachment are referenced
        # from every cluster, and letting them constrain the layout stretches
        # the whole diagram to accommodate one framework node.
        crosses_boundary = src in boundary or tgt in boundary
        extra = (
            ' style = "dashed", weight = 1'
            if crosses_boundary
            else " weight = 12"
        )
        out.append(
            f'    {tgt}:r_{fk["tgt_col"]}:e -> {src}:l_{col}:w '
            f'[arrowtail = {tail}, color = "{group["edge"]}", label="{esc(col)}",{extra}];\n',
        )

    out.append("\n    /* --- Legend -------------------------------------------------- */\n\n")
    out.append(legend_node(meta))
    out.append("}\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# draw.io emitter
# ---------------------------------------------------------------------------

ROW_H = 20
HDR_H = 42
COL_W = 330
GAP_X = 480
GAP_Y = 70


def drawio_style(fill: str, stroke: str = "#4a5568") -> str:
    return (
        f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
        "align=left;verticalAlign=middle;spacingLeft=6;fontSize=11;"
    )


def build_drawio(schema: Schema, meta: dict) -> str:
    detail = meta["tables"]
    links = meta.get("link_tables", {}) or {}
    boundary = meta.get("boundary_tables", {}) or {}
    module_colors = meta["module_colors"]

    # lay entities out in columns, one column per subsystem
    order = ["core", "vault", "templates", "recruitment", "framework"]
    by_group: dict[str, list[tuple[str, dict, list[str] | None]]] = defaultdict(list)
    for t, s in detail.items():
        by_group[s["group"]].append((t, s, None))
    for t, s in links.items():
        by_group[s["group"]].append((t, s, None))
    for t, s in boundary.items():
        by_group[s["group"]].append((t, s, s.get("columns")))

    cells: list[str] = []
    port_of: dict[tuple[str, str], str] = {}
    cid = 2

    x = 40
    for group_name in order:
        entries = by_group.get(group_name, [])
        if not entries:
            continue
        group = meta["groups"][group_name]
        y = 80
        for table, spec, only in entries:
            cols = schema.columns[table]
            if only:
                index = {c["column_name"]: c for c in cols}
                cols = [index[c] for c in only if c in index]

            height = HDR_H + ROW_H * len(cols)
            tid = f"n{cid}"
            cid += 1

            subtitle = spec.get("subtitle", "")
            if spec.get("empty"):
                subtitle += " · EMPTY IN PRODUCTION"
            # draw.io renders the value as HTML, but the value lives in an XML
            # attribute — so the whole HTML fragment must itself be escaped.
            header_label = xml_escape(
                f"<b>{table}</b><br/>"
                f'<font style="font-size:9px">{subtitle}</font>',
                {'"': "&quot;"},
            )
            cells.append(
                f'        <mxCell id="{tid}" value="{header_label}" '
                f'style="swimlane;html=1;startSize={HDR_H};fillColor={group["color"]};'
                f'strokeColor=#2d3748;fontColor=#ffffff;fontSize=12;align=center;" '
                f'vertex="1" parent="1">\n'
                f'          <mxGeometry x="{x}" y="{y}" width="{COL_W}" height="{height}" as="geometry"/>\n'
                f"        </mxCell>",
            )

            pk, fkc = schema.pk[table], schema.fk_cols[table]
            for i, c in enumerate(cols):
                name = c["column_name"]
                rid = f"n{cid}"
                cid += 1
                port_of[(table, name)] = rid

                owner = schema.module_of(table, name)
                fill = (
                    PK_BG
                    if name in pk
                    else (FK_BG if name in fkc else module_colors.get(owner or "", "#ffffff"))
                )
                marker = "PK " if name in pk else ("FK " if name in fkc else "")
                typ = short_type(c) + (" N" if c["is_nullable"] == "YES" else "")
                label = xml_escape(f"{marker}{name} : {typ}")
                cells.append(
                    f'        <mxCell id="{rid}" value="{label}" '
                    f'style="{drawio_style(fill)}" vertex="1" parent="{tid}">\n'
                    f'          <mxGeometry y="{HDR_H + i * ROW_H}" width="{COL_W}" '
                    f'height="{ROW_H}" as="geometry"/>\n'
                    f"        </mxCell>",
                )
            y += height + GAP_Y
        x += GAP_X

    in_scope = set(detail) | set(links) | set(boundary)
    # Same edge suppression as the Graphviz output, so the two renderings show
    # the same relationships rather than disagreeing with each other.
    suppressed = set(meta.get("audit_columns") or []) | set(
        meta.get("ubiquitous_columns") or [],
    )
    seen: set[tuple[str, str, str]] = set()
    for fk in schema.fks:
        src, tgt, col = fk["src"], fk["tgt"], fk["src_col"]
        if src not in in_scope or tgt not in in_scope:
            continue
        if col in suppressed:
            continue
        if (src, tgt, col) in seen:
            continue
        seen.add((src, tgt, col))
        a = port_of.get((tgt, fk["tgt_col"]))
        b = port_of.get((src, col))
        if not a or not b:
            continue
        spec = detail.get(src) or links.get(src) or boundary.get(src) or {}
        group = meta["groups"].get(spec.get("group", "core"), meta["groups"]["core"])
        eid = f"e{cid}"
        cid += 1
        cells.append(
            f'        <mxCell id="{eid}" value="{xml_escape(col)}" '
            f'style="edgeStyle=entityRelationEdgeStyle;html=1;rounded=0;'
            f'strokeColor={group["edge"]};fontSize=9;endArrow=ERmany;startArrow=ERone;" '
            f'edge="1" parent="1" source="{a}" target="{b}">\n'
            f'          <mxGeometry relative="1" as="geometry"/>\n'
            f"        </mxCell>",
        )

    body = "\n".join(cells)
    title = xml_escape(meta["title"])
    return (
        f'<mxfile host="app.diagrams.net" type="device">\n'
        f'  <diagram id="odoo-hrms-erd" name="{title}">\n'
        f'    <mxGraphModel dx="1600" dy="1200" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="1169" pageHeight="826" math="0" shadow="0">\n'
        f"      <root>\n"
        f'        <mxCell id="0"/>\n'
        f'        <mxCell id="1" parent="0"/>\n'
        f"{body}\n"
        f"      </root>\n"
        f"    </mxGraphModel>\n"
        f"  </diagram>\n"
        f"</mxfile>\n"
    )


# ---------------------------------------------------------------------------


def main() -> None:
    meta = yaml.safe_load((HERE / "erd_meta.yaml").read_text(encoding="utf-8"))
    schema = Schema()

    in_scope = (
        set(meta["tables"])
        | set(meta.get("link_tables") or {})
        | set(meta.get("boundary_tables") or {})
    )
    missing = sorted(t for t in in_scope if not schema.columns.get(t))
    if missing:
        sys.exit(
            "These tables are in erd_meta.yaml but absent from the snapshot: "
            + ", ".join(missing),
        )

    (HERE / "erd.dot").write_text(build_dot(schema, meta), encoding="utf-8")
    (HERE / "ERD.drawio").write_text(build_drawio(schema, meta), encoding="utf-8")

    cols = sum(len(schema.columns[t]) for t in in_scope)
    print(f"erd.dot     : {len(in_scope)} tables, {cols} columns")
    print(f"ERD.drawio  : {len(in_scope)} tables")
    print("render      : dot -Tpdf docs/erd/erd.dot -o docs/erd/ERD.pdf")


if __name__ == "__main__":
    main()
