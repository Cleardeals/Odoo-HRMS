"""
Template Actions API Controller

Endpoints for template-level actions introduced after the print-mode /
header / margin refactor:

  POST   /api/v1/templates/<id>/detect-variables   - auto-detect variables from HTML
  POST   /api/v1/templates/<id>/duplicate          - duplicate a template
  POST   /api/v1/templates/<id>/toggle-favorite    - toggle the favorite flag
  GET    /api/v1/templates/<id>/download-pdf       - stream the last generated PDF
"""

import base64
import logging
import re

from odoo import http
from odoo.http import request

from .api_utils import serialize_template
from .main import (
    BaseAPIController,
    api_response,
    handle_api_errors,
    validate_api_key,
)

_logger = logging.getLogger(__name__)


class TemplateActionsAPIController(BaseAPIController):
    """
    API endpoints for template actions.

    Base URL: /api/v1/templates/<template_id>/
    """

    # ========================================================================
    # DETECT VARIABLES
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/detect-variables",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def detect_variables(self, template_id, **kwargs):
        """
        Scan a template's HTML content for ``{{variable}}`` placeholders and
        automatically create any variable records that do not already exist.

        Endpoint: POST /api/v1/templates/<template_id>/detect-variables

        Path Parameters:
            template_id (int): Template ID

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "3 new variable(s) detected and added.",
                "data": {
                    "new_variable_count": 3,
                    "new_variables": ["customer_name", "contract_date", "salary"],
                    "template": { ... }
                }
            }

        Error Responses:
            400: Template has no HTML content to scan
            404: Template not found
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        if not template.html_content:
            return api_response(
                success=False,
                message="Template has no HTML content to scan",
                status=400,
            )

        found = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", template.html_content))
        existing = set(template.variable_ids.mapped("name"))
        new_var_names = found - existing

        seq = max(template.variable_ids.mapped("sequence") or [0])
        for var_name in sorted(new_var_names):
            seq += 10
            label = var_name.replace("_", " ").title()
            request.env["document.template.variable"].sudo().create(
                {
                    "template_id": template.id,
                    "name": var_name,
                    "label": label,
                    "variable_type": "char",
                    "required": True,
                    "sequence": seq,
                },
            )

        # Reload to get updated variable_ids
        template.invalidate_recordset()

        new_count = len(new_var_names)
        message = (
            f"{new_count} new variable(s) detected and added."
            if new_var_names
            else "No new variables found."
        )

        _logger.info(
            "Variable detection via API: %d new variables for template %s (ID: %s)",
            new_count,
            template.name,
            template_id,
        )

        return api_response(
            success=True,
            message=message,
            data={
                "new_variable_count": new_count,
                "new_variables": sorted(new_var_names),
                "template": serialize_template(template),
            },
        )

    # ========================================================================
    # DUPLICATE TEMPLATE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/duplicate",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def duplicate_template(self, template_id, **kwargs):
        """
        Create a copy of an existing template (including its variables).

        Endpoint: POST /api/v1/templates/<template_id>/duplicate

        Path Parameters:
            template_id (int): Template ID to duplicate

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Template duplicated successfully",
                "data": {
                    "template": { ... }   // the new duplicate
                }
            }

        Error Responses:
            404: Template not found
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        new_template = template.copy()

        _logger.info(
            "Template duplicated via API: original ID %s → new ID %s",
            template_id,
            new_template.id,
        )

        return api_response(
            success=True,
            message="Template duplicated successfully",
            data={"template": serialize_template(new_template)},
            status=201,
        )

    # ========================================================================
    # TOGGLE FAVORITE
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/toggle-favorite",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def toggle_favorite(self, template_id, **kwargs):
        """
        Toggle the ``favorite`` flag on a template.

        Endpoint: POST /api/v1/templates/<template_id>/toggle-favorite

        Path Parameters:
            template_id (int): Template ID

        Headers:
            X-API-Key: Your API key

        Response Format:
            {
                "success": true,
                "message": "Template marked as favorite",
                "data": {
                    "favorite": true,
                    "template_id": 42
                }
            }

        Error Responses:
            404: Template not found
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        new_value = not template.favorite
        template.write({"favorite": new_value})

        message = (
            "Template marked as favorite" if new_value else "Template removed from favorites"
        )

        _logger.info(
            "Favorite toggled via API: template %s (ID: %s) → favorite=%s",
            template.name,
            template_id,
            new_value,
        )

        return api_response(
            success=True,
            message=message,
            data={"template_id": template_id, "favorite": new_value},
        )

    # ========================================================================
    # DOWNLOAD LAST GENERATED PDF
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/download-pdf",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def download_pdf(self, template_id, **kwargs):
        """
        Return the last PDF that was generated for this template.

        The PDF is returned as a base64-encoded string so that it can be
        consumed by JSON clients.  Pass ``?return_type=url`` to receive a
        short-lived Odoo attachment download URL instead.

        Endpoint: GET /api/v1/templates/<template_id>/download-pdf

        Path Parameters:
            template_id (int): Template ID

        Query Parameters:
            return_type (str): "base64" (default) | "url"

        Headers:
            X-API-Key: Your API key

        Response Format (base64):
            {
                "success": true,
                "message": "PDF retrieved successfully",
                "data": {
                    "filename": "My_Template.pdf",
                    "pdf_base64": "JVBERi0xLjQKJ...",
                    "mimetype": "application/pdf",
                    "size_bytes": 102400
                }
            }

        Response Format (url):
            {
                "success": true,
                "message": "PDF retrieved successfully",
                "data": {
                    "filename": "My_Template.pdf",
                    "download_url": "/web/content/document.template/42/pdf_file/My_Template.pdf?download=true",
                    "mimetype": "application/pdf"
                }
            }

        Error Responses:
            404: Template not found or no PDF available yet
        """
        template = request.env["document.template"].sudo().browse(template_id)

        if not template.exists():
            return api_response(
                success=False,
                message=f"Template with ID {template_id} not found",
                status=404,
            )

        if not template.has_pdf:
            return api_response(
                success=False,
                message="No PDF available for this template. Generate one first via the generate-pdf endpoint.",
                status=404,
            )

        filename = template.pdf_filename or "document.pdf"
        return_type = kwargs.get("return_type", "base64").lower()

        if return_type == "url":
            download_url = (
                f"/web/content/document.template/{template_id}"
                f"/pdf_file/{filename}?download=true"
            )
            return api_response(
                success=True,
                message="PDF retrieved successfully",
                data={
                    "filename": filename,
                    "download_url": download_url,
                    "mimetype": "application/pdf",
                },
            )

        # Decode the stored binary and re-encode as base64 string
        pdf_bytes = base64.b64decode(template.pdf_file)

        return api_response(
            success=True,
            message="PDF retrieved successfully",
            data={
                "filename": filename,
                "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
                "mimetype": "application/pdf",
                "size_bytes": len(pdf_bytes),
            },
        )
