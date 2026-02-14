# API Setup Guide - Document Template Manager

## Quick Start (3 Steps)

### Step 1: Configure API Key

1. Login to Odoo as Administrator
2. Navigate to: **Settings → Technical → Parameters → System Parameters**
3. Click **Create** and add:
   - **Key:** `document_template_manager.api_key`
   - **Value:** `your-secure-api-key-here` (generate a strong random key)

**Example using command line to generate a secure key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Upgrade the Module

```bash
python odoo-bin -c odoo.conf -d your_database -u document_template_manager
```

Or from the Odoo UI:
1. Go to **Apps**
2. Search for "Document Template Manager"
3. Click **Upgrade**

### Step 3: Test the API

```bash
# Test endpoint - List templates
curl -X GET http://localhost:8069/api/v1/templates \
  -H "X-API-Key: your-secure-api-key-here"
```

---

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/templates` | Create a new template |
| GET | `/api/v1/templates` | List all templates |
| GET | `/api/v1/templates/<id>` | Get a specific template |
| PUT/PATCH | `/api/v1/templates/<id>` | Update a template |
| DELETE | `/api/v1/templates/<id>` | Delete/Archive a template |

---

## Quick Test Examples

### Create a Template
```bash
curl -X POST http://localhost:8069/api/v1/templates \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "Test Template",
    "html_content": "<h1>Hello World</h1>",
    "summary": "A simple test template"
  }'
```

### List Templates
```bash
curl -X GET http://localhost:8069/api/v1/templates \
  -H "X-API-Key: your-api-key"
```

### Get Template by ID
```bash
curl -X GET http://localhost:8069/api/v1/templates/1 \
  -H "X-API-Key: your-api-key"
```

### Update Template
```bash
curl -X PUT http://localhost:8069/api/v1/templates/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "Updated Template Name",
    "favorite": true
  }'
```

### Archive Template
```bash
curl -X DELETE http://localhost:8069/api/v1/templates/1 \
  -H "X-API-Key: your-api-key"
```

---

## Testing with Postman

### 1. Import Collection Settings

**Base URL:** `http://localhost:8069` (or your Odoo server URL)

### 2. Configure Headers

Add these headers to all requests:
- **Key:** `X-API-Key`
- **Value:** `your-secure-api-key-here`

For POST/PUT/PATCH requests, also add:
- **Key:** `Content-Type`
- **Value:** `application/json`

### 3. Sample Request Body (POST)

```json
{
  "name": "Employee Contract",
  "html_content": "<div><h1>Employment Contract</h1><p>Employee: ${employee_name}</p></div>",
  "summary": "Standard employment contract template",
  "active": true,
  "variables": [
    {
      "name": "employee_name",
      "label": "Employee Name",
      "variable_type": "text",
      "required": true
    }
  ]
}
```

---

## Troubleshooting

### Issue: "API key required"
**Solution:** Ensure you're sending the `X-API-Key` header with every request.

### Issue: "Invalid API key"
**Solution:**
1. Check the API key in System Parameters: `document_template_manager.api_key`
2. Ensure the key matches exactly (no extra spaces)

### Issue: "API not configured properly"
**Solution:** The system parameter is missing. Follow Step 1 to create it.

### Issue: 404 Not Found
**Solution:**
1. Ensure the module is installed and upgraded
2. Check the URL path is correct: `/api/v1/templates`
3. Restart the Odoo server if needed

### Issue: CORS errors (from browser)
**Solution:** The API includes CORS headers (`cors='*'`). If still having issues:
1. Use a server-side client instead of browser
2. Or configure Odoo's CORS settings in the config file

---

## Security Best Practices

1. **Use HTTPS in production** - Never send API keys over HTTP
2. **Keep API keys confidential** - Store in environment variables
3. **Rotate keys periodically** - Change the system parameter value
4. **Limit API access** - Use firewall rules to restrict IP addresses
5. **Monitor API usage** - Check Odoo logs regularly for suspicious activity

---

## Python Integration Example

```python
import os
import requests

class DocumentTemplateAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }

    def create_template(self, name, html_content, **kwargs):
        """Create a new template"""
        data = {
            "name": name,
            "html_content": html_content,
            **kwargs
        }
        response = requests.post(
            f"{self.base_url}/api/v1/templates",
            json=data,
            headers=self.headers
        )
        return response.json()

    def list_templates(self, **filters):
        """List templates with optional filters"""
        response = requests.get(
            f"{self.base_url}/api/v1/templates",
            params=filters,
            headers=self.headers
        )
        return response.json()

    def get_template(self, template_id):
        """Get a specific template"""
        response = requests.get(
            f"{self.base_url}/api/v1/templates/{template_id}",
            headers=self.headers
        )
        return response.json()

    def update_template(self, template_id, **updates):
        """Update a template"""
        response = requests.put(
            f"{self.base_url}/api/v1/templates/{template_id}",
            json=updates,
            headers=self.headers
        )
        return response.json()

    def delete_template(self, template_id, hard_delete=False):
        """Delete/Archive a template"""
        response = requests.delete(
            f"{self.base_url}/api/v1/templates/{template_id}",
            params={"hard_delete": hard_delete},
            headers=self.headers
        )
        return response.json()

# Usage
api = DocumentTemplateAPI(
    base_url="http://localhost:8069",
    api_key=os.getenv("ODOO_API_KEY")
)

# Create template
result = api.create_template(
    name="Welcome Letter",
    html_content="<h1>Welcome ${name}!</h1>",
    summary="Welcome letter for new employees"
)
print(result)

# List templates
templates = api.list_templates(active=True, page=1, per_page=10)
print(templates)
```

---

## Next Steps

1. Read the full [API Documentation](./API_DOCUMENTATION.md)
2. Create your first template via API
3. Integrate with your external systems
4. Set up monitoring and logging

---

**Last Updated:** February 14, 2026
**Module Version:** 19.0.1.0.0
