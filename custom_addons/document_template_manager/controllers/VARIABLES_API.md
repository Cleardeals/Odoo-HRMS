# Template Variables API Reference

Quick reference for template variable management endpoints.

## Base URL
`/api/v1/templates/<template_id>/variables`

## Authentication
All endpoints require API key in headers:
```http
X-API-Key: your-secret-api-key-here
```

---

## Endpoints

### 1. List Template Variables

**GET** `/api/v1/templates/<template_id>/variables`

Get all variables for a specific template.

**Example:**
```bash
curl -X GET http://localhost:8069/api/v1/templates/1/variables \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "success": true,
  "message": "Variables retrieved successfully",
  "data": {
    "template": {
      "id": 1,
      "name": "Sales Contract"
    },
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
    ]
  }
}
```

---

### 2. Get Single Variable

**GET** `/api/v1/templates/<template_id>/variables/<variable_id>`

Get a specific variable from a template.

**Example:**
```bash
curl -X GET http://localhost:8069/api/v1/templates/1/variables/1 \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "success": true,
  "message": "Variable retrieved successfully",
  "data": {
    "variable": {
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
  }
}
```

---

### 3. Create Variable

**POST** `/api/v1/templates/<template_id>/variables`

Create a new variable for a template.

**Request Body:**
```json
{
  "name": "customer_name",
  "label": "Customer Name",
  "variable_type": "char",
  "default_value": "",
  "required": true,
  "sequence": 10,
  "selection_options": ""
}
```

**Field Details:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | Yes | - | Variable identifier (used in template as `{{name}}`) |
| label | string | Yes | - | Display label for the variable |
| variable_type | string | No | "char" | Type: `char`, `text`, `integer`, `float`, `date`, `selection` |
| default_value | string | No | "" | Default value for the variable |
| required | boolean | No | true | Whether the variable is required |
| sequence | integer | No | 10 | Display order (lower = first) |
| selection_options | string | No | "" | Comma-separated options (for `selection` type only) |

**Example:**
```bash
curl -X POST http://localhost:8069/api/v1/templates/1/variables \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "contract_date",
    "label": "Contract Date",
    "variable_type": "date",
    "required": true,
    "sequence": 20
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Variable created successfully",
  "data": {
    "variable": {
      "id": 2,
      "name": "contract_date",
      "label": "Contract Date",
      "variable_type": "date",
      "default_value": "",
      "required": true,
      "sequence": 20,
      "selection_options": "",
      "placeholder_tag": "{{contract_date}}"
    }
  }
}
```

---

### 4. Update Variable

**PUT/PATCH** `/api/v1/templates/<template_id>/variables/<variable_id>`

Update an existing variable. **Note:** The `name` field cannot be changed to prevent breaking existing templates.

**Request Body (all fields optional):**
```json
{
  "label": "Updated Label",
  "variable_type": "text",
  "default_value": "New default",
  "required": false,
  "sequence": 20,
  "selection_options": "Option1,Option2,Option3"
}
```

**Example:**
```bash
curl -X PUT http://localhost:8069/api/v1/templates/1/variables/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "label": "Customer Full Name",
    "required": false
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Variable updated successfully",
  "data": {
    "variable": {
      "id": 1,
      "name": "customer_name",
      "label": "Customer Full Name",
      "variable_type": "char",
      "default_value": "",
      "required": false,
      "sequence": 10,
      "selection_options": "",
      "placeholder_tag": "{{customer_name}}"
    }
  }
}
```

---

### 5. Delete Variable

**DELETE** `/api/v1/templates/<template_id>/variables/<variable_id>`

Permanently delete a variable from a template.

**Example:**
```bash
curl -X DELETE http://localhost:8069/api/v1/templates/1/variables/1 \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "success": true,
  "message": "Variable 'customer_name' deleted successfully"
}
```

---

## Variable Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| `char` | Short text (single line) | Names, titles, codes |
| `text` | Long text (multi-line) | Descriptions, addresses |
| `integer` | Whole number | Quantity, count, year |
| `float` | Decimal number | Price, percentage, weight |
| `date` | Date value | Contract date, birth date |
| `selection` | Dropdown list | Status, category, type |

---

## Complete Example Workflow

### 1. Create a Template
```bash
curl -X POST http://localhost:8069/api/v1/templates \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "Employee Contract",
    "html_content": "<h1>Employment Contract</h1><p>Employee: {{employee_name}}</p><p>Position: {{position}}</p><p>Salary: {{salary}}</p>",
    "summary": "Standard employment contract"
  }'
```

