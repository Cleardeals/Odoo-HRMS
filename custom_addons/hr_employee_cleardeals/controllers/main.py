# -*- coding: utf-8 -*-
"""
Base API Controller for HR Employee ClearDeals Module

Provides:
- Authentication mechanisms (API Key, Bearer Token)
- Common response formatting
- Error handling
- CORS support
- Rate limiting utilities
"""
import logging
import json
import functools
from datetime import datetime

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessError, ValidationError, UserError

_logger = logging.getLogger(__name__)


# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def validate_api_key(func):
    """
    Decorator to validate API key from request headers.
    
    Headers required:
        - X-API-Key: The API key configured in system parameters
        
    Or:
        - Authorization: Bearer <token>
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Get API key from headers
        api_key = request.httprequest.headers.get('X-API-Key')
        auth_header = request.httprequest.headers.get('Authorization')
        
        # Check for Bearer token
        if not api_key and auth_header:
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not api_key:
            return api_response(
                success=False,
                message='API key required. Provide X-API-Key header or Authorization: Bearer token',
                status=401
            )
        
        # Validate API key against system parameters
        valid_key = request.env['ir.config_parameter'].sudo().get_param(
            'hr_employee_cleardeals.api_key'
        )
        
        if not valid_key:
            _logger.error('API key not configured in system parameters')
            return api_response(
                success=False,
                message='API not configured properly',
                status=500
            )
        
        if api_key != valid_key:
            _logger.warning(f'Invalid API key attempt from {request.httprequest.remote_addr}')
            return api_response(
                success=False,
                message='Invalid API key',
                status=401
            )
        
        # API key is valid, proceed with request
        return func(self, *args, **kwargs)
    
    return wrapper


def validate_user_auth(func):
    """
    Decorator to validate user authentication via session or token.
    For endpoints that require logged-in user context.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not request.env.user or request.env.user._is_public():
            return api_response(
                success=False,
                message='Authentication required. Please login.',
                status=401
            )
        return func(self, *args, **kwargs)
    
    return wrapper


# ============================================================================
# RESPONSE FORMATTING
# ============================================================================

def api_response(success=True, data=None, message='', status=200, 
                 errors=None, meta=None):
    """
    Standardized API response format.
    
    Args:
        success (bool): Operation success status
        data (dict/list): Response payload
        message (str): Human-readable message
        status (int): HTTP status code
        errors (list): List of error details
        meta (dict): Metadata (pagination, timestamps, etc.)
    
    Returns:
        Response: JSON response with consistent structure
    """
    response_data = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }
    
    if data is not None:
        response_data['data'] = data
    
    if errors:
        response_data['errors'] = errors
    
    if meta:
        response_data['meta'] = meta
    
    return Response(
        json.dumps(response_data, default=str),
        content_type='application/json',
        status=status
    )


def paginate_response(records, page=1, per_page=20):
    """
    Helper to create pagination metadata.
    
    Args:
        records: Odoo recordset
        page (int): Current page number
        per_page (int): Records per page
    
    Returns:
        tuple: (paginated_records, meta_dict)
    """
    total = len(records)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated = records[start:end]
    
    meta = {
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_records': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }
    }
    
    return paginated, meta


# ============================================================================
# ERROR HANDLING
# ============================================================================

def handle_api_errors(func):
    """
    Decorator to handle common Odoo exceptions and format error responses.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        
        except AccessError as e:
            _logger.warning(f'Access denied: {str(e)}')
            return api_response(
                success=False,
                message='Access denied',
                errors=[{'type': 'AccessError', 'details': str(e)}],
                status=403
            )
        
        except ValidationError as e:
            _logger.warning(f'Validation error: {str(e)}')
            return api_response(
                success=False,
                message='Validation failed',
                errors=[{'type': 'ValidationError', 'details': str(e)}],
                status=400
            )
        
        except UserError as e:
            _logger.warning(f'User error: {str(e)}')
            return api_response(
                success=False,
                message=str(e),
                errors=[{'type': 'UserError', 'details': str(e)}],
                status=400
            )
        
        except ValueError as e:
            _logger.warning(f'Value error: {str(e)}')
            return api_response(
                success=False,
                message='Invalid input data',
                errors=[{'type': 'ValueError', 'details': str(e)}],
                status=400
            )
        
        except Exception as e:
            _logger.exception(f'Unexpected error in API: {str(e)}')
            return api_response(
                success=False,
                message='Internal server error',
                errors=[{'type': type(e).__name__, 'details': str(e)}],
                status=500
            )
    
    return wrapper


# ============================================================================
# BASE CONTROLLER
# ============================================================================

class BaseAPIController(http.Controller):
    """
    Base controller providing common API utilities.
    
    All API controllers should inherit from this class.
    """
    
    @http.route('/api/v1/health', type='http', auth='public', 
                methods=['GET'], csrf=False, cors='*')
    def health_check(self):
        """
        Health check endpoint.
        
        Returns:
            JSON response indicating API health status
        """
        return api_response(
            success=True,
            message='API is healthy',
            data={
                'version': '1.0.0',
                'module': 'hr_employee_cleardeals',
                'status': 'operational'
            }
        )
    
    @http.route('/api/v1/info', type='http', auth='public', 
                methods=['GET'], csrf=False, cors='*')
    def api_info(self):
        """
        API information endpoint.
        
        Returns:
            JSON response with API documentation info
        """
        endpoints = [
            {
                'path': '/api/v1/health',
                'method': 'GET',
                'description': 'Health check endpoint',
                'auth_required': False
            },
            {
                'path': '/api/v1/info',
                'method': 'GET',
                'description': 'API information and documentation',
                'auth_required': False
            },
            {
                'path': '/api/v1/employees',
                'method': 'GET',
                'description': 'List all employees with optional filtering',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/active',
                'method': 'GET',
                'description': 'List all active employees (recommended for most use cases)',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/<employee_id>',
                'method': 'GET',
                'description': 'Get detailed employee information',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/<employee_id>/documents',
                'method': 'GET',
                'description': 'Fetch all documents for specific employee',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/<employee_id>/documents/<document_id>/download',
                'method': 'GET',
                'description': 'Download a specific document file',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/<employee_id>/emergency-contact',
                'method': 'GET',
                'description': 'Get emergency contact information by employee ID',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/<employee_id>/assets',
                'method': 'GET',
                'description': 'Get asset allocation and details by employee ID',
                'auth_required': True
            },
            {
                'path': '/api/v1/employees/pending-documents',
                'method': 'GET',
                'description': 'Get list of employees with pending/missing documents',
                'auth_required': True
            },
        ]
        
        return api_response(
            success=True,
            message='HR Employee ClearDeals API',
            data={
                'version': '1.0.0',
                'base_url': '/api/v1',
                'authentication': {
                    'type': 'API Key',
                    'methods': [
                        'Header: X-API-Key',
                        'Header: Authorization: Bearer <token>'
                    ],
                    'setup': 'Settings → Technical → Parameters → System Parameters → Key: hr_employee_cleardeals.api_key'
                },
                'endpoints': endpoints,
                'documentation': 'See module README.md for comprehensive API documentation'
            }
        )
