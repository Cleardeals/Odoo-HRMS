# ClearDeals HR Customizations

## Overview

The **ClearDeals HR Customizations** module extends the standard Odoo HR Employee module to provide comprehensive employee management functionality tailored specifically for Indian business operations. This module integrates with the Open HRMS Employee Documents Expiry system to provide automated document lifecycle management with intelligent MIME type detection and vault synchronization.

**Module Name:** `hr_employee_cleardeals`  
**Version:** 1.0  
**Category:** Human Resources  
**License:** LGPL-3  

## Purpose

This module addresses the specific requirements of Indian HR operations by:

1. Implementing automatic employee ID generation with company-specific prefix (CD-XXXX)
2. Managing Indian statutory compliance documents (Aadhaar, PAN, Bank details)
3. Providing comprehensive document management with expiry tracking
4. Supporting onboarding and lifecycle document workflows
5. Enabling automated synchronization between employee form uploads and document vault
6. Supporting multiple file formats including PDF, JPEG, PNG, and other common formats

## Dependencies

### Required Modules

- **hr** - Base Odoo HR module providing core employee management
- **hr_employee_updation** - OHRMS module for employee profile updates
- **oh_employee_documents_expiry** - Document lifecycle management with expiry notifications

### Python Requirements

- Python 3.8+
- Standard Odoo dependencies
- Base64 encoding support for binary file handling

## Key Features

### 1. Automatic Employee ID Generation

- **Format:** CD-XXXX (e.g., CD-0001, CD-0002)
- **Prefix:** Configurable company prefix "CD-" for ClearDeals
- **Sequence:** Auto-incrementing 4-digit padded number
- **Implementation:** Automatic generation on employee record creation
- **Uniqueness:** Guaranteed unique IDs across the system

### 2. Employee Lifecycle Status Management

Track employee status throughout their tenure:

- **Onboarding** - New joinee in onboarding phase
- **Active** - Actively employed
- **Notice Period** - Resignation submitted, serving notice
- **Resigned** - Completed resignation process
- **Terminated** - Employment terminated by company

### 3. Indian Statutory Compliance

#### Aadhaar Card Management
- 12-digit validation with automatic formatting
- Support for space-separated format (XXXX XXXX XXXX)
- Regex validation: `^\d{12}$`

#### PAN Card Management
- Format validation: ABCDE1234F
- Uppercase letter conversion
- Regex validation: `^[A-Z]{5}[0-9]{4}[A-Z]$`

#### Bank Account Information
- Bank name and branch details
- Account number and IFSC code
- Account type selection (Savings/Current/Salary)
- Name verification for payroll
- CIBIL score tracking
- Bank document upload (Cancelled Cheque/Passbook Copy)

### 4. Comprehensive Document Management

#### Onboarding Documents
- Offer Letter
- Appointment Letter
- Employment Contract
- Non-Disclosure Agreement (NDA)
- Bond Document

#### Identity Documents
- Aadhaar Card Copy
- PAN Card Copy
- Passport Copy
- Driving License (mandatory for BDEs)
- Passport Size Photo (JPEG/PNG support)

#### Address Proof Documents
- Light Bill
- Phone Bill
- Rent Agreement

#### Experience Documents
- Relieving Letter (previous employer)
- Experience Letter (previous employer)
- Last 3 months Salary Slips

#### Educational Documents
- Resume/CV
- Education Background Summary
- Skill Set Documentation

#### Lifecycle Documents
- Appraisal Documents
- Increment Letters
- Notice Period Documentation

### 5. Document Vault Integration

The module features sophisticated automatic synchronization between employee form uploads and the document vault system.

#### Automated Synchronization Features

**Binary Field to Vault Mapping:**
- All document uploads automatically create entries in `hr.employee.document`
- Intelligent MIME type detection from file extensions and binary data
- Support for multiple file formats: PDF, JPEG, PNG, GIF, BMP, TIFF, DOCX, XLSX
- Automatic document type creation if not present in master data

**MIME Type Detection:**
- **Filename-based detection** - Primary method using file extensions
- **Binary data detection** - Fallback using magic number analysis
- **Supported formats:**
  - Images: JPEG (.jpg, .jpeg), PNG (.png), GIF (.gif), BMP (.bmp), TIFF (.tiff)
  - Documents: PDF (.pdf), Word (.doc, .docx), Excel (.xls, .xlsx)

**Magic Number Detection:**
```python
JPEG: 0xFF 0xD8
PNG:  0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A
PDF:  %PDF
BMP:  BM
GIF:  GIF87a or GIF89a
```

**Synchronization Triggers:**
- Employee record creation (all valid document fields)
- Employee record update (when any document field changes)
- Automatic vault record creation or update
- Attachment linking with proper MIME types

**Logging and Traceability:**
All synchronization operations are logged with detailed information:
```
[DOCUMENT SYNC] Starting vault sync for employee: {name} (ID: {id})
[DOCUMENT SYNC] Creating new document type: {type_name}
[DOCUMENT SYNC] Processing {field_name} -> {document_name}
[DOCUMENT SYNC] Detected MIME type: {mimetype} for file: {filename}
[DOCUMENT SYNC] Created attachment ID: {id} with MIME type: {mimetype}
[DOCUMENT SYNC] Completed: {count} documents synced to vault
```

