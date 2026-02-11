# HR Employee ClearDeals - Test Suite

> Comprehensive test suite with 213+ test cases covering all aspects of the HR Employee module.

## Quick Start

### Run All Tests
```bash
python odoo-bin -r odoo -w odoo --addons-path=addons,custom_addons \
  -d odoo_hrms -u hr_employee_cleardeals --test-enable --stop-after-init
```

### Run Specific Test Tag
```bash
python odoo-bin --test-tags=validation --test-enable --stop-after-init \
  --addons-path=addons,custom_addons -d odoo_hrms -u hr_employee_cleardeals
```

## Test Files Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_address_management.py` | 14 | Address fields, copying functionality |
| `test_asset_management.py` | 14 | IT asset allocation and tracking |
| `test_bank_information.py` | 18 | Bank details, CIBIL, UAN, ESIC |
| `test_document_expiry.py` | 9 | Document expiration tracking |
| `test_document_sync.py` | 23 | Document vault synchronization |
| `test_employee_creation.py` | 17 | Employee CRUD, ID generation |
| `test_lifecycle_status.py` | 13 | Status transitions, workflows |
| `test_mime_detection.py` | 34 | MIME type detection for files |
| `test_onchange_methods.py` | 15 | Form onchange behaviors |
| `test_security.py` | 8 | Access control, permissions |
| `test_ui_workflow.py` | 12 | End-to-end UI workflows |
| `test_validation_constraints.py` | 36 | Aadhaar/PAN validation |
| **TOTAL** | **213** | **All module functionality** |

## Available Test Tags

- `validation` - Data validation tests
- `document_sync` - Document synchronization
- `mime_detection` - MIME type detection
- `security` - Security and permissions
- `lifecycle` - Employee lifecycle
- `onchange` - OnChange methods
- `ui_workflow` - UI workflows
- `employee_creation` - Employee creation
- `bank` - Banking information
- `address` - Address management
- `asset` - Asset tracking
- `document_expiry` - Document expiry

## Test Results Summary

```
✅ 213/213 tests passing (100%)
✅ All critical paths covered
✅ Edge cases handled
✅ Performance validated
```

## Documentation

For detailed documentation, see [TEST_DOCUMENTATION.md](./TEST_DOCUMENTATION.md)

### What's Covered:
- Detailed test file reference
- Common utilities and helpers
- Writing new tests
- Best practices
- Troubleshooting guide
- Coverage metrics

## Quick Examples

### Example 1: Run Document Tests Only
```bash
python odoo-bin --test-tags=document --test-enable --stop-after-init \
  --addons-path=addons,custom_addons -d odoo_hrms -u hr_employee_cleardeals
```

### Example 2: Run Multiple Tags
```bash
python odoo-bin --test-tags=validation,security --test-enable --stop-after-init \
  --addons-path=addons,custom_addons -d odoo_hrms -u hr_employee_cleardeals
```

### Example 3: PowerShell - Show Only Results
```powershell
python odoo-bin --test-enable --stop-after-init `
  --addons-path=addons,custom_addons -d odoo_hrms `
  -u hr_employee_cleardeals 2>&1 | `
  Select-String -Pattern "(Starting Test|ERROR|FAIL|tests when loading)"
```

## Common Test Utilities

Located in `common.py`:

```python
# Create test employee
employee = self._create_test_employee(name='John Doe')

# Get base employee data
data = self._get_employee_base_values()

# Create test files
pdf = self._create_test_pdf_file()
jpg = self._create_test_jpeg_file()
png = self._create_test_png_file()

# Get valid test data
aadhaar_numbers = self._get_valid_aadhaar_numbers()
pan_numbers = self._get_valid_pan_numbers()
```

## Test Architecture

```
tests/
├── common.py              # Shared utilities & base class
├── test_*.py             # Individual test files
├── TEST_DOCUMENTATION.md # Comprehensive documentation
└── README.md             # This file (quick reference)
```

### Base Test Class: `HREmployeeCleardealsTestCase`
- Inherits from `odoo.tests.TransactionCase`
- Provides common fixtures (departments, jobs)
- Includes helper methods for test data
- Ensures test isolation via transactions

## Key Features Tested

### ✅ Core Functionality
- [x] Employee creation with auto ID (CD-XXXX)
- [x] Document vault synchronization
- [x] MIME type detection (PDF, JPEG, PNG)
- [x] Aadhaar validation (12 digits)
- [x] PAN validation (ABCDE1234F format)

### ✅ Advanced Features
- [x] Lifecycle status transitions
- [x] Document expiry tracking
- [x] Address copying functionality
- [x] Bank information management
- [x] Asset allocation tracking

### ✅ Security & Access
- [x] HR user permissions
- [x] Basic user restrictions
- [x] Record-level security
- [x] Field-level access control

### ✅ Integration & UI
- [x] OnChange methods
- [x] Smart buttons
- [x] Bulk operations
- [x] Complete workflows

## Validation Rules

### Aadhaar Number
- Format: Exactly 12 digits
- Spaces allowed: Yes
- Example: `123456789012` or `1234 5678 9012`

### PAN Number
- Format: 5 letters + 4 digits + 1 letter
- Case sensitive: No (auto-converts to uppercase)
- Example: `ABCDE1234F` or `abcde1234f` → `ABCDE1234F`

## Troubleshooting

### Tests fail when run together but pass individually?
- Check for shared state between tests
- Ensure proper transaction isolation
- Review `setUp()` vs `setUpClass()` usage

### Validation not triggering?
- Verify constraint decorator syntax
- Check field names in constraint
- Ensure field is in create/write values

### Database connection issues?
- Verify database name matches
- Check PostgreSQL is running
- Confirm connection credentials

## Contributing

When adding new tests:
1. Follow naming convention: `test_XX_descriptive_name`
2. Add descriptive docstring
3. Use appropriate tags
4. Utilize common utilities from `common.py`
5. Update this README and TEST_DOCUMENTATION.md

## Support

- 📖 Full Documentation: [TEST_DOCUMENTATION.md](./TEST_DOCUMENTATION.md)
- 🔧 Common Utilities: [common.py](./common.py)
- 📚 Odoo Testing Docs: https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html

---

**Test Suite Status**: ✅ All 213 tests passing  
**Last Updated**: February 11, 2026  
**Version**: 1.0
