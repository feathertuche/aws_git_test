import os
from jira import JIRA
import requests

# Get environment variables
jira_server = os.getenv('JIRA_SERVER')
jira_username = os.getenv('JIRA_USERNAME')
jira_api_token = os.getenv('JIRA_API_TOKEN')
github_token = os.getenv('GITHUB_TOKEN')
pr_title = os.getenv('PR_TITLE')
pr_number = os.getenv('PR_NUMBER')
repo_owner = os.getenv('REPO_OWNER')
repo_name = os.getenv('REPO_NAME')

# Connect to Jira
jira_options = {'server': jira_server}
jira = JIRA(options=jira_options, basic_auth=(jira_username, jira_api_token))

def update_pr_title_with_jira_url(pr_title, pr_number, repo_owner, repo_name):
    # Jira issue URL to append to PR title
    jira_url = f"{jira_server}/browse/{pr_title.split()[0]}"

    # Update pull request title with Jira issue URL
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    pr_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}'
    update_data = {'title': f"{pr_title} ({jira_url})"}
    response = requests.patch(pr_url, headers=headers, json=update_data)

    if response.status_code == 200:
        print(f"Pull request title updated successfully: {update_data['title']}")
    else:
        print(f"Failed to update pull request title. Status code: {response.status_code}")

# Extract issue_id from PR title (first string in the title)
issue_id = pr_title.split()[0]

if not issue_id:
    print("No issue ID found in PR title.")
    exit(1)  # Fail the check if no issue ID is found

# Define JQL (Jira Query Language) to find the specific issue
jql = f'id = "{issue_id}"'

# Get the issue from Jira
issues = jira.search_issues(jql)  # Adjust maxResults as needed

# Check if the issue_id exists in the project
if not issues:
    print(f"Issue ID {issue_id} not found.")
    exit(1)  # Fail the check if the issue ID is not found

# Since we're looking for a specific issue, there should only be one result
issue = issues[0]

# Prepare code change information
code_change_info = (f"A pull request has been created: {os.getenv('GITHUB_SERVER_URL')}/"
                    f"{os.getenv('GITHUB_REPOSITORY')}/pull/{pr_number}\n"
                    f"pr_title: {pr_title}")

# Retrieve current value of the "Code Changes" field
code_changes_field_id = 'customfield_10045'  # Replace with your actual field ID or name
current_value = getattr(issue.fields, code_changes_field_id, None)

# Append new code change information to current value, if exists
if current_value:
    new_value = f"{current_value}\n\n{code_change_info}"  # Separate with double newline for readability
else:
    new_value = code_change_info

# Update the Jira issue with the updated "Code Changes" field
issue.update(fields={code_changes_field_id: new_value})

print(f"Updated issue {issue_id} with code change information.")

# Update PR title with Jira URL
update_pr_title_with_jira_url(pr_title, pr_number, repo_owner, repo_name)