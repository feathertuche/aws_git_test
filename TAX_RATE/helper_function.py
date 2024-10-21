"""
helper functiosn to support Sage TAx rates
"""
from merge_integration.helper_functions import api_log


def get_nested(data, keys):
    """
    A helper function to take full path of the incoming Sage response payload
    """
    for key in keys:
        data = data.get(key, None)
        if data is None:
            return None
    return data


def sage_tax_rate(tax_rates_details, ):
    """
    Handles POST requests to insert Sage Tax Rate data into the Kloo Tax Rate system.

    Returns:
        Response indicating success or failure of data insertion.
    """
    try:
        # Fetch Sage data for Tax Details
        session_response, tax_details_response = tax_rates_details.get_itg_tax_details()
        # We are only interested in tax_details_response for further processing
        for tax in [tax_details_response]:
            if tax["status"] is False:
                return {
                    "status": False,
                    "error": f"Error in passthrough response: {tax_details_response}",
                }
            # Define the key path
            key_path = ["response", "response", "operation", "result", "data", "taxdetail"]
            # Fetch sage tax detail
            sage_tax_details = get_nested(tax, key_path)
            if sage_tax_details:
                return {
                    "status": True,
                    "message": "Sage passthrough response",
                    "data": sage_tax_details
                }

        return {
            "status": False,
            "error": "Tax details not found in the response"
        }

    except Exception as e:
        api_log(msg=f"Error fetching sage data: {e}")
        raise e
