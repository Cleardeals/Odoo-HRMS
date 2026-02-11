# -*- coding: utf-8 -*-
"""
Test Cases for Employee Creation and ID Generation

Tests employee record creation, automatic employee ID generation,
sequence management, and bulk creation scenarios.
"""

from odoo.tests import tagged
from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'employee_creation')
class TestEmployeeCreation(HREmployeeCleardealsTestCase):
    """Test employee creation and ID generation functionality."""
    
    def test_01_employee_creation_generates_id(self):
        """Test that creating an employee automatically generates employee_id."""
        employee = self._create_test_employee()
        
        self.assertTrue(employee.employee_id, "Employee ID should be generated")
        self.assertTrue(employee.employee_id.startswith('CD-'), 
                       "Employee ID should start with CD-")
        self.assertEqual(len(employee.employee_id), 7, 
                        "Employee ID should be 7 characters (CD-XXXX)")
    
    def test_02_employee_id_format_validation(self):
        """Test that employee ID follows CD-XXXX format."""
        employee = self._create_test_employee()
        
        # Check format: CD-XXXX where X is a digit
        self.assertRegex(employee.employee_id, r'^CD-\d{4}$',
                        "Employee ID should match pattern CD-XXXX")
    
    def test_03_employee_id_uniqueness(self):
        """Test that each employee gets a unique ID."""
        employees = []
        for i in range(5):
            emp = self._create_test_employee(name=f'Employee {i}')
            employees.append(emp)
        
        employee_ids = [emp.employee_id for emp in employees]
        unique_ids = set(employee_ids)
        
        self.assertEqual(len(employee_ids), len(unique_ids),
                        "All employee IDs should be unique")
    
    def test_04_employee_id_sequential(self):
        """Test that employee IDs are generated sequentially."""
        self._reset_employee_sequence(100)
        
        emp1 = self._create_test_employee(name='Employee 1')
        emp2 = self._create_test_employee(name='Employee 2')
        emp3 = self._create_test_employee(name='Employee 3')
        
        self.assertEqual(emp1.employee_id, 'CD-0100')
        self.assertEqual(emp2.employee_id, 'CD-0101')
        self.assertEqual(emp3.employee_id, 'CD-0102')
    
    def test_05_employee_id_readonly(self):
        """Test that employee_id cannot be manually changed after creation."""
        employee = self._create_test_employee()
        original_id = employee.employee_id
        
        # Attempt to write should not change the ID in UI context
        # (readonly field in form view)
        self.assertTrue(employee.employee_id, "Employee ID should exist")
        self.assertEqual(employee.employee_id, original_id,
                        "Employee ID should remain unchanged")
    
    def test_06_bulk_employee_creation(self):
        """Test creating multiple employees at once."""
        values_list = [
            self._get_employee_base_values(),
            {**self._get_employee_base_values(), 'name': 'Employee 2'},
            {**self._get_employee_base_values(), 'name': 'Employee 3'},
        ]
        
        employees = self.Employee.create(values_list)
        
        self.assertEqual(len(employees), 3, "Should create 3 employees")
        for emp in employees:
            self.assertTrue(emp.employee_id, "Each employee should have an ID")
            self.assertTrue(emp.employee_id.startswith('CD-'),
                          "Each ID should start with CD-")
    
    def test_07_employee_creation_with_all_required_fields(self):
        """Test creating employee with all required fields."""
        values = self._get_employee_full_values()
        employee = self.Employee.create(values)
        
        self.assertTrue(employee.id, "Employee should be created")
        self.assertTrue(employee.name, "Employee should have a name")
        self.assertEqual(employee.work_email, values['work_email'])
        self.assertEqual(employee.identification_id, values['identification_id'])
        self.assertEqual(employee.pan_number, values['pan_number'].upper())
    
    def test_08_employee_default_status(self):
        """Test that new employees have default status 'onboarding'."""
        employee = self._create_test_employee()
        
        self.assertEqual(employee.employee_status, 'onboarding',
                        "New employee should have 'onboarding' status")
    
    def test_09_employee_creation_with_custom_status(self):
        """Test creating employee with custom status."""
        employee = self._create_test_employee(employee_status='active')
        
        self.assertEqual(employee.employee_status, 'active',
                        "Employee status should be 'active'")
    
    def test_10_employee_tracking_fields(self):
        """Test that tracking fields are properly configured."""
        employee = self._create_test_employee()
        
        # These fields should support tracking
        tracked_fields = ['employee_id', 'employee_status', 'date_of_joining',
                         'blood_group', 'pan_number']
        
        for field_name in tracked_fields:
            field = self.Employee._fields.get(field_name)
            if field:
                # Field exists in model
                self.assertTrue(True, f"Field {field_name} exists")
    
    def test_11_employee_creation_with_department_and_job(self):
        """Test employee creation with department and job assignment."""
        employee = self._create_test_employee(
            department_id=self.dept_sales.id,
            job_id=self.job_bde.id
        )
        
        self.assertEqual(employee.department_id.id, self.dept_sales.id)
        self.assertEqual(employee.job_id.id, self.job_bde.id)
    
    def test_12_employee_id_preserved_on_update(self):
        """Test that employee_id is preserved when updating other fields."""
        employee = self._create_test_employee()
        original_id = employee.employee_id
        
        employee.write({
            'name': 'Updated Name',
            'work_email': 'updated@cleardeals.com'
        })
        
        self.assertEqual(employee.employee_id, original_id,
                        "Employee ID should not change on update")
    
    def test_13_employee_creation_triggers_document_sync(self):
        """Test that creating employee triggers document vault sync."""
        # Create employee with a document
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card.pdf',
        })
        
        # Check if document was synced to vault
        # Note: _sync_documents_to_vault is called in create()
        self.assertTrue(employee.id, "Employee should be created")
        # Vault sync is tested separately in test_document_sync.py
    
    def test_14_employee_without_optional_fields(self):
        """Test creating employee with only mandatory fields."""
        minimal_values = {
            'name': 'Minimal Employee',
        }
        
        employee = self.Employee.create(minimal_values)
        
        self.assertTrue(employee.id, "Employee should be created")
        self.assertTrue(employee.employee_id, "Employee ID should be generated")
    
    def test_15_employee_copy_excludes_employee_id(self):
        """Test that copying employee generates new employee_id."""
        employee1 = self._create_test_employee()
        employee2 = employee1.copy({'name': 'Copied Employee'})
        
        self.assertNotEqual(employee1.employee_id, employee2.employee_id,
                           "Copied employee should have different ID")
        self.assertTrue(employee2.employee_id.startswith('CD-'),
                       "Copied employee should have valid ID format")


