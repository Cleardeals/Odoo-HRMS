# Document Template Manager API Documentation

**Version:** 1.0
**Base URL:** `http://your-odoo-server.com/api/v1`
**Authentication:** API Key

---

## Table of Contents

1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Create Template](#create-template)
   - [List Templates](#list-templates)
   - [Get Template](#get-template)
   - [Update Template](#update-template)
   - [Delete Template](#delete-template)
5. [Examples](#examples)

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

## Endpoints

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
  "html_content": "<div style='font-family: Arial;'><h1>Sales Contract</h1><p>Customer: ${customer_name}</p></div>",
  "summary": "Template for standard sales contracts",
  "category_id": 1,
  "tag_ids": [1, 2, 3],
  "active": true,
  "favorite": false,
  "variables": [
    {
      "name": "customer_name",
      "label": "Customer Name",
      "variable_type": "text",
      "default_value": "",
      "required": true,
      "help_text": "Full name of the customer"
    },
    {
      "name": "contract_date",
      "label": "Contract Date",
      "variable_type": "date",
      "default_value": "",
      "required": true,
      "help_text": "Date of contract signing"
    }
  ]
}
```

**Request Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Template name |
| html_content | string | Yes | HTML content with variables |
| summary | string | No | Brief description |
| category_id | integer | No | Category ID |
| tag_ids | array | No | Array of tag IDs |
| active | boolean | No | Active status (default: true) |
| favorite | boolean | No | Favorite status (default: false) |
| variables | array | No | Array of variable objects |

**Variable Object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable identifier (e.g., "customer_name") |
| label | string | Yes | Display label |
| variable_type | string | No | Type: text, date, number, boolean (default: text) |
| default_value | string | No | Default value |
| required | boolean | No | Is required (default: false) |
| help_text | string | No | Helper text |

**Response:**

```json
{
  "success": true,
  "message": "Template created successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "template": {
      "id": 1,
      "name": "Sales Contract Template",
      "summary": "Template for standard sales contracts",
      "html_content": "<div>...</div>",
      "category_id": {
        "id": 1,
        "name": "Contracts"
      },
      "tag_ids": [
        {"id": 1, "name": "Sales", "color": 1},
        {"id": 2, "name": "Legal", "color": 2}
      ],
      "active": true,
      "favorite": false,
      "variable_count": 2,
      "variables": [
        {
          "id": 1,
          "name": "customer_name",
          "label": "Customer Name",
          "variable_type": "text",
          "default_value": "",
          "required": true,
          "help_text": "Full name of the customer"
        }
      ],
      "company_id": {
        "id": 1,
        "name": "Your Company"
      },
      "create_date": "2026-02-14T12:00:00",
      "write_date": "2026-02-14T12:00:00"
    }
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
      "category_id": {"id": 1, "name": "Contracts"},
      "tag_ids": [{"id": 1, "name": "Sales", "color": 1}],
      "active": true,
      "favorite": false,
      "variable_count": 2,
      "variables": [
        {
          "id": 1,
          "name": "customer_name",
          "label": "Customer Name",
          "variable_type": "text",
          "default_value": "",
          "required": true,
          "help_text": "Full name of the customer"
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

Update an existing template.

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

**Request Body:**

All fields are optional. Include only the fields you want to update.

```json
{
  "name": "Updated Sales Contract Template",
  "html_content": "<div>Updated content...</div>",
  "summary": "Updated description",
  "category_id": 2,
  "tag_ids": [1, 3, 5],
  "active": true,
  "favorite": true
}
```

**Response:**

```json
{
  "success": true,
  "message": "Template updated successfully",
  "timestamp": "2026-02-14T12:00:00Z",
  "data": {
    "template": {
      "id": 1,
      "name": "Updated Sales Contract Template",
      "summary": "Updated description",
      // ... full template data
    }
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

## Examples

### Example 1: Create a Simple Template

```bash
curl -X POST http://localhost:8069/api/v1/templates \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "name": "Welcome Letter",
    "html_content": "<div><h1>Welcome ${employee_name}!</h1><p>We are excited to have you join our team.</p></div>",
    "summary": "Welcome letter for new employees"
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

### Example 4: Update a Template

```bash
curl -X PUT http://localhost:8069/api/v1/templates/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "name": "Updated Welcome Letter",
    "favorite": true
  }'
```

### Example 5: Archive a Template

```bash
curl -X DELETE "http://localhost:8069/api/v1/templates/1?hard_delete=false" \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example 6: Create Template with Variables

```bash
curl -X POST http://localhost:8069/api/v1/templates \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "name": "Employee Contract",
    "html_content": "<div><h1>Employment Contract</h1><p>Employee: ${employee_name}</p><p>Position: ${position}</p><p>Start Date: ${start_date}</p><p>Salary: ${salary}</p></div>",
    "summary": "Standard employment contract template",
    "variables": [
      {
        "name": "employee_name",
        "label": "Employee Name",
        "variable_type": "text",
        "required": true,
        "help_text": "Full legal name of the employee"
      },
      {
        "name": "position",
        "label": "Job Position",
        "variable_type": "text",
        "required": true,
        "help_text": "Official job title"
      },
      {
        "name": "start_date",
        "label": "Start Date",
        "variable_type": "date",
        "required": true,
        "help_text": "First day of employment"
      },
      {
        "name": "salary",
        "label": "Annual Salary",
        "variable_type": "number",
        "required": true,
        "help_text": "Annual compensation amount"
      }
    ]
  }'
```

### Example 7: Using Python Requests

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8069/api/v1"
API_KEY = "your-secret-api-key-here"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Create a template
template_data = {
    "name": "Invoice Template",
    "html_content": "<div><h1>Invoice</h1><p>Amount: ${amount}</p></div>",
    "summary": "Standard invoice template",
    "active": True,
    "favorite": False
}

response = requests.post(
    f"{BASE_URL}/templates",
    headers=headers,
    json=template_data
)

if response.status_code == 201:
    result = response.json()
    print(f"Template created: {result['data']['template']['id']}")
    template_id = result['data']['template']['id']

    # Get the template
    get_response = requests.get(
        f"{BASE_URL}/templates/{template_id}",
        headers=headers
    )
    print(json.dumps(get_response.json(), indent=2))
else:
    print(f"Error: {response.json()}")
```

### Example 8: Using JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8069/api/v1';
const API_KEY = 'your-secret-api-key-here';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY
};

// Create a template
async function createTemplate() {
  try {
    const response = await axios.post(
      `${BASE_URL}/templates`,
      {
        name: 'Proposal Template',
        html_content: '<div><h1>Business Proposal</h1><p>Client: ${client_name}</p></div>',
        summary: 'Standard business proposal template',
        active: true
      },
      { headers }
    );

    console.log('Template created:', response.data);
    return response.data.data.template.id;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// List templates
async function listTemplates() {
  try {
    const response = await axios.get(
      `${BASE_URL}/templates?active=true&page=1&per_page=10`,
      { headers }
    );

    console.log('Templates:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Run examples
(async () => {
  const templateId = await createTemplate();
  await listTemplates();
})();
```

---

## Best Practices

1. **Always validate API responses** - Check the `success` field before processing data
2. **Handle errors gracefully** - Implement proper error handling for different status codes
3. **Use pagination** - For large datasets, use pagination to avoid performance issues
4. **Secure your API key** - Store API keys in environment variables, never in code
5. **Use meaningful variable names** - Make template variables descriptive and consistent
6. **Test in development first** - Always test API calls in a development environment
7. **Log API usage** - Keep track of API calls for debugging and monitoring
8. **Rate limiting** - Implement rate limiting on your side to avoid overwhelming the server

---

## Support

For technical support or feature requests, please contact the Internal Development Team.

**Module Version:** 19.0.1.0.0
**Last Updated:** February 14, 2026
