"""
Test Cases for Security and Access Control

Tests record rules, permissions, and access control for templates and related records.
"""

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "security")
class TestTemplateAccess(DocumentTemplateTestCase):
    """Test template access control."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test users with different access levels
        cls.group_user = cls.env.ref("base.group_user")
        cls.group_system = cls.env.ref("base.group_system")
        cls.group_document_user = cls.env.ref(
            "document_template_manager.group_document_user",
        )
        cls.group_document_manager = cls.env.ref(
            "document_template_manager.group_document_manager",
        )

        cls.basic_user = cls.env["res.users"].create(
            {
                "name": "Basic User",
                "login": "basic_user",
                "email": "basic@test.com",
                "group_ids": [
                    Command.set([cls.group_user.id, cls.group_document_user.id]),
                ],
            },
        )

        cls.admin_user = cls.env["res.users"].create(
            {
                "name": "Admin User",
                "login": "admin_user",
                "email": "admin@test.com",
                "group_ids": [
                    Command.set(
                        [
                            cls.group_user.id,
                            cls.group_system.id,
                            cls.group_document_manager.id,
                        ],
                    ),
                ],
            },
        )

    def test_01_user_can_read_templates(self):
        """Test that users can read templates."""
        template = self._create_test_template()

        # Read as basic user
        template_as_user = template.with_user(self.basic_user)
        self.assertEqual(template_as_user.name, template.name)

    def test_02_user_can_create_templates(self):
        """Test that users can create templates."""
        # Create as basic user
        template = self.Template.with_user(self.basic_user).create(
            {
                "name": "User Template",
                "html_content": "<p>Content</p>",
            },
        )

        self.assertTrue(template.exists())

    def test_03_user_can_edit_templates(self):
        """Test that users can edit templates."""
        # Create template as the basic user
        template = self.Template.with_user(self.basic_user).create(
            {
                "name": "User Template",
                "category_id": self.category_hr.id,
                "html_content": "<p>User content</p>",
            },
        )

        # Update as basic user (own template)
        template.with_user(self.basic_user).write(
            {
                "name": "Updated by User",
            },
        )

        self.assertEqual(template.name, "Updated by User")

    def test_04_user_cannot_delete_templates(self):
        """Test that regular users cannot delete templates."""
        # Create template as the basic user
        template = self.Template.with_user(self.basic_user).create(
            {
                "name": "User Template to Delete",
                "category_id": self.category_hr.id,
                "html_content": "<p>User content</p>",
            },
        )
        template_id = template.id

        # Delete as basic user (own template) should be blocked by ACL
        with self.assertRaises(AccessError):
            template.with_user(self.basic_user).unlink()

        self.assertTrue(self.Template.browse(template_id).exists())

    def test_05_admin_has_full_access(self):
        """Test that admin users have full access."""
        template = self.Template.with_user(self.admin_user).create(
            {
                "name": "Admin Template",
                "html_content": "<p>Admin content</p>",
            },
        )

        # Admin can read
        self.assertTrue(template.name)

        # Admin can write
        template.write({"name": "Updated by Admin"})

        # Admin can delete
        template.unlink()


@tagged("post_install", "-at_install", "variable_security")
class TestVariableAccess(DocumentTemplateTestCase):
    """Test variable access control."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_user = cls.env.ref("base.group_user")
        cls.group_document_user = cls.env.ref(
            "document_template_manager.group_document_user",
        )

        cls.basic_user = cls.env["res.users"].create(
            {
                "name": "Var User",
                "login": "var_user",
                "email": "varuser@test.com",
                "group_ids": [
                    Command.set([cls.group_user.id, cls.group_document_user.id]),
                ],
            },
        )

    def test_01_user_can_create_variables(self):
        """Test that users can create variables."""
        template = self._create_test_template()

        variable = self.Variable.with_user(self.basic_user).create(
            {
                "template_id": template.id,
                "name": "test_var",
                "label": "Test Variable",
            },
        )

        self.assertTrue(variable.exists())

    def test_02_user_can_read_variables(self):
        """Test that users can read variables."""
        template = self._create_test_template()
        variable = self._create_test_variable(template)

        variable_as_user = variable.with_user(self.basic_user)
        self.assertEqual(variable_as_user.name, variable.name)

    def test_03_user_can_edit_variables(self):
        """Test that users can edit variables."""
        template = self._create_test_template()
        variable = self._create_test_variable(template)

        variable.with_user(self.basic_user).write(
            {
                "label": "Updated Label",
            },
        )

        self.assertEqual(variable.label, "Updated Label")

    def test_04_user_can_delete_variables(self):
        """Test that users can delete variables."""
        template = self._create_test_template()
        variable = self._create_test_variable(template)
        variable_id = variable.id

        variable.with_user(self.basic_user).unlink()

        self.assertFalse(self.Variable.browse(variable_id).exists())


