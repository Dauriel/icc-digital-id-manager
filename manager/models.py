import uuid
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.fields.json import JSONField
from model_utils.models import TimeStampedModel
import re


class Schema(TimeStampedModel):
    name = models.CharField(max_length=50)
    schema_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    enabled = models.BooleanField(default=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="schemas",
    )
    schema_json = JSONField()

    def __str__(self):
        if self.schema_id:
            return "{0}:{1}".format(self.name, self.schema_id)

        return "{0}:".format(self.name)

    class Meta:
        ordering = ("-created",)


class CredentialDefinition(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    credential_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        limit_choices_to={"schema_id__isnull": False},
    )
    enabled = models.BooleanField(default=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="credential_definitions",
    )
    support_revocation = models.BooleanField(default=True)

    def credential_json(self):
        return {
            "schema_id": self.schema.schema_id,
            "tag": re.sub("\W", "", self.name.lower()),
            "support_revocation": str(self.support_revocation).lower(),
        }

    def __str__(self):
        if self.credential_id:
            return "{0}:{1}".format(self.name, self.credential_id)

        return "{0}:".format(self.name)

    class Meta:
        ordering = ("-created",)


class CredentialRequest(TimeStampedModel):
    code = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    credential_definition = models.ForeignKey(
        CredentialDefinition,
        on_delete=models.CASCADE,
        related_name="credential_requests",
        limit_choices_to={"credential_id__isnull": False},
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="credential_requests",
    )
    credential_data = JSONField()
    email = models.EmailField(blank=None, null=False)

    def __str__(self):
        return f"{self.code}"

    @property
    def invitation_url(self):
        return f"{settings.SITE_URL}/credential-obtain?code={self.code}"

    @property
    def connection_invitation_polling_url(self):
        return f"{settings.SITE_URL}/connection-check?code={self.code}"

    @property
    def credential_offer_polling_url(self):
        return f"{settings.SITE_URL}/credential-check?code={self.code}"

    class Meta:
        ordering = ("-created",)


class ConnectionInvitation(TimeStampedModel):
    connection_id = models.CharField(max_length=100, unique=True)
    invitation_json = JSONField()
    accepted = models.BooleanField(default=False)
    credential_request = models.ForeignKey(
        CredentialRequest,
        on_delete=models.CASCADE,
        related_name="connection_invitations",
    )

    def __str__(self):
        return f"Conn:{self.connection_id}-accepted:{self.accepted}"


class CredentialOffer(TimeStampedModel):
    connection_id = models.CharField(max_length=100, unique=True)
    offer_json = JSONField()
    accepted = models.BooleanField(default=False)
    credential_request = models.ForeignKey(
        CredentialRequest,
        on_delete=models.CASCADE,
        related_name="credential_offers",
    )

    def __str__(self):
        return f"Offer:{self.connection_id}-accepted:{self.accepted}"
