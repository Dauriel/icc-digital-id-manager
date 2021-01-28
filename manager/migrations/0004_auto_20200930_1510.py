# Generated by Django 3.1 on 2020-09-30 15:10

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_extensions.db.fields.json
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0003_credentialrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="credentialrequest",
            name="code",
            field=models.CharField(default=uuid.uuid4, max_length=36),
        ),
        migrations.AddField(
            model_name="credentialrequest",
            name="email",
            field=models.EmailField(
                blank=None, default="icc-digital-id-manager@demo.com", max_length=254
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="CredentialOffer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("connection_id", models.CharField(max_length=100)),
                (
                    "offer_json",
                    django_extensions.db.fields.json.JSONField(default=dict),
                ),
                ("accepted", models.BooleanField(default=False)),
                (
                    "credential_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="connection_offers",
                        to="manager.credentialrequest",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="ConnectionInvitation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("connection_id", models.CharField(max_length=100)),
                (
                    "invitation_json",
                    django_extensions.db.fields.json.JSONField(default=dict),
                ),
                ("accepted", models.BooleanField(default=False)),
                (
                    "credential_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="connection_invitations",
                        to="manager.credentialrequest",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
    ]