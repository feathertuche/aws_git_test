from django.core.management.base import BaseCommand
from INVOICES.models import Invoice, InvoiceAttachmentLogs
from LINKTOKEN.model import ErpLinkToken
from merge_integration.helper_functions import api_log
from services.merge_service import MergeInvoiceApiService
from django.db.models import Count, Q


class Command(BaseCommand):
    api_log(msg='..........Processing pending attachment(s) through CRON.........')

    def handle(self, *args, **options):
        """
        The entry point function for Django management command execution
        """

        # self.pending_attachment_creation()
        Command.check_logs_for_success()


    @staticmethod
    def fetch_pending_attachment_status():
        """
        Function to check if send_to_accounting_portal_attachment field in invoice
        table is in pending state
        """
        t = Invoice.objects.filter(send_to_accounting_portal='pending').values_list('id', 'invoice_number')

        # check if the data is present based on the filter
        if t:
            ids, invoice_numbers = zip(*t)
            return list(ids), list(invoice_numbers)
        else:
            return [], []  # Return empty lists if no data
        # print("ID List:", len(id_list))
        # print("Invoice Number List:", len(invoice_number_list))

    @staticmethod
    def check_logs_for_success():
        invoice_ids, invoice_nums = Command.fetch_pending_attachment_status()

        # Open a text file to write the output
        with open('output.txt', 'w') as f:
            # Loop through each invoice_id
            for ids in invoice_ids:
                # Query tbl2 to check for 'attachment' and 'invoice' types with status 'success'
                matching_rows = InvoiceAttachmentLogs.objects.filter(invoice_id=ids, status='success')

                # Extract rows with different types
                attachment = matching_rows.filter(type='attachment').exists()
                invoice = matching_rows.filter(type='invoice').exists()

                # Ensure both types are present
                if attachment and invoice:
                    f.write(f"Invoice {ids} has both 'attachment' and 'invoice' types with success status.\n")
                else:
                    f.write(f"Invoice {ids} is missing a 'success' status for one of the types.\n")

    @staticmethod
    def extract_token_info(attachment_data):
        """
        Extract account_token and org_id for each erp_link_token_id.
        Handles missing erp_link_token_id gracefully.
        """
        # Collect all unique erp_link_token_ids from attachment_data
        erp_link_token_ids = [erp_link_token_id for _, _, _, _, erp_link_token_id in attachment_data]
        # api_log(msg=f"erp_link_token_ids::: {erp_link_token_ids}")
        # Create a dictionary to hold account_token and org_id for each erp_link_token_id
        token_info = {}
        missing_tokens = []

        for token_id in erp_link_token_ids:
            # api_log(msg=f"token_id::: {token_id}")
            filter_token = ErpLinkToken.objects.filter(id=token_id).first()
            # api_log(msg=f"this is filter token bloc{filter_token}")
            if filter_token:
                token_info[token_id] = {
                    'account_token': filter_token.account_token,
                    'org_id': filter_token.org_id
                }
                api_log(msg=f"token_info bloc::: {token_info[token_id]}")
            else:
                # Log a warning or message instead of raising an exception
                missing_tokens.append(token_id)
                # Optionally log a message here if using a logging framework
                api_log(msg=f"Warning: No ErpLinkToken found for id {token_id}")

        # Optionally log missing tokens if necessary
        if missing_tokens:
            print(f"Missing erp_link_token_id(s): {', '.join(map(str, missing_tokens))}")

        return token_info

    @staticmethod
    def pending_attachment_creation():
        """
        create xero Invoice attachment
        """
        MAX_RETRIES = 5
        # calling fetch_pending_attachment_status to fetch ORM output
        attachment_data = Command.fetch_pending_attachment_status()

        # Ensure there is data to work with
        if not attachment_data:
            return False

        # Extract token info
        # api_log(msg=f"attachment_data in attach creation function in cron file::: {attachment_data}")
        token_info = Command.extract_token_info(attachment_data)
        for kloo_invoice_id, invoice_number, invoice_attachment, erp_id, erp_link_token_id in attachment_data:

            # Get the invoice object to check and update retry count
            retry_count = Command.get_retry_count(kloo_invoice_id)

            # Check if retry count is less than max retries
            if retry_count >= MAX_RETRIES:
                api_log(msg=f"Retry limit reached for Invoice ID: {kloo_invoice_id}. Skipping.")
                continue

            if erp_link_token_id not in token_info:
                continue  # Skip if no token info available for this erp_link_token_id

            account_token = token_info[erp_link_token_id]['account_token']
            org_id = token_info[erp_link_token_id]['org_id']

            # Instantiate MergeInvoiceApiService with account_token, org_id, and erp_link_token_id
            merge_service = MergeInvoiceApiService(
                account_token,
                org_id,
                erp_link_token_id
            )
            attachment_payload = {
                "id": kloo_invoice_id,
                "file_name": invoice_attachment,
                "file_url": f'http://dev.getkloo.com/{invoice_attachment}',
                "integration_params": {
                    "transaction_id": erp_id,
                    "transaction_name": "invoices",  # hard-coded value
                },
            }
            # api_log(msg=f"attachment_payload::: {attachment_payload}")
            create_attachment = merge_service.create_attachment(attachment_payload)
            # api_log(msg=f"create_attachment:::=> {create_attachment}")
            if create_attachment:
                # If attachment creation is successful, update the status to 'success'
                Command.update_invoice_status(kloo_invoice_id, "success", retry_count=0)
                api_log(msg=f"Successfully created attachment for Invoice ID: {kloo_invoice_id}")
            else:
                # If creation fails, increment retry count
                Command.update_invoice_status(kloo_invoice_id, "pending", retry_count=retry_count + 1)
                api_log(
                    msg=f"Failed to create attachment for Invoice ID: {kloo_invoice_id}. Retry count: {retry_count}")

        return True

    @staticmethod
    def get_retry_count(kloo_invoice_id):
        """
        Function to get retry count from the database
        """
        return Invoice.objects.filter(id=kloo_invoice_id).values_list('retry_count', flat=True).first()

    @staticmethod
    def update_invoice_status(kloo_invoice_id, status, retry_count):
        """
        Function to update invoice status and retry count in the database
        """
        Invoice.objects.filter(id=kloo_invoice_id).update(
            send_to_accounting_portal_attachment=status,
            retry_count=retry_count
        )
