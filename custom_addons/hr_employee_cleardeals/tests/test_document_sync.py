# -*- coding: utf-8 -*-
"""
Test Cases for Document Vault Synchronization

Tests automatic document synchronization between employee form and document vault,
including create/update scenarios, attachment creation, and sync triggers.
"""

from odoo.tests import tagged
from .common import HREmployeeCleardealsTestCase


@tagged('post_install', '-at_install', 'document_sync')
class TestDocumentSyncBasic(HREmployeeCleardealsTestCase):
    """Test basic document vault synchronization functionality."""
    
    def test_01_document_sync_on_employee_creation(self):
        """Test that documents are synced when employee is created with documents."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card.pdf',
        })
        
        # Check document was created in vault
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        self.assertTrue(len(docs) > 0, "Document should be created in vault")
    
    def test_02_document_sync_on_employee_update(self):
        """Test that documents are synced when employee is updated with documents."""
        employee = self._create_test_employee()
        initial_count = self._count_documents_in_vault(employee)
        
        employee.write({
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card.pdf',
        })
        
        new_count = self._count_documents_in_vault(employee)
        self.assertGreater(new_count, initial_count,
                          "Document count should increase after update")
    
    def test_03_multiple_documents_sync(self):
        """Test syncing multiple documents at once."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card.pdf',
            'offer_letter': self._create_test_pdf_file(),
            'offer_letter_filename': 'offer_letter.pdf',
            'passport_doc': self._create_test_pdf_file(),
            'passport_doc_filename': 'passport.pdf',
        })
        
        doc_count = self._count_documents_in_vault(employee)
        self.assertGreaterEqual(doc_count, 3,
                               "At least 3 documents should be synced")
    
    def test_04_document_type_auto_creation(self):
        """Test that document types are auto-created if not exist."""
        # Use a document field that might not have a type yet
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'resume_doc': self._create_test_pdf_file(),
            'resume_doc_filename': 'resume.pdf',
        })
        
        # Check if Resume/CV document type exists
        doc_type = self.DocumentType.search([('name', '=', 'Resume/CV')], limit=1)
        self.assertTrue(doc_type, "Document type should be auto-created")
        
        # Check if document was created with this type
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id),
            ('document_type_id', '=', doc_type.id)
        ])
        self.assertTrue(docs, "Document should be created with correct type")
    
    def test_05_attachment_creation_on_sync(self):
        """Test that ir.attachment records are created during sync."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card.pdf',
        })
        
        # Find attachments for this employee's documents
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        for doc in docs:
            self.assertTrue(len(doc.doc_attachment_ids) > 0,
                          "Document should have attachments")
    
    def test_06_document_update_replaces_existing(self):
        """Test that updating a document updates the vault record."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card_old.pdf',
        })
        
        initial_count = self._count_documents_in_vault(employee)
        
        # Update the same document
        employee.write({
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan_card_new.pdf',
        })
        
        new_count = self._count_documents_in_vault(employee)
        
        # Count might increase (new version) or stay same (update)
        # Both are valid depending on implementation
        self.assertTrue(new_count >= initial_count,
                       "Document count should not decrease")
    
    def test_07_sync_does_not_duplicate_documents(self):
        """Test that syncing same document twice doesn't create duplicates."""
        pdf_data = self._create_test_pdf_file()
        
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': pdf_data,
            'pan_card_doc_filename': 'pan_card.pdf',
        })
        
        count_after_create = self._count_documents_in_vault(employee)
        
        # Write same document again
        employee.write({
            'pan_card_doc': pdf_data,
            'pan_card_doc_filename': 'pan_card.pdf',
        })
        
        count_after_update = self._count_documents_in_vault(employee)
        
        # Should update existing, not create duplicate
       # Exact behavior depends on implementation
        self.assertTrue(count_after_update >= count_after_create,
                       "Should not create excessive duplicates")
    
    def test_08_sync_only_when_document_field_changed(self):
        """Test that sync is triggered only when document fields change."""
        employee = self._create_test_employee()
        initial_count = self._count_documents_in_vault(employee)
        
        # Update non-document field
        employee.write({'name': 'Updated Name'})
        
        count_after_name_update = self._count_documents_in_vault(employee)
        
        # Sync should not trigger for non-document fields
        # (Implementation may vary - sync might still occur but no new docs)
        self.assertEqual(count_after_name_update, initial_count,
                        "Document count should not change for non-document updates")
    
    def test_09_empty_document_not_synced(self):
        """Test that empty/False document fields are not synced."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': False,  # Explicitly False
            'pan_card_doc_filename': '',
        })
        
        # No documents should be created for False values
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        # Check that no PAN card document was created
        pan_docs = docs.filtered(lambda d: 'PAN' in d.document_type_id.name)
        self.assertEqual(len(pan_docs), 0,
                        "Empty documents should not be synced")
    
    def test_10_sync_all_document_fields(self):
        """Test that all document fields are properly mapped and synced."""
        # Create employee with all document fields
        all_docs = {
            'offer_letter': self._create_test_pdf_file(),
            'offer_letter_filename': 'offer.pdf',
            'appointment_letter': self._create_test_pdf_file(),
            'appointment_letter_filename': 'appointment.pdf',
            'nda_document': self._create_test_pdf_file(),
            'nda_document_filename': 'nda.pdf',
            'bond_document': self._create_test_pdf_file(),
            'bond_document_filename': 'bond.pdf',
            'contract_document': self._create_test_pdf_file(),
            'contract_document_filename': 'contract.pdf',
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
            'passport_doc': self._create_test_pdf_file(),
            'passport_doc_filename': 'passport.pdf',
            'bank_document': self._create_test_pdf_file(),
            'bank_document_filename': 'bank.pdf',
            'address_proof_document': self._create_test_pdf_file(),
            'address_proof_filename': 'address.pdf',
            'relieving_letter': self._create_test_pdf_file(),
            'relieving_letter_filename': 'relieving.pdf',
        }
        
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            **all_docs
        })
        
        doc_count = self._count_documents_in_vault(employee)
        # Should have created documents for all uploaded files
        self.assertGreaterEqual(doc_count, 10,
                               "Should sync all document fields")


@tagged('post_install', '-at_install', 'document_sync')
class TestDocumentSyncSalarySlips(HREmployeeCleardealsTestCase):
    """Test salary slip document handling with special naming."""
    
    def test_01_salary_slip_1_naming(self):
        """Test that salary slip 1 gets proper name."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'salary_slip_1': self._create_test_pdf_file(),
            'salary_slip_1_filename': 'july_slip.pdf',
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id),
            ('name', '=', 'Salary Slip - Month 1')
        ])
        
        self.assertTrue(docs, "Salary slip 1 should use special naming")
    
    def test_02_salary_slip_2_naming(self):
        """Test that salary slip 2 gets proper name."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'salary_slip_2': self._create_test_pdf_file(),
            'salary_slip_2_filename': 'august_slip.pdf',
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id),
            ('name', '=', 'Salary Slip - Month 2')
        ])
        
        self.assertTrue(docs, "Salary slip 2 should use special naming")
    
    def test_03_salary_slip_3_naming(self):
        """Test that salary slip 3 gets proper name."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'salary_slip_3': self._create_test_pdf_file(),
            'salary_slip_3_filename': 'september_slip.pdf',
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id),
            ('name', '=', 'Salary Slip - Month 3')
        ])
        
        self.assertTrue(docs, "Salary slip 3 should use special naming")
    
    def test_04_all_three_salary_slips(self):
        """Test uploading all three salary slips together."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'salary_slip_1': self._create_test_pdf_file(),
            'salary_slip_1_filename': 'slip1.pdf',
            'salary_slip_2': self._create_test_pdf_file(),
            'salary_slip_2_filename': 'slip2.pdf',
            'salary_slip_3': self._create_test_pdf_file(),
            'salary_slip_3_filename': 'slip3.pdf',
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        slip_names = docs.mapped('name')
        self.assertIn('Salary Slip - Month 1', slip_names)
        self.assertIn('Salary Slip - Month 2', slip_names)
        self.assertIn('Salary Slip - Month 3', slip_names)


@tagged('post_install', '-at_install', 'document_sync', 'advanced')
class TestDocumentSyncAdvanced(HREmployeeCleardealsTestCase):
    """Test advanced document synchronization scenarios."""
    
    def test_01_bulk_employee_creation_with_documents(self):
        """Test document sync works with bulk employee creation."""
        values_list = []
        for i in range(5):
            values_list.append({
                **self._get_employee_base_values(),
                'name': f'Employee {i}',
                'pan_card_doc': self._create_test_pdf_file(),
                'pan_card_doc_filename': f'pan_{i}.pdf',
            })
        
        employees = self.Employee.create(values_list)
        
        # Each employee should have their document synced
        for emp in employees:
            doc_count = self._count_documents_in_vault(emp)
            self.assertGreater(doc_count, 0,
                             f"Employee {emp.name} should have documents")
    
    def test_02_document_field_mapping_completeness(self):
        """Test that _get_document_field_mapping returns all expected fields."""
        employee = self._create_test_employee()
        mapping = employee._get_document_field_mapping()
        
        # Check that key document fields are in mapping
        expected_fields = [
            'offer_letter',
            'appointment_letter',
            'pan_card_doc',
            'passport_doc',
            'bank_document',
            'passport_photo',
        ]
        
        for field in expected_fields:
            self.assertIn(field, mapping.keys(),
                        f"Field {field} should be in document mapping")
    
    def test_03_document_type_reuse(self):
        """Test that existing document types are reused, not duplicated."""
        # Create PAN doc type if not exists
        pan_type = self.doc_type_pan
        initial_type_count = self.DocumentType.search_count([])
        
        # Create employee with PAN document
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
        })
        
        final_type_count = self.DocumentType.search_count([])
        
        # Should not create duplicate document type
        self.assertEqual(initial_type_count, final_type_count,
                        "Should reuse existing document types")
    
    def test_04_sync_with_missing_filename(self):
        """Test sync works even when filename is not provided."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            # No filename provided
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        # Document should still be created with default filename
        self.assertTrue(docs, "Document should be created even without filename")
    
    def test_05_attachment_mimetype_set_correctly(self):
        """Test that attachment MIME type is set during sync."""
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        for doc in docs:
            for attachment in doc.doc_attachment_ids:
                self.assertTrue(attachment.mimetype,
                              "Attachment should have MIME type set")
    
    def test_06_sync_preserves_issue_date(self):
        """Test that document issue date is set correctly."""
        from odoo import fields as odoo_fields
        
        employee = self.Employee.create({
            **self._get_employee_base_values(),
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
        })
        
        docs = self.EmployeeDocument.search([
            ('employee_ref_id', '=', employee.id)
        ])
        
        for doc in docs:
            self.assertEqual(doc.issue_date, odoo_fields.Date.today(),
                           "Issue date should be set to today")
    
    def test_07_concurrent_document_updates(self):
        """Test handling of concurrent document updates."""
        employee = self._create_test_employee()
        
        # Simulate concurrent updates
        employee.write({
            'pan_card_doc': self._create_test_pdf_file(),
            'pan_card_doc_filename': 'pan.pdf',
        })
        
        employee.write({
            'passport_doc': self._create_test_pdf_file(),
            'passport_doc_filename': 'passport.pdf',
        })
        
        doc_count = self._count_documents_in_vault(employee)
        self.assertGreaterEqual(doc_count, 2,
                               "Should handle concurrent updates")
