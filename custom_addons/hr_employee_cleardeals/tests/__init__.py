"""
Test Suite for ClearDeals HR India Customizations Module

This test suite provides comprehensive coverage of the hr_employee_cleardeals module,
including employee creation, validation, document management, and security.

Test Organization:
- common.py: Shared utilities and test data
- test_employee_creation.py: Employee creation and ID generation
- test_validation_constraints.py: Aadhaar, PAN, and other validations
- test_document_sync.py: Document vault synchronization
- test_mime_detection.py: MIME type detection from files
- test_onchange_methods.py: OnChange method behavior
- test_security.py: Security rules and access control
- test_lifecycle_status.py: Employee lifecycle management
- test_document_expiry.py: Document expiry notifications
- test_ui_workflow.py: End-to-end UI workflows
- test_asset_management.py: Asset tracking functionality
- test_address_management.py: Address handling
- test_bank_information.py: Bank account validation
"""

from . import (
    common,
    test_address_management,
    test_asset_management,
    test_bank_information,
    test_document_expiry,
    test_document_sync,
    test_employee_creation,
    test_lifecycle_status,
    test_mime_detection,
    test_onchange_methods,
    test_security,
    test_ui_workflow,
    test_validation_constraints,
)
