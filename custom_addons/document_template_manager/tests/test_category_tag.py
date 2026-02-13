"""
Test Cases for Categories and Tags

Tests document categories and tags functionality including hierarchy,
validation, and relationships.
"""

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "categories")
class TestCategory(DocumentTemplateTestCase):
    """Test document categories."""

    def test_01_create_simple_category(self):
        """Test creating a basic category."""
        category = self.Category.create(
            {
                "name": "Test Category",
                "sequence": 10,
            },
        )

        self.assertEqual(category.name, "Test Category")
        self.assertEqual(category.sequence, 10)

    def test_02_category_name_required(self):
        """Test that category name is required."""
        with self.assertRaises(ValidationError):
            self.Category.create(
                {
                    "sequence": 10,
                },
            )

    def test_03_category_with_parent(self):
        """Test creating category with parent (hierarchy)."""
        parent = self._create_test_category(name="Parent Category")
        child = self.Category.create(
            {
                "name": "Child Category",
                "parent_id": parent.id,
            },
        )

        self.assertEqual(child.parent_id, parent)
        self.assertIn(child, parent.child_ids)

    def test_04_category_hierarchy_depth(self):
        """Test multi-level category hierarchy."""
        level1 = self._create_test_category(name="Level 1")
        level2 = self.Category.create(
            {
                "name": "Level 2",
                "parent_id": level1.id,
            },
        )
        level3 = self.Category.create(
            {
                "name": "Level 3",
                "parent_id": level2.id,
            },
        )

        self.assertEqual(level3.parent_id, level2)
        self.assertEqual(level2.parent_id, level1)

    def test_05_category_document_count(self):
        """Test that document_count is computed correctly."""
        category = self._create_test_category()

        self.assertEqual(category.document_count, 0)

        # Create template with this category
        self._create_test_template(category_id=category.id)
        category.invalidate_recordset()  # Refresh computed field
        self.assertEqual(category.document_count, 1)

        self._create_test_template(category_id=category.id)
        category.invalidate_recordset()  # Refresh computed field
        self.assertEqual(category.document_count, 2)

    def test_06_category_color(self):
        """Test setting color on category."""
        category = self._create_test_category(color=5)

        self.assertEqual(category.color, 5)

    def test_07_category_sequence_ordering(self):
        """Test that categories are ordered by sequence."""
        cat1 = self._create_test_category(name="Cat 1", sequence=30)
        cat2 = self._create_test_category(name="Cat 2", sequence=10)
        cat3 = self._create_test_category(name="Cat 3", sequence=20)

        categories = self.Category.search(
            [
                ("id", "in", [cat1.id, cat2.id, cat3.id]),
            ],
            order="sequence, name",
        )

        self.assertEqual(categories[0], cat2)
        self.assertEqual(categories[1], cat3)
        self.assertEqual(categories[2], cat1)

    def test_08_delete_parent_category_orphans_children(self):
        """Test that deleting parent category handles children."""
        parent = self._create_test_category(name="Parent")
        child = self.Category.create(
            {
                "name": "Child",
                "parent_id": parent.id,
            },
        )
        child_id = child.id

        # Delete parent (cascade)
        parent.unlink()

        # Child should be deleted (cascade)
        self.assertFalse(self.Category.browse(child_id).exists())

    def test_09_category_translatable_name(self):
        """Test that category name is translatable."""
        # Check that name field is translatable
        field = self.Category._fields["name"]
        self.assertTrue(field.translate)


@tagged("post_install", "-at_install", "tags")
class TestTag(DocumentTemplateTestCase):
    """Test document tags."""

    def test_01_create_simple_tag(self):
        """Test creating a basic tag."""
        tag = self.Tag.create(
            {
                "name": "Test Tag",
                "color": 3,
            },
        )

        self.assertEqual(tag.name, "Test Tag")
        self.assertEqual(tag.color, 3)

    def test_02_tag_name_required(self):
        """Test that tag name is required."""
        with self.assertRaises(ValidationError):
            self.Tag.create(
                {
                    "color": 1,
                },
            )

    def test_03_tag_unique_name(self):
        """Test that tag names must be unique."""
        self.Tag.create(
            {
                "name": "Unique Tag",
            },
        )

        with self.assertRaises(
            ValidationError,
            msg="Duplicate tag name should raise error",
        ):
            self.Tag.create(
                {
                    "name": "Unique Tag",
                },
            )

    def test_04_tag_name_case_sensitive_uniqueness(self):
        """Test that tag name uniqueness is exact."""
        tag1 = self.Tag.create({"name": "TestTag"})
        tag2 = self.Tag.create({"name": "testtag"})

        # Both should exist (case-sensitive)
        self.assertNotEqual(tag1.id, tag2.id)

    def test_05_tag_color_defaults_to_zero(self):
        """Test that tag color defaults to 0."""
        tag = self.Tag.create(
            {
                "name": "No Color Tag",
            },
        )

        self.assertEqual(tag.color, 0)

    def test_06_tag_ordered_by_name(self):
        """Test that tags are ordered by name."""
        tag1 = self._create_test_tag(name="Zebra")
        tag2 = self._create_test_tag(name="Apple")
        tag3 = self._create_test_tag(name="Mango")

        tags = self.Tag.search(
            [
                ("id", "in", [tag1.id, tag2.id, tag3.id]),
            ],
            order="name",
        )

        self.assertEqual(tags[0], tag2)  # Apple
        self.assertEqual(tags[1], tag3)  # Mango
        self.assertEqual(tags[2], tag1)  # Zebra

    def test_07_tag_translatable_name(self):
        """Test that tag name is translatable."""
        # Check that name field is translatable
        field = self.Tag._fields["name"]
        self.assertTrue(field.translate)

    def test_08_delete_tag(self):
        """Test deleting a tag."""
        tag = self._create_test_tag()
        tag_id = tag.id

        tag.unlink()

        self.assertFalse(self.Tag.browse(tag_id).exists())


