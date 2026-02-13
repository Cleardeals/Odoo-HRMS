"""
Common Test Utilities and Fixtures for Document Template Manager

Provides shared utilities, test data, and helper methods for the test suite.
"""

import base64
import re

from odoo.tests import common


class DocumentTemplateTestCase(common.TransactionCase):
    """
    Base test case class for document_template_manager module.
    Provides common setup, utility methods, and test data for all test cases.
    """

    @classmethod
    def setUpClass(cls):
        """Set up common test data and objects."""
        super().setUpClass()

        # Models
        cls.Template = cls.env["document.template"]
        cls.Variable = cls.env["document.template.variable"]
        cls.Category = cls.env["document.category"]
        cls.Tag = cls.env["document.tag"]
        cls.ExportWizard = cls.env["document.export.wizard"]
        cls.ExportWizardLine = cls.env["document.export.wizard.line"]
        cls.Attachment = cls.env["ir.attachment"]
        cls.Company = cls.env["res.company"]

        # Test Company
        cls.company = cls.env.company

        # Test Categories
        cls.category_hr = cls.Category.create(
            {
                "name": "HR Documents",
                "sequence": 10,
                "color": 1,
            },
        )

        cls.category_legal = cls.Category.create(
            {
                "name": "Legal Documents",
                "sequence": 20,
                "color": 2,
            },
        )

        cls.category_finance = cls.Category.create(
            {
                "name": "Finance Documents",
                "sequence": 30,
                "color": 3,
            },
        )

        # Test Tags
        cls.tag_confidential = cls.Tag.create(
            {
                "name": "Confidential",
                "color": 1,
            },
        )

        cls.tag_internal = cls.Tag.create(
            {
                "name": "Internal",
                "color": 2,
            },
        )

        cls.tag_external = cls.Tag.create(
            {
                "name": "External",
                "color": 3,
            },
        )

    def _create_test_template(self, **kwargs):
        """
        Create a basic template for testing.

        Args:
            **kwargs: Additional field values to override defaults

        Returns:
            document.template: Created template record
        """
        values = {
            "name": "Test Template",
            "category_id": self.category_hr.id,
            "html_content": "<h1>Test Document</h1><p>This is a test.</p>",
            "active": True,
        }
        values.update(kwargs)
        return self.Template.create(values)

    def _create_template_with_variables(self, **kwargs):
        """
        Create a template with pre-defined variables.

        Args:
            **kwargs: Additional field values to override defaults

        Returns:
            document.template: Created template with variables
        """
        values = {
            "name": "Template with Variables",
            "category_id": self.category_hr.id,
            "html_content": """
                <h1>{{employee_name}}</h1>
                <p>Position: {{job_title}}</p>
                <p>Salary: {{salary}}</p>
                <p>Start Date: {{start_date}}</p>
            """,
            "active": True,
        }
        values.update(kwargs)
        template = self.Template.create(values)

        # Create variables
        self.Variable.create(
            [
                {
                    "template_id": template.id,
                    "name": "employee_name",
                    "label": "Employee Name",
                    "variable_type": "char",
                    "required": True,
                    "sequence": 10,
                },
                {
                    "template_id": template.id,
                    "name": "job_title",
                    "label": "Job Title",
                    "variable_type": "char",
                    "required": True,
                    "sequence": 20,
                },
                {
                    "template_id": template.id,
                    "name": "salary",
                    "label": "Salary",
                    "variable_type": "float",
                    "required": False,
                    "default_value": "50000.00",
                    "sequence": 30,
                },
                {
                    "template_id": template.id,
                    "name": "start_date",
                    "label": "Start Date",
                    "variable_type": "date",
                    "required": True,
                    "sequence": 40,
                },
            ],
        )

        return template

    def _create_test_variable(self, template, **kwargs):
        """
        Create a test variable for a template.

        Args:
            template: Template record to attach variable to
            **kwargs: Field values

        Returns:
            document.template.variable: Created variable record
        """
        values = {
            "template_id": template.id,
            "name": "test_variable",
            "label": "Test Variable",
            "variable_type": "char",
            "required": True,
            "sequence": 10,
        }
        values.update(kwargs)
        return self.Variable.create(values)

    def _create_test_category(self, **kwargs):
        """
        Create a test category.

        Args:
            **kwargs: Field values

        Returns:
            document.category: Created category record
        """
        values = {
            "name": "Test Category",
            "sequence": 10,
            "color": 0,
        }
        values.update(kwargs)
        return self.Category.create(values)

    def _create_test_tag(self, **kwargs):
        """
        Create a test tag.

        Args:
            **kwargs: Field values

        Returns:
            document.tag: Created tag record
        """
        values = {
            "name": "Test Tag",
            "color": 0,
        }
        values.update(kwargs)
        return self.Tag.create(values)

    def _create_export_wizard(self, template, **kwargs):
        """
        Create an export wizard instance for testing.

        Args:
            template: Template to export
            **kwargs: Additional field values

        Returns:
            document.export.wizard: Created wizard record
        """
        values = {
            "template_id": template.id,
        }
        values.update(kwargs)
        return self.ExportWizard.with_context(
            default_template_id=template.id,
        ).create(values)

    def _get_sample_html_content(self, with_variables=False):
        """
        Get sample HTML content for testing.

        Args:
            with_variables: Whether to include variable placeholders

        Returns:
            str: HTML content
        """
        if with_variables:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Document</title>
