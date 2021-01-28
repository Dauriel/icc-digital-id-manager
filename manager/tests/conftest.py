import pytest
from django.contrib.auth.models import User
from post_office.models import EmailTemplate

from manager.models import (
    ConnectionInvitation,
    CredentialOffer,
    CredentialRequest,
    CredentialDefinition,
    Schema,
)


@pytest.fixture
def admin_user():
    return User.objects.create_user("admin", "admin@admin.com", "admin123")


@pytest.fixture
def schema(admin_user):
    return Schema.objects.create(
        name="schema",
        schema_id="testschema:1:id:1.0",
        creator=admin_user,
        schema_json={
            "attributes": ["schema_key_1", "schema_key_2"],
        },
    )


@pytest.fixture
def credential_definition(schema, admin_user):
    return CredentialDefinition.objects.create(
        name="credential_definition",
        credential_id="testcredentialdefinition:1:2:3:test",
        schema=schema,
        creator=admin_user,
        support_revocation=True,
    )


@pytest.fixture
def credential_request(credential_definition, admin_user):
    return CredentialRequest.objects.create(
        credential_definition=credential_definition,
        creator=admin_user,
        credential_data={
            "credential_data_key_1": "credential_data_value_1",
            "credential_data_key_2": "credential_data_value_2",
        },
        email="test@emails.com",
        code="12345",
    )


@pytest.fixture
def credential_offer(credential_request):
    return CredentialOffer.objects.create(
        connection_id="1",
        offer_json={
            "offer_key_1": "offer_value_1",
            "offer_key_2": "offer_value_2",
        },
        credential_request=credential_request,
    )


@pytest.fixture
def connection_invitation(credential_request):
    return ConnectionInvitation.objects.create(
        connection_id="1",
        invitation_json={
            "connection_invitation_key_1": "connection_invitation_value_1",
            "connection_invitation_key_2": "connection_invitation_value_2",
            "invitation": {
                "connection_invitation_key_1": "connection_invitation_value_1",
                "connection_invitation_key_2": "connection_invitation_value_2",
            },
            "invitation_url": "invitation.test.url",
        },
        credential_request=credential_request,
    )


@pytest.fixture
def invitation_template():
    name = "invitation"
    return EmailTemplate.objects.create(
        name=name,
        subject="Test UN Digital ID Credential Issuance",
        content="",
        html_content="<html></html>",
    )
