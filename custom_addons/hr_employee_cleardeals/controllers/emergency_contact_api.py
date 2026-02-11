# -*- coding: utf-8 -*-
"""
Emergency Contact API Controller

Endpoint for employee emergency contact information retrieval.
"""
import logging

from odoo import http
from odoo.http import request

from .main import (
    validate_api_key, 
    handle_api_errors,
    api_response,
)

_logger = logging.getLogger(__name__)


class EmergencyContactAPIController(http.Controller):
    """
    API endpoints for emergency contact information.
    
    Base URL: /api/v1/employees/<employee_id>/emergency-contact
    """
    
    @http.route('/api/v1/employees/<string:employee_id>/emergency-contact', 
                type='http', auth='public', methods=['GET'], 
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def get_employee_emergency_contact(self, employee_id, **kwargs):
        """
        Get emergency contact information for a specific employee.
        
        Endpoint: GET /api/v1/employees/<employee_id>/emergency-contact
        
        Path Parameters:
            employee_id (str): Employee ID (e.g., CD-0001)
        
        Query Parameters:
            include_personal (bool): Include personal contact info (default: false)
            include_medical (bool): Include medical info like blood group (default: false)
        
        Headers:
            X-API-Key: Your API key
        
        Response Format:
            {
                "success": true,
                "message": "Emergency contact retrieved successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "employee": {
                        "id": 1,
                        "employee_id": "CD-0001",
                        "name": "John Doe",
                        "department": "Engineering",
                        "job_title": "Senior Developer"
                    },
                    "emergency_contact": {
                        "name": "Jane Doe",
                        "phone": "+91-9876543210",
                        "relationship": "Spouse"
                    },
                    "personal_contact": {  // if include_personal=true
                        "personal_phone": "+91-9876543211",
                        "personal_email": "john.doe@gmail.com",
                        "work_phone": "+91-9876543212",
                        "work_email": "john@company.com"
                    },
                    "medical_info": {  // if include_medical=true
                        "blood_group": "O+"
                    }
                }
            }
        
        Error Responses:
            404: Employee not found
            401: Invalid API key
        
        Use Cases:
            - Emergency alert systems
            - Medical emergency response
            - Safety and security applications
            - Compliance and regulatory reporting
        """
        # Parse parameters
        include_personal = kwargs.get('include_personal', 'false').lower() == 'true'
        include_medical = kwargs.get('include_medical', 'false').lower() == 'true'
        
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
        
        # Build response data
        response_data = {
            'employee': {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.name,
                'department': employee.department_id.name if employee.department_id else None,
                'job_title': employee.job_id.name if employee.job_id else None,
                'employee_status': employee.employee_status,
            },
            'emergency_contact': {
                'name': employee.emergency_contact,
                'phone': employee.emergency_phone,
                'relationship': employee.emergency_contact_relationship if hasattr(employee, 'emergency_contact_relationship') else None,
            }
        }
        
        # Include personal contact info if requested
        if include_personal:
            response_data['personal_contact'] = {
                'personal_phone': employee.private_phone,
                'personal_email': employee.private_email,
                'work_phone': employee.work_phone,
                'work_email': employee.work_email,
            }
        
        # Include medical info if requested
        if include_medical:
            response_data['medical_info'] = {
                'blood_group': employee.blood_group if hasattr(employee, 'blood_group') else None,
            }
        
        return api_response(
            success=True,
            message='Emergency contact information retrieved successfully',
            data=response_data
        )
