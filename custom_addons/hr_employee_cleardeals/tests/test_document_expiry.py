"""
Test Cases for Document Expiry Notifications

Tests document expiry tracking and notification system.
"""

from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'document_expiry')
class TestDocumentExpiry(HREmployeeCleardealsTestCase):
    """Test document expiry functionality."""

    def test_01_create_document_with_expiry_date(self):
        """Test creating document with expiry date."""
        employee = self._create_test_employee()

        expiry_date = date.today() + timedelta(days=30)
        doc = self.EmployeeDocument.create({
            'name': 'Test Document',
            'employee_ref_id': employee.id,
            'document_type_id': self.doc_type_pan.id,
            'expiry_date': expiry_date,
        })

        self.assertEqual(doc.expiry_date, expiry_date)

    def test_02_document_without_expiry(self):
        """Test document can exist without expiry date."""
        employee = self._create_test_employee()

        doc = self.EmployeeDocument.create({
            'name': 'No Expiry Document',
            'employee_ref_id': employee.id,
            'document_type_id': self.doc_type_pan.id,
            'expiry_date': False,
        })

        self.assertFalse(doc.expiry_date,
                        "Document can have no expiry date")

    def test_03_notification_type_options(self):
        """Test all notification type options are available."""
        employee = self._create_test_employee()

        notification_types = ['single', 'multi', 'everyday', 'everyday_after']

        for notif_type in notification_types:
            with self.subTest(notif_type=notif_type):
                doc = self.EmployeeDocument.create({
                    'name': f'Doc {notif_type}',
                    'employee_ref_id': employee.id,
                    'document_type_id': self.doc_type_pan.id,
                    'notification_type': notif_type,
                })
                self.assertEqual(doc.notification_type, notif_type)

    def test_04_before_days_setting(self):
        """Test setting days before expiry for notification."""
        employee = self._create_test_employee()

        doc = self.EmployeeDocument.create({
            'name': 'Test Document',
            'employee_ref_id': employee.id,
            'document_type_id': self.doc_type_pan.id,
            'before_days': 7,
        })

        self.assertEqual(doc.before_days, 7)

    def test_05_issue_date_defaults_to_today(self):
        """Test that issue_date defaults to today."""
        employee = self._create_test_employee()

        doc = self.EmployeeDocument.create({
            'name': 'Test Document',
            'employee_ref_id': employee.id,
            'document_type_id': self.doc_type_pan.id,
        })

        self.assertEqual(doc.issue_date, fields.Date.today())

    def test_06_expired_document_detection(self):
        """Test that system prevents creating expired documents."""
        employee = self._create_test_employee()

        # System should prevent creating expired documents
        with self.assertRaises(UserError, msg="Should prevent expired document creation"):
            self.EmployeeDocument.create({
                'name': 'Expired Document',
                'employee_ref_id': employee.id,
                'document_type_id': self.doc_type_pan.id,
                'expiry_date': date.today() - timedelta(days=1),
            })

    def test_07_upcoming_expiry_documents(self):
        """Test finding documents expiring soon."""
        employee = self._create_test_employee()

        # Create document expiring in 7 days
        upcoming_doc = self.EmployeeDocument.create({
            'name': 'Upcoming Expiry',
            'employee_ref_id': employee.id,
            'document_type_id': self.doc_type_pan.id,
            'expiry_date': date.today() + timedelta(days=7),
            'before_days': 7,
        })

        # Search for documents expiring within 10 days
        expiry_threshold = date.today() + timedelta(days=10)
        upcoming_docs = self.EmployeeDocument.search([
            ('expiry_date', '<=', expiry_threshold),
            ('expiry_date', '>=', date.today()),
        ])

        self.assertIn(upcoming_doc, upcoming_docs,
                     "Should find upcoming expiry documents")


@tagged('post_install', '-at_install', 'document_expiry', 'notifications')
class TestExpiryNotifications(HREmployeeCleardealsTestCase):
    """Test expiry notification system."""

    def test_01_mail_reminder_method_exists(self):
        """Test that mail_reminder method is available."""
        doc = self.EmployeeDocument.create({
            'name': 'Test',
            'employee_ref_id': self._create_test_employee().id,
            'document_type_id': self.doc_type_pan.id,
        })

        # Method should exist
        self.assertTrue(hasattr(doc, 'mail_reminder'),
                       "Document should have mail_reminder method")

    def test_02_notification_for_expiring_today(self):
        """Test notification for document expiring today."""
        employee = self._create_test_employee()

        doc = self.EmployeeDocument.create({
            'name': 'Expiring Today',
            'employee_ref_id': employee.id,
            'document_type_id': self.doc_type_pan.id,
            'expiry_date': date.today(),
            'notification_type': 'single',
        })

        # Should be eligible for notification
        self.assertEqual(doc.expiry_date, date.today())