### 6. Enhanced Employee Form Structure

#### Tab 1: Work Information
- Department and Job Position (with inline creation)
- Manager Assignment (with avatar widget)
- Date of Joining
- Asset Tracking (Laptop, SIM, Phone, PC, Physical ID)
- Departure Information (when inactive)

#### Tab 2: Personal Details
- Legal Identity (Full name, Gender, Marital Status, DOB, Blood Group)
- Private Contact Information
- Permanent Address (Odoo structured address widget)
- Current Address (with "Same as Permanent" toggle)
- Emergency Contact Details (Name, Phone, Relationship)
- Government IDs (Aadhaar, PAN)
- Passport Size Photo Upload

#### Tab 3: Indian Statutory & Bank
- Complete bank account details
- Payroll verification fields
- Bank document uploads

#### Tab 4: Background & Academics
- Education background summary
- Experience documents from previous employer
- Previous 3 months salary slips
- Resume and skill set documentation

#### Tab 5: Document Checklist
- Complete onboarding document repository
- Address proof management
- Identity document collection
- Internal lifecycle document tracking

### 7. Asset Management

Boolean toggle tracking for issued assets:
- Laptop
- SIM Card
- Phone
- PC/Desktop
- Physical ID Card

### 8. Address Management

**Permanent Address:**
- Utilizes Odoo's structured address widget
- Fields: Street, Street2, City, State, ZIP/PIN Code, Country
- Integration with state and country master data

**Current Address:**
- Free-text field for flexibility
- "Same as Permanent" toggle for automatic copying
- Automatic address concatenation from structured permanent address

## Technical Architecture

### Data Model Extensions

**Model:** `hr.employee` (inherited)

#### Custom Fields

**Identity & Status:**
```python
employee_id = fields.Char(string='Employee ID', readonly=True, index=True, tracking=True)
employee_status = fields.Selection([...], default='onboarding', required=True, tracking=True)
```

**Personal Information:**
```python
blood_group = fields.Selection([('a+', 'A+'), ('a-', 'A-'), ...])
current_address = fields.Text(string='Current Address')
same_as_permanent = fields.Boolean(string='Same as Permanent Address')
emergency_contact_relationship = fields.Char(string='Relationship')
pan_number = fields.Char(string='PAN Number', size=10)
passport_photo = fields.Binary(string='Passport Size Photo', attachment=True)
passport_photo_filename = fields.Char(string='Passport Photo Filename')
```

**Banking Information:**
```python
bank_name = fields.Char(string='Bank Name')
bank_acc_number = fields.Char(string='Account Number')
ifsc_code = fields.Char(string='IFSC Code')
account_type = fields.Selection([('savings', 'Savings'), ('current', 'Current'), ('salary', 'Salary')])
name_as_per_bank = fields.Char(string='Name as per Bank')
cibil_score = fields.Integer(string='CIBIL Score')
```

**Document Fields:**
All document fields follow the pattern:
```python
{field_name} = fields.Binary(string='...', attachment=True, groups="hr.group_hr_user")
{field_name}_filename = fields.Char(string='...')
```

**Asset Tracking:**
```python
asset_laptop = fields.Boolean(string='Laptop Issued', tracking=True)
asset_sim = fields.Boolean(string='SIM Card Issued', tracking=True)
# ... additional asset fields
```

### Core Methods

#### Employee ID Generation
```python
@api.model_create_multi
def create(self, vals_list):
    """Auto-generate Employee ID with CD-XXXX sequence."""
    for vals in vals_list:
        if not vals.get('employee_id') or vals.get('employee_id') == '/':
            vals['employee_id'] = self.env['ir.sequence'].next_by_code('hr.employee.cd.id') or 'CD-0000'
    employees = super(HrEmployee, self).create(vals_list)
    for employee in employees:
        employee._sync_documents_to_vault()
    return employees
```

#### Document Vault Synchronization
```python
def write(self, vals):
    """Auto sync documents when binary fields are updated."""
    result = super(HrEmployee, self).write(vals)
    document_fields = self._get_document_field_mapping().keys()
    if any(field in vals for field in document_fields):
        for employee in self:
            employee._sync_documents_to_vault()
    return result
```

#### MIME Type Detection
```python
def _detect_mimetype_from_filename(self, filename):
    """Detect MIME type based on file extension."""
    # Returns tuple: (mimetype, default_extension)
    
def _detect_mimetype_from_binary(self, binary_data):
    """Detect MIME type from binary data using magic numbers."""
    # Returns tuple: (mimetype, extension) or None
```

#### Vault Synchronization Logic
```python
def _sync_documents_to_vault(self):
    """
    Automatically create/update hr.employee.document records
    from binary field uploads in the employee form.
    """
    # 1. Iterate through all document field mappings
    # 2. Detect MIME type (filename first, then binary)
    # 3. Create ir.attachment with proper mimetype
    # 4. Create or update hr.employee.document record
    # 5. Link attachment to document vault
```

### Validation Constraints

