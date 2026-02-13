"""
Test Cases for Template Creation and Management

Tests template CRUD operations, field validation, and basic template management.
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "template_creation")
class TestTemplateCreation(DocumentTemplateTestCase):
    """Test basic template creation and management."""

    def test_01_create_simple_template(self):
        """Test creating a basic template with required fields."""
        template = self.Template.create(
            {
                "name": "Simple Template",
                "html_content": "<h1>Hello World</h1>",
            },
        )

        self.assertTrue(template, "Template should be created")
        self.assertEqual(template.name, "Simple Template")
        self.assertTrue(template.active, "Template should be active by default")
        self.assertFalse(
            template.favorite, "Template should not be favorite by default",
        )

    def test_02_create_template_with_category(self):
        """Test creating template with category assignment."""
        template = self.Template.create(
            {
                "name": "HR Template",
                "category_id": self.category_hr.id,
                "html_content": "<p>Content</p>",
            },
        )

        self.assertEqual(template.category_id, self.category_hr)
        self.assertEqual(template.category_id.name, "HR Documents")

    def test_03_create_template_with_tags(self):
        """Test creating template with multiple tags."""
        template = self.Template.create(
            {
                "name": "Tagged Template",
                "tag_ids": [(6, 0, [self.tag_confidential.id, self.tag_internal.id])],
                "html_content": "<p>Content</p>",
            },
        )

        self.assertEqual(len(template.tag_ids), 2)
        self.assertIn(self.tag_confidential, template.tag_ids)
        self.assertIn(self.tag_internal, template.tag_ids)

    def test_04_template_name_required(self):
        """Test that template name is required."""
        with self.assertRaises(ValidationError, msg="Name should be required"):
            self.Template.create(
                {
                    "html_content": "<p>Content</p>",
                },
            )

    def test_05_template_company_defaults_to_current(self):
        """Test that company_id defaults to current company."""
        template = self._create_test_template()

        self.assertEqual(template.company_id, self.env.company)

    def test_06_multiple_templates_creation(self):
        """Test creating multiple templates at once."""
        templates = self.Template.create(
            [
                {
                    "name": "Template 1",
                    "html_content": "<p>Content 1</p>",
                },
                {
                    "name": "Template 2",
                    "html_content": "<p>Content 2</p>",
                },
                {
                    "name": "Template 3",
                    "html_content": "<p>Content 3</p>",
                },
            ],
        )

        self.assertEqual(len(templates), 3)
        for template in templates:
            self.assertTrue(template.id)
            self.assertTrue(template.active)

    def test_07_template_with_summary(self):
        """Test template with summary field."""
        template = self.Template.create(
            {
                "name": "Documented Template",
                "summary": "This is a comprehensive offer letter template.",
                "html_content": "<p>Content</p>",
            },
        )

        self.assertEqual(
            template.summary, "This is a comprehensive offer letter template.",
        )

    def test_08_template_inactive_flag(self):
        """Test creating template as inactive."""
        template = self.Template.create(
            {
                "name": "Inactive Template",
                "html_content": "<p>Content</p>",
                "active": False,
            },
        )

        self.assertFalse(template.active)

    def test_09_template_with_empty_content(self):
        """Test that template can be created with empty content."""
        template = self.Template.create(
            {
                "name": "Empty Template",
                "html_content": False,
            },
        )

        self.assertFalse(template.html_content)

    def test_10_template_html_content_sanitization(self):
        """Test that HTML content is stored properly."""
        html = """
        <h1>Title</h1>
        <p>Paragraph with <strong>bold</strong> and <em>italic</em>.</p>
        <script>alert('test');</script>
        """
        template = self.Template.create(
            {
                "name": "HTML Template",
                "html_content": html,
            },
        )

        self.assertIn("<h1>Title</h1>", template.html_content)
        self.assertIn("<strong>bold</strong>", template.html_content)


@tagged("post_install", "-at_install", "template_crud")
class TestTemplateUpdate(DocumentTemplateTestCase):
    """Test template update operations."""

    def test_01_update_template_name(self):
        """Test updating template name."""
        template = self._create_test_template()
        original_name = template.name

        template.write({"name": "Updated Template Name"})

        self.assertEqual(template.name, "Updated Template Name")
        self.assertNotEqual(template.name, original_name)

    def test_02_update_template_content(self):
        """Test updating template HTML content."""
        template = self._create_test_template()

        new_content = "<h2>Updated Content</h2><p>New paragraph.</p>"
        template.write({"html_content": new_content})

        self.assertEqual(template.html_content, new_content)

    def test_03_update_template_category(self):
        """Test changing template category."""
        template = self._create_test_template(
            category_id=self.category_hr.id,
        )

        template.write({"category_id": self.category_legal.id})

        self.assertEqual(template.category_id, self.category_legal)

    def test_04_add_tags_to_template(self):
        """Test adding tags to existing template."""
        template = self._create_test_template()

        template.write(
            {
                "tag_ids": [(6, 0, [self.tag_confidential.id])],
            },
        )

        self.assertEqual(len(template.tag_ids), 1)
        self.assertIn(self.tag_confidential, template.tag_ids)

    def test_05_remove_tags_from_template(self):
        """Test removing tags from template."""
        template = self.Template.create(
            {
                "name": "Tagged Template",
                "tag_ids": [(6, 0, [self.tag_confidential.id, self.tag_internal.id])],
                "html_content": "<p>Content</p>",
            },
        )

        template.write({"tag_ids": [(6, 0, [self.tag_confidential.id])]})

        self.assertEqual(len(template.tag_ids), 1)
        self.assertIn(self.tag_confidential, template.tag_ids)
        self.assertNotIn(self.tag_internal, template.tag_ids)

    def test_06_deactivate_template(self):
        """Test deactivating a template."""
        template = self._create_test_template()

        template.write({"active": False})

        self.assertFalse(template.active)

    def test_07_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        template = self._create_test_template()

        template.write(
            {
                "name": "Multi-Update Template",
                "summary": "Updated summary",
                "category_id": self.category_finance.id,
                "favorite": True,
            },
        )

        self.assertEqual(template.name, "Multi-Update Template")
        self.assertEqual(template.summary, "Updated summary")
        self.assertEqual(template.category_id, self.category_finance)
        self.assertTrue(template.favorite)


@tagged("post_install", "-at_install", "template_delete")
class TestTemplateDelete(DocumentTemplateTestCase):
    """Test template deletion operations."""

    def test_01_delete_simple_template(self):
        """Test deleting a template without variables."""
        template = self._create_test_template()
        template_id = template.id

        template.unlink()

        self.assertFalse(self.Template.browse(template_id).exists())

    def test_02_delete_template_with_variables(self):
        """Test deleting template cascades to variables."""
        template = self._create_template_with_variables()
        variable_ids = template.variable_ids.ids

        template.unlink()

        self.assertFalse(self.Template.browse(template.id).exists())
        for var_id in variable_ids:
            self.assertFalse(self.Variable.browse(var_id).exists())

    def test_03_delete_multiple_templates(self):
        """Test deleting multiple templates at once."""
        templates = self.Template.create(
            [
                {"name": "Template 1", "html_content": "<p>1</p>"},
                {"name": "Template 2", "html_content": "<p>2</p>"},
                {"name": "Template 3", "html_content": "<p>3</p>"},
            ],
        )
        template_ids = templates.ids

        templates.unlink()

        for tid in template_ids:
            self.assertFalse(self.Template.browse(tid).exists())


@tagged("post_install", "-at_install", "template_copy")
class TestTemplateCopy(DocumentTemplateTestCase):
    """Test template duplication functionality."""

    def test_01_copy_simple_template(self):
        """Test copying a simple template."""
        original = self._create_test_template(name="Original Template")

        copy = original.copy()

        self.assertNotEqual(copy.id, original.id)
        self.assertEqual(copy.name, "Original Template (Copy)")
        self.assertEqual(copy.html_content, original.html_content)

    def test_02_copy_template_with_variables(self):
        """Test that copying template also copies variables."""
        original = self._create_template_with_variables()
        original_var_count = len(original.variable_ids)

        copy = original.copy()

        self.assertEqual(len(copy.variable_ids), original_var_count)
        self.assertNotEqual(copy.id, original.id)
        for orig_var, copy_var in zip(original.variable_ids, copy.variable_ids):
            self.assertNotEqual(orig_var.id, copy_var.id)
            self.assertEqual(orig_var.name, copy_var.name)
            self.assertEqual(orig_var.label, copy_var.label)

    def test_03_copy_template_clears_pdf(self):
        """Test that copied template does not include PDF file."""
        original = self._create_test_template()
        original.write({"pdf_file": self._create_test_pdf_bytes()})

        copy = original.copy()

        self.assertTrue(original.pdf_file)
        self.assertFalse(copy.pdf_file)

    def test_04_copy_template_with_custom_name(self):
        """Test copying template with custom default values."""
        original = self._create_test_template(name="Original")

        copy = original.copy(default={"name": "Custom Copy Name"})

        self.assertEqual(copy.name, "Custom Copy Name")
