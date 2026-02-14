"""
Template Variables API Controller

Endpoints for managing template variables (CRUD operations).
"""

import logging

from odoo import http
from odoo.http import request

from .api_utils import serialize_variable
from .main import (
    BaseAPIController,
    api_response,
    handle_api_errors,
    parse_json_body,
    validate_api_key,
)

_logger = logging.getLogger(__name__)


class TemplateVariablesAPIController(BaseAPIController):
    """
    API endpoints for template variable management.

    Base URL: /api/v1/templates/<template_id>/variables
    """

    # ========================================================================
    # LIST VARIABLES
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/variables",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def list_template_variables(self, template_id, **kwargs):
        """
        Get all variables for a specific template.

        Endpoint: GET /api/v1/templates/<template_id>/variables

        Path Parameters:
            template_id (int): Template ID

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Variables retrieved successfully",
                "data": {
                    "template": {
                        "id": 1,
                        "name": "Sales Contract"
                    },
                    "variables": [
                        {
                            "id": 1,
                            "name": "customer_name",
                            "label": "Customer Name",
                            "variable_type": "char",
                            "default_value": "",
                            "required": true,
                            "sequence": 10,
                            "selection_options": "",
                            "placeholder_tag": "{{customer_name}}"
                        }
                    ]
                }
            }
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        variables_data = [serialize_variable(var) for var in template.variable_ids]

        return api_response(
            success=True,
            message="Variables retrieved successfully",
            data={
                "template": {"id": template.id, "name": template.name},
                "variables": variables_data,
            },
        )

    # ========================================================================
    # GET SINGLE VARIABLE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/variables/<int:variable_id>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def get_template_variable(self, template_id, variable_id, **kwargs):
        """
        Get a specific variable from a template.

        Endpoint: GET /api/v1/templates/<template_id>/variables/<variable_id>

        Path Parameters:
            template_id (int): Template ID
            variable_id (int): Variable ID

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Variable retrieved successfully",
                "data": {
                    "variable": {...}
                }
            }
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        variable = request.env["document.template.variable"].sudo().browse(variable_id)

        if not variable.exists() or variable.template_id.id != template_id:
            return api_response(
                success=False,
                message=f"Variable with ID {variable_id} not found in template {template_id}",
                status=404,
            )

        return api_response(
            success=True,
            message="Variable retrieved successfully",
            data={"variable": serialize_variable(variable)},
        )

    # ========================================================================
    # CREATE VARIABLE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/variables",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def create_template_variable(self, template_id, **kwargs):
        """
        Create a new variable for a template.

        Endpoint: POST /api/v1/templates/<template_id>/variables

        Path Parameters:
            template_id (int): Template ID

        Headers:
            X-API-Key: Your API key
            Content-Type: application/json

        Request Body:
            {
                "name": "customer_name",  # Required
                "label": "Customer Name",  # Required
                "variable_type": "char",  # Optional: char, text, integer, float, date, selection
                "default_value": "",  # Optional
                "required": true,  # Optional (default: true)
                "sequence": 10,  # Optional (default: 10)
                "selection_options": "Option1,Option2"  # Optional (for selection type)
            }

        Response Format:
            {
                "success": true,
                "message": "Variable created successfully",
                "data": {
                    "variable": {...}
                }
            }
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        # Parse request body
        data = parse_json_body()

        # Validate required fields
        if not data.get("name"):
            return api_response(
                success=False,
                message="Variable name is required",
                status=400,
                errors=[{"field": "name", "message": "This field is required"}],
            )

        if not data.get("label"):
            return api_response(
                success=False,
                message="Variable label is required",
                status=400,
                errors=[{"field": "label", "message": "This field is required"}],
            )

        # Prepare variable values
        var_vals = {
            "template_id": template_id,
            "name": data["name"],
            "label": data["label"],
            "variable_type": data.get("variable_type", "char"),
            "default_value": data.get("default_value", ""),
            "required": data.get("required", True),
            "sequence": data.get("sequence", 10),
        }

        # Add selection_options if provided
        if data.get("selection_options"):
            var_vals["selection_options"] = data["selection_options"]

        # Create variable
        variable = request.env["document.template.variable"].sudo().create(var_vals)

        _logger.info(
            "Variable created via API: %s for template %s (ID: %s)",
            variable.name,
            template.name,
            template_id,
        )

        return api_response(
            success=True,
            message="Variable created successfully",
            data={"variable": serialize_variable(variable)},
            status=201,
        )

    # ========================================================================
    # UPDATE VARIABLE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/variables/<int:variable_id>",
        type="http",
        auth="public",
        methods=["PUT", "PATCH"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def update_template_variable(self, template_id, variable_id, **kwargs):
        """
        Update a variable in a template.

        Endpoint: PUT/PATCH /api/v1/templates/<template_id>/variables/<variable_id>

        Path Parameters:
            template_id (int): Template ID
            variable_id (int): Variable ID

        Headers:
            X-API-Key: Your API key
            Content-Type: application/json

        Request Body:
            {
                "label": "Updated Label",  # Optional
                "variable_type": "text",  # Optional
                "default_value": "New default",  # Optional
                "required": false,  # Optional
                "sequence": 20,  # Optional
                "selection_options": "A,B,C"  # Optional
            }

        Response Format:
            {
                "success": true,
                "message": "Variable updated successfully",
                "data": {
                    "variable": {...}
                }
            }
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        variable = request.env["document.template.variable"].sudo().browse(variable_id)

        if not variable.exists() or variable.template_id.id != template_id:
            return api_response(
                success=False,
                message=f"Variable with ID {variable_id} not found in template {template_id}",
                status=404,
            )

        # Parse request body
        data = parse_json_body()

        if not data:
            return api_response(
                success=False,
                message="No data provided for update",
                status=400,
            )

        # Prepare update values (name cannot be changed to prevent breaking templates)
        update_vals = {}

        allowed_fields = [
            "label",
            "variable_type",
            "default_value",
            "required",
            "sequence",
            "selection_options",
        ]

        for field in allowed_fields:
            if field in data:
                update_vals[field] = data[field]

        # Update variable
        variable.write(update_vals)

        _logger.info(
            "Variable updated via API: %s (ID: %s) in template %s",
            variable.name,
            variable_id,
            template_id,
        )

        return api_response(
            success=True,
            message="Variable updated successfully",
            data={"variable": serialize_variable(variable)},
        )

    # ========================================================================
    # DELETE VARIABLE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/variables/<int:variable_id>",
        type="http",
        auth="public",
        methods=["DELETE"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def delete_template_variable(self, template_id, variable_id, **kwargs):
        """
        Delete a variable from a template.

        Endpoint: DELETE /api/v1/templates/<template_id>/variables/<variable_id>

        Path Parameters:
            template_id (int): Template ID
            variable_id (int): Variable ID

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Variable deleted successfully"
            }
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        variable = request.env["document.template.variable"].sudo().browse(variable_id)

        if not variable.exists() or variable.template_id.id != template_id:
            return api_response(
                success=False,
                message=f"Variable with ID {variable_id} not found in template {template_id}",
                status=404,
            )

        variable_name = variable.name
        variable.unlink()

        _logger.info(
            "Variable deleted via API: %s (ID: %s) from template %s",
            variable_name,
            variable_id,
            template_id,
        )

        return api_response(
            success=True,
            message=f"Variable '{variable_name}' deleted successfully",
        )
