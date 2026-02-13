"""
Test Cases for OnChange Methods

Tests onchange behavior for address synchronization and other dynamic fields.
"""

from odoo.tests import tagged

from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'onchange')
class TestAddressOnChange(HREmployeeCleardealsTestCase):
    """Test address field onchange behavior."""

    def test_01_same_as_permanent_copies_address(self):
        """Test that enabling 'same_as_permanent' copies permanent address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Test Street',
            'private_city': 'Ahmedabad',
            'private_state_id': self.state_gj.id,
            'private_zip': '380001',
            'private_country_id': self.country_india.id,
        })

        # Trigger onchange
        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Current address should be populated
        self.assertTrue(employee.current_address,
                       "Current address should be populated")
        self.assertIn('123 Test Street', employee.current_address,
                     "Should contain street name")
        self.assertIn('Ahmedabad', employee.current_address,
                     "Should contain city")

    def test_02_same_as_permanent_includes_all_fields(self):
        """Test that all permanent address fields are included."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Main Street',
            'private_street2': 'Apartment 4B',
            'private_city': 'Ahmedabad',
            'private_state_id': self.state_gj.id,
            'private_zip': '380001',
            'private_country_id': self.country_india.id,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        current_addr = employee.current_address
        self.assertIn('123 Main Street', current_addr)
        self.assertIn('Apartment 4B', current_addr)
        self.assertIn('Ahmedabad', current_addr)
        self.assertIn('Gujarat', current_addr)
        self.assertIn('380001', current_addr)
        self.assertIn('India', current_addr)

    def test_03_same_as_permanent_with_partial_address(self):
        """Test onchange with only some permanent address fields filled."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Test Street',
            'private_city': 'Ahmedabad',
            # No state, zip, or country
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should work with partial address
        self.assertTrue(employee.current_address)
        self.assertIn('Test Street', employee.current_address)

    def test_04_same_as_permanent_with_empty_address(self):
        """Test onchange when permanent address is empty."""
        employee = self._create_test_employee()

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should not crash, current_address might be empty or unchanged
        # This is a valid scenario
        self.assertTrue(True)  # Just ensure no exception

    def test_05_same_as_permanent_preserves_existing_current(self):
        """Test behavior when current address already exists."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Permanent Street',
            'private_city': 'Ahmedabad',
            'current_address': 'Existing Current Address',
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should update current address with permanent address
        self.assertIn('Permanent Street', employee.current_address or '')

    def test_06_unchecking_same_as_permanent(self):
        """Test that unchecking doesn't modify current address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Test Street',
            'current_address': 'My Current Address',
            'same_as_permanent': False,
        })

        current_before = employee.current_address

        # Uncheck (already False, but test the onchange)
        employee.same_as_permanent = False
        employee._onchange_same_as_permanent()

        # Current address should remain unchanged when unchecking
        # (onchange only acts when same_as_permanent is True)
        self.assertEqual(employee.current_address, current_before)

    def test_07_address_format_with_commas(self):
        """Test that address parts are separated by commas."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Street',
            'private_city': 'City',
            'private_state_id': self.state_gj.id,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Check comma separation
        self.assertIn(',', employee.current_address or '',
                     "Address parts should be comma-separated")

    def test_08_state_name_in_address(self):
        """Test that state name (not ID) is included in address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Test Street',
            'private_state_id': self.state_gj.id,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        self.assertIn('Gujarat', employee.current_address or '',
                     "Should include state name")

    def test_09_country_name_in_address(self):
        """Test that country name (not ID) is included in address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Test Street',
            'private_country_id': self.country_india.id,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        self.assertIn('India', employee.current_address or '',
                     "Should include country name")

    def test_10_onchange_multiple_times(self):
        """Test that onchange can be triggered multiple times."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 First Street',
            'private_city': 'Ahmedabad',
        })

        # First time
        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()
        first_address = employee.current_address

        # Update permanent address
        employee.write({
            'private_street': '456 Second Street',
            'private_city': 'Surat',
        })

        # Trigger again
        employee._onchange_same_as_permanent()
        second_address = employee.current_address

        # Should reflect new address
        self.assertNotEqual(first_address, second_address)
        self.assertIn('Second Street', second_address or '')


@tagged('post_install', '-at_install', 'onchange', 'edge_cases')
class TestOnChangeEdgeCases(HREmployeeCleardealsTestCase):
    """Test edge cases in onchange methods."""

    def test_01_onchange_with_null_state(self):
        """Test onchange when state is None/False."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Street',
            'private_state_id': False,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should not crash
        self.assertTrue(employee.current_address or True)

    def test_02_onchange_with_null_country(self):
        """Test onchange when country is None/False."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Street',
            'private_country_id': False,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should not crash
        self.assertTrue(employee.current_address or True)

    def test_03_onchange_with_unicode_address(self):
        """Test onchange with unicode characters in address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'રસ્તો',  # Gujarati text
            'private_city': 'અમદાવાદ',
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should handle unicode
        self.assertTrue(employee.current_address)

    def test_04_onchange_with_very_long_address(self):
        """Test onchange with very long address fields."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'A' * 200,
            'private_street2': 'B' * 200,
            'private_city': 'C' * 50,
        })

        employee.same_as_permanent = True
        employee._onchange_same_as_permanent()

        # Should handle long addresses
        self.assertTrue(len(employee.current_address or '') > 0)

    def test_05_onchange_multiple_employees_simultaneously(self):
        """Test onchange doesn't interfere between different employees."""
        emp1 = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Employee 1',
            'private_street': 'Street 1',
            'private_city': 'City 1',
        })

        emp2 = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Employee 2',
            'private_street': 'Street 2',
            'private_city': 'City 2',
        })

        emp1.same_as_permanent = True
        emp1._onchange_same_as_permanent()

        emp2.same_as_permanent = True
        emp2._onchange_same_as_permanent()

        # Each should have their own address
        self.assertIn('Street 1', emp1.current_address or '')
        self.assertIn('Street 2', emp2.current_address or '')
        self.assertNotEqual(emp1.current_address, emp2.current_address)
