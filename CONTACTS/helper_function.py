def format_contacts_payload(contact_data):
    """
    Format the contact data into the Kloo format
    """
    formatted_data = []

    for contact in contact_data:
        erp_remote_data = None
        if contact.remote_data is not None:
            erp_remote_data = [
                contact_remote_data.data for contact_remote_data in contact.remote_data
            ]

        formatted_entry = {
            "id": contact.id,
            "remote_id": contact.remote_id,
            "name": contact.name,
            "is_supplier": contact.is_supplier,
            "is_customer": contact.is_customer,
            "email_address": contact.email_address,
            "tax_number": contact.tax_number,
            "status": contact.status,
            "currency": contact.currency,
            "remote_updated_at": contact.remote_updated_at.isoformat(),
            "company": contact.company,
            "addresses": [
                {
                    "type": addr.type,
                    "street_1": addr.street_1,
                    "street_2": addr.street_2,
                    "city": addr.city,
                    "state": addr.state,
                    "country_subdivision": addr.country_subdivision,
                    "country": addr.country,
                    "zip_code": addr.zip_code,
                    "created_at": addr.created_at.isoformat(),
                    "modified_at": addr.modified_at.isoformat(),
                }
                for addr in contact.addresses
            ],
            "phone_numbers": [
                {
                    "number": phone.number,
                    "type": phone.type,
                    "created_at": phone.created_at.isoformat(),
                    "modified_at": phone.modified_at.isoformat(),
                }
                for phone in contact.phone_numbers
            ],
            "remote_was_deleted": contact.remote_was_deleted,
            "created_at": contact.created_at.isoformat(),
            "modified_at": contact.modified_at.isoformat(),
            "field_mappings": contact.field_mappings,
            "remote_data": erp_remote_data,
        }
        formatted_data.append(formatted_entry)
    kloo_format_json = {"erp_contacts": formatted_data}

    return kloo_format_json
