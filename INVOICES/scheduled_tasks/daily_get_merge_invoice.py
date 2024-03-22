"""
Cron job to get invoices from the merge and post them to kloo
"""

from merge_integration.helper_functions import api_log


def main():
    # Get all invoices from merge
    api_log(msg="Getting invoices from merge")
