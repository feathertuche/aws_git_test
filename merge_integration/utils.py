import os
import sys
from merge.client import Merge as MergeClient
import boto3
import json
from dotenv import load_dotenv

def create_merge_client():
    base_url = os.environ.get("BASE_URL")
    account_token = os.environ.get("ACCOUNT_TOKEN")
    api_key = os.environ.get("API_KEY")
    if not all([base_url, account_token, api_key]):
        raise ValueError("Missing required environment variables for Merge client.")

    return MergeClient(base_url=base_url, account_token=account_token, api_key=api_key)

def get_secret_data(secret_id):
    """
    This function is used to retrieve secret password.
    """
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_id)
    data = response['SecretString']
    return json.loads(data)


def get_db_password(rds_host):
    """
    Get the database password from RDS.
    """
    secretid_key_dict = {'dev': {'secret_id': 'kloo-dev-environment-variables', 'key': 'Dev_DB_PASSWORD'},
                        'stage': {'secret_id': 'kloo-Stage-Environment-Variables', 'key': 'Stage_db_password'},
                        'demo': {'secret_id': 'kloo_environment_variables_demo', 'key': 'Demo_DB_Password'},
                        'prod': {'secret_id': 'kloo_environment_variable_prod', 'key': 'Production_DB_Password'}}

    environments_list = list(secretid_key_dict.keys())

    if rds_host is not None:
        environment = next((substring for substring in environments_list if substring in rds_host), None)
        if environment:
            secretid_key = secretid_key_dict[environment]
            secret_id = secretid_key['secret_id']
            data2 = get_secret_data(secret_id)
            ERP_DB_PASSWORD = data2[secretid_key['key']]
            return ERP_DB_PASSWORD

    # Return a default value or handle the case when no environment is found
    return None