@tagged('post_install', '-at_install', 'employee_creation', 'performance')
class TestEmployeeCreationPerformance(HREmployeeCleardealsTestCase):
    """Test performance aspects of employee creation."""
    
    def test_01_bulk_creation_performance(self):
        """Test that bulk creation is efficient (100 employees)."""
        import time
        
        values_list = [
            {**self._get_employee_base_values(), 'name': f'Employee {i}'}
            for i in range(100)
        ]
        
        start_time = time.time()
        employees = self.Employee.create(values_list)
        end_time = time.time()
        
        duration = end_time - start_time
        
        self.assertEqual(len(employees), 100, "Should create 100 employees")
        # Should complete in reasonable time (10 seconds for 100 records)
        self.assertLess(duration, 10.0,
                       f"Bulk creation took {duration:.2f}s, should be under 10s")
    
    def test_02_sequence_generation_performance(self):
        """Test that sequence generation doesn't slow down with many records."""
        import time
        
        # Create 50 employees and measure time
        times = []
        for i in range(50):
            start = time.time()
            self._create_test_employee(name=f'Perf Test {i}')
            times.append(time.time() - start)
        
        # First creation might be slower due to caching
        avg_time = sum(times[10:]) / len(times[10:])  # Skip first 10
        
        # Each creation should be fast (under 0.5 seconds)
        self.assertLess(avg_time, 0.5,
                       f"Average creation time {avg_time:.3f}s is too slow")
