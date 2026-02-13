"""
Test Cases for UI Workflows

Tests end-to-end user interface workflows and integration scenarios.
"""

from odoo.tests import tagged

from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'ui_workflow')
class TestEmployeeCreationWorkflow(HREmployeeCleardealsTestCase):
    """Test complete employee creation workflow."""

    def test_01_minimal_employee_creation_workflow(self):
        """Test creating employee with minimal required fields."""
        employee = self.Employee.create({
            'name': 'Minimal Employee',
        })

        self.assertTrue(employee.id)
        self.assertTrue(employee.employee_id)
        self.assertEqual(employee.employee_status, 'onboarding')

    def test_02_complete_employee_creation_workflow(self):
        """Test creating employee with all fields filled."""
        employee_data = self._get_employee_full_values()
        employee = self.Employee.create(employee_data)

        # Verify all fields were saved
        self.assertTrue(employee.name, "Employee should have a name")
        self.assertEqual(employee.work_email, employee_data['work_email'])
        self.assertEqual(employee.identification_id, employee_data['identification_id'])
        self.assertEqual(employee.pan_number, employee_data['pan_number'].upper())
        self.assertTrue(employee.employee_id)

    def test_03_onboarding_with_documents_workflow(self):
        """Test complete onboarding workflow with document upload."""
        employee = self.Employee.create({
            **self._get_employee_full_values(),
            'offer_letter': self._create_test_pdf_file(),
            'offer_letter_filename': 'offer.pdf',
            'appointment_letter': self._create_test_pdf_file(),
            'appointment_letter_filename': 'appointment.pdf',
            'nda_document': self._create_test_pdf_file(),
            'nda_document_filename': 'nda.pdf',
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
            'passport_photo': self._create_test_jpeg_file(),
            'passport_photo_filename': 'photo.jpg',
        })

        # Verify employee created
        self.assertTrue(employee.id)

        # Verify documents synced
        doc_count = self._count_documents_in_vault(employee)
        self.assertGreater(doc_count, 0)

        # Verify employee can access document vault
        result = employee.action_document_view()
        self.assertEqual(result['res_model'], 'hr.employee.document')

    def test_04_employee_update_workflow(self):
        """Test updating employee information."""
        employee = self._create_test_employee()
        original_id = employee.employee_id

        # Update employee details
        employee.write({
            'legal_name': 'Updated Legal Name',
            'birthday': '1990-01-01',
            'blood_group': 'a+',
            'identification_id': '123456789012',
            'pan_number': 'ABCDE1234F',
        })

        # Verify updates
        self.assertEqual(employee.legal_name, 'Updated Legal Name')
        self.assertEqual(employee.blood_group, 'a+')
        self.assertEqual(employee.employee_id, original_id)  # ID unchanged

    def test_05_document_upload_after_creation_workflow(self):
        """Test uploading documents after employee creation."""
        employee = self._create_test_employee()
        initial_doc_count = self._count_documents_in_vault(employee)

        # Upload document later
        employee.write({
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
        })

        # Verify document synced
        new_doc_count = self._count_documents_in_vault(employee)
        self.assertGreater(new_doc_count, initial_doc_count)

    def test_06_employee_lifecycle_complete_workflow(self):
        """Test complete employee lifecycle from onboarding to exit."""
        # Create employee (onboarding)
        employee = self.Employee.create({
            **self._get_employee_full_values(),
            'employee_status': 'onboarding',
            'date_of_joining': '2024-01-01',
        })

        # Mark as active
        employee.write({'employee_status': 'active'})
        self.assertEqual(employee.employee_status, 'active')

        # Issue assets
        employee.write({
            'asset_laptop': True,
            'asset_sim': True,
            'asset_physical_id': True,
        })

        # Employee submits resignation
        employee.write({'employee_status': 'notice'})

        # Complete resignation
        employee.write({'employee_status': 'resigned'})

        # Verify final state
        self.assertEqual(employee.employee_status, 'resigned')
        self.assertTrue(employee.asset_laptop)


@tagged('post_install', '-at_install', 'ui_workflow', 'integration')
class TestIntegrationWorkflows(HREmployeeCleardealsTestCase):
    """Test integration workflows with other modules."""

    def test_01_document_vault_smart_button(self):
        """Test document vault smart button functionality."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
        })

        # Get document count
        doc_count = employee.document_count
        self.assertGreater(doc_count, 0, "Should have documents")

        # Open document vault view
        action = employee.action_document_view()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'hr.employee.document')
        self.assertIn('domain', action)

    def test_02_address_copy_workflow(self):
        """Test address copy functionality workflow."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Main Street',
            'private_city': 'Ahmedabad',
            'private_state_id': self.state_gj.id,
            'private_country_id': self.country_india.id,
        })

        # Enable "same as permanent"
        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Verify address copied
        self.assertTrue(employee.current_address)
        self.assertIn('Main Street', employee.current_address)

    def test_03_bulk_import_workflow(self):
        """Test bulk employee import workflow."""
        # Simulate importing multiple employees
        import_data = []
        for i in range(10):
            import_data.append({
                **self._get_employee_base_values(),
                'name': f'Imported Employee {i}',
                'work_email': f'import{i}@test.com',
            })

        employees = self.Employee.create(import_data)

        # Verify all created with unique IDs
        self.assertEqual(len(employees), 10)
        employee_ids = employees.mapped('employee_id')
        self.assertEqual(len(set(employee_ids)), 10, "All IDs should be unique")


@tagged('post_install', '-at_install', 'ui_workflow', 'edge_cases')
class TestWorkflowEdgeCases(HREmployeeCleardealsTestCase):
    """Test edge cases in UI workflows."""

    def test_01_create_employee_special_characters_name(self):
        """Test creating employee with special characters in name."""
        employee = self._create_test_employee(
            name="O'Brien-Smith (Jr.)",
        )

        self.assertEqual(employee.name, "O'Brien-Smith (Jr.)")

    def test_02_create_employee_unicode_name(self):
        """Test creating employee with unicode characters."""
        employee = self._create_test_employee(
            name="राज कुमार",  # Hindi name
        )

        self.assertEqual(employee.name, "राज कुमार")

    def test_03_upload_replace_document_workflow(self):
        """Test replacing existing document with new one."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_old.pdf',
        })

        # Replace document
        employee.write({
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_new.pdf',
        })

        # Verify document updated/replaced
        doc_count = self._count_documents_in_vault(employee)
        self.assertGreater(doc_count, 0)