#### Aadhaar Validation
```python
@api.constrains('identification_id')
def _check_aadhar_format(self):
    """Aadhaar must be exactly 12 digits (spaces allowed for readability)."""
    for rec in self:
        if rec.identification_id:
            cleaned = rec.identification_id.replace(' ', '')
            if not re.match(r'^\d{12}$', cleaned):
                raise ValidationError(_('Aadhaar number must be exactly 12 digits.'))
```

#### PAN Validation
```python
@api.constrains('pan_number')
def _check_pan_format(self):
    """PAN format: ABCDE1234F (5 letters + 4 digits + 1 letter)."""
    for rec in self:
        if rec.pan_number:
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', rec.pan_number.upper()):
                raise ValidationError(_('PAN number must follow the format ABCDE1234F'))
```

### OnChange Methods

#### Address Synchronization
```python
@api.onchange('same_as_permanent')
def _onchange_same_as_permanent(self):
    """Copy structured permanent address into current_address text."""
    if self.same_as_permanent:
        parts = filter(None, [
            self.private_street,
            self.private_street2,
            self.private_city,
            self.private_state_id.name if self.private_state_id else '',
            self.private_zip,
            self.private_country_id.name if self.private_country_id else '',
        ])
        self.current_address = ', '.join(parts) or self.current_address
```

## Security Configuration

### Record-Level Security Rules

**Employee Self-Access:**
```xml
<record id="rule_hr_employee_self_access" model="ir.rule">
    <field name="name">Employee: See Own Profile</field>
    <field name="model_id" ref="hr.model_hr_employee"/>
    <field name="domain_force">['|', ('user_id', '=', user.id), ('id', '=', user.employee_id.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
</record>
```

**HR/Admin Full Access:**
```xml
<record id="rule_hr_employee_admin_access" model="ir.rule">
    <field name="name">HR/Admin: All Access</field>
    <field name="model_id" ref="hr.model_hr_employee"/>
    <field name="domain_force">[(1, '=', 1)]</field>
    <field name="groups" eval="[(4, ref('hr.group_hr_user')), (4, ref('base.group_system'))]"/>
</record>
```

### Field-Level Security

All sensitive fields are restricted to HR group:
```python
groups="hr.group_hr_user"
```

## Data Configuration

### Sequence Configuration

**Employee ID Sequence:**
```xml
<record id="seq_employee_id_cleardeals" model="ir.sequence">
    <field name="name">Employee ID Sequence</field>
    <field name="code">hr.employee.cd.id</field>
    <field name="prefix">CD-</field>
    <field name="padding">4</field>
    <field name="company_id" eval="False"/>
</record>
```

### Document Type Master Data

Pre-configured document types include:

**Onboarding:** Offer Letter, Appointment Letter, NDA, Bond, Contract  
**Identity:** Aadhaar, PAN, Passport, Driving License  
**Banking:** Bank Documents  
**Address:** Address Proof  
**Experience:** Relieving Letter, Experience Letter, Salary Slips  
**Education:** Resume/CV  
**Lifecycle:** Appraisal, Increment Letter, Notice Period  

## View Architecture

### Form View Customization

**Priority:** 20 (loads after OHRMS modules)  
**Inherit ID:** `hr.view_employee_form`  
**Method:** XPath inheritance

**Key Modifications:**
1. Header enhancement with Employee ID and Status
2. Complete replacement of Work Information tab
3. Complete replacement of Personal Details tab
4. Addition of Indian Statutory & Bank tab
5. Addition of Background & Academics tab
6. Addition of Document Checklist tab
7. Hidden base Resume and Payroll tabs (obsoleted by new structure)

## Installation

### Prerequisites

1. Odoo 16.0 or higher
2. Open HRMS modules (hr_employee_updation, oh_employee_documents_expiry)
3. Base hr module

### Installation Steps

1. **Copy Module:**
   ```bash
   cp -r hr_employee_cleardeals /path/to/odoo/custom_addons/
   ```

2. **Update App List:**
   - Navigate to Apps menu
   - Click "Update Apps List"
   - Search for "ClearDeals HR India Customizations"

3. **Install Module:**
   - Click Install button
   - Module will automatically install dependencies

4. **Verify Installation:**
   - Check employee form for new fields
   - Verify Employee ID sequence generation
   - Test document vault synchronization

## Configuration

### Post-Installation Configuration

1. **Employee ID Sequence:**
   - Navigate to Settings > Technical > Sequences & Identifiers > Sequences
   - Search for "Employee ID Sequence" (Code: hr.employee.cd.id)
   - Adjust starting number if needed
   - Modify prefix if required (default: CD-)

2. **Document Types:**
   - Navigate to HR > Configuration > Document Types
   - Verify all required document types are present
   - Add custom document types as needed

3. **Security Groups:**
   - Verify HR Officer/HR Manager groups have appropriate access
   - Configure employee self-service access if required

4. **Validation Rules:**
   - Aadhaar and PAN validation are active by default
   - Customize regex patterns if different formats are required

## Usage Guidelines

### Creating New Employee

