"""
Helper functions for COMPANY_INFO app
"""
from merge_integration.helper_functions import api_log
from LINKTOKEN.model import ErpLinkToken
from TAX_RATE.views import SageFetchTaxDetails


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


def handle_sage_intacct(request):
    """
    Handles the Sage Intacct integration logic, including fetching
    the integration name and performing necessary actions if it matches.
    Returns a status message or error if applicable.
    """

    erp_link_token_id = request.data.get("erp_link_token_id")
    integration_name = ErpLinkToken.get_integration_name_token_by_id(erp_link_token_id)
    api_log(msg=f"Integration name in COMPANY INFO helper function: {integration_name}")

    # check if there is any integration name at all
    if integration_name:
        integration_name = integration_name.strip().lower().replace("-", " ")
        api_log(msg=f"Integration name after normalization: {integration_name}")

        # Check if the integration name is Sage Intacct
        if integration_name == "sage intacct":
            api_log(msg="Started: SAGE TAX RATES")

            try:
                # Call Sage Tax Rate APIView class to fetch tax rate from Sage Intacct
                sage_fetch_tax_details = SageFetchTaxDetails(erp_link_token_id=erp_link_token_id)
                sage_tax_rate_response = sage_fetch_tax_details.post(request)
                api_log(msg=f"sage_tax_rate_response::: {sage_tax_rate_response}")
                api_log(msg="Ended: SAGE TAX RATES")
                return {"status": "success", "data": sage_tax_rate_response}
            except Exception as e:
                api_log(msg=f"Error during Sage Intacct processing: {str(e)}")
                return {"status": "error", "message": str(e)}

    message = "Integration name is not Sage Intacct, skipping Sage Tax Rate"
    api_log(msg=f"ignore message:: {message}")
    return {"status": "no_action", "message": message}