"""
Template PDF Generation API Controller

Endpoints for generating PDF documents from templates with variable substitution.
"""

import base64
import logging
import re

from odoo import http
from odoo.http import request

from .main import (
    BaseAPIController,
    api_response,
    handle_api_errors,
    parse_json_body,
    validate_api_key,
)

_logger = logging.getLogger(__name__)


class TemplatePDFAPIController(BaseAPIController):
    """
    API endpoints for PDF generation from templates.

    Base URL: /api/v1/templates/<template_id>/generate-pdf
    """

    # ========================================================================
    # GENERATE PDF
    # ========================================================================

    @http.route(
        "/api/v1/templates/<int:template_id>/generate-pdf",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    @validate_api_key
    @handle_api_errors
    def generate_pdf(self, template_id, **kwargs):
        """
        Generate a PDF from a template with variable values.

        Endpoint: POST /api/v1/templates/<template_id>/generate-pdf

        Path Parameters:
            template_id (int): Template ID

        Headers:
            X-API-Key: Your API key
            Content-Type: application/json

        Request Body:
            {
                "variables": {
                    "customer_name": "John Doe",
                    "contract_date": "2026-02-14",
                    "salary": "50000"
                },
                "filename": "Contract_JohnDoe.pdf",  # Optional, default: template name
                "return_type": "base64"  # Optional: "base64" (default) or "url"
            }

        Response Format (base64):
            {
                "success": true,
                "message": "PDF generated successfully",
                "data": {
                    "filename": "Contract_JohnDoe.pdf",
                    "pdf_base64": "JVBERi0xLjQKJ...",
                    "mimetype": "application/pdf",
                    "size_bytes": 102400
                }
            }

        Response Format (url):
            {
                "success": true,
                "message": "PDF generated successfully",
                "data": {
                    "filename": "Contract_JohnDoe.pdf",
                    "download_url": "/web/content/123/Contract_JohnDoe.pdf?download=true",
                    "attachment_id": 123,
                    "mimetype": "application/pdf",
                    "size_bytes": 102400
                }
            }

        Error Responses:
            400: Missing required variables or invalid data
            404: Template not found
            500: PDF generation failed
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
                message="Request body is required",
                status=400,
            )

        variables = data.get("variables", {})
        if not isinstance(variables, dict):
            return api_response(
                success=False,
                message="Variables must be a dictionary/object",
                status=400,
                errors=[
                    {
                        "field": "variables",
                        "message": "Expected object with variable name-value pairs",
                    },
                ],
            )

        # Validate required variables
        required_vars = template.variable_ids.filtered(lambda v: v.required)
        missing_vars = []

        for var in required_vars:
            if (
                var.name not in variables
                or not str(variables.get(var.name, "")).strip()
            ):
                missing_vars.append(var.label or var.name)

        if missing_vars:
            return api_response(
                success=False,
                message=f"Missing required variables: {', '.join(missing_vars)}",
                status=400,
                errors=[
                    {
                        "field": "variables",
                        "message": f"Required variables missing: {', '.join(missing_vars)}",
                        "missing_variables": missing_vars,
                    },
                ],
            )

        # Render HTML with variable substitution
        rendered_html = self._render_template_html(template, variables)

        # Generate PDF
        try:
            pdf_bytes = template._generate_pdf_bytes(rendered_html)
        except Exception as e:
            _logger.exception("PDF generation failed")
            return api_response(
                success=False,
                message="PDF generation failed",
                status=500,
                errors=[{"type": "PDFGenerationError", "details": str(e)}],
            )

        # Determine filename
        filename = data.get("filename")
        if not filename:
            # Use template name with sanitization
            safe_name = template.name.replace("/", "-").replace("\\", "-")
            filename = f"{safe_name}.pdf"
        elif not filename.endswith(".pdf"):
            filename = f"{filename}.pdf"

        # Determine return type
        return_type = data.get("return_type", "base64").lower()

        if return_type == "url":
            # Create attachment and return download URL
            attachment = (
                request.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": filename,
                        "type": "binary",
                        "datas": base64.b64encode(pdf_bytes),
                        "mimetype": "application/pdf",
                        "res_model": "document.template",
                        "res_id": template_id,
                    },
                )
            )

            download_url = f"/web/content/{attachment.id}/{filename}?download=true"

            _logger.info(
                "PDF generated via API (URL): %s for template %s (ID: %s)",
                filename,
                template.name,
                template_id,
            )

            return api_response(
                success=True,
                message="PDF generated successfully",
                data={
                    "filename": filename,
                    "download_url": download_url,
                    "attachment_id": attachment.id,
                    "mimetype": "application/pdf",
                    "size_bytes": len(pdf_bytes),
                },
                status=201,
            )

        # Return base64 encoded PDF
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        _logger.info(
            "PDF generated via API (base64): %s for template %s (ID: %s)",
            filename,
            template.name,
            template_id,
        )

        return api_response(
            success=True,
            message="PDF generated successfully",
            data={
                "filename": filename,
                "pdf_base64": pdf_base64,
                "mimetype": "application/pdf",
                "size_bytes": len(pdf_bytes),
            },
            status=201,
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _render_template_html(self, template, variables):
        """
        Render template HTML by replacing variable placeholders with values.

        Args:
            template: document.template record
            variables: dict of variable name -> value

        Returns:
            str: Rendered HTML
        """
        html = template.html_content or ""

        # Replace each variable placeholder {{variable_name}} with its value
        for var_name, var_value in variables.items():
            # Match {{variable_name}} with optional whitespace
            pattern = r"\{\{\s*" + re.escape(str(var_name)) + r"\s*\}\}"
            html = re.sub(pattern, str(var_value or ""), html)

        return html
