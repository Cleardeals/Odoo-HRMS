# Document Template Manager API Documentation

**Version:** 1.1
**Base URL:** `http://your-odoo-server.com/api/v1`
**Authentication:** API Key

---

## Table of Contents

1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Template CRUD](#template-crud)
     - [Create Template](#create-template)
     - [List Templates](#list-templates)
     - [Get Template](#get-template)
     - [Update Template](#update-template)
     - [Delete Template](#delete-template)
   - [Template Actions](#template-actions)
     - [Detect Variables](#detect-variables)
     - [Duplicate Template](#duplicate-template)
     - [Toggle Favorite](#toggle-favorite)
     - [Download PDF](#download-pdf)
   - [PDF Generation](#pdf-generation)
     - [Generate PDF](#generate-pdf)
   - [Variables](#variables)
5. [Template Object Schema](#template-object-schema)
6. [Examples](#examples)

---

## Authentication

All API endpoints require authentication via API Key.

### Setup API Key

1. Navigate to: **Settings → Technical → Parameters → System Parameters**
2. Create a new parameter:
   - **Key:** `document_template_manager.api_key`
   - **Value:** Your secure API key (e.g., `your-secret-api-key-here`)

### Using API Key

Provide the API key in request headers using one of these methods:

**Method 1: X-API-Key Header**
```http
X-API-Key: your-secret-api-key-here
```

**Method 2: Authorization Bearer Token**
```http
Authorization: Bearer your-secret-api-key-here
```

---

## Response Format

All API responses follow a standardized JSON format:

### Success Response

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    // Response data here
  },
  "meta": {
    // Optional metadata (pagination, etc.)
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error description",
  "timestamp": "2026-02-14T12:00:00Z",
  "errors": [
    {
      "type": "ValidationError",
      "details": "Detailed error message"
    }
  ]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input or validation failed |
| 401 | Unauthorized | Invalid or missing API key |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error occurred |

### Error Types

- **ValidationError:** Input validation failed
- **AccessError:** Permission denied
- **UserError:** Business logic error
- **ValueError:** Invalid data type or format
- **KeyError:** Missing required field

---

## Template Object Schema

All template endpoints return the following object structure:

```json
{
  "id": 1,
  "name": "Sales Contract Template",
  "summary": "Template for standard sales contracts",
  "html_content": "<div>...</div>",
  "header_html": "<div>Company Header HTML</div>",
  "print_mode": "letterhead",
  "show_header": true,
  "margin_top": 40.0,
  "margin_bottom": 25.0,
  "margin_left": 20.0,
  "margin_right": 20.0,
  "category_id": {"id": 1, "name": "Contracts"},
  "tag_ids": [
    {"id": 1, "name": "Sales", "color": 1}
  ],
  "active": true,
  "favorite": false,
  "has_pdf": false,
  "pdf_filename": "Sales Contract Template.pdf",
  "variable_count": 2,
  "variables": [
    {
      "id": 1,
      "name": "customer_name",
      "label": "Customer Name",
      "variable_type": "char",
      "default_value": "",
      "required": true,
      "sequence": 10,
      "selection_options": "",
      "placeholder_tag": "{{customer_name}}"
    }
  ],
  "company_id": {"id": 1, "name": "Your Company"},
  "create_date": "2026-02-14T12:00:00",
  "write_date": "2026-02-14T12:00:00"
}
```

### Print Mode

| Value | Description |
|-------|-------------|
| `letterhead` | Large top/bottom margins for pre-printed letterhead paper. No digital header rendered. **Default.** |
| `digital` | Standard margins. The `header_html` is rendered on every PDF page when `show_header` is `true`. |

### Default Margins by Print Mode

| Print Mode | Top | Bottom | Left | Right |
|------------|-----|--------|------|-------|
| `letterhead` | 40 mm | 25 mm | 20 mm | 20 mm |
| `digital` | 20 mm | 20 mm | 20 mm | 20 mm |

---

## Endpoints

## Template CRUD

---

## Create Template

Create a new document template.

**Endpoint:** `POST /api/v1/templates`

**Headers:**
```http
Content-Type: application/json
X-API-Key: your-secret-api-key-here
```

**Request Body:**

```json
{
  "name": "Sales Contract Template",
  "html_content": "<div><h1>Sales Contract</h1><p>Customer: {{customer_name}}</p></div>",
  "summary": "Template for standard sales contracts",
  "category_id": 1,
  "tag_ids": [1, 2, 3],
  "active": true,
  "favorite": false,
  "print_mode": "digital",
  "show_header": true,
  "header_html": "<div class='d-flex justify-content-between'><span>Acme Corp</span><span>{{contract_date}}</span></div>",
  "margin_top": 20.0,
  "margin_bottom": 20.0,
  "margin_left": 20.0,
  "margin_right": 20.0,
  "variables": [
    {
      "name": "customer_name",
      "label": "Customer Name",
      "variable_type": "char",
      "default_value": "",
      "required": true,
      "sequence": 10
    },
    {
      "name": "contract_date",
      "label": "Contract Date",
      "variable_type": "date",
      "default_value": "",
      "required": true,
      "sequence": 20
    }
  ]
}
```

**Request Body Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | **Yes** | - | Template name |
| html_content | string | **Yes** | - | HTML body with `{{variable}}` placeholders |
| summary | string | No | `""` | Brief description |
| category_id | integer | No | - | Category ID |
| tag_ids | array | No | `[]` | Array of tag IDs |
| active | boolean | No | `true` | Active status |
| favorite | boolean | No | `false` | Favorite status |
| print_mode | string | No | `"letterhead"` | `"letterhead"` or `"digital"` |
| show_header | boolean | No | `true` | Show `header_html` in PDF (digital mode only) |
| header_html | string | No | `""` | HTML rendered at the top of every PDF page (digital mode) |
| margin_top | float | No | mode-dependent | Top margin in mm |
| margin_bottom | float | No | mode-dependent | Bottom margin in mm |
| margin_left | float | No | `20.0` | Left margin in mm |
| margin_right | float | No | `20.0` | Right margin in mm |
| variables | array | No | `[]` | Array of variable objects (see below) |

**Variable Object:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | **Yes** | - | Variable identifier used in `{{placeholder}}` |
| label | string | **Yes** | - | Display label shown in the export wizard |
| variable_type | string | No | `"char"` | `char`, `text`, `integer`, `float`, `date`, `selection` |
| default_value | string | No | `""` | Pre-filled default value |
| required | boolean | No | `true` | Whether a value is mandatory at export time |
| sequence | integer | No | `10` | Sort order in the wizard |
| selection_options | string | No | `""` | Comma-separated choices (for `selection` type only) |

**Response:** `201 Created` — returns the full [Template Object](#template-object-schema).

```json
{
  "success": true,
  "message": "Template created successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "template": { "..." }
  }
}
```

---

## List Templates

Get a list of all templates with filtering and pagination.

**Endpoint:** `GET /api/v1/templates`

**Headers:**
```http
X-API-Key: your-secret-api-key-here
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | No | Filter by name (partial match) |
| category_id | integer | No | Filter by category ID |
| tag_ids | string | No | Comma-separated tag IDs (e.g., "1,2,3") |
| active | boolean | No | Filter by active status |
| favorite | boolean | No | Filter by favorite status |
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Records per page (default: 20, max: 100) |

**Example Request:**

```http
GET /api/v1/templates?name=contract&active=true&page=1&per_page=10
```

**Response:**

```json
{
  "success": true,
  "message": "Templates retrieved successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "templates": [
      {
        "id": 1,
        "name": "Sales Contract Template",
        "summary": "Template for sales contracts",
        "print_mode": "digital",
        "show_header": true,
        "has_pdf": false,
        "pdf_filename": "Sales Contract Template.pdf",
        "category_id": {"id": 1, "name": "Contracts"},
        "tag_ids": [{"id": 1, "name": "Sales", "color": 1}],
        "active": true,
        "favorite": false,
        "variable_count": 2,
        "create_date": "2026-02-14T12:00:00",
        "write_date": "2026-02-14T12:00:00"
      }
    ]
  },
  "meta": {
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total_records": 25,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## Get Template

Get a single template by ID.

**Endpoint:** `GET /api/v1/templates/<template_id>`

**Headers:**
```http
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| include_variables | boolean | No | Include variable details (default: true) |

**Example Request:**

```http
GET /api/v1/templates/1?include_variables=true
```

**Response:**

```json
{
  "success": true,
  "message": "Template retrieved successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "template": {
      "id": 1,
      "name": "Sales Contract Template",
      "summary": "Template for sales contracts",
      "html_content": "<div>...</div>",
      "header_html": "<div class='d-flex justify-content-between'>...</div>",
      "print_mode": "digital",
      "show_header": true,
      "margin_top": 20.0,
      "margin_bottom": 20.0,
      "margin_left": 20.0,
      "margin_right": 20.0,
      "category_id": {"id": 1, "name": "Contracts"},
      "tag_ids": [{"id": 1, "name": "Sales", "color": 1}],
      "active": true,
      "favorite": false,
      "has_pdf": false,
      "pdf_filename": "Sales Contract Template.pdf",
      "variable_count": 2,
      "variables": [
        {
          "id": 1,
          "name": "customer_name",
          "label": "Customer Name",
          "variable_type": "char",
          "default_value": "",
          "required": true,
          "sequence": 10,
          "selection_options": "",
          "placeholder_tag": "{{customer_name}}"
        }
      ],
      "company_id": {"id": 1, "name": "Your Company"},
      "create_date": "2026-02-14T12:00:00",
      "write_date": "2026-02-14T12:00:00"
    }
  }
}
```

---

## Update Template

Update an existing template. All body fields are optional — include only what you want to change.

**Endpoint:** `PUT /api/v1/templates/<template_id>` or `PATCH /api/v1/templates/<template_id>`

**Headers:**

```http
Content-Type: application/json
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Updatable Fields:**

| Field | Type | Description |
|-------|------|-------------|
| name | string | Template name |
| html_content | string | HTML body |
| header_html | string | Digital page header HTML |
| summary | string | Brief description |
| category_id | integer / null | Category ID (`null` to clear) |
| tag_ids | array | Full replacement list of tag IDs |
| active | boolean | Active status |
| favorite | boolean | Favorite status |
| print_mode | string | `"letterhead"` or `"digital"` |
| show_header | boolean | Show header in PDF |
| margin_top | float | Top margin in mm |
| margin_bottom | float | Bottom margin in mm |
| margin_left | float | Left margin in mm |
| margin_right | float | Right margin in mm |

**Example Request Body:**

```json
{
  "print_mode": "digital",
  "show_header": true,
  "header_html": "<div class='d-flex justify-content-between'><strong>Acme Corp</strong><span>Confidential</span></div>",
  "margin_top": 20.0,
  "favorite": true
}
```

**Response:** `200 OK` — returns the full updated [Template Object](#template-object-schema).

```json
{
  "success": true,
  "message": "Template updated successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "template": { "..." }
  }
}
```

---

## Delete Template

Delete (archive or permanently delete) a template.

**Endpoint:** `DELETE /api/v1/templates/<template_id>`

**Headers:**

```http
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| hard_delete | boolean | No | Permanently delete (default: false = archive) |

**Example Request:**

```http
DELETE /api/v1/templates/1?hard_delete=false
```

**Response:**

```json
{
  "success": true,
  "message": "Template 'Sales Contract Template' archived",
  "timestamp": "2026-02-14T12:00:00Z"
}
```

---

## Template Actions

---

## Detect Variables

Scan a template's HTML body for `{{variable}}` placeholders and automatically create any variable records that do not yet exist.

**Endpoint:** `POST /api/v1/templates/<template_id>/detect-variables`

**Headers:**

```http
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Response:**

```json
{
  "success": true,
  "message": "3 new variable(s) detected and added.",
  "timestamp": "2026-03-11T10:00:00Z",
  "data": {
    "new_variable_count": 3,
    "new_variables": ["contract_date", "customer_name", "salary"],
    "template": { "..." }
  }
}
```

When no new variables are found the response message is `"No new variables found."` and `new_variable_count` is `0`.

**Error Responses:**

| Code | Reason |
|------|--------|
| 400 | Template HTML content is empty |
| 404 | Template not found |

---

## Duplicate Template

Create an identical copy of a template, including all of its variables.

**Endpoint:** `POST /api/v1/templates/<template_id>/duplicate`

**Headers:**

```http
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Source template ID |

**Response:** `201 Created` — returns the new [Template Object](#template-object-schema).

```json
{
  "success": true,
  "message": "Template duplicated successfully",
  "timestamp": "2026-03-11T10:00:00Z",
  "data": {
    "template": { "..." }
  }
}
```

**Error Responses:**

| Code | Reason |
|------|--------|
| 404 | Template not found |

---

## Toggle Favorite

Flip the `favorite` flag on a template (on → off, off → on).

**Endpoint:** `POST /api/v1/templates/<template_id>/toggle-favorite`

**Headers:**

```http
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Response:**

```json
{
  "success": true,
  "message": "Template marked as favorite",
  "timestamp": "2026-03-11T10:00:00Z",
  "data": {
    "template_id": 42,
    "favorite": true
  }
}
```

**Error Responses:**

| Code | Reason |
|------|--------|
| 404 | Template not found |

---

## Download PDF

Return the **last PDF** that was generated for this template (via the [Generate PDF](#generate-pdf) endpoint or the Odoo UI export wizard).

**Endpoint:** `GET /api/v1/templates/<template_id>/download-pdf`

**Headers:**

```http
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| return_type | string | No | `"base64"` | `"base64"` or `"url"` |

**Response (base64):**

```json
{
  "success": true,
  "message": "PDF retrieved successfully",
  "data": {
    "filename": "Sales Contract Template.pdf",
    "pdf_base64": "JVBERi0xLjQKJ...",
    "mimetype": "application/pdf",
    "size_bytes": 102400
  }
}
```

**Response (url):**

```json
{
  "success": true,
  "message": "PDF retrieved successfully",
  "data": {
    "filename": "Sales Contract Template.pdf",
    "download_url": "/web/content/document.template/1/pdf_file/Sales Contract Template.pdf?download=true",
    "mimetype": "application/pdf"
  }
}
```

**Error Responses:**

| Code | Reason |
|------|--------|
| 404 | Template not found, or no PDF has been generated yet |

---

## PDF Generation

---

## Generate PDF

Render all `{{variable}}` placeholders with the provided values and produce a PDF.

**Endpoint:** `POST /api/v1/templates/<template_id>/generate-pdf`

**Headers:**

```http
Content-Type: application/json
X-API-Key: your-secret-api-key-here
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Request Body:**

```json
{
  "variables": {
    "customer_name": "John Doe",
    "contract_date": "2026-03-11",
    "salary": "50000"
  },
  "filename": "Contract_JohnDoe.pdf",
  "return_type": "base64"
}
```

**Request Body Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| variables | object | No | `{}` | Key-value map of variable name → string value |
| filename | string | No | template name + `.pdf` | Output filename |
| return_type | string | No | `"base64"` | `"base64"` to receive the PDF inline, `"url"` for a one-time download link |

**Response (base64):** `201 Created`

```json
{
  "success": true,
  "message": "PDF generated successfully",
  "data": {
    "filename": "Contract_JohnDoe.pdf",
    "pdf_base64": "JVBERi0xLjQKJ...",
    "mimetype": "application/pdf",
    "size_bytes": 102400
  }
}
```

**Response (url):** `201 Created`

```json
{
  "success": true,
  "message": "PDF generated successfully",
  "data": {
    "filename": "Contract_JohnDoe.pdf",
    "download_url": "/web/content/123/Contract_JohnDoe.pdf?download=true",
    "attachment_id": 123,
    "mimetype": "application/pdf",
    "size_bytes": 102400
  }
}
```

**Error Responses:**

| Code | Reason |
|------|--------|
| 400 | Required variables missing or invalid request body |
| 404 | Template not found |
| 500 | PDF generation failed |

---

## Variables

Full CRUD for template variables is available under the `/variables` sub-resource. See [VARIABLES_API.md](./VARIABLES_API.md) for detailed documentation.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/templates/<id>/variables` | List all variables for a template |
| GET | `/api/v1/templates/<id>/variables/<var_id>` | Get a single variable |
| POST | `/api/v1/templates/<id>/variables` | Create a variable |
| PUT/PATCH | `/api/v1/templates/<id>/variables/<var_id>` | Update a variable |
| DELETE | `/api/v1/templates/<id>/variables/<var_id>` | Delete a variable |

---

## Examples

### Example 1: Create a Digital Template with Header

```bash
curl -X POST http://localhost:8069/api/v1/templates \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "name": "Employment Contract",
    "html_content": "<h1>Contract for {{employee_name}}</h1><p>Start date: {{start_date}}</p>",
    "print_mode": "digital",
    "show_header": true,
    "header_html": "<div class=\"d-flex justify-content-between\"><strong>Acme Corp</strong><span>HR Department</span></div>",
    "summary": "Standard employment contract"
  }'
```

### Example 2: List Templates with Filters

```bash
curl -X GET "http://localhost:8069/api/v1/templates?active=true&page=1&per_page=10" \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 3: Get a Specific Template

```bash
curl -X GET http://localhost:8069/api/v1/templates/1 \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 4: Switch to Letterhead Mode

```bash
curl -X PATCH http://localhost:8069/api/v1/templates/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "print_mode": "letterhead",
    "margin_top": 40.0,
    "margin_bottom": 25.0
  }'
```

### Example 5: Detect Variables Automatically

```bash
curl -X POST http://localhost:8069/api/v1/templates/1/detect-variables \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 6: Generate a PDF

```bash
curl -X POST http://localhost:8069/api/v1/templates/1/generate-pdf \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "variables": {
      "employee_name": "Jane Smith",
      "start_date": "2026-04-01"
    },
    "filename": "Contract_JaneSmith.pdf",
    "return_type": "url"
  }'
```

### Example 7: Download the Last Generated PDF (base64)

```bash
curl -X GET "http://localhost:8069/api/v1/templates/1/download-pdf" \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 8: Duplicate a Template

```bash
curl -X POST http://localhost:8069/api/v1/templates/1/duplicate \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 9: Toggle Favorite

```bash
curl -X POST http://localhost:8069/api/v1/templates/1/toggle-favorite \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 10: Archive a Template

```bash
curl -X DELETE "http://localhost:8069/api/v1/templates/1?hard_delete=false" \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 11: Python Integration

```python
import os
import base64
import requests

BASE_URL = "http://localhost:8069/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": os.getenv("ODOO_API_KEY"),
}

# --- Create a digital template ---
template_resp = requests.post(
    f"{BASE_URL}/templates",
    headers=HEADERS,
    json={
        "name": "Offer Letter",
        "html_content": "<h1>Dear {{candidate_name}},</h1><p>Salary: {{salary}}</p>",
        "print_mode": "digital",
        "show_header": True,
        "header_html": "<div><strong>Acme Corp</strong></div>",
    },
)
tpl = template_resp.json()["data"]["template"]
print(f"Created template ID: {tpl['id']}")

# --- Auto-detect variables ---
detect_resp = requests.post(
    f"{BASE_URL}/templates/{tpl['id']}/detect-variables",
    headers=HEADERS,
)
print(detect_resp.json()["message"])  # e.g. "2 new variable(s) detected and added."

# --- Generate a PDF ---
pdf_resp = requests.post(
    f"{BASE_URL}/templates/{tpl['id']}/generate-pdf",
    headers=HEADERS,
    json={
        "variables": {"candidate_name": "Alice", "salary": "60,000"},
        "filename": "OfferLetter_Alice.pdf",
        "return_type": "base64",
    },
)
pdf_b64 = pdf_resp.json()["data"]["pdf_base64"]
with open("OfferLetter_Alice.pdf", "wb") as f:
    f.write(base64.b64decode(pdf_b64))
print("PDF saved.")
```

---

## Best Practices

1. **Always validate API responses** - Check the `success` field before processing data
2. **Handle errors gracefully** - Implement proper error handling for different status codes
3. **Use pagination** - For large datasets, use pagination to avoid performance issues
4. **Secure your API key** - Store API keys in environment variables, never in code
5. **Use `{{variable}}` syntax** - Template placeholders must use double curly braces, not `${}`
6. **Run detect-variables after editing HTML** - Call the detect-variables action endpoint whenever you update `html_content` to keep variable records in sync
7. **Choose print_mode intentionally** - Use `digital` for branded PDFs with a header; use `letterhead` for printing on pre-printed paper
8. **Test in development first** - Always test API calls in a development environment
9. **Log API usage** - Check Odoo server logs regularly for errors or suspicious activity

---

## Support

For technical support or feature requests, please contact the Internal Development Team.

**Module Version:** 19.0.1.1.0
**Last Updated:** March 11, 2026
