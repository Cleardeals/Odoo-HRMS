# API Specifications

OpenAPI 3.1 specifications for the HTTP APIs we have built in-house on this Odoo
deployment. Third-party and upstream Odoo addons are out of scope — only the two
custom modules below expose an API we own and maintain.

| Module | Specification | Operations | API key system parameter |
|---|---|---|---|
| `hr_employee_cleardeals` | [hr_employee_cleardeals.openapi.yaml](hr_employee_cleardeals.openapi.yaml) | 12 | `hr_employee_cleardeals.api_key` |
| `document_template_manager` | [document_template_manager.openapi.yaml](document_template_manager.openapi.yaml) | 17 | `document_template_manager.api_key` |

Both APIs share the `/api/v1` prefix but are independent: separate route
namespaces (`/api/v1/employees…` vs `/api/v1/templates…`), separate API keys, and
separate response-handling code. `/api/v1/health` and `/api/v1/info` belong to
the HR module.

## Authentication

Every operation except `/api/v1/health` and `/api/v1/info` requires a static API
key, sent as either header:

```
X-API-Key: <key>
Authorization: Bearer <key>
```

The key is read from an Odoo system parameter (Settings → Technical → Parameters
→ System Parameters). It is a shared secret, not a JWT: it does not expire, does
not identify a user, and is not scoped. The routes are declared `auth='public'`
and record access is performed with `sudo()`, so a leaked key grants full access
to every operation in the corresponding specification.

## Response envelope

Both APIs return the same JSON envelope:

```json
{
  "success": true,
  "message": "Human readable message",
  "timestamp": "2026-02-14T12:00:00.000000Z",
  "data": {},
  "errors": [],
  "meta": {}
}
```

`data`, `errors` and `meta` are omitted when empty. The one exception is
`GET /api/v1/employees/{employee_id}/documents/{document_id}/download`, which
streams the raw file on success and only uses the envelope for errors.

## Checking the specifications

Two checks, and the difference between them matters.

**1. Are the documents well-formed?**

```bash
python3 -m openapi_spec_validator docs/api/hr_employee_cleardeals.openapi.yaml docs/api/document_template_manager.openapi.yaml
```

This validates against the official OpenAPI meta-schema. It catches broken
`$ref`s, invalid parameter locations, duplicate `operationId`s — the things that
break Swagger UI and code generators.

It does **not** check that the specification is true. A document describing an
API that does not exist validates perfectly.

**2. Do the specifications match the code?**

```bash
python3 docs/api/check_route_parity.py
```

This parses every `@http.route` decorator out of both modules' controllers with
Python's `ast` module and diffs `(path, method)` against the specs. It reports
routes present in the code but undocumented, routes documented but absent from
the code, and method drift (a `PATCH` added to a route the spec only lists
`PUT` for). Exit status is non-zero on any mismatch.

`--list` prints what the controllers actually expose, without comparing:

```bash
python3 docs/api/check_route_parity.py --list
```

Both checks run in CI as the **OpenAPI Specifications** job in
`.github/workflows/test.yml`. That job is part of the *Run Odoo Tests* workflow
on purpose: `deploy.yml` triggers on that workflow succeeding, so a specification
that has drifted from the controllers blocks the deploy rather than merely
printing a warning.

Requirements: `pip install pyyaml openapi-spec-validator`.

## Viewing the specifications

Any OpenAPI 3.1 renderer works — Swagger UI, Redoc, Stoplight, or the built-in
viewers in VS Code, Postman and Insomnia. Postman collections are planned as a
follow-up and can be generated from these files.

## Keeping the specifications current

These files are hand-maintained and are not generated from the controllers at
runtime. When a route is added, removed, or its parameters change in
`custom_addons/<module>/controllers/`, update the matching specification in the
same change.
