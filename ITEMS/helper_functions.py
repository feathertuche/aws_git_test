"""
Helper Functions for the ITEMS package
"""


def format_items_data(items_data: dict):
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
            "id": item.id,
            "remote_id": item.remote_id,
            "created_at": item.created_at.isoformat(),
            "modified_at": item.modified_at.isoformat(),
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
