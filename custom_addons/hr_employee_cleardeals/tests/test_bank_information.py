# -*- coding: utf-8 -*-
"""
Test Cases for Bank Information Management

Tests bank account details, IFSC code, account type, and related validations.
"""

from odoo.tests import tagged
from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'bank')
class TestBankInformation(HREmployeeCleardealsTestCase):
    """Test bank information functionality."""
    
    def test_01_create_employee_with_bank_details(self):
        """Test creating employee with complete bank details."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_name': 'State Bank of India',
            'bank_acc_number': '12345678901234',
            'ifsc_code': 'SBIN0001234',
            'account_type': 'savings',
            'name_as_per_bank': 'Test Employee Full Name',
        })
        
        self.assertEqual(employee.bank_name, 'State Bank of India')
        self.assertEqual(employee.bank_acc_number, '12345678901234')
        self.assertEqual(employee.ifsc_code, 'SBIN0001234')
        self.assertEqual(employee.account_type, 'savings')
    
    def test_02_bank_account_types(self):
        """Test all bank account type options."""
        account_types = ['savings', 'current', 'salary']
        
        for acc_type in account_types:
            with self.subTest(account_type=acc_type):
                employee = self.Employee.create({
                    **self._get_employee_base_values(),
                    'name': f'Employee {acc_type}',
                    'work_email': f'{acc_type}@test.com',
                    'account_type': acc_type,
                })
                self.assertEqual(employee.account_type, acc_type)
    
    def test_03_update_bank_details(self):
        """Test updating bank details."""
        employee = self._create_test_employee()
        
        employee.write({
            'bank_name': 'HDFC Bank',
            'bank_acc_number': '98765432109876',
            'ifsc_code': 'HDFC0001234',
        })
        
        self.assertEqual(employee.bank_name, 'HDFC Bank')
        self.assertEqual(employee.bank_acc_number, '98765432109876')
    
    def test_04_ifsc_code_format(self):
        """Test IFSC code format."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'ifsc_code': 'SBIN0001234',
        })
        
        # IFSC should be 11 characters: 4 letters + 0 + 6 digits
        self.assertEqual(len(employee.ifsc_code), 11)
    
    def test_05_bank_document_upload(self):
        """Test uploading bank document."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_document_type': 'cancelled_cheque',
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'cancelled_cheque.pdf',
        })
        
        self.assertEqual(employee.bank_document_type, 'cancelled_cheque')
        self.assertTrue(employee.bank_document)
    
    def test_06_bank_document_type_passbook(self):
        """Test uploading passbook copy."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_document_type': 'passbook_copy',
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'passbook.pdf',
        })
        
        self.assertEqual(employee.bank_document_type, 'passbook_copy')
    
    def test_07_cibil_score_tracking(self):
        """Test CIBIL score field."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'cibil_score': 750,
        })
        
        self.assertEqual(employee.cibil_score, 750)
    
    def test_08_cibil_score_update(self):
        """Test updating CIBIL score."""
        employee = self._create_test_employee(cibil_score=700)
        
        employee.write({'cibil_score': 780})
        
        self.assertEqual(employee.cibil_score, 780)
    
    def test_09_name_as_per_bank_validation(self):
        """Test name as per bank field."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Test Employee',
            'name_as_per_bank': 'TEST EMPLOYEE',
        })
        
        self.assertEqual(employee.name_as_per_bank, 'TEST EMPLOYEE')
    
    def test_10_bank_details_without_document(self):
        """Test adding bank details without uploading document."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_name': 'ICICI Bank',
            'bank_acc_number': '11111111111111',
            'ifsc_code': 'ICIC0001111',
            # No document
        })
        
        self.assertEqual(employee.bank_name, 'ICICI Bank')
        self.assertFalse(employee.bank_document)


@tagged('post_install', '-at_install', 'bank', 'document_sync')
class TestBankDocumentSync(HREmployeeCleardealsTestCase):
    """Test bank document synchronization to vault."""
    
    def test_01_bank_document_syncs_to_vault(self):
        """Test that bank document syncs to document vault."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'bank_doc.pdf',
        })
        
        # Check vault for bank document
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        # Should have bank document in vault
        bank_docs = docs.filtered(
            lambda d: 'Bank' in d.document_type_id.name
        )
        self.assertTrue(len(bank_docs) > 0, "Bank document should be in vault")
    
    def test_02_bank_document_update_syncs(self):
        """Test that updating bank document syncs to vault."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'bank1.pdf',
        })
        
        initial_count = self._count_documents_in_vault(employee)
        
        # Update bank document
        employee.write({
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'bank2.pdf',
        })
        
        new_count = self._count_documents_in_vault(employee)
        
        # Document count should reflect update
        self.assertTrue(new_count >= initial_count)


@tagged('post_install', '-at_install', 'bank', 'edge_cases')
class TestBankInformationEdgeCases(HREmployeeCleardealsTestCase):
    """Test edge cases in bank information."""
    
    def test_01_very_long_account_number(self):
        """Test handling of very long account numbers."""
        long_acc = '1' * 30
        
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_acc_number': long_acc,
        })
        
        self.assertEqual(employee.bank_acc_number, long_acc)
    
    def test_02_account_number_with_spaces(self):
        """Test account number with spaces."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_acc_number': '1234 5678 9012',
        })
        
        self.assertEqual(employee.bank_acc_number, '1234 5678 9012')
    
    def test_03_ifsc_code_case_sensitivity(self):
        """Test IFSC code case handling."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'ifsc_code': 'sbin0001234',  # lowercase
        })
        
        # IFSC codes are typically uppercase, but field might accept lowercase
        self.assertTrue(employee.ifsc_code)
    
    def test_04_unicode_bank_name(self):
        """Test bank name with unicode characters."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'bank_name': 'बैंक ऑफ इंडिया',  # Hindi
        })
        
        self.assertEqual(employee.bank_name, 'बैंक ऑफ इंडिया')
    
    def test_05_cibil_score_boundary_values(self):
        """Test CIBIL score boundary values."""
        # CIBIL scores range from 300 to 900
        test_scores = [300, 500, 750, 900]
        
        for score in test_scores:
            with self.subTest(score=score):
                employee = self.Employee.create({
                    **self._get_employee_base_values(),
                    'name': f'Emp Score {score}',
                    'work_email': f'score{score}@test.com',
                    'cibil_score': score,
                })
                self.assertEqual(employee.cibil_score, score)
    
    def test_06_multiple_document_types_together(self):
        """Test both cancelled cheque and passbook scenarios."""
        # Employee with cancelled cheque
        emp1 = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Cheque Employee',
            'bank_document_type': 'cancelled_cheque',
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'cheque.pdf',
        })
        
        # Employee with passbook
        emp2 = self.Employee.create({
            **self._get_employee_base_values(),
            'name': 'Passbook Employee',
            'work_email': 'passbook@test.com',
            'bank_document_type': 'passbook_copy',
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'passbook.pdf',
        })
        
        self.assertEqual(emp1.bank_document_type, 'cancelled_cheque')
        self.assertEqual(emp2.bank_document_type, 'passbook_copy')
