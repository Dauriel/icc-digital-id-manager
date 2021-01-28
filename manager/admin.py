from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from aca.client import ACAClientFactory
from manager.models import (
    Schema,
    CredentialDefinition,
    CredentialRequest,
    ConnectionInvitation,
    CredentialOffer,
)


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_id", "enabled", "creator", "created")
    list_display_links = ("id",)
    list_filter = ("enabled",)
    search_fields = (
        "creator__username",
        "creator__first_name",
        "creator__last_name",
        "name",
        "schema_json",
    )

    change_form_template = "schema_changeform.html"

    def response_change(self, request, obj):
        if "_upload-schema" in request.POST:
            self.upload_schema(obj)
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)

    def upload_schema(self, instance):
        aca_client = ACAClientFactory.create_client()
        aca_schema = aca_client.create_schema(instance.schema_json)
        instance.schema_id = aca_schema.get("schema_id")
        instance.save()


@admin.register(CredentialDefinition)
class CredentialDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "credential_id",
        "schema",
        "enabled",
        "creator",
        "created",
    )
    list_display_links = ("id",)
    list_filter = ("enabled",)
    search_fields = (
        "creator__username",
        "creator__first_name",
        "creator__last_name",
        "name",
    )

    change_form_template = "credentialdefinition_changeform.html"

    def response_change(self, request, obj):
        if "_upload-cred-def" in request.POST:
            self.upload_cred_def(obj)
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)

    def upload_cred_def(self, instance):
        aca_client = ACAClientFactory.create_client()
        aca_schema = aca_client.create_credential_definition(instance.credential_json())
        instance.credential_id = aca_schema.get("credential_definition_id")
        instance.save()


@admin.register(CredentialRequest)
class CredentialRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "credential_definition",
        "code",
        "email",
        "invitation_url",
        "connection",
        "credential",
        "creator",
        "created",
        "modified",
    )
    list_display_links = ("id",)
    list_filter = ("credential_definition",)
    search_fields = (
        "credential_data",
        "creator__username",
        "creator__first_name",
        "creator__last_name",
        "credential_definition__name",
        "credential_definition__credential_id",
    )

    def connection(self, item):
        connection_invitation = item.connection_invitations.order_by("-created").first()
        return connection_invitation.accepted if connection_invitation else False

    def credential(self, item):
        credential_offer = item.credential_offers.order_by("-created").first()
        return credential_offer.accepted if credential_offer else False

    connection.boolean = True
    credential.boolean = True


@admin.register(ConnectionInvitation)
class ConnectionInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "connection_id",
        "credential_request_link",
        "accepted",
        "created",
        "modified",
    )
    list_display_links = ("id",)
    list_filter = ("accepted",)
    search_fields = ("connection_id",)

    def credential_request_link(self, item):
        url = reverse("admin:manager_credentialrequest_change", args=[item.credential_request.id])
        link = f'<a href="{url}">{item.credential_request}</a>'
        return mark_safe(link)

    credential_request_link.short_description = "Credential Request"


@admin.register(CredentialOffer)
class CredentialOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "connection_id",
        "credential_request",
        "accepted",
        "created",
        "modified",
    )
    list_display_links = ("id",)
    list_filter = ("accepted",)
    search_fields = ("connection_id",)
