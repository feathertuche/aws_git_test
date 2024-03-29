"""
Helper functions for COMPANY_INFO app
"""


def format_merge_company_data(organization_data):
    """
    Format the company data to merge with the company info
    """
    formatted_addresses = [
        {
            "type": addr.type,
            "street_1": addr.street_1,
            "street_2": addr.street_2,
            "city": addr.city,
            "state": addr.state,
            "country_subdivision": addr.country_subdivision,
            "country": addr.country,
            "zip_code": addr.zip_code,
            "created_at": addr.created_at.isoformat() + "Z",
            "modified_at": addr.modified_at.isoformat() + "Z",
        }
        for addr in organization_data.results[0].addresses
    ]

    formatted_data = []
    for organization in organization_data.results:
        formatted_entry = {
            "id": organization.id,
            "remote_id": organization.remote_id,
            "name": organization.name,
            "legal_name": organization.legal_name,
            "tax_number": organization.tax_number,
            "fiscal_year_end_month": organization.fiscal_year_end_month,
            "fiscal_year_end_day": organization.fiscal_year_end_day,
            "currency": organization.currency,
            "remote_created_at": organization.remote_created_at.isoformat() + "Z",
            "urls": organization.urls,
            "addresses": formatted_addresses,
            "phone_numbers": [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": organization.created_at.isoformat() + "Z",
                    "modified_at": organization.modified_at.isoformat() + "Z",
                }
                for phone in organization.phone_numbers
            ],
            "remote_was_deleted": organization.remote_was_deleted,
            "created_at": organization.created_at.isoformat() + "Z",
            "modified_at": organization.modified_at.isoformat() + "Z",
            "field_mappings": organization.field_mappings,
            "remote_data": None,
        }
        formatted_data.append(formatted_entry)
        kloo_format_json = {"companies": formatted_data}

    return kloo_format_json
