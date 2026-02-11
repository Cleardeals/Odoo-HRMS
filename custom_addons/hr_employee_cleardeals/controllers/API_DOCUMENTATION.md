# API Documentation - HR Employee ClearDeals

**Version:** 1.0  
**Base URL:** `http://your-odoo-domain.com/api/v1`  
**Authentication:** API Key  
**Module:** hr_employee_cleardeals

---

## Table of Contents

1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Health & Info](#health--info)
   - [Employee Management](#employee-management)
   - [Document Management](#document-management)
6. [Code Examples](#code-examples)
7. [Testing with Postman](#testing-with-postman)
8. [Troubleshooting](#troubleshooting)

---

## Authentication

All API endpoints (except health and info) require authentication using an API key.

### Setting Up API Key

1. Navigate to Odoo backend as Administrator
2. Go to **Settings → Technical → Parameters → System Parameters**
3. Create a new parameter:
   - **Key:** `hr_employee_cleardeals.api_key`
   - **Value:** Your secure random API key (e.g., `sk_live_1234567890abcdef`)

### Using API Key in Requests

**Method 1: Custom Header (Recommended)**
```http
X-API-Key: your_api_key_here
```

**Method 2: Authorization Header**
```http
Authorization: Bearer your_api_key_here
```

### Security Best Practices

- ✅ Use HTTPS in production
- ✅ Rotate API keys regularly
- ✅ Use different keys for development and production
- ✅ Never commit API keys to version control
- ✅ Use environment variables to store keys
- ❌ Never share API keys in public channels

---

## Response Format

All API responses follow a standardized JSON structure:

### Success Response

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2026-02-11T12:34:56.789Z",
  "data": {
    "employees": [],
    "total_count": 10
  },
  "meta": {
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total_records": 10,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error description",
  "timestamp": "2026-02-11T12:34:56.789Z",
  "data": null,
  "errors": [
    {
      "type": "ValidationError",
      "details": "Employee ID is required"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Operation status (true/false) |
| `message` | string | Human-readable message |
| `timestamp` | string | ISO 8601 formatted timestamp |
| `data` | object/array | Response payload |
| `errors` | array | Error details (only on failures) |
| `meta` | object | Metadata (pagination, etc.) |

---

## Error Handling

### HTTP Status Codes

| Status | Description | Common Causes |
|--------|-------------|---------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters, validation errors |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server-side error |

### Common Error Types

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `AccessError` | Permission denied | Check user permissions |
| `ValidationError` | Invalid input data | Verify request parameters |
| `UserError` | Business logic constraint | Check business rules |
| `ValueError` | Invalid value type | Verify data types |

---

## Rate Limiting

Currently, there are no rate limits enforced. However, we recommend:

- **Development:** Max 100 requests/minute
- **Production:** Max 1000 requests/minute

Implement client-side throttling to avoid overloading the server.

---

## Endpoints

### Health & Info

#### 1. Health Check

Check API availability and status.

**Endpoint:** `GET /api/v1/health`  
**Auth Required:** No  
**CORS Enabled:** Yes

**Request:**
```http
GET /api/v1/health HTTP/1.1
Host: your-odoo-domain.com
```

**Response:**
```json
{
  "success": true,
  "message": "API is healthy",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "status": "healthy",
    "version": "1.0",
    "module": "hr_employee_cleardeals"
  }
}
```

---

#### 2. API Information

Get API documentation and available endpoints.

**Endpoint:** `GET /api/v1/info`  
**Auth Required:** No  
**CORS Enabled:** Yes

**Request:**
```http
GET /api/v1/info HTTP/1.1
Host: your-odoo-domain.com
```

**Response:**
```json
{
  "success": true,
  "message": "API information",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "version": "1.0",
    "module": "hr_employee_cleardeals",
    "authentication": "API Key (X-API-Key header or Bearer token)",
    "base_url": "http://your-odoo-domain.com/api/v1",
    "endpoints": [
      {
        "path": "/api/v1/health",
        "method": "GET",
        "description": "Health check",
        "auth_required": false
      },
      ...
    ]
  }
}
```

---

### Employee Management

#### 3. List Employees

Get a paginated list of employees with optional filtering.

**Endpoint:** `GET /api/v1/employees`  
**Auth Required:** Yes  
**CORS Enabled:** Yes

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `department` | string | No | - | Filter by department name |
| `status` | string | No | - | Filter by employee_status |
| `search` | string | No | - | Search by name or employee_id |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 20 | Records per page (max: 100) |

**Employee Status Values:**
- `onboarding` - New employee in onboarding
- `active` - Active employee
- `notice` - Employee serving notice period
- `resigned` - Resigned employee
- `terminated` - Terminated employee

**Request:**
```http
GET /api/v1/employees?department=Engineering&status=active&page=1&per_page=10 HTTP/1.1
Host: your-odoo-domain.com
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "success": true,
  "message": "Employees retrieved successfully",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "employees": [
      {
        "id": 1,
        "employee_id": "CD-0001",
        "name": "John Doe",
        "work_email": "john@company.com",
        "department": "Engineering",
        "job_title": "Senior Developer",
        "employee_status": "active",
        "date_of_joining": "2025-01-15"
      }
    ],
    "total_count": 1
  },
  "meta": {
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total_records": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

#### 4. Get Employee Details

Get detailed information about a specific employee.

**Endpoint:** `GET /api/v1/employees/<employee_id>`  
**Auth Required:** Yes  
**CORS Enabled:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `employee_id` | string | Employee ID (e.g., CD-0001) |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fields` | string | No | basic,contact | Comma-separated field groups |

**Field Groups:**
- `basic` - Basic employee information
- `contact` - Contact details
- `banking` - Bank account details
- `address` - Address information
- `assets` - Asset allocation details
- `documents` - Document summary
- `statutory` - Statutory details (PAN, Aadhaar)

**Request:**
```http
GET /api/v1/employees/CD-0001?fields=basic,contact,banking HTTP/1.1
Host: your-odoo-domain.com
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "success": true,
  "message": "Employee details retrieved successfully",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "basic": {
      "id": 1,
      "employee_id": "CD-0001",
      "name": "John Doe",
      "legal_name": "Johnathan Doe",
      "date_of_birth": "1990-05-15",
      "gender": "male",
      "marital_status": "married",
      "blood_group": "O+",
      "date_of_joining": "2025-01-15",
      "employee_status": "active",
      "department": "Engineering",
      "job_title": "Senior Developer"
    },
    "contact": {
      "work_email": "john@company.com",
      "work_phone": "+91-9876543210",
      "personal_email": "john.doe@gmail.com",
      "personal_phone": "+91-9876543211",
      "emergency_contact_name": "Jane Doe",
      "emergency_contact_phone": "+91-9876543212"
    },
    "banking": {
      "bank_account_number": "12345678901234",
      "ifsc_code": "HDFC0001234",
      "account_type": "savings",
      "uan_number": "123456789012",
      "esic_number": "1234567890",
      "cibil_score": 750
    }
  }
}
```

---

### Document Management

#### 5. Get Employee Documents

Fetch all documents for a specific employee.

**Endpoint:** `GET /api/v1/employees/<employee_id>/documents`  
**Auth Required:** Yes  
**CORS Enabled:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `employee_id` | string | Employee ID (e.g., CD-0001) |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `document_type` | string | No | - | Filter by document type name |
| `include_binary` | boolean | No | false | Include base64 file data |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 20 | Records per page (max: 100) |

**Request:**
```http
GET /api/v1/employees/CD-0001/documents?include_binary=false&page=1 HTTP/1.1
Host: your-odoo-domain.com
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "success": true,
  "message": "Documents retrieved successfully",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "employee": {
      "id": 1,
      "employee_id": "CD-0001",
      "name": "John Doe",
      "work_email": "john@company.com",
      "department": "Engineering",
      "job_title": "Senior Developer",
      "employee_status": "active"
    },
    "documents": [
      {
        "id": 1,
        "document_name": "PAN Card - CD-0001",
        "document_type": "PAN Card",
        "file_name": "pan_card.pdf",
        "file_size": 102400,
        "mimetype": "application/pdf",
        "uploaded_date": "2026-01-15",
        "expiry_date": null,
        "is_expired": false,
        "is_expiring_soon": false
      },
      {
        "id": 2,
        "document_name": "Aadhaar Card - CD-0001",
        "document_type": "Aadhaar Card",
        "file_name": "aadhaar.pdf",
        "file_size": 204800,
        "mimetype": "application/pdf",
        "uploaded_date": "2026-01-15",
        "expiry_date": null,
        "is_expired": false,
        "is_expiring_soon": false
      },
      {
        "id": 3,
        "document_name": "Passport - CD-0001",
        "document_type": "Passport",
        "file_name": "passport_photo.jpg",
        "file_size": 51200,
        "mimetype": "image/jpeg",
        "uploaded_date": "2026-01-20",
        "expiry_date": "2035-01-20",
        "is_expired": false,
        "is_expiring_soon": false
      }
    ],
    "document_count": 3
  },
  "meta": {
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total_records": 3,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

**With Binary Data:**

When `include_binary=true`, each document will include a `file_data` field containing base64-encoded file content:

```json
{
  "id": 1,
  "document_name": "PAN Card - CD-0001",
  "document_type": "PAN Card",
  "file_name": "pan_card.pdf",
  "file_size": 102400,
  "mimetype": "application/pdf",
  "uploaded_date": "2026-01-15",
  "expiry_date": null,
  "is_expired": false,
  "is_expiring_soon": false,
  "file_data": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvcGFnZXM..."
}
```

---

#### 6. Download Employee Document

Download a specific document file.

**Endpoint:** `GET /api/v1/employees/<employee_id>/documents/<document_id>/download`  
**Auth Required:** Yes  
**CORS Enabled:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `employee_id` | string | Employee ID (e.g., CD-0001) |
| `document_id` | integer | Document record ID |

**Request:**
```http
GET /api/v1/employees/CD-0001/documents/1/download HTTP/1.1
Host: your-odoo-domain.com
X-API-Key: your_api_key_here
```

**Response:**

Binary file download with appropriate headers:

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="pan_card.pdf"
Content-Length: 102400

[Binary file content]
```

**Supported MIME Types:**
- `application/pdf` - PDF documents
- `image/jpeg` - JPEG images
- `image/png` - PNG images
- `image/jpg` - JPG images
- Other types as uploaded

---

## Code Examples

### Python (requests library)

```python
import requests

# Configuration
BASE_URL = "http://your-odoo-domain.com/api/v1"
API_KEY = "your_api_key_here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. Health Check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. List Employees
params = {
    "department": "Engineering",
    "status": "active",
    "page": 1,
    "per_page": 10
}
response = requests.get(
    f"{BASE_URL}/employees", 
    headers=headers, 
    params=params
)
print(response.json())

# 3. Get Employee Details
employee_id = "CD-0001"
params = {"fields": "basic,contact,banking"}
response = requests.get(
    f"{BASE_URL}/employees/{employee_id}", 
    headers=headers,
    params=params
)
print(response.json())

# 4. Get Employee Documents
response = requests.get(
    f"{BASE_URL}/employees/{employee_id}/documents",
    headers=headers,
    params={"include_binary": "false"}
)
print(response.json())

# 5. Download Document
document_id = 1
response = requests.get(
    f"{BASE_URL}/employees/{employee_id}/documents/{document_id}/download",
    headers=headers
)

# Save file
if response.status_code == 200:
    filename = response.headers.get(
        'Content-Disposition'
    ).split('filename=')[1].strip('"')
    
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded: {filename}")
```

### JavaScript (Fetch API)

```javascript
// Configuration
const BASE_URL = 'http://your-odoo-domain.com/api/v1';
const API_KEY = 'your_api_key_here';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// 1. List Employees
async function listEmployees() {
    const params = new URLSearchParams({
        department: 'Engineering',
        status: 'active',
        page: 1,
        per_page: 10
    });
    
    const response = await fetch(`${BASE_URL}/employees?${params}`, {
        method: 'GET',
        headers: headers
    });
    
    const data = await response.json();
    console.log(data);
}

// 2. Get Employee Details
async function getEmployeeDetails(employeeId) {
    const params = new URLSearchParams({
        fields: 'basic,contact,banking'
    });
    
    const response = await fetch(
        `${BASE_URL}/employees/${employeeId}?${params}`,
        {
            method: 'GET',
            headers: headers
        }
    );
    
    const data = await response.json();
    console.log(data);
}

// 3. Get Employee Documents
async function getEmployeeDocuments(employeeId) {
    const response = await fetch(
        `${BASE_URL}/employees/${employeeId}/documents`,
        {
            method: 'GET',
            headers: headers
        }
    );
    
    const data = await response.json();
    console.log(data);
}

// 4. Download Document
async function downloadDocument(employeeId, documentId) {
    const response = await fetch(
        `${BASE_URL}/employees/${employeeId}/documents/${documentId}/download`,
        {
            method: 'GET',
            headers: headers
        }
    );
    
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'document.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
    }
}

// Usage
listEmployees();
getEmployeeDetails('CD-0001');
getEmployeeDocuments('CD-0001');
downloadDocument('CD-0001', 1);
```

### cURL

```bash
# Set variables
BASE_URL="http://your-odoo-domain.com/api/v1"
API_KEY="your_api_key_here"

# 1. Health Check
curl -X GET "$BASE_URL/health"

# 2. List Employees
curl -X GET "$BASE_URL/employees?department=Engineering&status=active" \
  -H "X-API-Key: $API_KEY"

# 3. Get Employee Details
curl -X GET "$BASE_URL/employees/CD-0001?fields=basic,contact,banking" \
  -H "X-API-Key: $API_KEY"

# 4. Get Employee Documents
curl -X GET "$BASE_URL/employees/CD-0001/documents" \
  -H "X-API-Key: $API_KEY"

# 5. Download Document
curl -X GET "$BASE_URL/employees/CD-0001/documents/1/download" \
  -H "X-API-Key: $API_KEY" \
  -o document.pdf
```

---

## Testing with Postman

### Setup

1. **Create Collection:**
   - Name: `HR Employee ClearDeals API`
   - Base URL: `{{base_url}}`

2. **Environment Variables:**
   - `base_url`: `http://your-odoo-domain.com/api/v1`
   - `api_key`: `your_api_key_here`

3. **Collection Headers:**
   - Key: `X-API-Key`
   - Value: `{{api_key}}`

### Sample Requests

**1. Health Check**
```
Method: GET
URL: {{base_url}}/health
Headers: (none required)
```

**2. List Employees**
```
Method: GET
URL: {{base_url}}/employees
Params:
  - department: Engineering
  - status: active
  - page: 1
  - per_page: 10
```

**3. Get Employee Details**
```
Method: GET
URL: {{base_url}}/employees/CD-0001
Params:
  - fields: basic,contact,banking
```

**4. Get Employee Documents**
```
Method: GET
URL: {{base_url}}/employees/CD-0001/documents
Params:
  - include_binary: false
  - page: 1
```

**5. Download Document**
```
Method: GET
URL: {{base_url}}/employees/CD-0001/documents/1/download
Send and Download: (Click Send and Download button)
```

### Postman Collection JSON

Save this as `postman_collection.json`:

```json
{
  "info": {
    "name": "HR Employee ClearDeals API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "List Employees",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "X-API-Key",
            "value": "{{api_key}}"
          }
        ],
        "url": {
          "raw": "{{base_url}}/employees?page=1&per_page=10",
          "host": ["{{base_url}}"],
          "path": ["employees"],
          "query": [
            {"key": "page", "value": "1"},
            {"key": "per_page", "value": "10"}
          ]
        }
      }
    }
  ]
}
```

---

## Troubleshooting

### Common Issues

#### 1. 401 Unauthorized Error

**Problem:** API key not recognized

**Solutions:**
- ✅ Verify API key is set in System Parameters
- ✅ Check header format: `X-API-Key: your_key` or `Authorization: Bearer your_key`
- ✅ Ensure no extra spaces in header value
- ✅ Verify API key matches exactly (case-sensitive)

#### 2. 404 Employee Not Found

**Problem:** Employee ID not found

**Solutions:**
- ✅ Verify employee_id exists (e.g., "CD-0001")
- ✅ Check if employee is active
- ✅ Ensure correct spelling and format
- ✅ Use exact employee_id from database

#### 3. CORS Errors (Browser)

**Problem:** Cross-origin request blocked

**Solutions:**
- ✅ CORS is enabled (`cors='*'`) on all endpoints
- ✅ Ensure Odoo server allows CORS in configuration
- ✅ Check browser console for specific CORS error
- ✅ Use server-side requests if browser issues persist

#### 4. Empty Document List

**Problem:** No documents returned for employee

**Solutions:**
- ✅ Check if employee has any documents uploaded
- ✅ Verify document_type_id is set for documents
- ✅ Check if documents are synced to vault
- ✅ Review query filters (remove to see all)

#### 5. Binary Data Not Included

**Problem:** file_data field missing in response

**Solutions:**
- ✅ Set `include_binary=true` query parameter
- ✅ Check if document has file_data stored
- ✅ Verify document upload was successful
- ✅ Use download endpoint for large files

### Debug Mode

Enable Odoo logging to see API requests:

```python
# In odoo.conf
log_level = debug
log_handler = :DEBUG
```

Check logs at: `/var/log/odoo/odoo.log`

### Testing Checklist

- [ ] API key configured in System Parameters
- [ ] Employee exists with correct employee_id
- [ ] Documents uploaded for employee
- [ ] Headers formatted correctly
- [ ] Query parameters URL-encoded
- [ ] HTTPS used in production
- [ ] CORS enabled for browser requests
- [ ] Error responses logged for debugging

---

## API Design Principles

This API follows these best practices:

1. **RESTful Design:** Resource-based URLs with standard HTTP methods
2. **Consistent Responses:** Standardized JSON structure across all endpoints
3. **Proper Status Codes:** Meaningful HTTP status codes for all scenarios
4. **Pagination:** Built-in pagination for list endpoints
5. **Filtering:** Flexible filtering options with query parameters
6. **Security:** API key authentication with secure storage
7. **Error Handling:** Detailed error messages with proper logging
8. **CORS Support:** Cross-origin requests enabled
9. **Documentation:** Comprehensive inline and external documentation
10. **Odoo Standards:** Follows Odoo controller and ORM patterns

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial release with employee and document endpoints |

---

## Support

For issues or questions:

- **Module:** hr_employee_cleardeals
- **Version:** 1.0
- **Python:** 3.12.6
- **Odoo:** 19.0
- **Database:** PostgreSQL

---

**End of API Documentation**
