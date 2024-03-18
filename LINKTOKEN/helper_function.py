from django.db import connection

from LINKTOKEN.model import ErpLinkToken


def get_org_entity(organization_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT
        soe.id
        FROM organization_configurations soc1
        JOIN organization_entity_details soe ON soe.organization_configurations_id = soc1.id
        WHERE 1 = 1
        AND soc1.organization_id = %s
        AND soc1.config_key_name = 'org_entities'
        AND soe.deleted_at IS NULL
        ORDER BY CASE WHEN soe.status = 'default' THEN 0 ELSE 1 END, soe.id ASC""",
            [organization_id],
        )
        row = cursor.fetchone()
        return row


def create_erp_link_token(request):
    link_token_record = ErpLinkToken(**request)

    link_token_record.save()
    return link_token_record