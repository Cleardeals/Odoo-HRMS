"""
Base API Controller for Document Template Manager Module

Provides:
- Authentication mechanisms (API Key, Bearer Token)
- Common response formatting
- Error handling
- CORS support
- Logging utilities
"""

import functools
import json
import logging
from datetime import datetime

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import Response, request

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
        api_key = request.httprequest.headers.get("X-API-Key")
        auth_header = request.httprequest.headers.get("Authorization")

        # Check for Bearer token
        if not api_key and auth_header:
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix

        if not api_key:
            return api_response(
                success=False,
                message="API key required. Provide X-API-Key header or Authorization: Bearer token",
                status=401,
            )

        # Validate API key against system parameters
        valid_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "document_template_manager.api_key",
            )
        )

        if not valid_key:
            _logger.error("API key not configured in system parameters")
            return api_response(
                success=False,
                message="API not configured properly. Contact system administrator.",
                status=500,
            )

        if api_key != valid_key:
            _logger.warning(
                "Invalid API key attempt from %s",
                request.httprequest.remote_addr,
            )
            return api_response(
                success=False,
                message="Invalid API key",
                status=401,
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
                message="Authentication required. Please login.",
                status=401,
            )
        return func(self, *args, **kwargs)

    return wrapper


# ============================================================================
# RESPONSE FORMATTING
# ============================================================================


def api_response(
    success=True,
    data=None,
    message="",
    status=200,
    errors=None,
    meta=None,
):
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
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if data is not None:
        response_data["data"] = data

    if errors:
        response_data["errors"] = errors

    if meta:
        response_data["meta"] = meta

    return Response(
        json.dumps(response_data, default=str),
        content_type="application/json",
        status=status,
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
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total_records": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
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
            _logger.warning("Access denied: %s", e)
            return api_response(
                success=False,
                message="Access denied",
                errors=[{"type": "AccessError", "details": str(e)}],
                status=403,
            )

        except ValidationError as e:
            _logger.warning("Validation error: %s", e)
            return api_response(
                success=False,
                message="Validation failed",
                errors=[{"type": "ValidationError", "details": str(e)}],
                status=400,
            )

        except UserError as e:
            _logger.warning("User error: %s", e)
            return api_response(
                success=False,
                message=str(e),
                errors=[{"type": "UserError", "details": str(e)}],
                status=400,
            )

        except ValueError as e:
            _logger.warning("Value error: %s", e)
            return api_response(
                success=False,
                message="Invalid input data",
                errors=[{"type": "ValueError", "details": str(e)}],
                status=400,
            )

        except KeyError as e:
            _logger.warning("Missing required field: %s", e)
            return api_response(
                success=False,
                message=f"Missing required field: {e!s}",
                errors=[{"type": "KeyError", "details": str(e)}],
                status=400,
            )

        except Exception as e:
            _logger.exception("Unexpected error in API")
            return api_response(
                success=False,
                message="Internal server error",
                errors=[{"type": type(e).__name__, "details": str(e)}],
                status=500,
            )

    return wrapper


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def parse_json_body():
    """
    Parse JSON request body and return as dict.

    Returns:
        dict: Parsed JSON data

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        data = request.httprequest.get_data(as_text=True)
        if not data:
            return {}
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e!s}")


def get_query_params():
    """
    Get query parameters from request.

    Returns:
        dict: Query parameters
    """
    return dict(request.httprequest.args)


# ============================================================================
# BASE API CONTROLLER
# ============================================================================


class BaseAPIController(http.Controller):
    """
    Base controller class for API endpoints.
    Provides common utilities and setup.
    """

    def _serialize_record(self, record, fields_list):
        """
        Serialize a single record to dict.

        Args:
            record: Odoo record
            fields_list (list): Fields to include

        Returns:
            dict: Serialized record
        """
        result = {}
        for field_name in fields_list:
            if "." in field_name:
                # Handle related fields
                parts = field_name.split(".")
                value = record
                for part in parts:
                    if value:
                        value = getattr(value, part, None)
                result[field_name] = value
            else:
                field = record._fields.get(field_name)
                if not field:
                    continue

                value = record[field_name]

                if field.type == "many2one":
                    result[field_name] = (
                        {
                            "id": value.id,
                            "name": value.display_name,
                        }
                        if value
                        else None
                    )
                elif field.type in ("one2many", "many2many"):
                    result[field_name] = [
                        {"id": r.id, "name": r.display_name} for r in value
                    ]
                elif field.type == "binary":
                    # Skip binary fields by default for performance
                    result[field_name] = bool(value)
                elif field.type in ("date", "datetime"):
                    result[field_name] = value.isoformat() if value else None
                else:
                    result[field_name] = value

        return result

    def _serialize_records(self, records, fields_list):
        """
        Serialize multiple records to list of dicts.

        Args:
            records: Odoo recordset
            fields_list (list): Fields to include

        Returns:
            list: List of serialized records
        """
        return [self._serialize_record(rec, fields_list) for rec in records]
