"""
Asset Management API Controller

Endpoints for employee asset information and tracking.
"""
import logging

from odoo import http
from odoo.http import request

from .main import (
    api_response,
    handle_api_errors,
    validate_api_key,
)

_logger = logging.getLogger(__name__)


class AssetAPIController(http.Controller):
    """
    API endpoints for employee asset management.
    
    Base URL: /api/v1/employees/<employee_id>/assets
    """

    @http.route('/api/v1/employees/<string:employee_id>/assets',
                type='http', auth='public', methods=['GET'],
                csrf=False, cors='*')
    @validate_api_key
    @handle_api_errors
    def get_employee_assets(self, employee_id, **kwargs):
        """
        Get all asset information for a specific employee.
        
        Endpoint: GET /api/v1/employees/<employee_id>/assets
        
        Path Parameters:
            employee_id (str): Employee ID (e.g., CD-0001)
        
        Query Parameters:
            include_details (bool): Include detailed specifications (default: true)
            include_allocation (bool): Include allocation dates and status (default: true)
        
        Headers:
            X-API-Key: Your API key
        
        Response Format:
            {
                "success": true,
                "message": "Asset information retrieved successfully",
                "timestamp": "2026-02-11T12:00:00Z",
                "data": {
                    "employee": {
                        "id": 1,
                        "employee_id": "CD-0001",
                        "name": "John Doe",
                        "department": "Engineering",
                        "job_title": "Senior Developer",
                        "employee_status": "active"
                    },
                    "issued_assets": {
                        "laptop": true,
                        "sim_card": true,
                        "phone": false,
                        "pc_desktop": false,
                        "physical_id_card": true
                    },
                    "laptop_details": {
                        "brand": "Dell",
                        "model": "Latitude 7420",
                        "serial_number": "ABC123XYZ789",
                        "ram": "16GB",
                        "storage": "512GB SSD",
                        "processor": "Intel Core i7",
                        "allocation_date": "2025-01-15"
                    },
                    "asset_summary": {
                        "total_assets_issued": 3,
                        "asset_types": ["Laptop", "SIM Card", "Physical ID Card"]
                    }
                }
            }
        
        Error Responses:
            404: Employee not found
            401: Invalid API key
        
        Use Cases:
            - IT asset tracking and inventory management
            - Employee onboarding/offboarding asset checklists
            - Asset allocation reporting
            - Compliance and audit trails
            - Asset return verification during exit process
        """
        # Parse parameters
        include_details = kwargs.get('include_details', 'true').lower() == 'true'
        include_allocation = kwargs.get('include_allocation', 'true').lower() == 'true'

        # Find employee by employee_id
        employee = request.env['hr.employee'].sudo().search([
            ('employee_id', '=', employee_id),
        ], limit=1)

        if not employee:
            return api_response(
                success=False,
                message=f'Employee with ID {employee_id} not found',
                status=404,
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
            'issued_assets': {
                'laptop': employee.asset_laptop if hasattr(employee, 'asset_laptop') else False,
                'sim_card': employee.asset_sim if hasattr(employee, 'asset_sim') else False,
                'phone': employee.asset_phone if hasattr(employee, 'asset_phone') else False,
                'pc_desktop': employee.asset_pc if hasattr(employee, 'asset_pc') else False,
                'physical_id_card': employee.asset_physical_id if hasattr(employee, 'asset_physical_id') else False,
            },
        }

        # Count issued assets
        issued_count = sum([
            employee.asset_laptop if hasattr(employee, 'asset_laptop') else False,
            employee.asset_sim if hasattr(employee, 'asset_sim') else False,
            employee.asset_phone if hasattr(employee, 'asset_phone') else False,
            employee.asset_pc if hasattr(employee, 'asset_pc') else False,
            employee.asset_physical_id if hasattr(employee, 'asset_physical_id') else False,
        ])

        # Build asset type list
        asset_types = []
        if employee.asset_laptop if hasattr(employee, 'asset_laptop') else False:
            asset_types.append('Laptop')
        if employee.asset_sim if hasattr(employee, 'asset_sim') else False:
            asset_types.append('SIM Card')
        if employee.asset_phone if hasattr(employee, 'asset_phone') else False:
            asset_types.append('Phone')
        if employee.asset_pc if hasattr(employee, 'asset_pc') else False:
            asset_types.append('PC/Desktop')
        if employee.asset_physical_id if hasattr(employee, 'asset_physical_id') else False:
            asset_types.append('Physical ID Card')

        # Add laptop details if laptop is issued and details requested
        if include_details and (employee.asset_laptop if hasattr(employee, 'asset_laptop') else False):
            laptop_details = {}

            # Add laptop fields if they exist
            if hasattr(employee, 'laptop_brand'):
                laptop_details['brand'] = employee.laptop_brand
            if hasattr(employee, 'laptop_model'):
                laptop_details['model'] = employee.laptop_model
            if hasattr(employee, 'laptop_serial_number'):
                laptop_details['serial_number'] = employee.laptop_serial_number
            if hasattr(employee, 'ram'):
                laptop_details['ram'] = employee.ram
            if hasattr(employee, 'storage'):
                laptop_details['storage'] = employee.storage
            if hasattr(employee, 'processor'):
                laptop_details['processor'] = employee.processor

            # Add allocation date if requested
            if include_allocation and hasattr(employee, 'laptop_allocation_date') and employee.laptop_allocation_date:
                laptop_details['allocation_date'] = employee.laptop_allocation_date.strftime('%Y-%m-%d')

            # Only add laptop_details if there's actual data
            if laptop_details:
                response_data['laptop_details'] = laptop_details

        # Add asset summary
        response_data['asset_summary'] = {
            'total_assets_issued': issued_count,
            'asset_types': asset_types,
            'has_laptop': employee.asset_laptop if hasattr(employee, 'asset_laptop') else False,
            'has_mobile_assets': (employee.asset_sim if hasattr(employee, 'asset_sim') else False) or
                                  (employee.asset_phone if hasattr(employee, 'asset_phone') else False),
        }

        return api_response(
            success=True,
            message='Asset information retrieved successfully',
            data=response_data,
        )