1. Navigate to HR > Employees > Create
2. System automatically generates Employee ID (CD-XXXX)
3. Fill header information (Name, Job Title, Work Email, Phone)
4. Select Employee Status (default: Onboarding)
5. Complete Work Information tab
6. Fill Personal Details (mandatory for compliance)
7. Add Bank Account Information
8. Upload required documents
9. Documents automatically sync to vault
10. Save employee record

### Uploading Documents

**Supported Formats:**
- Images: JPEG, PNG, GIF, BMP, TIFF
- Documents: PDF, DOCX, XLSX

**Process:**
1. Navigate to appropriate tab (Personal/Bank/Background/Checklist)
2. Click on document field
3. Select file from file system
4. File automatically uploads and syncs to vault
5. Check document vault (Smart Button) to verify

### Document Vault Access

**Via Smart Button:**
1. Open employee record
2. Click "Documents" smart button (shows count)
3. View all synced documents
4. Add expiry dates and notification settings

**Direct Access:**
1. Navigate to HR > Documents > Employee Documents
2. Filter by employee
3. Manage document lifecycle

### Managing Document Expiry

**Setting Expiry Notifications:**
1. Open employee document from vault
2. Set Expiry Date
3. Configure Notification Type:
   - Single: Notification on expiry date
   - Multi: Notification before few days
   - Everyday: Daily notifications until expiry
   - Everyday After: Notifications on and after expiry
4. Set number of days before notification
5. System automatically sends email notifications

## Integration with OHRMS Document Expiry

### Document Model Integration

**Model:** `hr.employee.document`

**Key Fields:**
- `name` - Document number/identifier
- `document_type_id` - Link to document type master
- `employee_ref_id` - Link to employee record
- `issue_date` - Date of document issue
- `expiry_date` - Document expiration date
- `doc_attachment_ids` - Many2many attachments
- `notification_type` - Expiry notification configuration
- `before_days` - Days before expiry for notification

**Automated Features:**
- Cron job for expiry email notifications
- Configurable notification schedules
- Employee-specific document tracking
- Attachment management via ir.attachment

## Troubleshooting

### Common Issues

**Issue: Employee ID not generating**
- **Solution:** Check if sequence "hr.employee.cd.id" exists
- **Verify:** Settings > Technical > Sequences
- **Reset:** Create new sequence or reset counter

**Issue: Document not syncing to vault**
- **Solution:** Check server logs for [DOCUMENT SYNC] entries
- **Verify:** Document type exists in master data
- **Check:** File upload completed successfully

**Issue: MIME type not detected correctly**
- **Solution:** Ensure filename includes proper extension
- **Verify:** File is not corrupted
- **Check:** File format is supported

**Issue: Aadhaar/PAN validation failing**
- **Solution:** Verify format matches requirements
- **Aadhaar:** 12 digits (spaces allowed)
- **PAN:** ABCDE1234F format (5 letters, 4 digits, 1 letter)

**Issue: Documents smart button shows zero**
- **Solution:** Save employee record after document upload
- **Verify:** Document vault sync completed
- **Check:** Refresh browser cache

### Debug Mode

Enable debug logging for document sync:
```python
_logger = logging.getLogger(__name__)
# Already configured in hr_employee.py
```

Check Odoo logs for detailed sync information:
```bash
tail -f /var/log/odoo/odoo-server.log | grep "DOCUMENT SYNC"
```

## Upgrade and Migration

### Upgrading Module

1. **Backup Database:**
   ```bash
   pg_dump odoo_database > backup_$(date +%Y%m%d).sql
   ```

2. **Update Module Files:**
   ```bash
   cd /path/to/custom_addons
   git pull origin main  # Or copy updated files
   ```

3. **Upgrade Module:**
   ```bash
   odoo-bin -u hr_employee_cleardeals -d odoo_database
   ```

4. **Verify Upgrade:**
   - Check employee form loads correctly
   - Test document upload and sync
   - Verify all customizations intact

### Data Migration

When migrating existing employee data:

1. **Export existing data** using Odoo export feature
2. **Map fields** to new structure
3. **Import data** with proper field mapping
4. **Trigger document sync** by updating any document field
5. **Verify vault synchronization** for all employees

## Best Practices

### Data Entry

1. **Complete all mandatory fields** during initial employee creation
2. **Upload documents immediately** to trigger vault sync
3. **Set expiry dates** for all time-bound documents
4. **Use standard formats** for government IDs
5. **Maintain consistent naming** for uploaded files

### Document Management

1. **Regular audits** of document expiry dates
2. **Proactive renewal** before expiry
3. **Maintain digital copies** of all statutory documents
4. **Update vault** when documents are renewed
5. **Archive old documents** instead of deleting

### Security

1. **Limit access** to HR Officer/Manager groups only
2. **Regular access reviews** for sensitive employee data
3. **Enable audit trail** for all employee record changes
4. **Encrypt database** containing sensitive documents
5. **Regular backups** of employee data and documents

## Contributing

### Code Standards

- Follow Odoo development guidelines
- Use proper Python docstrings
- Include XML comments for view modifications
- Log all important operations
- Write comprehensive commit messages

### Testing

Before submitting changes:
1. Test employee creation workflow
2. Verify document upload and sync
3. Test validation constraints
4. Check security rules
5. Verify UI/UX consistency

