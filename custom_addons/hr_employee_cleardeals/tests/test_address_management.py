"""
Test Cases for Address Management

Tests permanent and current address handling, including structured address fields.
"""

from odoo.tests import tagged

from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'address')
class TestPermanentAddress(HREmployeeCleardealsTestCase):
    """Test permanent address functionality."""

    def test_01_create_employee_with_permanent_address(self):
        """Test creating employee with complete permanent address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Main Street',
            'private_street2': 'Apartment 4B',
            'private_city': 'Ahmedabad',
            'private_state_id': self.state_gj.id,
            'private_zip': '380001',
            'private_country_id': self.country_india.id,
        })

        self.assertEqual(employee.private_street, '123 Main Street')
        self.assertEqual(employee.private_city, 'Ahmedabad')
        self.assertEqual(employee.private_state_id.id, self.state_gj.id)
        self.assertEqual(employee.private_zip, '380001')

    def test_02_permanent_address_with_only_street(self):
        """Test minimal permanent address with only street."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Simple Street Address',
        })

        self.assertEqual(employee.private_street, 'Simple Street Address')
        self.assertFalse(employee.private_city)

    def test_03_update_permanent_address(self):
        """Test updating permanent address."""
        employee = self._create_test_employee()

        employee.write({
            'private_street': 'New Street',
            'private_city': 'New City',
        })

        self.assertEqual(employee.private_street, 'New Street')
        self.assertEqual(employee.private_city, 'New City')

    def test_04_state_country_relationship(self):
        """Test state belongs to correct country."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_state_id': self.state_gj.id,
            'private_country_id': self.country_india.id,
        })

        self.assertEqual(employee.private_state_id.country_id.id,
                        employee.private_country_id.id)

    def test_05_address_with_unicode_characters(self):
        """Test address with unicode/non-ASCII characters."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'સ્ટ્રીટ રોડ',  # Gujarati
            'private_city': 'અમદાવાદ',
        })

        self.assertEqual(employee.private_street, 'સ્ટ્રીટ રોડ')
        self.assertEqual(employee.private_city, 'અમદાવાદ')


@tagged('post_install', '-at_install', 'address')
class TestCurrentAddress(HREmployeeCleardealsTestCase):
    """Test current address functionality."""

    def test_01_create_employee_with_current_address(self):
        """Test creating employee with current address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'current_address': '456 Current Street, Current City, 400001',
        })

        self.assertEqual(employee.current_address,
                        '456 Current Street, Current City, 400001')

    def test_02_current_address_different_from_permanent(self):
        """Test current address can be different from permanent."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': 'Permanent Street',
            'current_address': 'Current Address Text',
        })

        self.assertEqual(employee.private_street, 'Permanent Street')
        self.assertEqual(employee.current_address, 'Current Address Text')
        self.assertNotEqual(employee.private_street, employee.current_address)

    def test_03_same_as_permanent_toggle(self):
        """Test same_as_permanent toggle functionality."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Test Street',
            'private_city': 'Test City',
            'same_as_permanent': False,
        })

        self.assertFalse(employee.same_as_permanent)

        employee.write({'same_as_permanent': True})
        employee._onchange_same_as_permanent()

        self.assertTrue(employee.same_as_permanent)
        self.assertIn('Test Street', employee.current_address or '')

    def test_04_clear_current_address(self):
        """Test clearing current address."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'current_address': 'Some address',
        })

        employee.write({'current_address': False})

        self.assertFalse(employee.current_address)

    def test_05_very_long_current_address(self):
        """Test current address with very long text."""
        long_address = 'A' * 500  # 500 characters

        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'current_address': long_address,
        })

        self.assertEqual(len(employee.current_address), 500)


@tagged('post_install', '-at_install', 'address', 'integration')
class TestAddressIntegration(HREmployeeCleardealsTestCase):
    """Test address integration scenarios."""

    def test_01_complete_address_workflow(self):
        """Test complete address entry workflow."""
        # Create employee with permanent address
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'private_street': '123 Main Street',
            'private_city': 'Ahmedabad',
            'private_state_id': self.state_gj.id,
            'private_zip': '380001',
            'private_country_id': self.country_india.id,
        })

        # Initially current address is different
        employee.write({'current_address': 'Temporary PG Address'})

        # Later, moves to permanent address
        employee.write({'same_as_permanent': True})
        employee._onchange_same_as_permanent()

        # Verify current address updated
        self.assertIn('Main Street', employee.current_address or '')

    def test_02_address_search_by_city(self):
        """Test searching employees by city."""
        emp1 = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Ahmedabad Employee',
            'private_city': 'Ahmedabad',
        })

        emp2 = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Surat Employee',
            'work_email': 'surat@test.com',
            'private_city': 'Surat',
        })

        ahmedabad_employees = self.Employee.search([
            ('private_city', '=', 'Ahmedabad'),
            ('id', 'in', [emp1.id, emp2.id]),
        ])

        self.assertIn(emp1, ahmedabad_employees)
        self.assertNotIn(emp2, ahmedabad_employees)

    def test_03_address_search_by_state(self):
        """Test searching employees by state."""
        employees = self.Employee.create([
            {**self._get_employee_base_values(),
             'name': f'Gujarat Emp {i}',
             'work_email': f'gj{i}@test.com',
             'private_state_id': self.state_gj.id}
            for i in range(3)
        ])

        gujarat_employees = self.Employee.search([
            ('private_state_id', '=', self.state_gj.id),
            ('id', 'in', employees.ids),
        ])

        self.assertEqual(len(gujarat_employees), 3)

    def test_04_address_multiline_formatting(self):
        """Test address with newlines/multiple lines."""
        multiline_address = "Building A, Floor 3\nTech Park\nAhmedabad - 380015"

        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'current_address': multiline_address,
        })

        self.assertEqual(employee.current_address, multiline_address)
