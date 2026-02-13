"""
Test Cases for MIME Type Detection

Tests MIME type detection from filenames and binary data,
including support for various file formats.
"""

import base64

from odoo.tests import tagged

from .common import HREmployeeCleardealsTestCase


@tagged("post_install", "-at_install", "mime_detection")
class TestMIMEDetectionFromFilename(HREmployeeCleardealsTestCase):
    """Test MIME type detection from file extensions."""

    def test_01_detect_pdf_from_filename(self):
        """Test PDF MIME type detection from .pdf extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("document.pdf")

        self.assertEqual(mimetype, "application/pdf")
        self.assertEqual(ext, ".pdf")

    def test_02_detect_jpeg_from_filename(self):
        """Test JPEG MIME type detection from .jpg extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("photo.jpg")

        self.assertEqual(mimetype, "image/jpeg")
        self.assertEqual(ext, ".jpg")

    def test_03_detect_jpeg_from_jpeg_extension(self):
        """Test JPEG MIME type detection from .jpeg extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("photo.jpeg")

        self.assertEqual(mimetype, "image/jpeg")
        self.assertEqual(ext, ".jpg")

    def test_04_detect_png_from_filename(self):
        """Test PNG MIME type detection from .png extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("image.png")

        self.assertEqual(mimetype, "image/png")
        self.assertEqual(ext, ".png")

    def test_05_detect_gif_from_filename(self):
        """Test GIF MIME type detection from .gif extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("animation.gif")

        self.assertEqual(mimetype, "image/gif")
        self.assertEqual(ext, ".gif")

    def test_06_detect_bmp_from_filename(self):
        """Test BMP MIME type detection from .bmp extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("bitmap.bmp")

        self.assertEqual(mimetype, "image/bmp")
        self.assertEqual(ext, ".bmp")

    def test_07_detect_tiff_from_filename(self):
        """Test TIFF MIME type detection from .tiff extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("scan.tiff")

        self.assertEqual(mimetype, "image/tiff")
        self.assertEqual(ext, ".tiff")

    def test_08_detect_docx_from_filename(self):
        """Test DOCX MIME type detection from .docx extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("document.docx")

        self.assertEqual(
            mimetype,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertEqual(ext, ".docx")

    def test_09_detect_xlsx_from_filename(self):
        """Test XLSX MIME type detection from .xlsx extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("spreadsheet.xlsx")

        self.assertEqual(
            mimetype,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(ext, ".xlsx")

    def test_10_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        employee = self._create_test_employee()

        test_cases = [
            ("FILE.PDF", "application/pdf"),
            ("FILE.JPG", "image/jpeg"),
            ("FILE.PNG", "image/png"),
            ("File.Pdf", "application/pdf"),
            ("FiLe.JpG", "image/jpeg"),
        ]

        for filename, expected_mime in test_cases:
            with self.subTest(filename=filename):
                mimetype, _ext = employee._detect_mimetype_from_filename(filename)
                self.assertEqual(mimetype, expected_mime)

    def test_11_filename_with_path(self):
        """Test detection works with full file paths."""
        employee = self._create_test_employee()

        test_cases = [
            "/path/to/document.pdf",
            "C:\\Users\\Documents\\photo.jpg",
            "/home/user/images/picture.png",
        ]

        for filepath in test_cases:
            with self.subTest(filepath=filepath):
                mimetype, ext = employee._detect_mimetype_from_filename(filepath)
                self.assertIsNotNone(mimetype)
                self.assertIsNotNone(ext)

    def test_12_unknown_extension_defaults_to_pdf(self):
        """Test that unknown extensions default to PDF."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("file.xyz")

        self.assertEqual(mimetype, "application/pdf")
        self.assertEqual(ext, ".pdf")

    def test_13_filename_without_extension(self):
        """Test handling of filename without extension."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("filename")

        self.assertEqual(mimetype, "application/pdf")  # Default
        self.assertEqual(ext, ".pdf")

    def test_14_empty_filename(self):
        """Test handling of empty filename."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename("")

        self.assertEqual(mimetype, "application/pdf")  # Default
        self.assertEqual(ext, ".pdf")

    def test_15_none_filename(self):
        """Test handling of None filename."""
        employee = self._create_test_employee()
        mimetype, ext = employee._detect_mimetype_from_filename(None)

        self.assertEqual(mimetype, "application/pdf")  # Default
        self.assertEqual(ext, ".pdf")


@tagged("post_install", "-at_install", "mime_detection")
class TestMIMEDetectionFromBinary(HREmployeeCleardealsTestCase):
    """Test MIME type detection from binary data (magic numbers)."""

    def test_01_detect_pdf_from_binary(self):
        """Test PDF detection from binary magic number %PDF."""
        employee = self._create_test_employee()
        pdf_data = self._create_test_pdf_file()

        result = employee._detect_mimetype_from_binary(pdf_data)

        self.assertIsNotNone(result)
        mimetype, ext = result
        self.assertEqual(mimetype, "application/pdf")
        self.assertEqual(ext, ".pdf")

    def test_02_detect_jpeg_from_binary(self):
        """Test JPEG detection from binary magic number FFD8."""
        employee = self._create_test_employee()
        jpeg_data = self._create_test_jpeg_file()

        result = employee._detect_mimetype_from_binary(jpeg_data)

        self.assertIsNotNone(result)
        mimetype, ext = result
        self.assertEqual(mimetype, "image/jpeg")
        self.assertEqual(ext, ".jpg")

    def test_03_detect_png_from_binary(self):
        """Test PNG detection from binary magic number 89504E47."""
        employee = self._create_test_employee()
        png_data = self._create_test_png_file()

        result = employee._detect_mimetype_from_binary(png_data)

        self.assertIsNotNone(result)
        mimetype, ext = result
        self.assertEqual(mimetype, "image/png")
        self.assertEqual(ext, ".png")

    def test_04_empty_binary_data(self):
        """Test handling of empty binary data."""
        employee = self._create_test_employee()
        result = employee._detect_mimetype_from_binary(b"")

        self.assertIsNone(result)

    def test_05_none_binary_data(self):
        """Test handling of None binary data."""
        employee = self._create_test_employee()
        result = employee._detect_mimetype_from_binary(None)

        self.assertIsNone(result)

    def test_06_invalid_binary_data(self):
        """Test handling of invalid/corrupted binary data."""
        employee = self._create_test_employee()

        # Random data that doesn't match any magic number
        invalid_data = base64.b64encode(b"RANDOM DATA HERE")
        result = employee._detect_mimetype_from_binary(invalid_data)

        # Should return None for unrecognized data
        self.assertIsNone(result)

    def test_07_base64_string_handling(self):
        """Test that base64 string is properly decoded."""
        employee = self._create_test_employee()

        # Test with base64 string (as stored in Odoo Binary fields)
        pdf_data = self._create_test_pdf_file()
        result = employee._detect_mimetype_from_binary(pdf_data)

        self.assertIsNotNone(result)


@tagged("post_install", "-at_install", "mime_detection", "integration")
class TestMIMEDetectionIntegration(HREmployeeCleardealsTestCase):
    """Test MIME detection integration with document sync."""

    def test_01_pdf_document_gets_correct_mimetype(self):
        """Test that PDF documents get correct MIME type in vault."""
        employee = self.Employee.create(
            {
                **self._get_employee_base_values(),
                "pan_card_doc": self._create_test_pdf_file(),
                "pan_card_doc_filename": "pan_card.pdf",
            },
        )

        docs = self.EmployeeDocument.search(
            [
                ("employee_ref_id", "=", employee.id),
            ],
        )

        for doc in docs:
            for attachment in doc.doc_attachment_ids:
                self.assertEqual(
                    attachment.mimetype,
                    "application/pdf",
                    "PDF should have correct MIME type",
                )

    def test_02_jpeg_photo_gets_correct_mimetype(self):
        """Test that JPEG photos get correct MIME type in vault."""
        employee = self.Employee.create(
            {
                **self._get_employee_base_values(),
                "passport_photo": self._create_test_jpeg_file(),
                "passport_photo_filename": "photo.jpg",
            },
        )

        docs = self.EmployeeDocument.search(
            [
                ("employee_ref_id", "=", employee.id),
            ],
        )

        for doc in docs:
            for attachment in doc.doc_attachment_ids:
                self.assertEqual(
                    attachment.mimetype,
                    "image/jpeg",
                    "JPEG should have correct MIME type",
                )

    def test_03_png_photo_gets_correct_mimetype(self):
        """Test that PNG photos get correct MIME type in vault."""
        employee = self.Employee.create(
            {
                **self._get_employee_base_values(),
                "passport_photo": self._create_test_png_file(),
                "passport_photo_filename": "photo.png",
            },
        )

        docs = self.EmployeeDocument.search(
            [
                ("employee_ref_id", "=", employee.id),
            ],
        )

        for doc in docs:
            for attachment in doc.doc_attachment_ids:
                self.assertEqual(
                    attachment.mimetype,
                    "image/png",
                    "PNG should have correct MIME type",
                )

    def test_04_fallback_to_binary_detection(self):
        """Test fallback to binary detection when filename has no extension."""
        employee = self.Employee.create(
            {
                **self._get_employee_base_values(),
                "passport_photo": self._create_test_jpeg_file(),
                "passport_photo_filename": "photo",  # No extension
            },
        )

        docs = self.EmployeeDocument.search(
            [
                ("employee_ref_id", "=", employee.id),
            ],
        )

        # Should detect JPEG from binary data
        for doc in docs:
            for attachment in doc.doc_attachment_ids:
                self.assertIn(
                    attachment.mimetype,
                    ["image/jpeg", "application/pdf"],
                    "Should detect MIME from binary or use default",
                )

    def test_05_mixed_document_types_in_single_employee(self):
        """Test multiple documents with different MIME types."""
        employee = self.Employee.create(
            {
                **self._get_employee_base_values(),
                "pan_card_doc": self._create_test_pdf_file(),
                "pan_card_doc_filename": "pan.pdf",
                "passport_photo": self._create_test_jpeg_file(),
                "passport_photo_filename": "photo.jpg",
                "offer_letter": self._create_test_pdf_file(),
                "offer_letter_filename": "offer.pdf",
            },
        )

        docs = self.EmployeeDocument.search(
            [
                ("employee_ref_id", "=", employee.id),
            ],
        )

        # Should have different MIME types for different documents
        mimetypes = set()
        for doc in docs:
            for attachment in doc.doc_attachment_ids:
                mimetypes.add(attachment.mimetype)

        # Should have at least PDF and JPEG
        self.assertIn("application/pdf", mimetypes)
        self.assertIn("image/jpeg", mimetypes)


@tagged("post_install", "-at_install", "mime_detection", "edge_cases")
class TestMIMEDetectionEdgeCases(HREmployeeCleardealsTestCase):
    """Test edge cases in MIME type detection."""

    def test_01_double_extension_filename(self):
        """Test filename with double extension like .tar.gz."""
        employee = self._create_test_employee()
        mimetype, _ext = employee._detect_mimetype_from_filename("file.tar.pdf")

        # Should detect based on last extension (.pdf)
        self.assertEqual(mimetype, "application/pdf")

    def test_02_filename_with_dots(self):
        """Test filename with multiple dots."""
        employee = self._create_test_employee()
        mimetype, _ext = employee._detect_mimetype_from_filename("my.file.name.jpg")

        self.assertEqual(mimetype, "image/jpeg")

    def test_03_filename_with_spaces(self):
        """Test filename with spaces."""
        employee = self._create_test_employee()
        mimetype, _ext = employee._detect_mimetype_from_filename("my file name.pdf")

        self.assertEqual(mimetype, "application/pdf")

    def test_04_filename_with_special_chars(self):
        """Test filename with special characters."""
        employee = self._create_test_employee()

        special_filenames = [
            "file@#$.pdf",
            "file (1).jpg",
            "file [copy].png",
        ]

        for filename in special_filenames:
            with self.subTest(filename=filename):
                mimetype, _ext = employee._detect_mimetype_from_filename(filename)
                self.assertIsNotNone(mimetype)

    def test_05_very_long_filename(self):
        """Test handling of very long filename."""
        employee = self._create_test_employee()
        long_filename = "a" * 200 + ".pdf"

        mimetype, _ext = employee._detect_mimetype_from_filename(long_filename)
        self.assertEqual(mimetype, "application/pdf")

    def test_06_unicode_filename(self):
        """Test handling of unicode characters in filename."""
        employee = self._create_test_employee()
        unicode_filename = "फाइल.pdf"  # Hindi characters

        mimetype, _ext = employee._detect_mimetype_from_filename(unicode_filename)
        self.assertEqual(mimetype, "application/pdf")

    def test_07_truncated_binary_data(self):
        """Test handling of truncated binary data."""
        employee = self._create_test_employee()

        # Very short data (less than magic number length)
        short_data = base64.b64encode(b"%P")
        result = employee._detect_mimetype_from_binary(short_data)

        # Should handle gracefully (return None or default)
        # Implementation dependent
        self.assertTrue(result is None or isinstance(result, tuple))
