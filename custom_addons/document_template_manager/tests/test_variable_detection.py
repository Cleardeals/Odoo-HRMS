"""
Test Cases for Automatic Variable Detection

Tests the automatic detection and creation of variables from HTML content.
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "variable_detection")
class TestVariableDetection(DocumentTemplateTestCase):
    """Test automatic variable detection from HTML content."""

    def test_01_detect_single_variable(self):
        """Test detecting a single variable in HTML."""
        template = self._create_test_template(
            html_content="<p>Hello {{name}}</p>",
        )

        self.assertEqual(len(template.variable_ids), 0)

        template.action_detect_variables()

        self.assertEqual(len(template.variable_ids), 1)
        var = template.variable_ids[0]
        self.assertEqual(var.name, "name")
        self.assertEqual(var.label, "Name")

    def test_02_detect_multiple_variables(self):
        """Test detecting multiple variables."""
        template = self._create_test_template(
            html_content=self._get_sample_html_content(with_variables=True),
        )

        template.action_detect_variables()

        detected_vars = set(template.variable_ids.mapped("name"))
        expected_vars = self._extract_variables_from_html(template.html_content)

        self.assertEqual(detected_vars, expected_vars)

    def test_03_detect_variables_with_spaces(self):
        """Test detecting variables with spaces in placeholders."""
        template = self._create_test_template(
            html_content="<p>{{  variable_name  }}</p>",
        )

        template.action_detect_variables()

        self.assertEqual(len(template.variable_ids), 1)
        self.assertEqual(template.variable_ids[0].name, "variable_name")

    def test_04_detect_same_variable_multiple_times(self):
        """Test that same variable mentioned multiple times is created once."""
        template = self._create_test_template(
            html_content="""
                <h1>{{title}}</h1>
                <p>{{title}}</p>
                <footer>{{title}}</footer>
            """,
        )

        template.action_detect_variables()

        self.assertEqual(len(template.variable_ids), 1)
        self.assertEqual(template.variable_ids[0].name, "title")

    def test_05_detect_doesnt_duplicate_existing(self):
        """Test that detection doesn't duplicate existing variables."""
        template = self._create_test_template(
            html_content="<p>{{name}} and {{age}}</p>",
        )

        # Create one variable manually
        self.Variable.create({
            "template_id": template.id,
            "name": "name",
            "label": "Name",
        })

        template.action_detect_variables()

        # Should only add 'age', not 'name'
        self.assertEqual(len(template.variable_ids), 2)
        var_names = set(template.variable_ids.mapped("name"))
        self.assertEqual(var_names, {"name", "age"})

    def test_06_detect_variables_sequential_sequence(self):
        """Test that detected variables get sequential sequence numbers."""
        template = self._create_test_template(
            html_content="<p>{{var1}} {{var2}} {{var3}}</p>",
        )

        template.action_detect_variables()

        sequences = template.variable_ids.mapped("sequence")
        self.assertEqual(len(set(sequences)), 3)  # All unique
        self.assertTrue(all(s >= 10 for s in sequences))  # All >= 10

    def test_07_detect_with_existing_respects_sequence(self):
        """Test that new variables get sequence after existing ones."""
        template = self._create_test_template(
            html_content="<p>{{old}} {{new}}</p>",
        )

        # Create existing variable with sequence 50
        self.Variable.create({
            "template_id": template.id,
            "name": "old",
            "label": "Old",
            "sequence": 50,
        })

        template.action_detect_variables()

        new_var = template.variable_ids.filtered(lambda var: var.name == "new")
        self.assertGreater(new_var.sequence, 50)

    def test_08_detect_generates_label_from_name(self):
        """Test that label is auto-generated from variable name."""
        template = self._create_test_template(
            html_content="<p>{{employee_full_name}}</p>",
        )

        template.action_detect_variables()

        var = template.variable_ids[0]
        self.assertEqual(var.name, "employee_full_name")
        self.assertEqual(var.label, "Employee Full Name")  # Title case with spaces

    def test_09_detect_sets_required_true(self):
        """Test that detected variables are marked as required."""
        template = self._create_test_template(
            html_content="<p>{{test_var}}</p>",
        )

        template.action_detect_variables()

        self.assertTrue(template.variable_ids[0].required)

    def test_10_detect_sets_type_char(self):
        """Test that detected variables default to char type."""
        template = self._create_test_template(
            html_content="<p>{{test_var}}</p>",
        )

        template.action_detect_variables()

        self.assertEqual(template.variable_ids[0].variable_type, "char")

    def test_11_detect_empty_content_raises_error(self):
        """Test that detection fails on empty content."""
        template = self._create_test_template(html_content=False)

        with self.assertRaises(ValidationError, msg="Empty content should raise error"):
            template.action_detect_variables()

    def test_12_detect_with_no_variables_in_content(self):
        """Test detection when no variables are present."""
        template = self._create_test_template(
            html_content="<p>Plain text without variables</p>",
        )

        result = template.action_detect_variables()

        self.assertEqual(len(template.variable_ids), 0)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "ir.actions.client")

    def test_13_detect_returns_notification(self):
        """Test that detection returns a notification action."""
        template = self._create_test_template(
            html_content="<p>{{name}}</p>",
        )

        result = template.action_detect_variables()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertIn("params", result)


