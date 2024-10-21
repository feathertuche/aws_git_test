# Generated by Django 5.0.1 on 2024-02-15 09:33

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ERPLogs",
            fields=[
                (
                    "id",
                    models.UUIDField(editable=False, primary_key=True, serialize=False),
                ),
                ("org_id", models.CharField(max_length=255)),
                ("link_token_id", models.CharField(max_length=36)),
                ("link_token", models.CharField(max_length=255)),
                ("label", models.CharField(max_length=255)),
                ("sync_start_time", models.DateTimeField()),
                ("sync_end_time", models.DateTimeField()),
                (
                    "sync_status",
                    models.CharField(
                        choices=[
                            ("in progress", "in progress"),
                            ("success", "success"),
                            ("failed", "failed"),
                        ],
                        default="in progress",
                        max_length=15,
                    ),
                ),
                ("error_message", models.TextField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "erp_sync_logs",
            },
        ),
    ]