### 2. Add Variables to Template
```bash
# Variable 1: Employee Name
curl -X POST http://localhost:8069/api/v1/templates/1/variables \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "employee_name",
    "label": "Employee Name",
    "variable_type": "char",
    "required": true,
    "sequence": 10
  }'

# Variable 2: Position
curl -X POST http://localhost:8069/api/v1/templates/1/variables \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "position",
    "label": "Job Position",
    "variable_type": "char",
    "required": true,
    "sequence": 20
  }'

# Variable 3: Salary
curl -X POST http://localhost:8069/api/v1/templates/1/variables \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "salary",
    "label": "Annual Salary",
    "variable_type": "float",
    "required": true,
    "sequence": 30
  }'
```

### 3. List All Variables
```bash
curl -X GET http://localhost:8069/api/v1/templates/1/variables \
  -H "X-API-Key: your-api-key"
```

### 4. Update a Variable
```bash
curl -X PUT http://localhost:8069/api/v1/templates/1/variables/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "label": "Full Employee Name",
    "sequence": 5
  }'
```

### 5. Delete a Variable
```bash
curl -X DELETE http://localhost:8069/api/v1/templates/1/variables/3 \
  -H "X-API-Key: your-api-key"
```

---

## Python Client Example

```python
import requests

class TemplateVariableAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }

    def list_variables(self, template_id):
        """List all variables for a template"""
        response = requests.get(
            f"{self.base_url}/api/v1/templates/{template_id}/variables",
            headers=self.headers
        )
        return response.json()

    def get_variable(self, template_id, variable_id):
        """Get a specific variable"""
        response = requests.get(
            f"{self.base_url}/api/v1/templates/{template_id}/variables/{variable_id}",
            headers=self.headers
        )
        return response.json()

    def create_variable(self, template_id, **var_data):
        """Create a new variable"""
        response = requests.post(
            f"{self.base_url}/api/v1/templates/{template_id}/variables",
            json=var_data,
            headers=self.headers
        )
        return response.json()

    def update_variable(self, template_id, variable_id, **updates):
        """Update a variable"""
        response = requests.put(
            f"{self.base_url}/api/v1/templates/{template_id}/variables/{variable_id}",
            json=updates,
            headers=self.headers
        )
        return response.json()

    def delete_variable(self, template_id, variable_id):
        """Delete a variable"""
        response = requests.delete(
            f"{self.base_url}/api/v1/templates/{template_id}/variables/{variable_id}",
            headers=self.headers
        )
        return response.json()

# Usage
api = TemplateVariableAPI("http://localhost:8069", "your-api-key")

# Create variables
api.create_variable(
    template_id=1,
    name="employee_name",
    label="Employee Name",
    variable_type="char",
    required=True
)

# List all variables
result = api.list_variables(template_id=1)
print(result)

# Update a variable
api.update_variable(
    template_id=1,
    variable_id=1,
    label="Full Name",
    sequence=5
)

# Delete a variable
api.delete_variable(template_id=1, variable_id=2)
```

---

## Error Responses

### Template Not Found (404)
```json
{
  "success": false,
  "message": "Template with ID 999 not found",
  "timestamp": "2026-02-14T12:00:00Z"
}
```

### Variable Not Found (404)
```json
{
  "success": false,
  "message": "Variable with ID 999 not found in template 1",
  "timestamp": "2026-02-14T12:00:00Z"
}
```

### Missing Required Field (400)
```json
{
  "success": false,
  "message": "Variable name is required",
  "timestamp": "2026-02-14T12:00:00Z",
  "errors": [
    {
      "field": "name",
      "message": "This field is required"
    }
  ]
}
```

### Invalid API Key (401)
```json
{
  "success": false,
  "message": "Invalid API key",
  "timestamp": "2026-02-14T12:00:00Z"
}
```

---

## Best Practices

1. **Use meaningful variable names** - Use snake_case: `customer_name`, `contract_date`
2. **Set appropriate sequences** - Order variables logically (10, 20, 30...)
3. **Use selection type wisely** - For predefined options: `status`, `department`
4. **Validate before deleting** - Ensure variable is not used in template content
5. **Keep variables synchronized** - Update template HTML when adding/removing variables
6. **Use descriptive labels** - Help users understand what each variable represents

---

**Last Updated:** February 14, 2026
**API Version:** 1.0
