# -*- coding: utf-8 -*-
"""
Common Test Utilities and Fixtures

Provides shared utilities, test data, and helper methods for the test suite.
"""

import base64
import os
from odoo.tests import common


class HREmployeeCleardealsTestCase(common.TransactionCase):
    """
    Base test case class for hr_employee_cleardeals module.
    
    Provides common setup, utility methods, and test data for all test cases.
    """

    @classmethod
    def setUpClass(cls):
        """Set up common test data and objects."""
        super(HREmployeeCleardealsTestCase, cls).setUpClass()
        
        # Models
        cls.Employee = cls.env['hr.employee']
        cls.Department = cls.env['hr.department']
        cls.Job = cls.env['hr.job']
        cls.DocumentType = cls.env['document.type']
        cls.EmployeeDocument = cls.env['hr.employee.document']
        cls.Attachment = cls.env['ir.attachment']
        cls.Sequence = cls.env['ir.sequence']
        cls.Country = cls.env['res.country']
        cls.State = cls.env['res.country.state']
        
        # Test Department
        cls.dept_sales = cls.Department.create({
            'name': 'Sales Department',
        })
        
        # Test Job Position
        cls.job_bde = cls.Job.create({
            'name': 'Business Development Executive',
            'department_id': cls.dept_sales.id,
        })
        
        # Test Country and State (India)
        cls.country_india = cls.Country.search([('code', '=', 'IN')], limit=1)
        if not cls.country_india:
            cls.country_india = cls.Country.create({
                'name': 'India',
                'code': 'IN',
            })
        
        cls.state_gj = cls.State.search([
            ('country_id', '=', cls.country_india.id),
            ('code', '=', 'GJ')
        ], limit=1)
        if not cls.state_gj:
            cls.state_gj = cls.State.create({
                'name': 'Gujarat',
                'code': 'GJ',
                'country_id': cls.country_india.id,
            })
        
        # Document Types
        cls.doc_type_pan = cls._get_or_create_doc_type('PAN Card')
        cls.doc_type_aadhaar = cls._get_or_create_doc_type('Aadhaar Card')
        cls.doc_type_bank = cls._get_or_create_doc_type('Bank Document')
        cls.doc_type_offer = cls._get_or_create_doc_type('Offer Letter')
        cls.doc_type_passport_photo = cls._get_or_create_doc_type('Passport Photo')
    
    @classmethod
    def _get_or_create_doc_type(cls, name):
        """Get or create document type."""
        doc_type = cls.DocumentType.search([('name', '=', name)], limit=1)
        if not doc_type:
            doc_type = cls.DocumentType.create({
                'name': name,
            })
        return doc_type
    
    def _get_employee_base_values(self):
        """
        Get base employee data for testing.
        
        Returns:
            dict: Basic employee values
        """
        return {
            'name': 'Test Employee',
            'work_email': 'test.employee@cleardeals.com',
            'work_phone': '+91-9876543210',
            'department_id': self.dept_sales.id,
            'job_id': self.job_bde.id,
        }
    
    def _get_employee_full_values(self):
        """
        Get complete employee data for testing.
        
        Returns:
            dict: Complete employee values with all fields
        """
        base = self._get_employee_base_values()
        base.update({
            'legal_name': 'Test Employee Full Name',
            'sex': 'male',
            'marital': 'single',
            'birthday': '1995-01-15',
            'blood_group': 'o+',
            'private_phone': '+91-9876543211',
            'private_email': 'test.personal@example.com',
            'private_street': '123 Test Street',
            'private_city': 'Ahmedabad',
            'private_state_id': self.state_gj.id,
            'private_zip': '380001',
            'private_country_id': self.country_india.id,
            'emergency_contact': 'Emergency Contact Name',
            'emergency_phone': '+91-9876543212',
            'emergency_contact_relationship': 'Father',
            'identification_id': '123456789012',  # Valid Aadhaar
            'pan_number': 'ABCDE1234F',  # Valid PAN
            'bank_name': 'State Bank of India',
            'bank_acc_number': '12345678901234',
            'ifsc_code': 'SBIN0001234',
            'account_type': 'savings',
            'name_as_per_bank': 'Test Employee Full Name',
        })
        return base
    
    def _create_test_employee(self, **kwargs):
        """
        Create a test employee with optional overrides.
        
        Args:
            **kwargs: Field values to override defaults
            
        Returns:
            hr.employee: Created employee record
        """
        values = self._get_employee_base_values()
        values.update(kwargs)
        return self.Employee.create(values)
    
    def _create_test_pdf_file(self):
        """
        Create a minimal valid PDF file for testing.
        
        Returns:
            bytes: Base64 encoded PDF content
        """
        # Minimal PDF file
        pdf_content = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000109 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n200\n%%EOF'
        return base64.b64encode(pdf_content)
    
    def _create_test_jpeg_file(self):
        """
        Create a minimal valid JPEG file for testing.
        
        Returns:
            bytes: Base64 encoded JPEG content
        """
        # Minimal JPEG file (FFD8 magic number)
        jpeg_content = (
            b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
            b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xFF\xC0\x00\x0b\x08\x00'
            b'\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x14\x00\x01\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xDA\x00\x08\x01'
            b'\x01\x00\x00?\x00\x7F\x00\xFF\xD9'
        )
        return base64.b64encode(jpeg_content)
    
    def _create_test_png_file(self):
        """
        Create a minimal valid PNG file for testing.
        
        Returns:
            bytes: Base64 encoded PNG content
        """
        # Minimal PNG file (89504E47 magic number)
        png_content = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return base64.b64encode(png_content)
    
    def _get_valid_aadhaar_numbers(self):
        """
        Get list of valid Aadhaar numbers for testing.
        
        Returns:
            list: Valid Aadhaar number formats
        """
        return [
            '123456789012',
            '1234 5678 9012',  # With spaces
            '987654321098',
            '111122223333',
        ]
    
    def _get_invalid_aadhaar_numbers(self):
        """
        Get list of invalid Aadhaar numbers for testing.
        
        Returns:
            list: Invalid Aadhaar number formats
        """
        return [
            '12345678901',    # 11 digits
            '1234567890123',  # 13 digits
            'ABCD12345678',   # Contains letters
            '123-456-789',    # Invalid format
            '',               # Empty
        ]
    
    def _get_valid_pan_numbers(self):
        """
        Get list of valid PAN numbers for testing.
        
        Returns:
            list: Valid PAN number formats
        """
        return [
            'ABCDE1234F',
            'XYZAB5678C',
            'PQRST9012D',
            'abcde1234f',  # Should be converted to uppercase
        ]
    
    def _get_invalid_pan_numbers(self):
        """
        Get list of invalid PAN numbers for testing.
        
        Returns:
            list: Invalid PAN number formats
        """
        return [
            'ABC1234567',     # Too short
            'ABCDE12345F',    # Too long
            '12345ABCDE',     # Wrong format
            'ABCDE-1234-F',   # With hyphens
            'ABCD1234F',      # 4 letters instead of 5
            '',               # Empty
        ]
    
    def _count_documents_in_vault(self, employee):
        """
        Count documents in vault for an employee.
        
        Args:
            employee: Employee record
            
        Returns:
            int: Number of documents in vault
        """
        return self.EmployeeDocument.search_count([
            ('employee_ref_id', '=', employee.id)
        ])
    
    def _get_sequence_next_value(self):
        """
        Get the next sequence value without consuming it.
        
        Returns:
            str: Next employee ID that would be generated
        """
        sequence = self.Sequence.search([('code', '=', 'hr.employee.cd.id')], limit=1)
        if sequence:
            return sequence.get_next_char(sequence.number_next_actual)
        return 'CD-0001'
    
    def _reset_employee_sequence(self, start_number=1):
        """
        Reset employee ID sequence to a specific number.
        
        Args:
            start_number: Starting sequence number
        """
        sequence = self.Sequence.search([('code', '=', 'hr.employee.cd.id')], limit=1)
        if sequence:
            sequence.write({'number_next_actual': start_number})
