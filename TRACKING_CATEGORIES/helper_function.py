def format_tracking_categories_payload(tracking_categories):
    """
    Format tracking categories data for Kloo API
    """
    field_mappings = [
        {"organization_defined_targets": {}, "linked_account_defined_targets": {}}
    ]

    formatted_data = []
    for category in tracking_categories:
        erp_remote_data = None
        if category.remote_data is not None:
            erp_remote_data = [
                category_remote_data.data
                for category_remote_data in category.remote_data
            ]

        formatted_entry = {
            "id": category.id,
            "name": category.name,
            "status": category.status,
            "category_type": category.category_type,
            "parent_category": category.parent_category,
            "company": category.company,
            "remote_was_deleted": category.remote_was_deleted,
            "remote_id": category.remote_id,
            "created_at": category.created_at.isoformat(),
            "updated_at": category.modified_at.isoformat(),
            "field_mappings": field_mappings,
            "remote_data": erp_remote_data,
        }
        formatted_data.append(formatted_entry)
    kloo_format_json = {"tracking_category": formatted_data}

    return kloo_format_json
