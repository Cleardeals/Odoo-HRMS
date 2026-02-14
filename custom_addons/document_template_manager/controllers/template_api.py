"""
Document Template API Controller

Endpoints for document template management.
"""

import logging

from odoo import http
from odoo.http import request

from .main import (
    BaseAPIController,
    api_response,
    handle_api_errors,
    paginate_response,
    parse_json_body,
    validate_api_key,
)

_logger = logging.getLogger(__name__)


class TemplateAPIController(BaseAPIController):
    """
    API endpoints for document template operations.

    Base URL: /api/v1/templates
    """

    # ========================================================================
    # CREATE TEMPLATE
    # ========================================================================

    @http.route(
        "/api/v1/templates",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def create_template(self, **kwargs):
        """
        Create a new document template.

        Endpoint: POST /api/v1/templates

        Headers:
            X-API-Key: Your API key
            OR
            Authorization: Bearer <your_api_key>
            Content-Type: application/json

        Request Body:
            {
                "name": "Sales Contract Template",  # Required
                "html_content": "<div>...</div>",   # Required
                "summary": "Template for sales contracts",  # Optional
                "category_id": 1,  # Optional - Category ID
                "tag_ids": [1, 2, 3],  # Optional - List of tag IDs
                "active": true,  # Optional - Default: true
                "favorite": false,  # Optional - Default: false
                "variables": [  # Optional - List of variables
                    {
                        "name": "customer_name",
                        "label": "Customer Name",
                        "variable_type": "char",  # char, text, integer, float, date, selection
                        "default_value": "",
                        "required": true,
                        "sequence": 10,
                        "selection_options": "Option1,Option2,Option3"  # For selection type only
                    }
                ]
            }

        Response Format:
            {
                "success": true,
                "message": "Template created successfully",
                "timestamp": "2026-02-14T12:00:00Z",
                "data": {
                    "template": {
                        "id": 1,
                        "name": "Sales Contract Template",
                        "summary": "Template for sales contracts",
                        "html_content": "<div>...</div>",
                        "category_id": {"id": 1, "name": "Contracts"},
                        "tag_ids": [
                            {"id": 1, "name": "Sales"},
                            {"id": 2, "name": "Legal"}
                        ],
                        "active": true,
                        "favorite": false,
                        "variable_count": 1,
                        "company_id": {"id": 1, "name": "Your Company"},
                        "create_date": "2026-02-14T12:00:00",
                        "write_date": "2026-02-14T12:00:00"
                    }
                }
            }

        Error Responses:
            400: Invalid input data or validation failed
            401: Invalid or missing API key
            500: Internal server error
        """
        # Parse request body
        data = parse_json_body()

        # Validate required fields
        if not data.get("name"):
            return api_response(
                success=False,
                message="Template name is required",
                status=400,
                errors=[{"field": "name", "message": "This field is required"}],
            )

        if not data.get("html_content"):
            return api_response(
                success=False,
                message="Template content is required",
                status=400,
                errors=[
                    {"field": "html_content", "message": "This field is required"},
                ],
            )

        # Prepare template values
        template_vals = {
            "name": data["name"],
            "html_content": data["html_content"],
            "summary": data.get("summary", ""),
            "active": data.get("active", True),
            "favorite": data.get("favorite", False),
        }

        # Handle category
        if data.get("category_id"):
            category = (
                request.env["document.category"]
                .sudo()
                .browse(
                    data["category_id"],
                )
            )
            if not category.exists():
                return api_response(
                    success=False,
                    message=f"Category with ID {data['category_id']} not found",
                    status=400,
                )
            template_vals["category_id"] = category.id

        # Create template
        template = request.env["document.template"].sudo().create(template_vals)

        # Handle tags (many2many)
        if data.get("tag_ids"):
            tag_ids = data["tag_ids"]
            if not isinstance(tag_ids, list):
                tag_ids = [tag_ids]

            tags = request.env["document.tag"].sudo().browse(tag_ids)
            existing_tags = tags.filtered(lambda t: t.exists())

            if len(existing_tags) != len(tag_ids):
                _logger.warning(
                    "Some tag IDs not found: %s",
                    set(tag_ids) - set(existing_tags.ids),
                )

            template.write({"tag_ids": [(6, 0, existing_tags.ids)]})

        # Handle variables
        if data.get("variables"):
            for var_data in data["variables"]:
                if not var_data.get("name") or not var_data.get("label"):
                    continue

                var_vals = {
                    "template_id": template.id,
                    "name": var_data["name"],
                    "label": var_data["label"],
                    "variable_type": var_data.get("variable_type", "char"),
                    "default_value": var_data.get("default_value", ""),
                    "required": var_data.get("required", True),
                    "sequence": var_data.get("sequence", 10),
                }
                # Add selection_options only for selection type
                if var_data.get("selection_options"):
                    var_vals["selection_options"] = var_data["selection_options"]

                request.env["document.template.variable"].sudo().create(var_vals)

        # Serialize and return
        template_data = self._serialize_template(template)

        _logger.info(
            "Template created via API: %s (ID: %s)",
            template.name,
            template.id,
        )

        return api_response(
            success=True,
            message="Template created successfully",
            data={"template": template_data},
            status=201,
        )

    # ========================================================================
    # LIST TEMPLATES
    # ========================================================================

    @http.route(
        "/api/v1/templates",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def list_templates(self, **kwargs):
        """
        List all document templates with filtering and pagination.

        Endpoint: GET /api/v1/templates

        Query Parameters:
            name (str): Filter by template name (partial match)
            category_id (int): Filter by category ID
            tag_ids (str): Comma-separated tag IDs (e.g., "1,2,3")
            active (bool): Filter by active status (true/false)
            favorite (bool): Filter by favorite status (true/false)
            page (int): Page number for pagination (default: 1)
            per_page (int): Records per page (default: 20, max: 100)

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Templates retrieved successfully",
                "timestamp": "2026-02-14T12:00:00Z",
                "data": {
                    "templates": [...]
                },
                "meta": {
                    "pagination": {
                        "current_page": 1,
                        "per_page": 20,
                        "total_records": 50,
                        "total_pages": 3,
                        "has_next": true,
                        "has_prev": false
                    }
                }
            }
        """
        # Build domain for filtering
        domain = []

        if kwargs.get("name"):
            domain.append(("name", "ilike", kwargs["name"]))

        if kwargs.get("category_id"):
            try:
                domain.append(("category_id", "=", int(kwargs["category_id"])))
            except ValueError:
                return api_response(
                    success=False,
                    message="Invalid category_id",
                    status=400,
                )

        if kwargs.get("tag_ids"):
            try:
                tag_ids = [int(tid) for tid in kwargs["tag_ids"].split(",")]
                domain.append(("tag_ids", "in", tag_ids))
            except ValueError:
                return api_response(
                    success=False,
                    message="Invalid tag_ids format. Use comma-separated integers.",
                    status=400,
                )

        if kwargs.get("active"):
            active_val = kwargs["active"].lower() in ("true", "1", "yes")
            domain.append(("active", "=", active_val))

        if kwargs.get("favorite"):
            favorite_val = kwargs["favorite"].lower() in ("true", "1", "yes")
            domain.append(("favorite", "=", favorite_val))

        # Get pagination params
        try:
            page = int(kwargs.get("page", 1))
            per_page = min(int(kwargs.get("per_page", 20)), 100)
        except ValueError:
            return api_response(
                success=False,
                message="Invalid pagination parameters",
                status=400,
            )

        # Search templates
        templates = request.env["document.template"].sudo().search(domain)

        # Paginate
        paginated_templates, meta = paginate_response(templates, page, per_page)

        # Serialize
        templates_data = [
            self._serialize_template(template) for template in paginated_templates
        ]

        return api_response(
            success=True,
            message="Templates retrieved successfully",
            data={"templates": templates_data},
            meta=meta,
        )

    # ========================================================================
    # GET SINGLE TEMPLATE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def get_template(self, template_id, **kwargs):
        """
        Get a single template by ID.

        Endpoint: GET /api/v1/templates/<template_id>

        Path Parameters:
            template_id (int): Template ID

        Query Parameters:
            include_variables (bool): Include variable details (default: true)

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Template retrieved successfully",
                "data": {
                    "template": {...}
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

        include_variables = kwargs.get("include_variables", "true").lower() in (
            "true",
            "1",
            "yes",
        )

        template_data = self._serialize_template(
            template,
            include_variables=include_variables,
        )

        return api_response(
            success=True,
            message="Template retrieved successfully",
            data={"template": template_data},
        )

    # ========================================================================
    # UPDATE TEMPLATE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>",
        type="http",
        auth="public",
        methods=["PUT", "PATCH"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def update_template(self, template_id, **kwargs):
        """
        Update an existing template.

        Endpoint: PUT/PATCH /api/v1/templates/<template_id>

        Path Parameters:
            template_id (int): Template ID

        Headers:
            X-API-Key: Your API key
            Content-Type: application/json

        Request Body:
            {
                "name": "Updated Template Name",  # Optional
                "html_content": "<div>...</div>",  # Optional
                "summary": "Updated summary",  # Optional
                "category_id": 2,  # Optional
                "tag_ids": [1, 2],  # Optional
                "active": false,  # Optional
                "favorite": true  # Optional
            }

        Response Format:
            {
                "success": true,
                "message": "Template updated successfully",
                "data": {
                    "template": {...}
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

        if not data:
            return api_response(
                success=False,
                message="No data provided for update",
                status=400,
            )

        # Prepare update values
        update_vals = {}

        allowed_fields = [
            "name",
            "html_content",
            "summary",
            "active",
            "favorite",
        ]

        for field in allowed_fields:
            if field in data:
                update_vals[field] = data[field]

        # Handle category
        if "category_id" in data:
            if data["category_id"] is None:
                update_vals["category_id"] = False
            else:
                category = (
                    request.env["document.category"]
                    .sudo()
                    .browse(
                        data["category_id"],
                    )
                )
                if not category.exists():
                    return api_response(
                        success=False,
                        message=f"Category with ID {data['category_id']} not found",
                        status=400,
                    )
                update_vals["category_id"] = category.id

        # Handle tags
        if "tag_ids" in data:
            tag_ids = data["tag_ids"]
            if not isinstance(tag_ids, list):
                tag_ids = [tag_ids]

            tags = request.env["document.tag"].sudo().browse(tag_ids)
            existing_tags = tags.filtered(lambda t: t.exists())

            update_vals["tag_ids"] = [(6, 0, existing_tags.ids)]

        # Update template
        template.write(update_vals)

        # Serialize and return
        template_data = self._serialize_template(template)

        _logger.info(
            "Template updated via API: %s (ID: %s)",
            template.name,
            template.id,
        )

        return api_response(
            success=True,
            message="Template updated successfully",
            data={"template": template_data},
        )

    # ========================================================================
    # DELETE TEMPLATE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>",
        type="http",
        auth="public",
        methods=["DELETE"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def delete_template(self, template_id, **kwargs):
        """
        Delete a template (archive or hard delete).

        Endpoint: DELETE /api/v1/templates/<template_id>

        Path Parameters:
            template_id (int): Template ID

        Query Parameters:
            hard_delete (bool): Permanently delete instead of archive (default: false)

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Template deleted successfully"
            }
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        template_name = template.name
        hard_delete = kwargs.get("hard_delete", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        if hard_delete:
            template.unlink()
            message = f"Template '{template_name}' permanently deleted"
        else:
            template.write({"active": False})
            message = f"Template '{template_name}' archived"

        _logger.info(
            "Template deleted via API: %s (ID: %s)",
            template_name,
            template_id,
        )

        return api_response(
            success=True,
            message=message,
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _serialize_template(self, template, include_variables=True):
        """
        Serialize a template record to dict.

        Args:
            template: document.template record
            include_variables (bool): Include variable details

        Returns:
            dict: Serialized template data
        """
        data = {
            "id": template.id,
            "name": template.name,
            "summary": template.summary or "",
            "html_content": template.html_content or "",
            "category_id": {
                "id": template.category_id.id,
                "name": template.category_id.name,
            }
            if template.category_id
            else None,
            "tag_ids": [
                {"id": tag.id, "name": tag.name, "color": tag.color}
                for tag in template.tag_ids
            ],
            "active": template.active,
            "favorite": template.favorite,
            "variable_count": template.variable_count,
            "company_id": {
                "id": template.company_id.id,
                "name": template.company_id.name,
            }
            if template.company_id
            else None,
            "create_date": (
                template.create_date.isoformat() if template.create_date else None
            ),
            "write_date": (
                template.write_date.isoformat() if template.write_date else None
            ),
        }

        if include_variables and template.variable_ids:
            data["variables"] = [
                {
                    "id": var.id,
                    "name": var.name,
                    "label": var.label,
                    "variable_type": var.variable_type,
                    "default_value": var.default_value or "",
                    "required": var.required,
                    "sequence": var.sequence,
                    "selection_options": var.selection_options or "",
                    "placeholder_tag": var.placeholder_tag or "",
                }
                for var in template.variable_ids
            ]

        return data