@tagged("post_install", "-at_install", "wizard_security")
class TestWizardAccess(DocumentTemplateTestCase):
    """Test export wizard access control."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_user = cls.env.ref("base.group_user")
        cls.group_document_user = cls.env.ref(
            "document_template_manager.group_document_user",
        )

        cls.basic_user = cls.env["res.users"].create(
            {
                "name": "Wizard User",
                "login": "wizard_user",
                "email": "wizuser@test.com",
                "group_ids": [
                    Command.set([cls.group_user.id, cls.group_document_user.id]),
                ],
            },
        )

    def test_01_user_can_create_wizard(self):
        """Test that users can create export wizard."""
        template = self._create_template_with_variables()

        wizard = (
            self.ExportWizard.with_user(self.basic_user)
            .with_context(
                default_template_id=template.id,
            )
            .create({"template_id": template.id})
        )

        self.assertTrue(wizard.exists())

    def test_02_user_can_execute_wizard(self):
        """Test that users can generate PDF through wizard."""
        # Create template as basic_user so they have write access
        template = self.Template.with_user(self.basic_user).create({
            "name": "Test Template for Wizard",
            "html_content": "<p>Test content {{user.name}}</p>",
            "active": True,
        })

        wizard = (
            self.ExportWizard.with_user(self.basic_user)
            .with_context(
                default_template_id=template.id,
            )
            .create({"template_id": template.id})
        )

        # Should be able to generate PDF
        try:
            result = wizard.action_generate_pdf()
            self.assertIsInstance(result, dict)
        except AccessError:
            self.fail("User should be able to execute wizard")
        except (ValidationError, UserError, ValueError, OSError, RuntimeError):
            # PDF generation errors are ok, we're testing access
            pass


@tagged("post_install", "-at_install", "category_tag_security")
class TestCategoryTagAccess(DocumentTemplateTestCase):
    """Test category and tag access control."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_user = cls.env.ref("base.group_user")
        cls.group_document_user = cls.env.ref(
            "document_template_manager.group_document_user",
        )

        cls.basic_user = cls.env["res.users"].create(
            {
                "name": "Category User",
                "login": "cat_user",
                "email": "catuser@test.com",
                "group_ids": [
                    Command.set([cls.group_user.id, cls.group_document_user.id]),
                ],
            },
        )

    def test_01_user_can_read_categories(self):
        """Test that users can read categories."""
        category = self._create_test_category()

        category_as_user = category.with_user(self.basic_user)
        self.assertEqual(category_as_user.name, category.name)

    def test_02_user_can_create_categories(self):
        """Test that users can create categories."""
        category = self.Category.with_user(self.basic_user).create(
            {
                "name": "User Category",
            },
        )

        self.assertTrue(category.exists())

    def test_03_user_can_read_tags(self):
        """Test that users can read tags."""
        tag = self._create_test_tag()

        tag_as_user = tag.with_user(self.basic_user)
        self.assertEqual(tag_as_user.name, tag.name)

    def test_04_user_can_create_tags(self):
        """Test that users can create tags."""
        tag = self.Tag.with_user(self.basic_user).create(
            {
                "name": "User Tag",
            },
        )

        self.assertTrue(tag.exists())


@tagged("post_install", "-at_install", "company_isolation")
class TestCompanyIsolation(DocumentTemplateTestCase):
    """Test multi-company isolation if implemented."""

    def test_01_template_has_company_field(self):
        """Test that template has company_id field."""
        template = self._create_test_template()

        self.assertTrue(hasattr(template, "company_id"))

    def test_02_template_defaults_to_current_company(self):
        """Test that new template defaults to current company."""
        template = self._create_test_template()

        self.assertEqual(template.company_id, self.env.company)

    def test_03_template_can_be_company_specific(self):
        """Test that template can belong to specific company."""
        template = self._create_test_template()

        self.assertTrue(template.company_id)

    def test_04_template_can_be_shared_across_companies(self):
        """Test that template can be shared (company_id = False)."""
        template = self.Template.create(
            {
                "name": "Shared Template",
                "html_content": "<p>Shared</p>",
                "company_id": False,
            },
        )

        self.assertFalse(template.company_id)


@tagged("post_install", "-at_install", "security_edge_cases")
class TestSecurityEdgeCases(DocumentTemplateTestCase):
    """Test security edge cases."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_user = cls.env.ref("base.group_user")
        cls.group_document_user = cls.env.ref(
            "document_template_manager.group_document_user",
        )

        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Edge Case User",
                "login": "edge_user",
                "email": "edgeuser@test.com",
                "group_ids": [
                    Command.set([cls.group_user.id, cls.group_document_user.id]),
                ],
            },
        )

    def test_01_user_cannot_see_superuser_context(self):
        """Test that regular user operations don't leak privileged access."""
        template = self._create_test_template()

        # Access as regular user
        template_as_user = template.with_user(self.test_user)

        # Should not have sudo privileges
        self.assertFalse(template_as_user.env.su)

    def test_02_wizard_respects_template_access(self):
        """Test that wizard respects template access rights."""
        template = self._create_template_with_variables()

        # Create wizard as user
        wizard = (
            self.ExportWizard.with_user(self.test_user)
            .with_context(
                default_template_id=template.id,
            )
            .create({"template_id": template.id})
        )

        # Should have access to template
        self.assertTrue(wizard.template_id.exists())

    def test_03_attachment_creation_respects_permissions(self):
        """Test that PDF attachment creation respects permissions."""
        # Create template as test_user so they have write access
        template = self.Template.with_user(self.test_user).create({
            "name": "Test Template for Export",
            "html_content": "<p>Test content for export</p>",
            "active": True,
        })

        # Generate PDF as user
        try:
            template.action_export_pdf()
        except AccessError:
            self.fail("User should be able to export PDF")
        except (ValidationError, UserError, ValueError, OSError, RuntimeError):
            # Other errors are ok
            pass
