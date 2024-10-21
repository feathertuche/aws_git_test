"""
Util functions for the link-token app
"""


def webhook_sync_modul_filter(module_name_merge):
    """
    Filter the module name to be displayed in the webhook sync module
    """
    module_label_map = {
        "TaxRate": "TAX RATE",
        "TrackingCategory": "TRACKING CATEGORIES",
        "CompanyInfo": "COMPANY INFO",
        "Account": "ACCOUNTS",
        "Contact": "CONTACTS",
        "Invoice": "INVOICES",
        "Item": "ITEMS",
    }
    return module_label_map.get(module_name_merge)
