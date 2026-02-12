# -*- coding: utf-8 -*-
"""
Employee API Controller

Endpoints for employee management and document access.
"""
import logging
import base64
import json

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

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
                'personal_email': employee.private_email,
                'personal_phone': employee.private_phone,
                'emergency_contact_name': employee.emergency_contact,
                'emergency_contact_phone': employee.emergency_phone,
                'emergency_contact_relationship': employee.emergency_contact_relationship,
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
    
    # ========================================================================
    # ACTIVE EMPLOYEES LIST
    # ========================================================================
    
    @http.route('/api/v1/employees/active', 
                type='http', auth='public', methods=['GET'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def list_active_employees(self, **kwargs):
        """
        List all active employees with optional filtering.
        
        Endpoint: GET /api/v1/employees/active
        
        Query Parameters:
            department (str): Filter by department name (optional)
            search (str): Search by name or employee_id (optional)
            page (int): Page number (default: 1)
            per_page (int): Records per page (default: 20, max: 100)
            fields (str): Comma-separated list of field groups to include (optional)
                          Options: basic, contact, banking, documents, assets, address, statutory
                          Default: basic
        
        Headers:
            X-API-Key: Your API key
        
        Response Format:
            {
                "success": true,
                "message": "Active employees retrieved successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "employees": [
                        {
                            "id": 1,
                            "employee_id": "CD-0001",
                            "name": "John Doe",
                            "work_email": "john@company.com",
                            "department": "Engineering",
                            "job_title": "Senior Developer",
                            "employee_status": "active",
                            "date_of_joining": "2025-01-15",
                            "contact": {...},  // if fields=contact
                            "banking": {...},  // if fields=banking
                            ...
                        }
                    ],
                    "total_count": 50
                },
                "meta": {
                    "pagination": {...}
                }
            }
        
        Error Responses:
            401: Invalid API key
            400: Invalid parameters
        """
        # Parse parameters
        department = kwargs.get('department')
        search = kwargs.get('search')
        page = int(kwargs.get('page', 1))
        per_page = min(int(kwargs.get('per_page', 20)), 100)
        fields_param = kwargs.get('fields', 'basic')
        requested_fields = [f.strip() for f in fields_param.split(',')]
        
        # Build search domain - ONLY active employees
        domain = [('employee_status', '=', 'active')]
        
        if department:
            domain.append(('department_id.name', 'ilike', department))
        
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
        
        # Format response with optional additional fields
        employees_data = []
        for emp in paginated:
            emp_data = {
                'id': emp.id,
                'employee_id': emp.employee_id,
                'name': emp.name,
                'work_email': emp.work_email,
                'department': emp.department_id.name if emp.department_id else None,
                'job_title': emp.job_id.name if emp.job_id else None,
                'employee_status': emp.employee_status,
                'date_of_joining': emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else None,
            }
            
            # Add optional field groups based on request
            if 'contact' in requested_fields:
                emp_data['contact'] = {
                    'work_phone': emp.work_phone,
                    'personal_email': emp.private_email,
                    'personal_phone': emp.private_phone,
                    'emergency_contact_name': emp.emergency_contact,
                    'emergency_contact_phone': emp.emergency_phone,
                    'emergency_contact_relationship': emp.emergency_contact_relationship,
                }
            
            if 'banking' in requested_fields:
                emp_data['banking'] = {
                    'bank_account_number': emp.bank_acc_number,
                    'ifsc_code': emp.ifsc_code,
                    'account_type': emp.account_type,
                    'uan_number': emp.uan_number,
                    'esic_number': emp.esic_number,
                }
            
            if 'address' in requested_fields:
                emp_data['address'] = {
                    'permanent': {
                        'address': emp.permanent_address,
                        'state': emp.permanent_state_id.name if emp.permanent_state_id else None,
                        'country': emp.permanent_country_id.name if emp.permanent_country_id else None,
                        'pincode': emp.permanent_pincode,
                    },
                    'current': {
                        'address': emp.current_address,
                        'state': emp.current_state_id.name if emp.current_state_id else None,
                        'country': emp.current_country_id.name if emp.current_country_id else None,
                        'pincode': emp.current_pincode,
                    }
                }
            
            if 'assets' in requested_fields:
                emp_data['assets'] = {
                    'laptop_brand': emp.laptop_brand,
                    'laptop_serial_number': emp.laptop_serial_number,
                    'laptop_model': emp.laptop_model,
                    'ram': emp.ram,
                    'storage': emp.storage,
                    'processor': emp.processor,
                }
            
            if 'documents' in requested_fields:
                doc_count = request.env['hr.employee.document'].sudo().search_count([
                    ('employee_ref_id', '=', emp.id)
                ])
                emp_data['documents'] = {
                    'total_documents': doc_count,
                    'documents_url': f'/api/v1/employees/{emp.employee_id}/documents'
                }
            
            if 'statutory' in requested_fields:
                emp_data['statutory'] = {
                    'aadhaar_number': emp.identification_id,
                    'pan_number': emp.pan_number,
                }
            
            employees_data.append(emp_data)
        
        return api_response(
            success=True,
            message='Active employees retrieved successfully',
            data={
                'employees': employees_data,
                'total_count': len(employees)
            },
            meta=meta
        )
    
    # ========================================================================
    # EMPLOYEE CREATION
    # ========================================================================
    
    @http.route('/api/v1/employees', 
                type='http', auth='public', methods=['POST'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def create_employee(self, **kwargs):
        """
        Create a new employee record.
        
        Endpoint: POST /api/v1/employees
        Content-Type: application/json
        
        Headers:
            X-API-Key: Your API key
            OR
            Authorization: Bearer <your_api_key>
        
        Request Body (JSON):
            {
                "name": "John Doe",  // REQUIRED
                "work_email": "john.doe@company.com",  // OPTIONAL but recommended
                "work_phone": "+91-9876543210",
                "mobile_phone": "+91-9876543210",
                "job_title": "Software Engineer",
                "department_id": 1,  // Department ID
                "job_id": 5,  // Job Position ID
                "date_of_joining": "2026-02-15",
                "employee_status": "onboarding",  // onboarding/active/notice/resigned/terminated
                
                // Personal Information
                "legal_name": "John Michael Doe",
                "sex": "male",  // male/female/other
                "marital": "single",  // single/married/cohabitant/widower/divorced
                "birthday": "1995-05-15",
                "private_phone": "+91-9988776655",
                "private_email": "john.personal@gmail.com",
                "blood_group": "o+",  // a+/a-/b+/b-/ab+/ab-/o+/o-
                
                // Address
                "private_street": "123 Main Street",
                "private_street2": "Apartment 4B",
                "private_city": "Mumbai",
                "private_state_id": 21,  // State ID
                "private_zip": "400001",
                "private_country_id": 104,  // Country ID (104 = India)
                "current_address": "456 Work Street, Mumbai",
                "same_as_permanent": false,
                
                // Emergency Contact
                "emergency_contact": "Jane Doe",
                "emergency_phone": "+91-9123456789",
                "emergency_contact_relationship": "Spouse",
                
                // Identity Documents
                "identification_id": "123456789012",  // Aadhaar (12 digits)
                "pan_number": "ABCDE1234F",  // PAN format: 5 letters + 4 digits + 1 letter
                
                // Bank Details
                "bank_name": "HDFC Bank",
                "bank_acc_number": "12345678901234",
                "ifsc_code": "HDFC0001234",
                "account_type": "savings",  // savings/current/salary
                "name_as_per_bank": "John Michael Doe",
                "bank_document_type": "cancelled_cheque",  // cancelled_cheque/passbook_copy
                
                // Education & Skills
                "education_background": "B.Tech in Computer Science from IIT Mumbai",
                "skill_set_summary": "Python, JavaScript, React, Node.js",
                
                // Assets (boolean)
                "asset_laptop": true,
                "asset_sim": true,
                "asset_phone": false,
                "asset_pc": false,
                "asset_physical_id": true
            }
        
        Response Format:
            {
                "success": true,
                "message": "Employee created successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "id": 15,
                    "employee_id": "CD-0015",
                    "name": "John Doe",
                    "work_email": "john.doe@company.com",
                    "employee_status": "onboarding",
                    "date_of_joining": "2026-02-15",
                    "department": "Engineering",
                    "job_title": "Software Engineer",
                    "created_date": "2026-02-11"
                }
            }
        
        Error Responses:
            400: Missing required fields or validation errors
            422: Invalid field values (e.g., wrong PAN format, invalid Aadhaar)
        
        Notes:
            - Employee ID (CD-XXXX) is auto-generated
            - Only 'name' field is required
            - PAN number is auto-converted to uppercase
            - Aadhaar must be exactly 12 digits
            - PAN must follow format: ABCDE1234F
            - Document binary fields should be uploaded separately via document upload endpoints
        """
        # Parse JSON from request body
        try:
            params = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, AttributeError):
            return api_response(
                success=False,
                message='Invalid JSON in request body',
                errors={'json': 'Request body must be valid JSON'},
                status=400
            )
        
        # Validate required fields
        if not params.get('name'):
            return api_response(
                success=False,
                message='Validation Error',
                errors={'name': 'Employee name is required'},
                status=400
            )
        
        # Prepare employee data
        employee_data = {}
        
        # ========== BASIC INFORMATION ==========
        # Required field
        employee_data['name'] = params.get('name').strip()
        
        # Work contact information
        if params.get('work_email'):
            employee_data['work_email'] = params.get('work_email').strip()
        if params.get('work_phone'):
            employee_data['work_phone'] = params.get('work_phone')
        if params.get('mobile_phone'):
            employee_data['mobile_phone'] = params.get('mobile_phone')
        
        # Job information
        if params.get('job_title'):
            employee_data['job_title'] = params.get('job_title')
        if params.get('department_id'):
            employee_data['department_id'] = params.get('department_id')
        if params.get('job_id'):
            employee_data['job_id'] = params.get('job_id')
        
        # Employment details
        if params.get('date_of_joining'):
            employee_data['date_of_joining'] = params.get('date_of_joining')
        if params.get('employee_status'):
            employee_data['employee_status'] = params.get('employee_status')
        
        # ========== PERSONAL INFORMATION ==========
        if params.get('legal_name'):
            employee_data['legal_name'] = params.get('legal_name')
        if params.get('sex'):
            employee_data['sex'] = params.get('sex')
        if params.get('marital'):
            employee_data['marital'] = params.get('marital')
        if params.get('birthday'):
            employee_data['birthday'] = params.get('birthday')
        if params.get('private_phone'):
            employee_data['private_phone'] = params.get('private_phone')
        if params.get('private_email'):
            employee_data['private_email'] = params.get('private_email')
        if params.get('blood_group'):
            employee_data['blood_group'] = params.get('blood_group')
        
        # ========== ADDRESS ==========
        if params.get('private_street'):
            employee_data['private_street'] = params.get('private_street')
        if params.get('private_street2'):
            employee_data['private_street2'] = params.get('private_street2')
        if params.get('private_city'):
            employee_data['private_city'] = params.get('private_city')
        if params.get('private_state_id'):
            employee_data['private_state_id'] = params.get('private_state_id')
        if params.get('private_zip'):
            employee_data['private_zip'] = params.get('private_zip')
        if params.get('private_country_id'):
            employee_data['private_country_id'] = params.get('private_country_id')
        if params.get('current_address'):
            employee_data['current_address'] = params.get('current_address')
        if params.get('same_as_permanent') is not None:
            employee_data['same_as_permanent'] = params.get('same_as_permanent')
        
        # ========== EMERGENCY CONTACT ==========
        if params.get('emergency_contact'):
            employee_data['emergency_contact'] = params.get('emergency_contact')
        if params.get('emergency_phone'):
            employee_data['emergency_phone'] = params.get('emergency_phone')
        if params.get('emergency_contact_relationship'):
            employee_data['emergency_contact_relationship'] = params.get('emergency_contact_relationship')
        
        # ========== IDENTITY DOCUMENTS ==========
        if params.get('identification_id'):
            employee_data['identification_id'] = params.get('identification_id')
        if params.get('pan_number'):
            # PAN will be auto-converted to uppercase in model's create method
            employee_data['pan_number'] = params.get('pan_number')
        
        # ========== BANK DETAILS ==========
        if params.get('bank_name'):
            employee_data['bank_name'] = params.get('bank_name')
        if params.get('bank_acc_number'):
            employee_data['bank_acc_number'] = params.get('bank_acc_number')
        if params.get('ifsc_code'):
            employee_data['ifsc_code'] = params.get('ifsc_code')
        if params.get('account_type'):
            employee_data['account_type'] = params.get('account_type')
        if params.get('name_as_per_bank'):
            employee_data['name_as_per_bank'] = params.get('name_as_per_bank')
        if params.get('cibil_score'):
            employee_data['cibil_score'] = params.get('cibil_score')
        if params.get('bank_document_type'):
            employee_data['bank_document_type'] = params.get('bank_document_type')
        
        # ========== EDUCATION & SKILLS ==========
        if params.get('education_background'):
            employee_data['education_background'] = params.get('education_background')
        if params.get('skill_set_summary'):
            employee_data['skill_set_summary'] = params.get('skill_set_summary')
        
        # ========== ASSETS ==========
        if params.get('asset_laptop') is not None:
            employee_data['asset_laptop'] = params.get('asset_laptop')
        if params.get('asset_sim') is not None:
            employee_data['asset_sim'] = params.get('asset_sim')
        if params.get('asset_phone') is not None:
            employee_data['asset_phone'] = params.get('asset_phone')
        if params.get('asset_pc') is not None:
            employee_data['asset_pc'] = params.get('asset_pc')
        if params.get('asset_physical_id') is not None:
            employee_data['asset_physical_id'] = params.get('asset_physical_id')
        
        # Create the employee record
        try:
            employee = request.env['hr.employee'].sudo().create(employee_data)
            
            # Prepare response data
            response_data = {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.name,
                'work_email': employee.work_email or None,
                'employee_status': employee.employee_status,
                'date_of_joining': employee.date_of_joining.strftime('%Y-%m-%d') if employee.date_of_joining else None,
                'department': employee.department_id.name if employee.department_id else None,
                'department_id': employee.department_id.id if employee.department_id else None,
                'job_title': employee.job_title or None,
                'job_id': employee.job_id.id if employee.job_id else None,
                'created_date': employee.create_date.strftime('%Y-%m-%d') if employee.create_date else None,
            }
            
            return api_response(
                success=True,
                message='Employee created successfully',
                data=response_data,
                status=201
            )
            
        except ValidationError as e:
            return api_response(
                success=False,
                message='Validation Error',
                errors={'validation': str(e)},
                status=422
            )
        except Exception as e:
            _logger.exception("Error creating employee")
            return api_response(
                success=False,
                message='Failed to create employee',
                errors={'error': str(e)},
                status=500
            )
