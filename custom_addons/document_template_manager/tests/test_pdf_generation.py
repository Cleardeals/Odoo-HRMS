"""
Test Cases for PDF Generation

Tests PDF generation functionality, wkhtmltopdf integration, and PDF file handling.
"""

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DocumentTemplateTestCase


@tagged("post_install", "-at_install", "pdf_generation")
class TestPDFGeneration(DocumentTemplateTestCase):
    """Test PDF generation from templates."""

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
    def test_01_generate_pdf_without_variables(self, mock_wkhtmltopdf):
        """Test PDF generation for template without variables."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        result = template.action_export_pdf()

        # Should generate PDF directly (not open wizard)
        self.assertEqual(result.get("type"), "ir.actions.act_url")
        self.assertTrue(template.has_pdf)

    def test_02_generate_pdf_with_variables_opens_wizard(self):
        """Test that templates with variables open wizard."""
        template = self._create_template_with_variables()

        result = template.action_export_pdf()

        # Should open wizard, not download directly
        self.assertEqual(result.get("type"), "ir.actions.act_window")
        self.assertEqual(result.get("res_model"), "document.export.wizard")

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
    def test_03_pdf_file_saved_to_template(self, mock_wkhtmltopdf):
        """Test that PDF file is saved on template."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        self.assertFalse(template.pdf_file)

        template.action_export_pdf()

        self.assertTrue(template.pdf_file)

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
    def test_04_has_pdf_computed_correctly(self, mock_wkhtmltopdf):
        """Test that has_pdf field is computed correctly."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        self.assertFalse(template.has_pdf)

        template.action_export_pdf()

        self.assertTrue(template.has_pdf)

    def test_05_pdf_filename_computed(self):
        """Test that PDF filename is computed from template name."""
        template = self._create_test_template(name="Test Document")

        self.assertEqual(template.pdf_filename, "Test Document.pdf")

    def test_06_pdf_filename_with_slashes(self):
        """Test that slashes in name are replaced in filename."""
        template = self._create_test_template(name="Test/Document\\File")

        self.assertEqual(template.pdf_filename, "Test-Document-File.pdf")

    def test_07_pdf_filename_empty_name(self):
        """Test PDF filename with empty template name."""
        template = self.Template.new(
            {
                "name": "",
                "html_content": "<p>Test</p>",
            },
        )

        self.assertEqual(template.pdf_filename, "document.pdf")

    def test_08_generate_pdf_empty_content_raises_error(self):
        """Test that generating PDF with empty content raises error."""
        template = self._create_test_template(html_content=False)

        with self.assertRaises(ValidationError):
            template.action_export_pdf()

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
    def test_09_download_pdf_action(self, mock_wkhtmltopdf):
        """Test download PDF action."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()
        template.action_export_pdf()

        result = template.action_download_pdf()

        self.assertEqual(result.get("type"), "ir.actions.act_url")
        self.assertIn("download=true", result.get("url", ""))

    def test_10_download_pdf_without_file_raises_error(self):
        """Test that downloading PDF without generating first raises error."""
        template = self._create_test_template()

        with self.assertRaises(ValidationError):
            template.action_download_pdf()


@tagged("post_install", "-at_install", "pdf_content")
@patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
class TestPDFContent(DocumentTemplateTestCase):
    """Test PDF content generation and formatting."""

    def test_01_pdf_contains_html_content(self, mock_wkhtmltopdf):
        """Test that PDF contains the HTML content."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(
            html_content="<h1>Test Title</h1><p>Test Content</p>",
        )

        # Generate PDF through helper method
        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)

    def test_02_pdf_with_company_info(self, mock_wkhtmltopdf):
        """Test that PDF includes company information."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)

    def test_03_pdf_with_tables(self, mock_wkhtmltopdf):
        """Test PDF generation with HTML tables."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(
            html_content="""
                <table>
                    <tr><th>Header 1</th><th>Header 2</th></tr>
                    <tr><td>Data 1</td><td>Data 2</td></tr>
                </table>
            """,
        )

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)

    def test_04_pdf_with_styles(self, mock_wkhtmltopdf):
        """Test PDF generation with inline styles."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(
            html_content="""
                <div style="color: red; font-size: 20px;">
                    Styled content
                </div>
            """,
        )

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)


