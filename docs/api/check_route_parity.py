#!/usr/bin/env python3
"""
Assert that the OpenAPI specifications describe exactly the routes the code
exposes -- no more, no fewer.

Spec validation (openapi-spec-validator) proves a document is well-formed. It
cannot prove the document is *true*: a specification describing an API that does
not exist validates perfectly. This script closes that gap by parsing every
``@http.route`` decorator out of the controllers and diffing (path, method)
against the specifications.

It reports three kinds of drift:

    missing   route exists in the code but not in the spec  -> consumers cannot see it
    extra     route documented but not in the code          -> consumers call a 404
    mismatch  path documented with the wrong methods        -> e.g. PATCH added, spec not updated

Usage
    python3 docs/api/check_route_parity.py            # check, exit 1 on drift
    python3 docs/api/check_route_parity.py --list     # print what the code exposes

Exit status is 0 when the specs match the code, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

REPO = Path(__file__).resolve().parents[2]

# Each Odoo module and the specification that documents it.
TARGETS = {
    "hr_employee_cleardeals": "docs/api/hr_employee_cleardeals.openapi.yaml",
    "document_template_manager": "docs/api/document_template_manager.openapi.yaml",
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

# Odoo path converters: <string:employee_id>, <int:template_id>, <name>
CONVERTER = re.compile(r"<(?:[a-zA-Z_][\w.]*(?:\([^)]*\))?:)?([a-zA-Z_]\w*)>")


def to_openapi_path(route: str) -> str:
    """'/api/v1/employees/<string:employee_id>' -> '/api/v1/employees/{employee_id}'"""
    return CONVERTER.sub(r"{\1}", route)


def literal(node: ast.AST):
    """Best-effort literal evaluation; returns None for anything dynamic."""
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def routes_from_source(path: Path) -> tuple[set[tuple[str, str]], list[str]]:
    """Extract {(openapi_path, method)} from one controller file."""
    found: set[tuple[str, str]] = set()
    warnings: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            # match @http.route(...) and @route(...)
            if not isinstance(dec, ast.Call):
                continue
            target = dec.func
            name = (
                target.attr
                if isinstance(target, ast.Attribute)
                else getattr(target, "id", "")
            )
            if name != "route":
                continue

            # first positional arg is the path, or a list of paths
            if not dec.args:
                warnings.append(f"{path.name}:{dec.lineno} route() with no path argument")
                continue
            raw = literal(dec.args[0])
            paths = [raw] if isinstance(raw, str) else raw
            if not paths or not all(isinstance(p, str) for p in paths):
                warnings.append(
                    f"{path.name}:{dec.lineno} route path is not a literal; skipped",
                )
                continue

            methods = None
            for kw in dec.keywords:
                if kw.arg == "methods":
                    methods = literal(kw.value)
            if methods is None:
                # Odoo accepts any method when none are declared. Assume GET and
                # say so, rather than silently inventing a contract.
                methods = ["GET"]
                warnings.append(
                    f"{path.name}:{dec.lineno} {paths[0]} declares no methods; assuming GET",
                )

            for p in paths:
                if not p.startswith("/api/"):
                    continue  # only the documented API surface is in scope
                for m in methods:
                    found.add((to_openapi_path(p), str(m).lower()))
    return found, warnings


def routes_from_module(module: str) -> tuple[set[tuple[str, str]], list[str]]:
    controllers = REPO / "custom_addons" / module / "controllers"
    if not controllers.is_dir():
        sys.exit(f"No controllers directory for module '{module}': {controllers}")
    found: set[tuple[str, str]] = set()
    warnings: list[str] = []
    for py in sorted(controllers.glob("*.py")):
        f, w = routes_from_source(py)
        found |= f
        warnings += w
    return found, warnings


def routes_from_spec(spec_path: Path) -> set[tuple[str, str]]:
    doc = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    return {
        (path, method)
        for path, item in (doc.get("paths") or {}).items()
        for method in item
        if method in HTTP_METHODS
    }


def render(pairs: set[tuple[str, str]]) -> list[str]:
    return [f"{m.upper():7s} {p}" for p, m in sorted(pairs, key=lambda x: (x[0], x[1]))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--list", action="store_true", help="print the routes found in the code and exit",
    )
    args = ap.parse_args()

    failed = False
    for module, rel_spec in TARGETS.items():
        spec_path = REPO / rel_spec
        code, warnings = routes_from_module(module)

        if args.list:
            print(f"\n{module} -- {len(code)} operations")
            for line in render(code):
                print(f"  {line}")
            continue

        if not spec_path.is_file():
            print(f"FAIL  {module}: specification not found at {rel_spec}")
            failed = True
            continue

        spec = routes_from_spec(spec_path)
        missing = code - spec
        extra = spec - code

        for w in warnings:
            print(f"WARN  {module}: {w}")

        if not missing and not extra:
            print(f"OK    {module}: {len(code)} operations match {rel_spec}")
            continue

        failed = True
        print(f"FAIL  {module}: {rel_spec} disagrees with the controllers")
        if missing:
            print("      in the code but NOT documented "
                  "(consumers cannot discover these):")
            for line in render(missing):
                print(f"        + {line}")
        if extra:
            print("      documented but NOT in the code "
                  "(consumers would get a 404):")
            for line in render(extra):
                print(f"        - {line}")

    if args.list:
        return 0

    if failed:
        print(
            "\nRoute parity check failed. Update the specification in "
            "docs/api/ to match the controllers, in the same change that "
            "altered the routes.",
        )
        return 1

    print("\nRoute parity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