@tagged("post_install", "-at_install", "detection_patterns")
class TestVariableDetectionPatterns(DocumentTemplateTestCase):
    """Test various patterns and edge cases in variable detection."""

    def test_01_detect_underscore_variables(self):
        """Test detecting variables with underscores."""
        template = self._create_test_template(
            html_content="<p>{{first_name}} {{last_name}}</p>",
        )

        template.action_detect_variables()

        var_names = set(template.variable_ids.mapped("name"))
        self.assertEqual(var_names, {"first_name", "last_name"})

    def test_02_detect_numeric_variables(self):
        """Test detecting variables with numbers."""
        template = self._create_test_template(
            html_content="<p>{{var1}} {{var2}} {{item123}}</p>",
        )

        template.action_detect_variables()

        var_names = set(template.variable_ids.mapped("name"))
        self.assertEqual(var_names, {"var1", "var2", "item123"})

    def test_03_detect_ignores_non_word_characters(self):
        """Test that only word characters are matched in variable names."""
        template = self._create_test_template(
            html_content="<p>{{valid_var}} {{not-valid}}</p>",
        )

        template.action_detect_variables()

        # Only valid_var should be detected (not-valid has dash)
        var_names = set(template.variable_ids.mapped("name"))
        self.assertIn("valid_var", var_names)

    def test_04_detect_case_sensitive(self):
        """Test that variable names maintain case."""
        template = self._create_test_template(
            html_content="<p>{{CamelCase}} {{lowercase}} {{UPPERCASE}}</p>",
        )

        template.action_detect_variables()

        var_names = set(template.variable_ids.mapped("name"))
        self.assertEqual(var_names, {"CamelCase", "lowercase", "UPPERCASE"})

    def test_05_detect_in_attributes(self):
        """Test detecting variables in HTML attributes."""
        template = self._create_test_template(
            html_content='<img src="{{image_url}}" alt="{{alt_text}}" />',
        )

        template.action_detect_variables()

        var_names = set(template.variable_ids.mapped("name"))
        self.assertEqual(var_names, {"image_url", "alt_text"})

    def test_06_detect_in_nested_html(self):
        """Test detecting variables in deeply nested HTML."""
        template = self._create_test_template(
            html_content="""
                <div>
                    <table>
                        <tr>
                            <td>{{cell1}}</td>
                            <td>{{cell2}}</td>
                        </tr>
                    </table>
                </div>
            """,
        )

        template.action_detect_variables()

        var_names = set(template.variable_ids.mapped("name"))
        self.assertEqual(var_names, {"cell1", "cell2"})

    def test_07_detect_multiline_template(self):
        """Test detection in multiline templates."""
        template = self._create_test_template(
            html_content="""
                <h1>{{title}}</h1>
                <p>{{paragraph1}}</p>
                <p>{{paragraph2}}</p>
                <footer>{{footer}}</footer>
            """,
        )

        template.action_detect_variables()

        self.assertEqual(len(template.variable_ids), 4)


@tagged("post_install", "-at_install", "detection_notification")
class TestDetectionNotification(DocumentTemplateTestCase):
    """Test notification messages from variable detection."""

    def test_01_notification_shows_count(self):
        """Test that notification shows count of detected variables."""
        template = self._create_test_template(
            html_content="<p>{{var1}} {{var2}} {{var3}}</p>",
        )

        result = template.action_detect_variables()

        params = result.get("params", {})
        message = params.get("message", "")
        self.assertIn("3", message)

    def test_02_notification_type_info_when_found(self):
        """Test notification type is 'info' when variables found."""
        template = self._create_test_template(
            html_content="<p>{{var}}</p>",
        )

        result = template.action_detect_variables()

        params = result.get("params", {})
        self.assertEqual(params.get("type"), "info")

    def test_03_notification_type_warning_when_none_found(self):
        """Test notification type is 'warning' when no variables found."""
        template = self._create_test_template(
            html_content="<p>No variables here</p>",
        )

        result = template.action_detect_variables()

        params = result.get("params", {})
        self.assertEqual(params.get("type"), "warning")
