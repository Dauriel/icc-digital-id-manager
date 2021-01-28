import pytest
from django.test import override_settings
from aca.client import ACAClient
from manager.models import ConnectionInvitation, CredentialOffer
from manager.credential_workflow import (
    _step_accept,
    connection_invitation_accept,
    is_credential_request_ready,
    credential_offer_accept,
    connection_invitation_create,
    credential_offer_create,
)


@pytest.mark.django_db
def test_connection_invitation_accept(connection_invitation):
    test_id = "1"
    assert not ConnectionInvitation.objects.filter(connection_id=test_id).first().accepted
    accepted_invitation = connection_invitation_accept(test_id)
    assert accepted_invitation.accepted
    assert ConnectionInvitation.objects.filter(connection_id=test_id).first().accepted


@pytest.mark.django_db
def test_connection_invitation_accept_not_found(connection_invitation):
    connection_invitation_accept("invalid")
    assert not ConnectionInvitation.objects.get(
        connection_id=connection_invitation.connection_id
    ).accepted


@pytest.mark.django_db
def test_credential_offer_accept(credential_offer):
    connection_id = "1"
    assert not CredentialOffer.objects.filter(connection_id=connection_id).first().accepted
    accepted_credential = credential_offer_accept(connection_id=connection_id)
    assert accepted_credential.accepted
    assert CredentialOffer.objects.filter(connection_id=connection_id).first().accepted


@pytest.mark.django_db
def test_credential_offer_accept_not_found(credential_offer):
    credential_offer_accept("invalid")
    assert not CredentialOffer.objects.get(id=credential_offer.id).accepted


@pytest.mark.django_db
def test_step_accept_connection_invitation(connection_invitation):
    connection_id = "1"
    assert not ConnectionInvitation.objects.filter(connection_id=connection_id).first().accepted
    accepted_invitation = _step_accept(ConnectionInvitation, connection_id=connection_id)
    assert accepted_invitation.accepted
    assert ConnectionInvitation.objects.filter(connection_id=connection_id).first().accepted


@pytest.mark.django_db
def test_step_accept_connection_invitation(credential_offer):
    connection_id = "1"
    assert not CredentialOffer.objects.filter(connection_id=connection_id).first().accepted
    accepted_credential = _step_accept(CredentialOffer, connection_id=connection_id)
    assert accepted_credential.accepted
    assert CredentialOffer.objects.filter(connection_id=connection_id).first().accepted


@pytest.mark.django_db
@override_settings(ACA_PY_URL="aca.py.url", ACA_PY_TRANSPORT_URL="aca.py.transport.url")
def test_connection_invitation_create(requests_mock, mocker, credential_request):
    mock_result = {
        "connection_id": "1",
        "invitation": {},
        "invitation_url": "invitation.url",
    }
    mocker.patch.object(
        ACAClient,
        "create_connection_invitation",
        return_value=mock_result,
    )
    invitation_url, invitation_b64 = connection_invitation_create(credential_request)
    assert invitation_url is not None
    assert invitation_url == "invitation.url"
    assert invitation_b64 is not None
    assert invitation_b64 == "e30="


@pytest.mark.django_db
@override_settings(ACA_PY_URL="aca.py.url", ACA_PY_TRANSPORT_URL="aca.py.transport.url")
def test_connection_invitation_create_accepted(requests_mock, mocker, connection_invitation):
    connection_invitation.accepted = True
    connection_invitation.save()
    mock_result = {
        "connection_id": "2",
        "invitation": {},
        "invitation_url": "invitation.url",
    }
    mocker.patch.object(
        ACAClient,
        "create_connection_invitation",
        return_value=mock_result,
    )
    invitation_url, invitation_b64 = connection_invitation_create(
        connection_invitation.credential_request
    )
    assert invitation_url is not None
    assert invitation_url == "invitation.url"
    assert invitation_b64 is not None
    assert invitation_b64 == "e30="


@pytest.mark.django_db
@override_settings(ACA_PY_URL="aca.py.url", ACA_PY_TRANSPORT_URL="aca.py.transport.url")
def test_connection_invitation_create_not_accepted(requests_mock, mocker, connection_invitation):
    mock_result = {
        "connection_id": "1",
        "invitation": {"invitation": 0},
        "invitation_url": "invitation.url",
    }
    mocker.patch.object(
        ACAClient,
        "create_connection_invitation",
        return_value=mock_result,
    )
    invitation_url, invitation_b64 = connection_invitation_create(
        connection_invitation.credential_request
    )
    assert invitation_url is not None
    assert invitation_url == "invitation.test.url"
    assert invitation_b64 is not None
    assert (
        invitation_b64
        == "eyJjb25uZWN0aW9uX2ludml0YXRpb25fa2V5XzEiOiAiY29ubmVjdGlvbl9pbnZpdGF0aW9uX3ZhbHVlXzEiLCAiY29ubmVjdGlvbl9pbnZpdGF0aW9uX2tleV8yIjogImNvbm5lY3Rpb25faW52aXRhdGlvbl92YWx1ZV8yIn0="
    )


@pytest.mark.django_db
@override_settings(ACA_PY_URL="aca.py.url", ACA_PY_TRANSPORT_URL="aca.py.transport.url")
def test_credential_offer_create(mocker, connection_invitation):
    connection_id = connection_invitation.connection_id
    expected_result = {
        "auto_issue": True,
        "connection_id": connection_id,
        "cred_def_id": connection_invitation.credential_request.credential_definition.credential_id,
        "credential_preview": {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/issue-credential/1.0/credential-preview",
            "attributes": [
                {
                    "name": "credential_data_key_1",
                    "value": "credential_data_value_1",
                    "mime-type": "text/plain",
                },
                {
                    "name": "credential_data_key_2",
                    "value": "credential_data_value_2",
                    "mime-type": "text/plain",
                },
            ],
        },
    }
    mocker.patch.object(
        ACAClient,
        "send_credential_offer",
        return_value=None,
    )
    assert not CredentialOffer.objects.filter(connection_id=connection_id).first()
    credential_offer = credential_offer_create(
        connection_id=connection_id, connection_invitation=connection_invitation
    )
    assert credential_offer == expected_result

    credential_offer_from_db = CredentialOffer.objects.filter(connection_id=connection_id).first()

    assert credential_offer_from_db
    assert credential_offer_from_db.offer_json == credential_offer
    assert credential_offer_from_db.connection_id == connection_id
    assert credential_offer_from_db.credential_request == connection_invitation.credential_request
    assert credential_offer_from_db.accepted == False


@pytest.mark.django_db
def test_is_credential_request_ready(credential_offer):
    code = "12345"
    request = is_credential_request_ready(code)
    assert request is not None
    assert request == credential_offer.credential_request


@pytest.mark.django_db
def test_is_credential_request_ready_accepted_offer(credential_offer):
    credential_offer.accepted = True
    credential_offer.save()
    code = "12345"
    with pytest.raises(RuntimeError):
        request = is_credential_request_ready(code)
        assert not request
