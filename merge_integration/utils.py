import os
import sys
from merge import Merge
from merge.client import Merge

def create_merge_client():
    base_url = os.environ.get("BASE_URL")
    account_token = os.environ.get("ACCOUNT_TOKEN")
    api_key = os.environ.get("API_KEY")
    if not all([base_url, account_token, api_key]):
        raise ValueError("Missing required environment variables for Merge client.")

    return Merge(base_url=base_url, account_token=account_token, api_key=api_key)