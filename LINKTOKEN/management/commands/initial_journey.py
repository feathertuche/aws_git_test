from datetime import timezone

from django.core.management.base import BaseCommand
from django.db import connection

from LINKTOKEN.queries import store_daily_or_force_sync_log, store_erp_daily_sync_logs
from merge_integration.helper_functions import api_log


class Command(BaseCommand):
    """
    Sanitization command to add the initial sync log for all completed linked accounts
    """

    help = "Sanitization command to add the initial sync log for all completed linked accounts"

    def handle(self, *args, **options):
        # get all linked account whose status are complete and daily force sync log is null
        linked_account_query = """
                            SELECT
                                erp_link_token.id,
                                label,
                                erp_sync_logs.sync_start_time,
                                erp_sync_logs.sync_end_time,
                                erp_link_token.org_id
                            FROM erp_link_token
                            LEFT JOIN daily_or_force_sync_log
                            ON erp_link_token.id = daily_or_force_sync_log.link_token_id
                            COLLATE utf8mb4_unicode_ci
                            JOIN erp_sync_logs
                            ON erp_link_token.id = erp_sync_logs.link_token_id
                            COLLATE utf8mb4_unicode_ci
                            WHERE erp_link_token.status = 'COMPLETE'
                            AND daily_or_force_sync_log.id is NUll
                            """

        # execute the query and get the linked accounts
        with connection.cursor() as cursor:
            cursor.execute(linked_account_query)
            linked_accounts = cursor.fetchall()

        if len(linked_accounts) == 0:
            print("No linked accounts found")
            return

        # get the linked account ids
        api_log(msg=f"Linked account ids: {linked_accounts}")

        # get all unqiue linked account ids
        linked_account_ids = set([account[0] for account in linked_accounts])

        # get the linked account ids
        api_log(msg=f"Linked account ids: {linked_account_ids}")

        for linked_account_id in linked_account_ids:
            # get the linked account details
            linked_account_modules_logs = [
                account
                for account in linked_accounts
                if account[0] == linked_account_id
            ]

            # get the lowest sync start time
            start_time = min(account[2] for account in linked_account_modules_logs)
            # get the highest sync end time
            end_time = max(account[3] for account in linked_account_modules_logs)

            api_log(msg=f"start_time: {start_time}, end_time: {end_time}")

            # get the linked account details
            api_log(msg=f"Linked account details: {linked_account_modules_logs}")

            # first create a daily sync log record
            store_daily_or_force_sync_log(
                {
                    "link_token_id": linked_account_id,
                    "sync_type": "daily_sync",
                    "status": "success",
                    "sync_date": start_time.astimezone(timezone.utc),
                    "start_date": start_time.astimezone(timezone.utc),
                    "end_date": end_time.astimezone(timezone.utc),
                    "is_initial_sync": True,
                }
            )

            # create the erp daily sync logs for all modules with the same start and end time
            for linked_account_module_log in linked_account_modules_logs:
                store_erp_daily_sync_logs(
                    {
                        "org_id": linked_account_module_log[4],
                        "link_token_id": linked_account_id,
                        "daily_or_force_sync_log_id": linked_account_id,
                        "link_token": linked_account_id,
                        "label": linked_account_module_log[1],
                        "sync_start_time": linked_account_module_log[2].astimezone(
                            timezone.utc
                        ),
                        "sync_end_time": linked_account_module_log[3].astimezone(
                            timezone.utc
                        ),
                        "sync_status": "success",
                        "error_message": f"API {linked_account_module_log[1]} Info completed successfully",
                    }
                )
