"""
Test Cases for Export Wizard

Tests the document export wizard, variable filling, PDF generation through wizard,
and all wizard functionality.
"""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "export_wizard")
class TestExportWizardCreation(DocumentTemplateTestCase):
    """Test export wizard creation and initialization."""

    def test_01_create_wizard_for_template(self):
        """Test creating wizard for a template with variables."""
        template = self._create_template_with_variables()

        wizard = self.ExportWizard.with_context(
            default_template_id=template.id,
        ).create({"template_id": template.id})

        self.assertEqual(wizard.template_id, template)
        self.assertEqual(wizard.template_name, template.name)

    def test_02_wizard_auto_creates_lines(self):
        """Test that wizard automatically creates lines for variables."""
        template = self._create_template_with_variables()

        wizard = self.ExportWizard.with_context(
            default_template_id=template.id,
        ).create({"template_id": template.id})

        self.assertEqual(len(wizard.line_ids), len(template.variable_ids))

    def test_03_wizard_lines_match_variables(self):
        """Test that wizard lines match template variables."""
        template = self._create_template_with_variables()

        wizard = self.ExportWizard.with_context(
            default_template_id=template.id,
        ).create({"template_id": template.id})

        for line in wizard.line_ids:
            self.assertIn(line.variable_id, template.variable_ids)
            self.assertEqual(line.name, line.variable_id.name)
            self.assertEqual(line.label, line.variable_id.label)
            self.assertEqual(line.variable_type, line.variable_id.variable_type)

    def test_04_wizard_line_default_values(self):
        """Test that wizard lines get default values from variables."""
        template = self._create_test_template()
        var = self.Variable.create(
            {
                "template_id": template.id,
                "name": "test_var",
                "label": "Test Variable",
                "default_value": "Default Value",
            },
        )

        wizard = self.ExportWizard.with_context(
            default_template_id=template.id,
        ).create({"template_id": template.id})

        line = wizard.line_ids.filtered(lambda line: line.variable_id == var)
        self.assertEqual(line.value_char, "Default Value")

    def test_05_wizard_lines_preserve_sequence(self):
        """Test that wizard lines respect variable sequence."""
        template = self._create_template_with_variables()

        wizard = self.ExportWizard.with_context(
            default_template_id=template.id,
        ).create({"template_id": template.id})

        # Lines should be in same order as sorted variables
        sorted_vars = template.variable_ids.sorted("sequence")
        for i, line in enumerate(wizard.line_ids.sorted("sequence")):
            self.assertEqual(line.variable_id, sorted_vars[i])

    def test_06_wizard_template_required(self):
        """Test that template_id is required for wizard."""
        with self.assertRaises(ValidationError):
            self.ExportWizard.create({})


@tagged("post_install", "-at_install", "wizard_preview")
class TestWizardPreview(DocumentTemplateTestCase):
    """Test wizard HTML preview functionality."""

    def test_01_preview_html_generated(self):
        """Test that preview HTML is computed."""
        template = self._create_template_with_variables()
        wizard = self._create_export_wizard(template)

        self.assertTrue(wizard.preview_html)
        self.assertIn("<h1>", wizard.preview_html)

    def test_02_preview_updates_on_value_change(self):
        """Test that preview updates when values change."""
        template = self._create_test_template(
            html_content="<h1>{{title}}</h1>",
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "title",
                "label": "Title",
            },
        )

        wizard = self._create_export_wizard(template)
        line = wizard.line_ids[0]

        # Set value
        line.write({"value_char": "My Title"})

        # Preview should contain the value
        self.assertIn("My Title", wizard.preview_html)

    def test_03_preview_with_empty_values(self):
        """Test preview with empty variable values."""
        template = self._create_template_with_variables()
        wizard = self._create_export_wizard(template)

        # All values are empty
        for line in wizard.line_ids:
            line.write({"value_char": ""})

        # Preview should still be generated (with empty placeholders)
        self.assertTrue(wizard.preview_html)

    def test_04_preview_with_no_template_content(self):
        """Test preview when template has no content."""
        template = self._create_test_template(html_content=False)
        wizard = self._create_export_wizard(template)

        self.assertIn("No content to preview", wizard.preview_html)


@tagged("post_install", "-at_install", "wizard_validation")
class TestWizardValidation(DocumentTemplateTestCase):
    """Test wizard validation before PDF generation."""

    def test_01_validate_required_fields_missing(self):
        """Test that validation fails when required fields are empty."""
        template = self._create_template_with_variables()
        wizard = self._create_export_wizard(template)

        # Leave required fields empty
        for line in wizard.line_ids:
            line.write({"value_char": ""})

        with self.assertRaises(ValidationError, msg="Required fields missing"):
            wizard.action_generate_pdf()

    def test_02_validate_required_fields_filled(self):
        """Test that validation passes when required fields are filled."""
        template = self._create_template_with_variables()
        wizard = self._create_export_wizard(template)

        # Fill all required fields
        values = self._get_variable_values()
        for line in wizard.line_ids:
            if line.is_required:
                line.write({"value_char": values.get(line.name, "Test Value")})

        # Should not raise
        try:
            wizard.action_generate_pdf()
        except (ValidationError, UserError, ValueError, OSError, RuntimeError) as e:
            # If PDF generation fails, that's ok - we're testing validation
            # ValidationError for missing fields should not be raised
            self.assertNotIsInstance(e, ValidationError)

    def test_03_validate_optional_fields_empty(self):
        """Test that validation passes with empty optional fields."""
        template = self._create_test_template(
            html_content="<h1>{{title}}</h1><p>{{optional}}</p>",
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "title",
                "label": "Title",
                "required": True,
            },
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "optional",
                "label": "Optional Field",
                "required": False,
            },
        )

        wizard = self._create_export_wizard(template)
        title_line = wizard.line_ids.filtered(lambda line: line.name == "title")
        title_line.write({"value_char": "Test Title"})

        # Optional field left empty - should not raise ValidationError
        try:
            wizard.action_generate_pdf()
        except ValidationError:
            self.fail("Should not raise ValidationError for empty optional fields")
        except (UserError, ValueError, OSError, RuntimeError):
            # Other exceptions (PDF generation) are ok
            pass


