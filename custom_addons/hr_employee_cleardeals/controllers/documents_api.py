"""
Documents Management API Controller

Endpoints for document tracking, compliance, and pending documents.
"""
import logging

from odoo import http
from odoo.http import request

from .main import (
    api_response,
    handle_api_errors,
    paginate_response,
    validate_api_key,
)

_logger = logging.getLogger(__name__)


class DocumentsAPIController(http.Controller):
    """
    API endpoints for document management and tracking.
    
    Base URL: /api/v1/documents
    """

    @http.route('/api/v1/employees/pending-documents',
                type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def get_employees_with_pending_documents(self, **kwargs):
        """
        Get list of employees with pending/missing documents.
        
        Endpoint: GET /api/v1/employees/pending-documents
        
        Query Parameters:
            employee_status (str): Filter by employee status (default: all)
                                   Options: onboarding, active, notice, resigned, terminated
            department (str): Filter by department name (optional)
            document_category (str): Filter by document category (optional)
                                     Options: onboarding, identity, bank, experience, all
            page (int): Page number (default: 1)
            per_page (int): Records per page (default: 20, max: 100)
            show_all_documents (bool): Show all document fields, not just missing (default: false)
        
        Headers:
            X-API-Key: Your API key
        
        Response Format:
            {
                "success": true,
                "message": "Employees with pending documents retrieved successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "employees": [
                        {
                            "id": 1,
                            "employee_id": "CD-0001",
                            "name": "John Doe",
                            "department": "Engineering",
                            "job_title": "Senior Developer",
                            "employee_status": "onboarding",
                            "date_of_joining": "2025-01-15",
                            "pending_documents": {
                                "onboarding": [
                                    {
                                        "field_name": "offer_letter",
                                        "document_name": "Offer Letter",
                                        "category": "onboarding",
                                        "is_uploaded": false,
                                        "is_required": true
                                    },
                                    {
                                        "field_name": "appointment_letter",
                                        "document_name": "Appointment Letter",
                                        "category": "onboarding",
                                        "is_uploaded": false,
                                        "is_required": true
                                    }
                                ],
                                "identity": [
                                    {
                                        "field_name": "pan_card_doc",
                                        "document_name": "PAN Card",
                                        "category": "identity",
                                        "is_uploaded": false,
                                        "is_required": true
                                    }
                                ]
                            },
                            "pending_count": 3,
                            "total_documents": 20,
                            "compliance_percentage": 85
                        }
                    ],
                    "summary": {
                        "total_employees": 1,
                        "total_pending_documents": 3,
                        "employees_with_pending": 1,
                        "compliance_rate": 85
                    }
                },
                "meta": {
                    "pagination": {...}
                }
            }
        
        Error Responses:
            401: Invalid API key
            400: Invalid parameters
        
        Use Cases:
            - HR compliance tracking and reporting
            - Onboarding document checklist monitoring
            - Audit trail for missing documents
            - Automated reminder systems for pending documents
            - Employee offboarding document collection
        """
        # Parse parameters
        employee_status = kwargs.get('employee_status')
        department = kwargs.get('department')
        document_category = kwargs.get('document_category', 'all')
        page = int(kwargs.get('page', 1))
        per_page = min(int(kwargs.get('per_page', 20)), 100)
        show_all_documents = kwargs.get('show_all_documents', 'false').lower() == 'true'

        # Build domain
        domain = []
        if employee_status:
            domain.append(('employee_status', '=', employee_status))
        if department:
            domain.append(('department_id.name', 'ilike', department))

        # Get all employees matching criteria
        employees = request.env['hr.employee'].sudo().search(
            domain,
            order='employee_id asc',
        )

        # Document field mapping with categories
        document_mapping = self._get_categorized_document_mapping()

        # Filter by document category if specified
        if document_category != 'all':
            if document_category in document_mapping:
                filtered_docs = {document_category: document_mapping[document_category]}
                document_mapping = filtered_docs
            else:
                document_mapping = {}

        # Process employees and check for pending documents
        employees_with_pending = []
        total_pending_count = 0

        for emp in employees:
            pending_docs = {}
            pending_count = 0
            total_docs = 0
            uploaded_docs = 0

            # Check each document category
            for category, docs in document_mapping.items():
                category_pending = []

                for field_name, doc_name in docs.items():
                    total_docs += 1
                    is_uploaded = bool(getattr(emp, field_name, None))

                    if is_uploaded:
                        uploaded_docs += 1

                    # Determine if document is required based on employee status
                    is_required = self._is_document_required(field_name, emp.employee_status)

                    # Add to pending list if not uploaded and (required or show_all_documents)
                    if not is_uploaded and (is_required or show_all_documents):
                        category_pending.append({
                            'field_name': field_name,
                            'document_name': doc_name,
                            'category': category,
                            'is_uploaded': is_uploaded,
                            'is_required': is_required,
                        })
                        pending_count += 1
                    elif show_all_documents:
                        category_pending.append({
                            'field_name': field_name,
                            'document_name': doc_name,
                            'category': category,
                            'is_uploaded': is_uploaded,
                            'is_required': is_required,
                        })

                if category_pending:
                    pending_docs[category] = category_pending

            # Only include employees with pending documents (or all if show_all_documents)
            if pending_count > 0 or show_all_documents:
                compliance_percentage = int(uploaded_docs / total_docs * 100) if total_docs > 0 else 100

                employees_with_pending.append({
                    'employee': emp,
                    'pending_docs': pending_docs,
                    'pending_count': pending_count,
                    'total_docs': total_docs,
                    'uploaded_docs': uploaded_docs,
                    'compliance_percentage': compliance_percentage,
                })
                total_pending_count += pending_count

        # Paginate results
        paginated, meta = paginate_response(employees_with_pending, page, per_page)

        # Format response
        employees_data = []
        for item in paginated:
            emp = item['employee']
            employees_data.append({
                'id': emp.id,
                'employee_id': emp.employee_id,
                'name': emp.name,
                'work_email': emp.work_email,
                'department': emp.department_id.name if emp.department_id else None,
                'job_title': emp.job_id.name if emp.job_id else None,
                'employee_status': emp.employee_status,
                'date_of_joining': emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else None,
                'pending_documents': item['pending_docs'],
                'pending_count': item['pending_count'],
                'total_documents': item['total_docs'],
                'uploaded_documents': item['uploaded_docs'],
                'compliance_percentage': item['compliance_percentage'],
            })

        # Calculate summary
        total_employees_with_pending = len(employees_with_pending)
        avg_compliance = int(sum([item['compliance_percentage'] for item in employees_with_pending]) / total_employees_with_pending) if total_employees_with_pending > 0 else 100

        return api_response(
            success=True,
            message='Employees with pending documents retrieved successfully',
            data={
                'employees': employees_data,
                'summary': {
                    'total_employees_checked': len(employees),
                    'employees_with_pending_documents': total_employees_with_pending,
                    'total_pending_documents': total_pending_count,
                    'average_compliance_rate': avg_compliance,
                },
            },
            meta=meta,
        )

    def _get_categorized_document_mapping(self):
        """
        Get document mapping organized by category.
        
        Returns:
            dict: {
                'category_name': {
                    'field_name': 'Document Name',
                    ...
                }
            }
        """
        return {
            'onboarding': {
                'offer_letter': 'Offer Letter',
                'appointment_letter': 'Appointment Letter',
                'nda_document': 'NDA',
                'bond_document': 'Bond Document',
                'contract_document': 'Employment Contract',
            },
            'identity': {
                'pan_card_doc': 'PAN Card',
                'passport_doc': 'Passport',
                'passport_photo': 'Passport Photo',
            },
            'bank': {
                'bank_document': 'Bank Document (Cancelled Cheque/Passbook)',
            },
            'address': {
                'address_proof_document': 'Address Proof',
            },
            'experience': {
                'relieving_letter': 'Relieving Letter',
                'experience_letter': 'Experience Letter',
                'salary_slip_1': 'Salary Slip - Month 1',
                'salary_slip_2': 'Salary Slip - Month 2',
                'salary_slip_3': 'Salary Slip - Month 3',
                'resume_doc': 'Resume/CV',
            },
            'lifecycle': {
                'appraisal_doc': 'Appraisal Document',
                'increment_letter': 'Increment Letter',
            },
        }

    def _is_document_required(self, field_name, employee_status):
        """
        Determine if a document is required based on employee status.
        
        Args:
            field_name (str): Document field name
            employee_status (str): Employee status (onboarding, active, etc.)
        
        Returns:
            bool: True if document is required, False otherwise
        """
        # Required documents for onboarding employees
        onboarding_required = [
            'offer_letter',
            'appointment_letter',
            'pan_card_doc',
            'bank_document',
            'passport_photo',
        ]

        # Required documents for all active employees
        active_required = [
            'pan_card_doc',
            'bank_document',
            'passport_photo',
        ]

        # Required documents for employees on notice/resigning
        notice_required = [
            'pan_card_doc',
        ]

        if employee_status == 'onboarding':
            return field_name in onboarding_required
        if employee_status == 'active':
            return field_name in active_required
        if employee_status in ['notice', 'resigned']:
            return field_name in notice_required
        return False
