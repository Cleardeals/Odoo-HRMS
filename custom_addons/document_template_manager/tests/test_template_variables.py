"""
Test Cases for Template Variables

Tests variable creation, management, types, validation, and placeholder generation.
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "template_variables")
class TestVariableCreation(DocumentTemplateTestCase):
    """Test variable creation and basic management."""

    def test_01_create_simple_variable(self):
        """Test creating a basic char variable."""
        template = self._create_test_template()
        variable = self.Variable.new(
            {
                "template_id": template.id,
                "name": "employee_name",
                "label": "Employee Name",
                "variable_type": "char",
                "required": True,
            },
        )

        self.assertEqual(variable.name, "employee_name")
        self.assertEqual(variable.label, "Employee Name")
        self.assertEqual(variable.variable_type, "char")
        self.assertTrue(variable.required)

    def test_02_create_text_variable(self):
        """Test creating a text (long text) variable."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "description",
                "label": "Description",
                "variable_type": "text",
                "required": False,
            },
        )

        self.assertEqual(variable.variable_type, "text")
        self.assertFalse(variable.required)

    def test_03_create_integer_variable(self):
        """Test creating an integer variable."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "age",
                "label": "Age",
                "variable_type": "integer",
            },
        )

        self.assertEqual(variable.variable_type, "integer")

    def test_04_create_float_variable(self):
        """Test creating a float/decimal variable."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "salary",
                "label": "Salary",
                "variable_type": "float",
                "default_value": "50000.00",
            },
        )

        self.assertEqual(variable.variable_type, "float")
        self.assertEqual(variable.default_value, "50000.00")

    def test_05_create_date_variable(self):
        """Test creating a date variable."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "start_date",
                "label": "Start Date",
                "variable_type": "date",
            },
        )

        self.assertEqual(variable.variable_type, "date")

    def test_06_create_selection_variable(self):
        """Test creating a selection/dropdown variable."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "department",
                "label": "Department",
                "variable_type": "selection",
                "selection_options": "HR,IT,Finance,Sales",
            },
        )

        self.assertEqual(variable.variable_type, "selection")
        self.assertEqual(variable.selection_options, "HR,IT,Finance,Sales")

    def test_07_variable_with_default_value(self):
        """Test variable with default value."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "company_name",
                "label": "Company Name",
                "variable_type": "char",
                "default_value": "Cleardeals",
            },
        )

        self.assertEqual(variable.default_value, "Cleardeals")

    def test_08_variable_sequence(self):
        """Test that variables respect sequence ordering."""
        template = self._create_test_template()
        var1 = self.Variable.create(
            {
                "template_id": template.id,
                "name": "var1",
                "label": "Variable 1",
                "sequence": 30,
            },
        )
        var2 = self.Variable.create(
            {
                "template_id": template.id,
                "name": "var2",
                "label": "Variable 2",
                "sequence": 10,
            },
        )
        var3 = self.Variable.create(
            {
                "template_id": template.id,
                "name": "var3",
                "label": "Variable 3",
                "sequence": 20,
            },
        )

        variables = template.variable_ids.sorted("sequence")
        self.assertEqual(variables[0], var2)
        self.assertEqual(variables[1], var3)
        self.assertEqual(variables[2], var1)

    def test_09_variable_required_defaults_true(self):
        """Test that required field defaults to True."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "test_var",
                "label": "Test Variable",
            },
        )

        self.assertTrue(variable.required)

    def test_10_variable_type_defaults_to_char(self):
        """Test that variable_type defaults to 'char'."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "test_var",
                "label": "Test Variable",
            },
        )

        self.assertEqual(variable.variable_type, "char")


@tagged("post_install", "-at_install", "variable_compute")
class TestVariableComputes(DocumentTemplateTestCase):
    """Test computed fields on variables."""

    def test_01_placeholder_tag_computed(self):
        """Test that placeholder_tag is computed correctly."""
        template = self._create_test_template()
        variable = self.Variable.create(
            {
                "template_id": template.id,
                "name": "employee_name",
                "label": "Employee Name",
            },
        )

        self.assertEqual(variable.placeholder_tag, "{{employee_name}}")

    def test_02_placeholder_tag_empty_name(self):
        """Test placeholder_tag when name is empty."""
        template = self._create_test_template()
        variable = self.Variable.new(
            {
                "template_id": template.id,
                "name": "",
                "label": "Test",
            },
        )

        self.assertEqual(variable.placeholder_tag, "")

    def test_03_variable_count_on_template(self):
        """Test that template's variable_count is computed correctly."""
        template = self._create_test_template()

        self.assertEqual(template.variable_count, 0)

        self.Variable.create(
            {
                "template_id": template.id,
                "name": "var1",
                "label": "Variable 1",
            },
        )
        self.assertEqual(template.variable_count, 1)

        self.Variable.create(
            {
                "template_id": template.id,
                "name": "var2",
                "label": "Variable 2",
            },
        )
        self.assertEqual(template.variable_count, 2)