@tagged("post_install", "-at_install", "wizard_rendering")
class TestWizardRendering(DocumentTemplateTestCase):
    """Test HTML rendering with variable replacement."""

    def test_01_render_simple_variable(self):
        """Test rendering single variable."""
        template = self._create_test_template(
            html_content="<h1>{{title}}</h1>",
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "title",
                "label": "Title",
            },
        )

        wizard = self._create_export_wizard(template)
        wizard.line_ids[0].write({"value_char": "Test Title"})

        rendered = wizard._render_html()

        self.assertIn("Test Title", rendered)
        self.assertNotIn("{{title}}", rendered)

    def test_02_render_multiple_variables(self):
        """Test rendering multiple variables."""
        template = self._create_template_with_variables()
        wizard = self._create_export_wizard(template)

        values = self._get_variable_values()
        for line in wizard.line_ids:
            line.write({"value_char": values.get(line.name, "Default")})

        rendered = wizard._render_html()

        # Check that variables are replaced
        self.assertIn("John Doe", rendered)
        self.assertIn("Software Engineer", rendered)
        self.assertNotIn("{{employee_name}}", rendered)
        self.assertNotIn("{{job_title}}", rendered)

    def test_03_render_with_spaces_in_placeholder(self):
        """Test rendering variables with spaces in placeholders."""
        template = self._create_test_template(
            html_content="<p>{{  title  }}</p>",
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "title",
                "label": "Title",
            },
        )

        wizard = self._create_export_wizard(template)
        wizard.line_ids[0].write({"value_char": "Spaced Title"})

        rendered = wizard._render_html()

        self.assertIn("Spaced Title", rendered)

    def test_04_render_same_variable_multiple_times(self):
        """Test that same variable is replaced everywhere."""
        template = self._create_test_template(
            html_content="""
                <h1>{{name}}</h1>
                <p>Welcome, {{name}}!</p>
                <footer>{{name}}</footer>
            """,
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "name",
                "label": "Name",
            },
        )

        wizard = self._create_export_wizard(template)
        wizard.line_ids[0].write({"value_char": "John"})

        rendered = wizard._render_html()

        # All occurrences should be replaced
        self.assertEqual(rendered.count("John"), 3)
        self.assertNotIn("{{name}}", rendered)


@tagged("post_install", "-at_install", "wizard_pdf_generation")
class TestWizardPDFGeneration(DocumentTemplateTestCase):
    """Test PDF generation through wizard."""

    def test_01_generate_pdf_action_returned(self):
        """Test that PDF generation returns download action."""
        template = self._create_test_template()
        wizard = self._create_export_wizard(template)

        result = wizard.action_generate_pdf()

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("type"), "ir.actions.act_url")
        self.assertIn("download", result.get("url", ""))

    def test_02_pdf_saved_to_template(self):
        """Test that generated PDF is saved to template."""
        template = self._create_test_template()
        wizard = self._create_export_wizard(template)

        self.assertFalse(template.pdf_file)

        wizard.action_generate_pdf()

        self.assertTrue(template.pdf_file)
        self.assertTrue(template.has_pdf)

    def test_03_attachment_created(self):
        """Test that attachment is created for download."""
        template = self._create_test_template()
        wizard = self._create_export_wizard(template)

        initial_attachment_count = self.Attachment.search_count([])

        wizard.action_generate_pdf()

        final_attachment_count = self.Attachment.search_count([])
        self.assertGreater(final_attachment_count, initial_attachment_count)

    def test_04_pdf_filename_correct(self):
        """Test that PDF has correct filename."""
        template = self._create_test_template(name="Test Document")
        wizard = self._create_export_wizard(template)

        result = wizard.action_generate_pdf()

        self.assertIn("Test Document.pdf", result.get("url", ""))


@tagged("post_install", "-at_install", "wizard_edge_cases")
class TestWizardEdgeCases(DocumentTemplateTestCase):
    """Test edge cases and error conditions."""

    def test_01_wizard_with_no_variables(self):
        """Test wizard with template having no variables."""
        template = self._create_test_template()

        wizard = self._create_export_wizard(template)

        self.assertEqual(len(wizard.line_ids), 0)

    def test_02_wizard_line_value_special_characters(self):
        """Test wizard line values with special characters."""
        template = self._create_test_template(
            html_content="<p>{{text}}</p>",
        )
        self.Variable.create(
            {
                "template_id": template.id,
                "name": "text",
                "label": "Text",
            },
        )

        wizard = self._create_export_wizard(template)
        wizard.line_ids[0].write({"value_char": "Test & <special> chars"})

        rendered = wizard._render_html()
        self.assertIn("Test & <special> chars", rendered)

    def test_03_wizard_multiple_instances(self):
        """Test creating multiple wizard instances for same template."""
        template = self._create_template_with_variables()

        wizard1 = self._create_export_wizard(template)
        wizard2 = self._create_export_wizard(template)

        self.assertNotEqual(wizard1.id, wizard2.id)
        self.assertEqual(len(wizard1.line_ids), len(wizard2.line_ids))