@tagged("post_install", "-at_install", "category_tag_relations")
class TestCategoryTagRelations(DocumentTemplateTestCase):
    """Test relationships between templates, categories, and tags."""

    def test_01_template_with_category(self):
        """Test assigning category to template."""
        template = self._create_test_template(
            category_id=self.category_hr.id,
        )

        self.assertEqual(template.category_id, self.category_hr)

    def test_02_template_with_multiple_tags(self):
        """Test assigning multiple tags to template."""
        template = self.Template.create(
            {
                "name": "Tagged Template",
                "html_content": "<p>Content</p>",
                "tag_ids": [
                    (
                        6,
                        0,
                        [
                            self.tag_confidential.id,
                            self.tag_internal.id,
                            self.tag_external.id,
                        ],
                    ),
                ],
            },
        )

        self.assertEqual(len(template.tag_ids), 3)

    def test_03_filter_templates_by_category(self):
        """Test filtering templates by category."""
        self._create_test_template(
            name="HR Doc",
            category_id=self.category_hr.id,
        )
        self._create_test_template(
            name="Legal Doc",
            category_id=self.category_legal.id,
        )

        hr_templates = self.Template.search(
            [
                ("category_id", "=", self.category_hr.id),
            ],
        )

        self.assertGreaterEqual(len(hr_templates), 1)

    def test_04_filter_templates_by_tag(self):
        """Test filtering templates by tag."""
        template = self.Template.create(
            {
                "name": "Confidential Template",
                "html_content": "<p>Content</p>",
                "tag_ids": [(6, 0, [self.tag_confidential.id])],
            },
        )

        tagged_templates = self.Template.search(
            [
                ("tag_ids", "in", [self.tag_confidential.id]),
            ],
        )

        self.assertIn(template, tagged_templates)

    def test_05_change_template_category(self):
        """Test changing template category."""
        template = self._create_test_template(
            category_id=self.category_hr.id,
        )

        template.write({"category_id": self.category_legal.id})

        self.assertEqual(template.category_id, self.category_legal)

    def test_06_add_tag_to_template(self):
        """Test adding tag to existing template."""
        template = self._create_test_template()

        template.write(
            {
                "tag_ids": [(4, self.tag_internal.id)],
            },
        )

        self.assertIn(self.tag_internal, template.tag_ids)

    def test_07_remove_tag_from_template(self):
        """Test removing tag from template."""
        template = self.Template.create(
            {
                "name": "Template",
                "html_content": "<p>Content</p>",
                "tag_ids": [(6, 0, [self.tag_confidential.id, self.tag_internal.id])],
            },
        )

        template.write(
            {
                "tag_ids": [(3, self.tag_confidential.id)],
            },
        )

        self.assertNotIn(self.tag_confidential, template.tag_ids)
        self.assertIn(self.tag_internal, template.tag_ids)

    def test_08_clear_template_category(self):
        """Test clearing category from template."""
        template = self._create_test_template(
            category_id=self.category_hr.id,
        )

        template.write({"category_id": False})

        self.assertFalse(template.category_id)

    def test_09_document_count_with_subcategories(self):
        """Test document count only counts direct children."""
        parent = self._create_test_category(name="Parent")
        child = self.Category.create(
            {
                "name": "Child",
                "parent_id": parent.id,
            },
        )

        self._create_test_template(category_id=child.id)

        # Parent's document_count should be 0 (doesn't count descendants)
        self.assertEqual(parent.document_count, 0)
        self.assertEqual(child.document_count, 1)
