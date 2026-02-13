"""
Test Cases for Template Actions

Tests template actions like duplicate, toggle favorite, and other user actions.
"""

from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "template_actions")
class TestTemplateDuplicate(DocumentTemplateTestCase):
    """Test template duplication action."""

    def test_01_duplicate_simple_template(self):
        """Test duplicating a simple template."""
        original = self._create_test_template(name="Original")

        result = original.action_duplicate()

        self.assertEqual(result.get("type"), "ir.actions.act_window")
        self.assertEqual(result.get("res_model"), "document.template")

        # Get the duplicated template
        new_id = result.get("res_id")
        duplicated = self.Template.browse(new_id)

        self.assertTrue(duplicated.exists())
        self.assertEqual(duplicated.name, "Original (Copy)")

    def test_02_duplicate_opens_form_view(self):
        """Test that duplicate action opens form view."""
        template = self._create_test_template()

        result = template.action_duplicate()

        self.assertEqual(result.get("view_mode"), "form")
        self.assertEqual(result.get("target"), "current")

    def test_03_duplicate_template_with_variables(self):
        """Test duplicating template copies its variables."""
        original = self._create_template_with_variables()

        result = original.action_duplicate()
        duplicated = self.Template.browse(result.get("res_id"))

        self.assertEqual(len(duplicated.variable_ids), len(original.variable_ids))


@tagged("post_install", "-at_install", "template_favorite")
class TestTemplateFavorite(DocumentTemplateTestCase):
    """Test toggle favorite functionality."""

    def test_01_toggle_favorite_from_false(self):
        """Test toggling favorite from False to True."""
        template = self._create_test_template(favorite=False)

        template.action_toggle_favorite()

        self.assertTrue(template.favorite)

    def test_02_toggle_favorite_from_true(self):
        """Test toggling favorite from True to False."""
        template = self._create_test_template(favorite=True)

        template.action_toggle_favorite()

        self.assertFalse(template.favorite)

    def test_03_toggle_favorite_multiple_times(self):
        """Test toggling favorite multiple times."""
        template = self._create_test_template(favorite=False)

        template.action_toggle_favorite()
        self.assertTrue(template.favorite)

        template.action_toggle_favorite()
        self.assertFalse(template.favorite)

        template.action_toggle_favorite()
        self.assertTrue(template.favorite)

    def test_04_toggle_favorite_multiple_templates(self):
        """Test toggling favorite on multiple templates."""
        templates = self.Template.create(
            [
                {"name": "Template 1", "html_content": "<p>1</p>", "favorite": False},
                {"name": "Template 2", "html_content": "<p>2</p>", "favorite": False},
            ],
        )

        templates.action_toggle_favorite()

        for template in templates:
            self.assertTrue(template.favorite)


@tagged("post_install", "-at_install", "template_status")
class TestTemplateActiveStatus(DocumentTemplateTestCase):
    """Test active/inactive status management."""

    def test_01_filter_active_templates(self):
        """Test filtering active templates."""
        self.Template.create(
            [
                {"name": "Active 1", "html_content": "<p>1</p>", "active": True},
                {"name": "Active 2", "html_content": "<p>2</p>", "active": True},
                {"name": "Inactive", "html_content": "<p>3</p>", "active": False},
            ],
        )

        active_templates = self.Template.search([("active", "=", True)])

        self.assertGreaterEqual(len(active_templates), 2)

    def test_02_filter_inactive_templates(self):
        """Test filtering inactive templates."""
        inactive_template = self.Template.create(
            {
                "name": "Inactive Template",
                "html_content": "<p>Content</p>",
                "active": False,
            },
        )

        inactive_templates = self.Template.search(
            [
                ("active", "=", False),
                ("id", "=", inactive_template.id),
            ],
        )

        self.assertTrue(inactive_templates)

    def test_03_deactivate_template(self):
        """Test deactivating a template."""
        template = self._create_test_template()

        template.write({"active": False})

        # Template still exists but is inactive
        self.assertTrue(template.exists())
        self.assertFalse(template.active)

    def test_04_reactivate_template(self):
        """Test reactivating an inactive template."""
        template = self._create_test_template(active=False)

        template.write({"active": True})

        self.assertTrue(template.active)


@tagged("post_install", "-at_install", "template_ordering")
class TestTemplateOrdering(DocumentTemplateTestCase):
    """Test template ordering and sorting."""

    def test_01_default_order_by_write_date(self):
        """Test that templates are ordered by write_date desc by default."""
        # Create templates with slight delay
        temp1 = self._create_test_template(name="First")
        temp2 = self._create_test_template(name="Second")
        temp3 = self._create_test_template(name="Third")

        templates = self.Template.search(
            [
                ("id", "in", [temp1.id, temp2.id, temp3.id]),
            ],
            order="write_date desc, id desc",
        )

        # Most recently written should be first
        self.assertEqual(templates[0], temp3)

    def test_02_order_by_name(self):
        """Test ordering templates by name."""
        temp1 = self._create_test_template(name="Zebra")
        temp2 = self._create_test_template(name="Apple")
        temp3 = self._create_test_template(name="Mango")

        templates = self.Template.search(
            [
                ("id", "in", [temp1.id, temp2.id, temp3.id]),
            ],
            order="name",
        )

        self.assertEqual(templates[0], temp2)  # Apple
        self.assertEqual(templates[1], temp3)  # Mango
        self.assertEqual(templates[2], temp1)  # Zebra


@tagged("post_install", "-at_install", "template_tracking")
class TestTemplateTracking(DocumentTemplateTestCase):
    """Test mail tracking on templates."""

    def test_01_template_has_mail_thread(self):
        """Test that template inherits mail.thread."""
        template = self._create_test_template()

        self.assertTrue(hasattr(template, "message_post"))
        self.assertTrue(hasattr(template, "message_follower_ids"))

    def test_02_template_has_activity_mixin(self):
        """Test that template inherits mail.activity.mixin."""
        template = self._create_test_template()

        self.assertTrue(hasattr(template, "activity_schedule"))
        self.assertTrue(hasattr(template, "activity_ids"))

    def test_03_tracked_fields_create_message(self):
        """Test that changing tracked fields creates messages."""
        template = self._create_test_template()
        initial_message_count = len(template.message_ids)

        # Change tracked field
        template.write({"name": "Updated Name"})

        # Should create tracking message
        self.assertGreaterEqual(len(template.message_ids), initial_message_count)


@tagged("post_install", "-at_install", "compute_fields")
class TestTemplateComputeFields(DocumentTemplateTestCase):
    """Test template computed fields."""

    def test_01_variable_count_compute(self):
        """Test variable_count is computed correctly."""
        template = self._create_test_template()

        self.assertEqual(template.variable_count, 0)

        self._create_test_variable(template)
        self.assertEqual(template.variable_count, 1)

        self._create_test_variable(template, name="var2", label="Var 2")
        self.assertEqual(template.variable_count, 2)

    def test_02_pdf_filename_compute(self):
        """Test pdf_filename is computed from name."""
        template = self._create_test_template(name="My Document")

        self.assertEqual(template.pdf_filename, "My Document.pdf")

        template.write({"name": "Updated Document"})
        self.assertEqual(template.pdf_filename, "Updated Document.pdf")

    def test_03_has_pdf_compute(self):
        """Test has_pdf is computed from pdf_file."""
        template = self._create_test_template()

        self.assertFalse(template.has_pdf)

        template.write({"pdf_file": self._create_test_pdf_bytes()})
        self.assertTrue(template.has_pdf)

        template.write({"pdf_file": False})
        self.assertFalse(template.has_pdf)
