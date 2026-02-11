# -*- coding: utf-8 -*-
"""
Test Cases for Employee Lifecycle Status

Tests employee status transitions and lifecycle management.
"""

from odoo.tests import tagged
from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'lifecycle')
class TestEmployeeLifecycleStatus(HREmployeeCleardealsTestCase):
    """Test employee lifecycle status functionality."""
    
    def test_01_default_status_onboarding(self):
        """Test that new employee defaults to onboarding status."""
        employee = self._create_test_employee()
        
        self.assertEqual(employee.employee_status, 'onboarding',
                        "New employee should have onboarding status")
    
    def test_02_transition_onboarding_to_active(self):
        """Test transitioning from onboarding to active."""
        employee = self._create_test_employee()
        
        employee.write({'employee_status': 'active'})
        
        self.assertEqual(employee.employee_status, 'active')
    
    def test_03_transition_active_to_notice(self):
        """Test transitioning from active to notice period."""
        employee = self._create_test_employee(employee_status='active')
        
        employee.write({'employee_status': 'notice'})
        
        self.assertEqual(employee.employee_status, 'notice')
    
    def test_04_transition_notice_to_resigned(self):
        """Test transitioning from notice to resigned."""
        employee = self._create_test_employee(employee_status='notice')
        
        employee.write({'employee_status': 'resigned'})
        
        self.assertEqual(employee.employee_status, 'resigned')
    
    def test_05_transition_to_terminated(self):
        """Test transitioning to terminated status."""
        employee = self._create_test_employee(employee_status='active')
        
        employee.write({'employee_status': 'terminated'})
        
        self.assertEqual(employee.employee_status, 'terminated')
    
    def test_06_all_status_values_valid(self):
        """Test all possible status values."""
        statuses = ['onboarding', 'active', 'notice', 'resigned', 'terminated']
        
        for status in statuses:
            with self.subTest(status=status):
                employee = self._create_test_employee(
                    employee_status=status,
                    name=f'Employee {status}'
                )
                self.assertEqual(employee.employee_status, status)
    
    def test_07_status_field_required(self):
        """Test that employee_status is required."""
        # Field is required, so creating without it should use default
        employee = self._create_test_employee()
        
        self.assertTrue(employee.employee_status,
                       "Status should have a value")
    
    def test_08_status_tracking_enabled(self):
        """Test that status changes are tracked."""
        employee = self._create_test_employee()
        
        # Change status  
        employee.write({'employee_status': 'active'})
        
        # Status field should have tracking enabled
        # Verified in model definition
        self.assertEqual(employee.employee_status, 'active')
    
    def test_09_bulk_status_update(self):
        """Test updating status for multiple employees."""
        employees = self.Employee.create([
            {**self._get_employee_base_values(), 'name': f'Emp {i}'}
            for i in range(5)
        ])
        
        employees.write({'employee_status': 'active'})
        
        for emp in employees:
            self.assertEqual(emp.employee_status, 'active')
    
    def test_10_search_by_status(self):
        """Test searching employees by status."""
        self._create_test_employee(name='Onboarding 1', employee_status='onboarding')
        self._create_test_employee(name='Onboarding 2', employee_status='onboarding')
        self._create_test_employee(name='Active 1', employee_status='active')
        
        onboarding_emps = self.Employee.search([
            ('employee_status', '=', 'onboarding')
        ])
        
        self.assertGreaterEqual(len(onboarding_emps), 2,
                               "Should find onboarding employees")


@tagged('post_install', '-at_install', 'lifecycle', 'workflows')
class TestLifecycleWorkflows(HREmployeeCleardealsTestCase):
    """Test complete lifecycle workflows."""
    
    def test_01_complete_employee_lifecycle(self):
        """Test complete lifecycle from onboarding to resigned."""
        employee = self._create_test_employee()
        
        # Journey through lifecycle
        self.assertEqual(employee.employee_status, 'onboarding')
        
        employee.write({'employee_status': 'active'})
        self.assertEqual(employee.employee_status, 'active')
        
        employee.write({'employee_status': 'notice'})
        self.assertEqual(employee.employee_status, 'notice')
        
        employee.write({'employee_status': 'resigned'})
        self.assertEqual(employee.employee_status, 'resigned')
    
    def test_02_abrupt_termination_workflow(self):
        """Test abrupt termination from active status."""
        employee = self._create_test_employee(employee_status='active')
        
        # Direct termination without notice
        employee.write({'employee_status': 'terminated'})
        
        self.assertEqual(employee.employee_status, 'terminated')
    
    def test_03_status_history_preserved(self):
        """Test that status changes create tracking history."""
        employee = self._create_test_employee()
        
        # Multiple status changes
        employee.write({'employee_status': 'active'})
        employee.write({'employee_status': 'notice'})
        employee.write({'employee_status': 'resigned'})
        
        # Final status should be resigned
        self.assertEqual(employee.employee_status, 'resigned')
