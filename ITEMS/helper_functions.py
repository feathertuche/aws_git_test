"""
Helper Functions for the ITEMS package
"""

import uuid


def format_items_data(items_data: dict, erp_link_token_id: str, organization_id: str):
    """
    Format items data for Kloo API
    """
    formatted_data = []

    for item in items_data:
        erp_remote_data = None
        if item.remote_data is not None:
            erp_remote_data = [
                item_remote_data.data for item_remote_data in item.remote_data
            ]

        formatted_items_data = {
            "id": str(uuid.uuid4()),
            "erp_id": item.id,
            "erp_link_token_id": erp_link_token_id,
            "organization_id": organization_id,
            "remote_id": item.remote_id,
            "erp_created_at": item.created_at.isoformat(),
            "erp_modified_at": item.modified_at.isoformat(),
            "name": item.name,
            "status": item.status,
            "unit_price": item.unit_price,
            "purchase_price": item.purchase_price,
            "purchase_account": item.purchase_account,
            "sales_account": item.sales_account,
            "company": item.company,
            "remote_updated_at": item.remote_updated_at.isoformat(),
            "remote_was_deleted": item.remote_was_deleted,
            "field_mappings": item.field_mappings,
            "remote_data": erp_remote_data,
        }

        formatted_data.append(formatted_items_data)

    formatted_items_data = {"erp_items": formatted_data}

    return formatted_items_data