## Support and Maintenance

### Module Maintainer

**Organization:** ClearDeals  
**Module:** hr_employee_cleardeals  
**Version:** 1.0  

### Logging and Monitoring

All critical operations are logged with prefix `[DOCUMENT SYNC]`:
- Employee creation and updates
- Document field changes
- Vault synchronization status
- MIME type detection
- Attachment creation
- Success/failure counts

Monitor logs regularly for sync issues and errors.

---

## REST API Endpoints

The module provides RESTful API endpoints for external system integration and programmatic access to employee data.

### API Configuration

**1. Set API Key:**
```
Settings → Technical → Parameters → System Parameters
Key: hr_employee_cleardeals.api_key
Value: your_secure_api_key
```

**2. Authentication:**

All API endpoints (except health check) require authentication via API key:

```bash
# Method 1: X-API-Key header (Recommended)
X-API-Key: your_api_key_here

# Method 2: Authorization Bearer token
Authorization: Bearer your_api_key_here
```

### Available Endpoints

**Total Endpoints: 8**

| # | Endpoint | Method | Auth | Description | Controller File |
|---|----------|--------|------|-------------|-----------------|
| 1 | `/api/v1/health` | GET | No | API health check | main.py |
| 2 | `/api/v1/employees/active` | GET | Yes | List all active employees | employee_api.py |
| 3 | `/api/v1/employees` | GET | Yes | List all employees (with filtering) | employee_api.py |
| 4 | `/api/v1/employees/<id>` | GET | Yes | Get employee details | employee_api.py |
| 5 | `/api/v1/employees/<id>/documents` | GET | Yes | Get employee documents | employee_api.py |
| 6 | `/api/v1/employees/<id>/documents/<doc_id>/download` | GET | Yes | Download document file | employee_api.py |
| 7 | `/api/v1/employees/<id>/emergency-contact` | GET | Yes | Get emergency contact info | emergency_contact_api.py |
| 8 | `/api/v1/employees/<id>/assets` | GET | Yes | Get asset allocation details | assets_api.py |

**Code Organization:**
- `controllers/main.py` - Base controller, authentication, health check
- `controllers/employee_api.py` - Employee listing and details endpoints
- `controllers/emergency_contact_api.py` - Emergency contact endpoint
- `controllers/assets_api.py` - Asset management endpoint

---

#### 1. Health Check

**Endpoint:** `GET /api/v1/health`  
**Auth Required:** No  
**Description:** Check API availability and module status

```bash
curl http://localhost:8069/api/v1/health
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

#### 2. List All Active Employees (NEW)

**Endpoint:** `GET /api/v1/employees/active`  
**Auth Required:** Yes  
**Description:** Retrieve all employees with active status

**Query Parameters:**
- `department` (string, optional) - Filter by department name
- `search` (string, optional) - Search by name or employee_id
- `page` (integer, default: 1) - Page number
- `per_page` (integer, default: 20, max: 100) - Records per page
- `fields` (string, optional) - Additional field groups: contact, banking, address, assets, documents, statutory

**Usage Examples:**

```bash
# Get all active employees (basic info only)
curl -X GET "http://localhost:8069/api/v1/employees/active" \
  -H "X-API-Key: your_api_key_here"

# Get active employees with contact and banking info
curl -X GET "http://localhost:8069/api/v1/employees/active?fields=basic,contact,banking" \
  -H "X-API-Key: your_api_key_here"

# Filter by department
curl -X GET "http://localhost:8069/api/v1/employees/active?department=Engineering" \
  -H "X-API-Key: your_api_key_here"

# Search by name
curl -X GET "http://localhost:8069/api/v1/employees/active?search=John" \
  -H "X-API-Key: your_api_key_here"

# Pagination with additional fields
curl -X GET "http://localhost:8069/api/v1/employees/active?page=1&per_page=50&fields=basic,contact,documents" \
  -H "X-API-Key: your_api_key_here"