@tagged("post_install", "-at_install", "variable_onchange")
class TestVariableOnchange(DocumentTemplateTestCase):
    """Test onchange methods for variables."""

    def test_01_auto_generate_name_from_label(self):
        """Test that name is auto-generated from label."""
        template = self._create_test_template()
        variable = self.Variable.new(
            {
                "template_id": template.id,
                "label": "Employee Full Name",
            },
        )

        variable._onchange_label()

        self.assertEqual(variable.name, "employee_full_name")

    def test_02_auto_generate_name_with_special_chars(self):
        """Test name generation with special characters."""
        template = self._create_test_template()
        variable = self.Variable.new(
            {
                "template_id": template.id,
                "label": "Employee's Salary (USD)!",
            },
        )

        variable._onchange_label()

        # Should convert to snake_case and remove special chars
        self.assertRegex(variable.name, r"^[a-z0-9_]+$")

    def test_03_auto_generate_name_no_override(self):
        """Test that existing name is not overridden."""
        template = self._create_test_template()
        variable = self.Variable.new(
            {
                "template_id": template.id,
                "name": "custom_name",
                "label": "Employee Name",
            },
        )

        variable._onchange_label()

        # Should keep custom_name
        self.assertEqual(variable.name, "custom_name")

    def test_04_auto_generate_name_lowercase(self):
        """Test that generated name is lowercase."""
        template = self._create_test_template()
        variable = self.Variable.new(
            {
                "template_id": template.id,
                "label": "EMPLOYEE NAME",
            },
        )

        variable._onchange_label()

        self.assertEqual(variable.name, "employee_name")


@tagged("post_install", "-at_install", "variable_constraints")
class TestVariableConstraints(DocumentTemplateTestCase):
    """Test variable constraints and validations."""

    def test_01_unique_variable_name_per_template(self):
        """Test that variable names must be unique within a template."""
        template = self._create_test_template()

        self.Variable.create(
            {
                "template_id": template.id,
                "name": "employee_name",
                "label": "Employee Name",
            },
        )

        with self.assertRaises(
            ValidationError,
            msg="Duplicate variable name should raise error",
        ):
            self.Variable.create(
                {
                    "template_id": template.id,
                    "name": "employee_name",
                    "label": "Another Name",
                },
            )

    def test_02_same_variable_name_different_templates_allowed(self):
        """Test that same variable name is allowed across different templates."""
        template1 = self._create_test_template(name="Template 1")
        template2 = self._create_test_template(name="Template 2")

        var1 = self.Variable.create(
            {
                "template_id": template1.id,
                "name": "employee_name",
                "label": "Employee Name",
            },
        )

        var2 = self.Variable.create(
            {
                "template_id": template2.id,
                "name": "employee_name",
                "label": "Employee Name",
            },
        )

        self.assertNotEqual(var1.id, var2.id)
        self.assertEqual(var1.name, var2.name)

    def test_03_template_id_required(self):
        """Test that template_id is required for variables."""
        with self.assertRaises(ValidationError):
            self.Variable.create(
                {
                    "name": "test_var",
                    "label": "Test Variable",
                },
            )

    def test_04_name_required(self):
        """Test that variable name is required."""
        template = self._create_test_template()

        with self.assertRaises(ValidationError):
            self.Variable.create(
                {
                    "template_id": template.id,
                    "label": "Test Variable",
                    "name": False,
                },
            )

    def test_05_label_required(self):
        """Test that variable label is required."""
        template = self._create_test_template()

        with self.assertRaises(ValidationError):
            self.Variable.create(
                {
                    "template_id": template.id,
                    "name": "test_var",
                    "label": False,
                },
            )


@tagged("post_install", "-at_install", "variable_crud")
class TestVariableCRUD(DocumentTemplateTestCase):
    """Test variable CRUD operations."""

    def test_01_update_variable_label(self):
        """Test updating variable label."""
        template = self._create_test_template()
        variable = self._create_test_variable(template)

        variable.write({"label": "Updated Label"})

        self.assertEqual(variable.label, "Updated Label")

    def test_02_update_variable_type(self):
        """Test updating variable type."""
        template = self._create_test_template()
        variable = self._create_test_variable(template, variable_type="char")

        variable.write({"variable_type": "integer"})

        self.assertEqual(variable.variable_type, "integer")

    def test_03_update_variable_required_flag(self):
        """Test toggling required flag."""
        template = self._create_test_template()
        variable = self._create_test_variable(template, required=True)

        variable.write({"required": False})

        self.assertFalse(variable.required)

    def test_04_update_variable_default_value(self):
        """Test updating default value."""
        template = self._create_test_template()
        variable = self._create_test_variable(template)

        variable.write({"default_value": "Default Text"})

        self.assertEqual(variable.default_value, "Default Text")

    def test_05_delete_variable(self):
        """Test deleting a variable."""
        template = self._create_test_template()
        variable = self._create_test_variable(template)
        variable_id = variable.id

        variable.unlink()

        self.assertFalse(self.Variable.browse(variable_id).exists())

    def test_06_delete_template_cascades_variables(self):
        """Test that deleting template deletes its variables."""
        template = self._create_template_with_variables()
        variable_ids = template.variable_ids.ids

        template.unlink()

        for var_id in variable_ids:
            self.assertFalse(self.Variable.browse(var_id).exists())

    def test_07_update_variable_sequence(self):
        """Test updating variable sequence."""
        template = self._create_test_template()
        variable = self._create_test_variable(template, sequence=10)

        variable.write({"sequence": 50})

        self.assertEqual(variable.sequence, 50)