</head>
<body>
    <h1>{{title}}</h1>
    <p>Dear {{recipient_name}},</p>
    <p>This is to inform you that {{message}}.</p>
    <p>Date: {{date}}</p>
    <p>Amount: {{amount}}</p>
    <p>Regards,<br>{{sender_name}}</p>
</body>
</html>
            """
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Document</title>
</head>
<body>
    <h1>Sample Document</h1>
    <p>This is a sample document without variables.</p>
    <table>
        <tr><th>Column 1</th><th>Column 2</th></tr>
        <tr><td>Data 1</td><td>Data 2</td></tr>
    </table>
</body>
</html>
        """

    def _create_test_pdf_bytes(self):
        """
        Create minimal valid PDF bytes for testing.

        Returns:
            bytes: Minimal PDF content
        """
        # Minimal valid PDF
        return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
307
%%EOF"""

    def _assert_pdf_valid(self, pdf_data):
        """
        Assert that PDF data is valid.

        Args:
            pdf_data: Binary PDF data or base64 encoded string
        """
        if isinstance(pdf_data, str):
            pdf_data = base64.b64decode(pdf_data)

        self.assertTrue(pdf_data, "PDF data should not be empty")
        self.assertTrue(
            pdf_data.startswith(b"%PDF"), "PDF should start with %PDF header",
        )
        self.assertIn(b"%%EOF", pdf_data, "PDF should contain EOF marker")

    def _get_variable_values(self):
        """
        Get sample variable values for wizard testing.

        Returns:
            dict: Variable name to value mapping
        """
        return {
            "employee_name": "John Doe",
            "job_title": "Software Engineer",
            "salary": "75000.00",
            "start_date": "2024-01-15",
            "title": "Important Notice",
            "recipient_name": "Jane Smith",
            "message": "Your request has been approved",
            "date": "2024-12-15",
            "amount": "10000.00",
            "sender_name": "HR Department",
        }

    def _count_variables_in_html(self, html_content):
        """
        Count unique variable placeholders in HTML content.

        Args:
            html_content: HTML string

        Returns:
            int: Number of unique variables
        """
        pattern = r"\{\{\s*(\w+)\s*\}\}"
        variables = set(re.findall(pattern, html_content))
        return len(variables)

    def _extract_variables_from_html(self, html_content):
        """
        Extract variable names from HTML content.

        Args:
            html_content: HTML string

        Returns:
            set: Set of variable names
        """
        pattern = r"\{\{\s*(\w+)\s*\}\}"
        return set(re.findall(pattern, html_content))
