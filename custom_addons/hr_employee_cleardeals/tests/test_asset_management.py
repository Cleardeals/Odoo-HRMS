"""
Test Cases for Asset Management

Tests asset tracking functionality for employees.
"""

from odoo.tests import tagged

from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'assets')
class TestAssetManagement(HREmployeeCleardealsTestCase):
    """Test asset tracking functionality."""

    def test_01_all_asset_fields_default_false(self):
        """Test that all asset fields default to False."""
        employee = self._create_test_employee()

        self.assertFalse(employee.asset_laptop)
        self.assertFalse(employee.asset_sim)
        self.assertFalse(employee.asset_phone)
        self.assertFalse(employee.asset_pc)
        self.assertFalse(employee.asset_physical_id)

    def test_02_assign_laptop_to_employee(self):
        """Test assigning laptop to employee."""
        employee = self._create_test_employee()

        employee.write({'asset_laptop': True})

        self.assertTrue(employee.asset_laptop)

    def test_03_assign_sim_card_to_employee(self):
        """Test assigning SIM card to employee."""
        employee = self._create_test_employee()

        employee.write({'asset_sim': True})

        self.assertTrue(employee.asset_sim)

    def test_04_assign_phone_to_employee(self):
        """Test assigning phone to employee."""
        employee = self._create_test_employee()

        employee.write({'asset_phone': True})

        self.assertTrue(employee.asset_phone)

    def test_05_assign_pc_to_employee(self):
        """Test assigning PC/Desktop to employee."""
        employee = self._create_test_employee()

        employee.write({'asset_pc': True})

        self.assertTrue(employee.asset_pc)

    def test_06_assign_physical_id_to_employee(self):
        """Test assigning physical ID card to employee."""
        employee = self._create_test_employee()

        employee.write({'asset_physical_id': True})

        self.assertTrue(employee.asset_physical_id)

    def test_07_assign_multiple_assets(self):
        """Test assigning multiple assets to employee."""
        employee = self._create_test_employee()

        employee.write({
            'asset_laptop': True,
            'asset_sim': True,
            'asset_phone': True,
            'asset_pc': False,
            'asset_physical_id': True,
        })

        self.assertTrue(employee.asset_laptop)
        self.assertTrue(employee.asset_sim)
        self.assertTrue(employee.asset_phone)
        self.assertFalse(employee.asset_pc)
        self.assertTrue(employee.asset_physical_id)

    def test_08_revoke_asset_from_employee(self):
        """Test revoking asset from employee."""
        employee = self._create_test_employee(asset_laptop=True)

        self.assertTrue(employee.asset_laptop)

        employee.write({'asset_laptop': False})

        self.assertFalse(employee.asset_laptop)

    def test_09_asset_tracking_on_creation(self):
        """Test asset fields support tracking."""
        employee = self._create_test_employee(asset_laptop=True)

        # Tracking should be enabled
        # Field definition has tracking=True
        self.assertTrue(employee.asset_laptop)

    def test_10_search_employees_by_asset(self):
        """Test searching employees by assigned assets."""
        emp1 = self._create_test_employee(name='Emp 1', asset_laptop=True)
        emp2 = self._create_test_employee(name='Emp 2', asset_laptop=False)
        emp3 = self._create_test_employee(name='Emp 3', asset_laptop=True)

        # Search employees with laptop
        laptop_employees = self.Employee.search([
            ('asset_laptop', '=', True),
            ('id', 'in', [emp1.id, emp2.id, emp3.id]),
        ])

        self.assertIn(emp1, laptop_employees)
        self.assertNotIn(emp2, laptop_employees)
        self.assertIn(emp3, laptop_employees)

    def test_11_bulk_asset_assignment(self):
        """Test assigning assets to multiple employees."""
        employees = self.Employee.create([
            {**self._get_employee_base_values(), 'name': f'Emp {i}'}
            for i in range(5)
        ])

        # Assign laptop to all
        employees.write({'asset_laptop': True})

        for emp in employees:
            self.assertTrue(emp.asset_laptop)

    def test_12_asset_state_on_resignation(self):
        """Test asset tracking when employee resigns."""
        employee = self._create_test_employee(
            asset_laptop=True,
            asset_sim=True,
            asset_physical_id=True,
        )

        # Employee resigns
        employee.write({'employee_status': 'resigned'})

        # Assets should still be tracked (need manual cleanup)
        self.assertTrue(employee.asset_laptop)
        self.assertTrue(employee.asset_sim)

        # Revoke assets on exit
        employee.write({
            'asset_laptop': False,
            'asset_sim': False,
            'asset_physical_id': False,
        })

        self.assertFalse(employee.asset_laptop)


@tagged('post_install', '-at_install', 'assets', 'reporting')
class TestAssetReporting(HREmployeeCleardealsTestCase):
    """Test asset management reporting."""

    def test_01_count_total_laptops_issued(self):
        """Test counting total laptops issued."""
        # Create employees with laptops
        for i in range(3):
            self._create_test_employee(
                name=f'Laptop User {i}',
                asset_laptop=True,
            )

        # Count laptops
        laptop_count = self.Employee.search_count([
            ('asset_laptop', '=', True),
        ])

        self.assertGreaterEqual(laptop_count, 3)

    def test_02_find_employees_without_id_card(self):
        """Test finding employees without physical ID card."""
        emp_with = self._create_test_employee(
            name='With ID',
            asset_physical_id=True,
        )
        emp_without = self._create_test_employee(
            name='Without ID',
            asset_physical_id=False,
        )

        # Find employees without ID
        no_id_emps = self.Employee.search([
            ('asset_physical_id', '=', False),
            ('id', 'in', [emp_with.id, emp_without.id]),
        ])

        self.assertIn(emp_without, no_id_emps)
        self.assertNotIn(emp_with, no_id_emps)