```

**Response:**
```json
{
  "success": true,
  "message": "Active employees retrieved successfully",
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
        "date_of_joining": "2025-01-15",
        "contact": {
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
          "esic_number": "1234567890"
        }
      }
    ],
    "total_count": 1
  },
  "meta": {
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total_records": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

**Field Groups Available:**
- `basic` - Default employee information (always included)
- `contact` - Contact details (phone, email, emergency contact)
- `banking` - Bank account, UAN, ESIC, IFSC details
- `address` - Permanent and current address information
- `assets` - Laptop and asset allocation details
- `documents` - Document count and URL
- `statutory` - PAN, Aadhaar numbers

---

#### 3. List All Employees

**Endpoint:** `GET /api/v1/employees`  
**Auth Required:** Yes  
**Description:** List all employees with optional status filtering

**Query Parameters:**
- `department` (string, optional) - Filter by department
- `status` (string, optional) - Filter by status: onboarding, active, notice, resigned, terminated
- `search` (string, optional) - Search by name or employee_id
- `page` (integer, default: 1) - Page number
- `per_page` (integer, default: 20, max: 100) - Records per page

```bash
# Get all employees
curl -X GET "http://localhost:8069/api/v1/employees" \
  -H "X-API-Key: your_api_key_here"

# Filter by status and department
curl -X GET "http://localhost:8069/api/v1/employees?status=active&department=Sales" \
  -H "X-API-Key: your_api_key_here"
```

---

#### 4. Get Employee Details

**Endpoint:** `GET /api/v1/employees/<employee_id>`  
**Auth Required:** Yes  
**Description:** Get detailed information about a specific employee

```bash
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001?fields=basic,contact,banking" \
  -H "X-API-Key: your_api_key_here"
```

---

#### 5. Get Employee Documents

**Endpoint:** `GET /api/v1/employees/<employee_id>/documents`  
**Auth Required:** Yes  
**Description:** Fetch all documents for an employee

**Query Parameters:**
- `document_type` (string, optional) - Filter by document type
- `include_binary` (boolean, default: false) - Include base64 file data
- `page` (integer, default: 1) - Page number
- `per_page` (integer, default: 20, max: 100) - Records per page

```bash
# Get document list
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/documents" \
  -H "X-API-Key: your_api_key_here"

# Get documents with binary data
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/documents?include_binary=true" \
  -H "X-API-Key: your_api_key_here"
```

---

#### 6. Download Employee Document

**Endpoint:** `GET /api/v1/employees/<employee_id>/documents/<document_id>/download`  
**Auth Required:** Yes  
**Description:** Download a specific document file

```bash
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/documents/1/download" \
  -H "X-API-Key: your_api_key_here" \
  -o document.pdf
```

---

#### 7. Get Employee Emergency Contact (NEW)

**Endpoint:** `GET /api/v1/employees/<employee_id>/emergency-contact`  
**Auth Required:** Yes  
**Description:** Retrieve emergency contact information for an employee

**Use Cases:**
- Emergency situations requiring immediate contact
- HR systems integration
- Safety and security applications
- Medical emergency response systems
- Compliance and regulatory reporting

**Query Parameters:**
- `include_personal` (boolean, default: false) - Include employee's personal contact information
- `include_medical` (boolean, default: false) - Include medical information (blood group)

**Usage Examples:**

```bash
# Get emergency contact only
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/emergency-contact" \
  -H "X-API-Key: your_api_key_here"

# Get with personal contact info
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/emergency-contact?include_personal=true" \
  -H "X-API-Key: your_api_key_here"

# Get with medical info
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/emergency-contact?include_medical=true" \
  -H "X-API-Key: your_api_key_here"

# Get all information
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/emergency-contact?include_personal=true&include_medical=true" \
  -H "X-API-Key: your_api_key_here"
```

**Response:**
```json
{
  "success": true,
  "message": "Emergency contact information retrieved successfully",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "employee": {
      "id": 1,
      "employee_id": "CD-0001",
      "name": "John Doe",
      "department": "Engineering",
      "job_title": "Senior Developer",
      "employee_status": "active"
    },
    "emergency_contact": {
      "name": "Jane Doe",
      "phone": "+91-9876543210",
      "relationship": "Spouse"
    },
    "personal_contact": {
      "personal_phone": "+91-9876543211",
      "personal_email": "john.doe@gmail.com",
      "work_phone": "+91-9876543212",
      "work_email": "john@company.com"
    },
    "medical_info": {
      "blood_group": "O+"
    }
  }
}
```

**Response Fields:**

| Field | Type | Always Included | Description |
|-------|------|-----------------|-------------|
| `employee.id` | integer | Yes | Employee database ID |
| `employee.employee_id` | string | Yes | Employee ID (CD-XXXX) |
| `employee.name` | string | Yes | Employee full name |
| `employee.department` | string | Yes | Department name |
| `employee.job_title` | string | Yes | Job title/position |
| `employee.employee_status` | string | Yes | Employment status |
| `emergency_contact.name` | string | Yes | Emergency contact name |
| `emergency_contact.phone` | string | Yes | Emergency contact phone |
| `emergency_contact.relationship` | string | Yes | Relationship to employee |
| `personal_contact.*` | object | If `include_personal=true` | Employee contact details |
| `medical_info.*` | object | If `include_medical=true` | Medical information |

**Integration Examples:**

**Python - Emergency Alert System:**
```python
import requests

def send_emergency_alert(employee_id, emergency_type):
    BASE_URL = "http://localhost:8069/api/v1"
    API_KEY = "your_api_key_here"
    
    # Get emergency contact
    response = requests.get(
        f"{BASE_URL}/employees/{employee_id}/emergency-contact",
        headers={"X-API-Key": API_KEY},
        params={"include_medical": "true"}
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        emergency_contact = data['emergency_contact']
        
        # Send SMS/call to emergency contact
        print(f\"Contacting {emergency_contact['name']} at {emergency_contact['phone']}\")\n        print(f\"Employee: {data['employee']['name']}\")\n        print(f\"Blood Group: {data['medical_info']['blood_group']}\")\n        \n        return emergency_contact\n    else:
        print(f\"Error: {response.json()['message']}\")\n        return None

# Example usage
send_emergency_alert('CD-0001', 'medical')
```

**JavaScript - Contact Directory App:**
```javascript
async function getEmergencyContacts(employeeIds) {
    const BASE_URL = 'http://localhost:8069/api/v1';
    const API_KEY = 'your_api_key_here';
    
    const contacts = [];
    
    for (const empId of employeeIds) {
        const response = await fetch(
            `${BASE_URL}/employees/${empId}/emergency-contact`,
            {
                headers: {'X-API-Key': API_KEY}
            }
        );
        
        if (response.ok) {
            const data = await response.json();
            contacts.push({
                employee: data.data.employee.name,
                emergencyName: data.data.emergency_contact.name,
                emergencyPhone: data.data.emergency_contact.phone,
                relationship: data.data.emergency_contact.relationship
            });
        }
    }
    
    return contacts;
}

// Usage
getEmergencyContacts(['CD-0001', 'CD-0002', 'CD-0003'])
    .then(contacts => console.table(contacts));
```

---

#### 8. Get Employee Assets (NEW)

**Endpoint:** `GET /api/v1/employees/<employee_id>/assets`  
**Auth Required:** Yes  
**Description:** Retrieve complete asset allocation information for an employee

**Use Cases:**
- IT asset tracking and inventory management
- Employee onboarding/offboarding asset checklists  
- Asset return verification during exit process
- Compliance and audit trails
- Asset allocation reporting
- Equipment lifecycle management

**Query Parameters:**
- `include_details` (boolean, default: true) - Include detailed laptop specifications
- `include_allocation` (boolean, default: true) - Include allocation dates

**Usage Examples:**

```bash
# Get all assets information
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/assets" \
  -H "X-API-Key: your_api_key_here"

# Get only asset status (without details)
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/assets?include_details=false" \
  -H "X-API-Key: your_api_key_here"

# Get assets with allocation dates
curl -X GET "http://localhost:8069/api/v1/employees/CD-0001/assets?include_allocation=true" \
  -H "X-API-Key: your_api_key_here"
```

**Response:**
```json
{
  "success": true,
  "message": "Asset information retrieved successfully",
  "timestamp": "2026-02-11T12:00:00Z",
  "data": {
    "employee": {
      "id": 1,
      "employee_id": "CD-0001",
      "name": "John Doe",
      "department": "Engineering",
      "job_title": "Senior Developer",
      "employee_status": "active"
    },
    "issued_assets": {
      "laptop": true,
      "sim_card": true,
      "phone": false,
      "pc_desktop": false,
      "physical_id_card": true
    },
    "laptop_details": {
      "brand": "Dell",
      "model": "Latitude 7420",
      "serial_number": "ABC123XYZ789",
      "ram": "16GB",
      "storage": "512GB SSD",
      "processor": "Intel Core i7",
      "allocation_date": "2025-01-15"
    },
    "asset_summary": {
      "total_assets_issued": 3,
      "asset_types": ["Laptop", "SIM Card", "Physical ID Card"],
      "has_laptop": true,
      "has_mobile_assets": true
    }
  }
}
```

**Response Fields:**

| Field | Type | Always Included | Description |
|-------|------|-----------------|-------------|
| `employee.*` | object | Yes | Employee basic information |
| `issued_assets.laptop` | boolean | Yes | Laptop issued status |
| `issued_assets.sim_card` | boolean | Yes | SIM card issued status |
| `issued_assets.phone` | boolean | Yes | Phone issued status |
| `issued_assets.pc_desktop` | boolean | Yes | PC/Desktop issued status |
| `issued_assets.physical_id_card` | boolean | Yes | ID card issued status |
| `laptop_details.*` | object | If laptop issued & `include_details=true` | Laptop specifications |
| `laptop_details.allocation_date` | string | If `include_allocation=true` | Date laptop was allocated |
| `asset_summary.*` | object | Yes | Summary of all assets |

**Integration Examples:**

**Python - Asset Tracking System:**
```python
import requests

def track_employee_assets(employee_id):
    BASE_URL = "http://localhost:8069/api/v1"
    API_KEY = "your_api_key_here"
    
    response = requests.get(
        f"{BASE_URL}/employees/{employee_id}/assets",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        
        print(f"Employee: {data['employee']['name']}")
        print(f"Total Assets: {data['asset_summary']['total_assets_issued']}")
        print(f"Asset Types: {', '.join(data['asset_summary']['asset_types'])}")
        
        if data['asset_summary']['has_laptop']:
            laptop = data.get('laptop_details', {})
            print(f"\nLaptop Details:")
            print(f"  Brand: {laptop.get('brand')}")
            print(f"  Model: {laptop.get('model')}")
            print(f"  Serial: {laptop.get('serial_number')}")
        
        return data
    else:
        print(f"Error: {response.json()['message']}")
        return None

# Example usage
track_employee_assets('CD-0001')
```

**JavaScript - Asset Checklist App:**
```javascript
async function getEmployeeAssets(employeeId) {
    const BASE_URL = 'http://localhost:8069/api/v1';
    const API_KEY = 'your_api_key_here';
    
    const response = await fetch(
        `${BASE_URL}/employees/${employeeId}/assets`,
        {
            headers: {'X-API-Key': API_KEY}
        }
    );
    
    if (response.ok) {
        const result = await response.json();
        const data = result.data;
        
        // Build asset checklist
        const checklist = {
            employee: data.employee.name,
            assetStatus: {
                laptop: data.issued_assets.laptop ? '✓' : '✗',
                simCard: data.issued_assets.sim_card ? '✓' : '✗',
                phone: data.issued_assets.phone ? '✓' : '✗',
                pcDesktop: data.issued_assets.pc_desktop ? '✓' : '✗',
                idCard: data.issued_assets.physical_id_card ? '✓' : '✗'
            },
            totalIssued: data.asset_summary.total_assets_issued
        };
        
        return checklist;
    } else {
        console.error('Failed to fetch assets');
        return null;
    }
}

// Usage
getEmployeeAssets('CD-0001')
    .then(checklist => console.table(checklist.assetStatus));
```

**Excel/CSV Export Integration:**
```python
import requests
import pandas as pd

def export_all_employee_assets(employee_ids):
    BASE_URL = "http://localhost:8069/api/v1"
    API_KEY = "your_api_key_here"
    
    assets_data = []
    
    for emp_id in employee_ids:
        response = requests.get(
            f"{BASE_URL}/employees/{emp_id}/assets",
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()['data']
            assets_data.append({
                'Employee ID': data['employee']['employee_id'],
                'Name': data['employee']['name'],
                'Department': data['employee']['department'],
                'Laptop': 'Yes' if data['issued_assets']['laptop'] else 'No',
                'SIM Card': 'Yes' if data['issued_assets']['sim_card'] else 'No',
                'Phone': 'Yes' if data['issued_assets']['phone'] else 'No',
                'PC/Desktop': 'Yes' if data['issued_assets']['pc_desktop'] else 'No',
                'ID Card': 'Yes' if data['issued_assets']['physical_id_card'] else 'No',
                'Total Assets': data['asset_summary']['total_assets_issued'],
                'Laptop Brand': data.get('laptop_details', {}).get('brand', 'N/A'),
                'Laptop Model': data.get('laptop_details', {}).get('model', 'N/A'),
                'Serial Number': data.get('laptop_details', {}).get('serial_number', 'N/A'),
            })
    
    # Create DataFrame and export to Excel
    df = pd.DataFrame(assets_data)
    df.to_excel('employee_assets_report.xlsx', index=False)
    print(f"Exported {len(assets_data)} employee asset records")

# Usage
export_all_employee_assets(['CD-0001', 'CD-0002', 'CD-0003'])
```

---

### API Response Format

All API responses follow this structure:

```json
{
  "success": true/false,
  "message": "Human-readable message",
  "timestamp": "ISO 8601 timestamp",
  "data": {...},
  "errors": [...],
  "meta": {
    "pagination": {...}
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid/missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

### Integration Examples

**Python:**
```python
import requests

BASE_URL = "http://localhost:8069/api/v1"
API_KEY = "your_api_key_here"
headers = {"X-API-Key": API_KEY}

# Get all active employees
response = requests.get(
    f"{BASE_URL}/employees/active",
    headers=headers,
    params={"fields": "basic,contact"}
)
employees = response.json()['data']['employees']
```

**JavaScript:**
```javascript
const BASE_URL = 'http://localhost:8069/api/v1';
const API_KEY = 'your_api_key_here';

async function getActiveEmployees() {
    const response = await fetch(`${BASE_URL}/employees/active`, {
        headers: {'X-API-Key': API_KEY}
    });
    const data = await response.json();
    return data.data.employees;
}
```

---

## Future Enhancements

### Planned Features

1. **Bulk Document Upload** - Upload multiple documents at once
2. **Document Templates** - Downloadable templates for common documents
3. **Digital Signatures** - E-signature integration for documents
4. **Mobile App Support** - Document upload via mobile application
5. **Advanced Analytics** - Dashboard for document compliance tracking
6. **OCR Integration** - Automatic data extraction from uploaded documents
7. **Multi-language Support** - Regional language support for documents
8. **Workflow Automation** - Approval workflows for sensitive documents

## License

This module is licensed under LGPL-3 (GNU Lesser General Public License v3).

## Acknowledgments

- **Odoo SA** - Base HR module framework
- **Cybrosys Technologies** - Open HRMS document expiry module
- **ClearDeals Development Team** - Custom module development

## Version History

### Version 1.0 (Current)
- Initial release
- Core employee management functionality
- Indian statutory compliance
- Document vault integration
- Automatic MIME type detection
- Image format support (JPEG/PNG)
- Comprehensive validation rules
- Auto-sync document vault
- **RESTful API endpoints (8 total)**:
  - Health check endpoint
  - Active employees listing with flexible field selection
  - All employees listing with filtering
  - Employee details retrieval
  - Document management (list & download)
  - Emergency contact information retrieval
  - Asset allocation and tracking
- **Clean API architecture**:
  - Decoupled controllers for better maintainability
  - Separate files: main.py, employee_api.py, emergency_contact_api.py, assets_api.py
  - Modular design following single responsibility principle
- API authentication via API key
- Standardized JSON response format
- CORS support for cross-origin requests
- Pagination support for large datasets

---

**Last Updated:** February 2026  
**Documentation Version:** 1.0