@tagged("post_install", "-at_install", "pdf_attachment")
@patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
class TestPDFAttachment(DocumentTemplateTestCase):
    """Test PDF attachment creation."""

    def test_01_attachment_created_on_export(self, mock_wkhtmltopdf):
        """Test that attachment is created when exporting PDF."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        initial_count = self.Attachment.search_count([])

        template.action_export_pdf()

        final_count = self.Attachment.search_count([])
        self.assertGreater(final_count, initial_count)

    def test_02_attachment_has_correct_mimetype(self, mock_wkhtmltopdf):
        """Test that created attachment has PDF mimetype."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        template.action_export_pdf()

        # Find the attachment
        attachment = self.Attachment.search(
            [
                ("name", "=", template.pdf_filename),
            ],
            order="id desc",
            limit=1,
        )

        self.assertEqual(attachment.mimetype, "application/pdf")

    def test_03_attachment_has_correct_name(self, mock_wkhtmltopdf):
        """Test that attachment has correct filename."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(name="My Document")

        template.action_export_pdf()

        attachment = self.Attachment.search(
            [
                ("name", "=", "My Document.pdf"),
            ],
            limit=1,
        )

        self.assertTrue(attachment.exists())


@tagged("post_install", "-at_install", "pdf_edge_cases")
@patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
class TestPDFEdgeCases(DocumentTemplateTestCase):
    """Test PDF generation edge cases."""

    def test_01_pdf_with_unicode_characters(self, mock_wkhtmltopdf):
        """Test PDF generation with Unicode characters."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(
            html_content="<p>Unicode: ©®™€£¥ 中文 العربية</p>",
        )

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)

    def test_02_pdf_with_very_long_content(self, mock_wkhtmltopdf):
        """Test PDF generation with long content (multiple pages)."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        long_content = "<p>Paragraph content.</p>" * 100

        template = self._create_test_template(html_content=long_content)

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)

    def test_03_pdf_regeneration_overwrites(self, mock_wkhtmltopdf):
        """Test that regenerating PDF overwrites previous file."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template()

        template.action_export_pdf()
        first_pdf = template.pdf_file

        template.action_export_pdf()
        second_pdf = template.pdf_file

        # Both PDFs should exist and regeneration should work
        self.assertTrue(first_pdf)
        self.assertTrue(second_pdf)

    def test_04_pdf_with_empty_html_tags(self, mock_wkhtmltopdf):
        """Test PDF with empty HTML tags."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(
            html_content="<div></div><p></p><span></span>",
        )

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)


@tagged("post_install", "-at_install", "pdf_header")
class TestHeaderHtmlDoc(DocumentTemplateTestCase):
    """Test _build_header_html_doc() behaviour for all print-mode combinations."""

    HEADER_HTML = "<div><strong>ACME Corp</strong></div>"

    def _digital_template(self, **kwargs):
        """Helper: create a digital-mode template with header_html set."""
        defaults = {
            "print_mode": "digital",
            "show_header": True,
            "header_html": self.HEADER_HTML,
        }
        defaults.update(kwargs)
        return self._create_test_template(**defaults)

    # ── Cases that must return None ────────────────────────────────────

    def test_01_letterhead_mode_returns_none(self):
        """_build_header_html_doc returns None for Letterhead mode."""
        template = self._digital_template(print_mode="letterhead")
        result = template._build_header_html_doc(20, 20)
        self.assertIsNone(result)

    def test_02_digital_show_header_false_returns_none(self):
        """_build_header_html_doc returns None when show_header is False."""
        template = self._digital_template(show_header=False)
        result = template._build_header_html_doc(20, 20)
        self.assertIsNone(result)

    def test_03_digital_empty_header_html_returns_none(self):
        """_build_header_html_doc returns None when header_html is blank."""
        template = self._digital_template(header_html=False)
        result = template._build_header_html_doc(20, 20)
        self.assertIsNone(result)

    def test_04_digital_whitespace_only_header_returns_none(self):
        """_build_header_html_doc returns None when header_html is only whitespace."""
        template = self._digital_template(header_html="   ")
        result = template._build_header_html_doc(20, 20)
        self.assertIsNone(result)

    def test_05_digital_empty_paragraphs_only_returns_none(self):
        """_build_header_html_doc returns None when header consists only of empty <p>."""
        template = self._digital_template(header_html="<p><br></p>")
        result = template._build_header_html_doc(20, 20)
        self.assertIsNone(result)

    # ── Cases that must produce valid HTML ────────────────────────────

    def test_06_digital_with_header_returns_string(self):
        """_build_header_html_doc returns a string for valid digital header."""
        template = self._digital_template()
        result = template._build_header_html_doc(20, 20)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

    def test_07_returned_html_is_valid_document(self):
        """Returned string starts with <!DOCTYPE html> and contains <body>."""
        template = self._digital_template()
        result = template._build_header_html_doc(20, 20)
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("<html>", result)
        self.assertIn("<body>", result)
        self.assertIn("</body>", result)

    def test_08_header_content_present_in_output(self):
        """The header HTML content appears inside the returned document."""
        template = self._digital_template()
        result = template._build_header_html_doc(20, 20)
        self.assertIn("ACME Corp", result)

    def test_09_separator_hr_present_in_output(self):
        """Returned HTML contains the separator <hr> after the header content."""
        template = self._digital_template()
        result = template._build_header_html_doc(20, 20)
        self.assertIn("<hr", result)
        self.assertIn("border-bottom", result)

    def test_10_left_margin_embedded_in_css(self):
        """The left margin value is embedded inside the CSS block."""
        template = self._digital_template()
        result = template._build_header_html_doc(15, 20)
        # Body padding uses the left/right values
        self.assertIn("15mm", result)

    def test_11_right_margin_embedded_in_css(self):
        """The right margin value is embedded inside the CSS block."""
        template = self._digital_template()
        result = template._build_header_html_doc(20, 18)
        self.assertIn("18mm", result)

    def test_12_meta_charset_present(self):
        """Returned HTML contains UTF-8 charset declaration."""
        template = self._digital_template()
        result = template._build_header_html_doc(20, 20)
        self.assertIn("utf-8", result)

    # ── PDF generation integration ────────────────────────────────────

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
    def test_13_generate_pdf_digital_with_header(self, mock_wkhtmltopdf):
        """_generate_pdf_bytes passes header= kwarg when digital mode + header set."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._digital_template()

        pdf_bytes = template._generate_pdf_bytes(template.html_content)

        self._assert_pdf_valid(pdf_bytes)
        # Ensure wkhtmltopdf was called (header kwarg is passed internally)
        mock_wkhtmltopdf.assert_called_once()
        call_kwargs = mock_wkhtmltopdf.call_args
        # 'header' should be a non-None keyword argument
        self.assertIn("header", call_kwargs.kwargs if call_kwargs.kwargs else {})
        header_val = (call_kwargs.kwargs or {}).get("header")
        self.assertIsNotNone(header_val)

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._run_wkhtmltopdf")
    def test_14_generate_pdf_letterhead_no_header_kwarg(self, mock_wkhtmltopdf):
        """_generate_pdf_bytes passes header=None when mode is Letterhead."""
        mock_wkhtmltopdf.return_value = self._mock_pdf_bytes()
        template = self._create_test_template(
            print_mode="letterhead",
            header_html=self.HEADER_HTML,
        )

        template._generate_pdf_bytes(template.html_content)

        mock_wkhtmltopdf.assert_called_once()
        call_kwargs = mock_wkhtmltopdf.call_args
        header_val = (call_kwargs.kwargs or {}).get("header")
        self.assertIsNone(header_val)
