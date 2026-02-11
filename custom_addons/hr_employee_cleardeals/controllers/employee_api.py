# -*- coding: utf-8 -*-
"""
Employee API Controller

Endpoints for employee management and document access.
"""
import logging
import base64

from odoo import http
from odoo.http import request

from .main import (
    BaseAPIController, 
    validate_api_key, 
    handle_api_errors,
    api_response,
    paginate_response
)

_logger = logging.getLogger(__name__)


class EmployeeAPIController(BaseAPIController):
    """
    API endpoints for employee operations.
    
    Base URL: /api/v1/employees
    """
    
    # ========================================================================
    # EMPLOYEE DOCUMENTS
    # ========================================================================
    
    @http.route('/api/v1/employees/<string:employee_id>/documents', 
                type='http', auth='public', methods=['GET'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def get_employee_documents(self, employee_id, **kwargs):
        """
        Fetch all documents for a specific employee by Employee ID.
        
        Endpoint: GET /api/v1/employees/<employee_id>/documents
        
        Path Parameters:
            employee_id (str): Employee ID (e.g., CD-0001)
        
        Query Parameters:
            document_type (str): Filter by document type name (optional)
            include_binary (bool): Include base64 file data (default: false)
            page (int): Page number for pagination (default: 1)
            per_page (int): Records per page (default: 20, max: 100)
        
        Headers:
            X-API-Key: Your API key
            OR
            Authorization: Bearer <your_api_key>
        
        Response Format:
            {
                "success": true,
                "message": "Documents retrieved successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "employee": {
                        "id": 1,
                        "employee_id": "CD-0001",
                        "name": "John Doe",
                        "work_email": "john@company.com"
                    },
                    "documents": [
                        {
                            "id": 1,
                            "document_name": "PAN Card - CD-0001",
                            "document_type": "PAN Card",
                            "file_name": "pan.pdf",
                            "file_size": 102400,
                            "mimetype": "application/pdf",
                            "uploaded_date": "2026-01-15",
                            "expiry_date": null,
                            "is_expired": false,
                            "file_data": "base64_encoded_data..."  // if include_binary=true
                        }
                    ]
                },
                "meta": {
                    "pagination": {
                        "current_page": 1,
                        "per_page": 20,
                        "total_records": 5,
                        "total_pages": 1,
                        "has_next": false,
                        "has_prev": false
                    }
                }
            }
        
        Error Responses:
            404: Employee not found
            403: Access denied
            401: Invalid API key
            400: Invalid parameters
        """
        # Parse query parameters
        document_type = kwargs.get('document_type')
        include_binary = kwargs.get('include_binary', 'false').lower() == 'true'
        page = int(kwargs.get('page', 1))
        per_page = min(int(kwargs.get('per_page', 20)), 100)  # Max 100 per page
        
        # Find employee by employee_id
        employee = request.env['hr.employee'].sudo().search([
            ('employee_id', '=', employee_id)
        ], limit=1)
        
        if not employee:
            return api_response(
                success=False,
                message=f'Employee with ID {employee_id} not found',
                status=404
            )
        
        # Build domain for document search
        domain = [('employee_ref_id', '=', employee.id)]
        
        if document_type:
            domain.append(('document_type_id.name', 'ilike', document_type))
        
        # Fetch documents
        documents = request.env['hr.employee.document'].sudo().search(
            domain,
            order='create_date desc'
        )
        
        # Paginate results
        paginated_docs, meta = paginate_response(documents, page, per_page)
        
        # Format response data
        employee_data = {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.name,
            'work_email': employee.work_email,
            'department': employee.department_id.name if employee.department_id else None,
            'job_title': employee.job_id.name if employee.job_id else None,
            'employee_status': employee.employee_status,
        }
        
        documents_data = []
        for doc in paginated_docs:
            # Get first attachment if available
            attachment = doc.doc_attachment_ids[0] if doc.doc_attachment_ids else None
            
            # Calculate expiry status
            is_expired = False
            is_expiring_soon = False
            if doc.expiry_date:
                from datetime import datetime, timedelta
                today = datetime.now().date()
                expiry = doc.expiry_date
                is_expired = expiry < today
                is_expiring_soon = (expiry - today).days <= 30 and not is_expired
            
            doc_data = {
                'id': doc.id,
                'document_name': doc.name,
                'document_type': doc.document_type_id.name if doc.document_type_id else None,
                'file_name': attachment.name if attachment else None,
                'file_size': len(base64.b64decode(attachment.datas)) if attachment and attachment.datas else 0,
                'mimetype': attachment.mimetype if attachment else None,
                'uploaded_date': doc.issue_date.strftime('%Y-%m-%d') if doc.issue_date else None,
                'expiry_date': doc.expiry_date.strftime('%Y-%m-%d') if doc.expiry_date else None,
                'is_expired': is_expired,
                'is_expiring_soon': is_expiring_soon,
                'description': doc.description or '',
            }
            
            # Include binary data if requested
            if include_binary and attachment and attachment.datas:
                doc_data['file_data'] = attachment.datas.decode('utf-8') if isinstance(attachment.datas, bytes) else attachment.datas
            
            documents_data.append(doc_data)
        
        return api_response(
            success=True,
            message='Documents retrieved successfully',
            data={
                'employee': employee_data,
                'documents': documents_data,
                'document_count': len(documents)
            },
            meta=meta
        )
    
    # ========================================================================
    # SINGLE DOCUMENT DOWNLOAD
    # ========================================================================
    
    @http.route('/api/v1/employees/<string:employee_id>/documents/<int:document_id>/download', 
                type='http', auth='public', methods=['GET'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def download_employee_document(self, employee_id, document_id, **kwargs):
        """
        Download a specific document file.
        
        Endpoint: GET /api/v1/employees/<employee_id>/documents/<document_id>/download
        
        Path Parameters:
            employee_id (str): Employee ID (e.g., CD-0001)
            document_id (int): Document record ID
        
        Headers:
            X-API-Key: Your API key
        
        Response:
            Binary file download with appropriate content-type header
        """
        # Find employee
        employee = request.env['hr.employee'].sudo().search([
            ('employee_id', '=', employee_id)
        ], limit=1)
        
        if not employee:
            return api_response(
                success=False,
                message=f'Employee with ID {employee_id} not found',
                status=404
            )
        
        # Find document
        document = request.env['hr.employee.document'].sudo().search([
            ('id', '=', document_id),
            ('employee_ref_id', '=', employee.id)
        ], limit=1)
        
        if not document:
            return api_response(
                success=False,
                message=f'Document {document_id} not found for employee {employee_id}',
                status=404
            )
        
        # Get first attachment
        attachment = document.doc_attachment_ids[0] if document.doc_attachment_ids else None
        
        if not attachment or not attachment.datas:
            return api_response(
                success=False,
                message='Document file data not available',
                status=404
            )
        
        # Decode base64 file data
        file_content = base64.b64decode(attachment.datas)
        
        # Return file as download
        headers = [
            ('Content-Type', attachment.mimetype or 'application/octet-stream'),
            ('Content-Disposition', f'attachment; filename="{attachment.name}"'),
            ('Content-Length', len(file_content))
        ]
        
        return request.make_response(file_content, headers)
    
    # ========================================================================
    # EMPLOYEE DETAILS
    # ========================================================================
    
    @http.route('/api/v1/employees/<string:employee_id>', 
                type='http', auth='public', methods=['GET'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def get_employee_details(self, employee_id, **kwargs):
        """
        Get detailed information about an employee.
        
        Endpoint: GET /api/v1/employees/<employee_id>
        
        Path Parameters:
            employee_id (str): Employee ID (e.g., CD-0001)
        
        Query Parameters:
            fields (str): Comma-separated list of field groups to include
                          Options: basic, contact, banking, documents, assets, address
                          Default: basic,contact
        
        Headers:
            X-API-Key: Your API key
        
        Response:
            {
                "success": true,
                "message": "Employee details retrieved successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "basic": { ... },
                    "contact": { ... },
                    "banking": { ... },
                    ...
                }
            }
        """
        # Parse fields parameter
        fields_param = kwargs.get('fields', 'basic,contact')
        requested_fields = [f.strip() for f in fields_param.split(',')]
        
        # Find employee
        employee = request.env['hr.employee'].sudo().search([
            ('employee_id', '=', employee_id)
        ], limit=1)
        
        if not employee:
            return api_response(
                success=False,
                message=f'Employee with ID {employee_id} not found',
                status=404
            )
        
        response_data = {}
        
        # Basic information
        if 'basic' in requested_fields:
            response_data['basic'] = {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.name,
                'legal_name': employee.legal_name,
                'date_of_birth': employee.birthday.strftime('%Y-%m-%d') if employee.birthday else None,
                'gender': employee.gender,
                'marital_status': employee.marital,
                'blood_group': employee.blood_group,
                'date_of_joining': employee.date_of_joining.strftime('%Y-%m-%d') if employee.date_of_joining else None,
                'employee_status': employee.employee_status,
                'department': employee.department_id.name if employee.department_id else None,
                'job_title': employee.job_id.name if employee.job_id else None,
            }
        
        # Contact information
        if 'contact' in requested_fields:
            response_data['contact'] = {
                'work_email': employee.work_email,
                'work_phone': employee.work_phone,
                'personal_email': employee.personal_email,
                'personal_phone': employee.personal_phone,
                'emergency_contact_name': employee.emergency_contact,
                'emergency_contact_phone': employee.emergency_phone,
            }
        
        # Banking information
        if 'banking' in requested_fields:
            response_data['banking'] = {
                'bank_account_number': employee.bank_acc_number,
                'ifsc_code': employee.ifsc_code,
                'account_type': employee.account_type,
                'uan_number': employee.uan_number,
                'esic_number': employee.esic_number,
                'cibil_score': employee.cibil_score,
            }
        
        # Address information
        if 'address' in requested_fields:
            response_data['address'] = {
                'permanent': {
                    'address': employee.permanent_address,
                    'state': employee.permanent_state_id.name if employee.permanent_state_id else None,
                    'country': employee.permanent_country_id.name if employee.permanent_country_id else None,
                    'pincode': employee.permanent_pincode,
                },
                'current': {
                    'address': employee.current_address,
                    'state': employee.current_state_id.name if employee.current_state_id else None,
                    'country': employee.current_country_id.name if employee.current_country_id else None,
                    'pincode': employee.current_pincode,
                    'same_as_permanent': employee.same_as_permanent_address,
                }
            }
        
        # Asset information
        if 'assets' in requested_fields:
            response_data['assets'] = {
                'laptop_brand': employee.laptop_brand,
                'laptop_serial_number': employee.laptop_serial_number,
                'laptop_model': employee.laptop_model,
                'ram': employee.ram,
                'storage': employee.storage,
                'processor': employee.processor,
                'laptop_allocation_date': employee.laptop_allocation_date.strftime('%Y-%m-%d') if employee.laptop_allocation_date else None,
            }
        
        # Document summary
        if 'documents' in requested_fields:
            doc_count = request.env['hr.employee.document'].sudo().search_count([
                ('employee_ref_id', '=', employee.id)
            ])
            response_data['documents'] = {
                'total_documents': doc_count,
                'documents_url': f'/api/v1/employees/{employee_id}/documents'
            }
        
        # Statutory information
        if 'statutory' in requested_fields:
            response_data['statutory'] = {
                'aadhaar_number': employee.identification_id,
                'pan_number': employee.pan_number,
            }
        
        return api_response(
            success=True,
            message='Employee details retrieved successfully',
            data=response_data
        )
    
    # ========================================================================
    # EMPLOYEE LIST
    # ========================================================================
    
    @http.route('/api/v1/employees', 
                type='http', auth='public', methods=['GET'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def list_employees(self, **kwargs):
        """
        List all employees with optional filtering.
        
        Endpoint: GET /api/v1/employees
        
        Query Parameters:
            department (str): Filter by department name
            status (str): Filter by employee_status (onboarding, active, notice, resigned, terminated)
            search (str): Search by name or employee_id
            page (int): Page number (default: 1)
            per_page (int): Records per page (default: 20, max: 100)
        
        Headers:
            X-API-Key: Your API key
        
        Response:
            List of employees with pagination metadata
        """
        # Parse parameters
        department = kwargs.get('department')
        status = kwargs.get('status')
        search = kwargs.get('search')
        page = int(kwargs.get('page', 1))
        per_page = min(int(kwargs.get('per_page', 20)), 100)
        
        # Build search domain
        domain = []
        
        if department:
            domain.append(('department_id.name', 'ilike', department))
        
        if status:
            domain.append(('employee_status', '=', status))
        
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('employee_id', 'ilike', search))
        
        # Search employees
        employees = request.env['hr.employee'].sudo().search(
            domain,
            order='employee_id asc'
        )
        
        # Paginate
        paginated, meta = paginate_response(employees, page, per_page)
        
        # Format response
        employees_data = []
        for emp in paginated:
            employees_data.append({
                'id': emp.id,
                'employee_id': emp.employee_id,
                'name': emp.name,
                'work_email': emp.work_email,
                'department': emp.department_id.name if emp.department_id else None,
                'job_title': emp.job_id.name if emp.job_id else None,
                'employee_status': emp.employee_status,
                'date_of_joining': emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else None,
            })
        
        return api_response(
            success=True,
            message='Employees retrieved successfully',
            data={
                'employees': employees_data,
                'total_count': len(employees)
            },
            meta=meta
        )
