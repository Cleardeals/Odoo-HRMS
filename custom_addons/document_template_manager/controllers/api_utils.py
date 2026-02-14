"""
API Utilities Module

Shared utility functions for API controllers.
"""


def serialize_template(template, include_variables=True):
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
        data["variables"] = [serialize_variable(var) for var in template.variable_ids]

    return data


def serialize_variable(variable):
    """
    Serialize a template variable record to dict.

    Args:
        variable: document.template.variable record

    Returns:
        dict: Serialized variable data
    """
    return {
        "id": variable.id,
        "name": variable.name,
        "label": variable.label,
        "variable_type": variable.variable_type,
        "default_value": variable.default_value or "",
        "required": variable.required,
        "sequence": variable.sequence,
        "selection_options": variable.selection_options or "",
        "placeholder_tag": variable.placeholder_tag or "",
    }
