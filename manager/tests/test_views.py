import pytest

from unittest.mock import patch
from rest_framework import status
from django.test import override_settings
from post_office import mail
from manager.models import CredentialRequest, CredentialDefinition
from manager.tests.api_view_test_classes import (
    TestRetrieveAPIView,
    TestListCreateAPIView,
)


@pytest.mark.django_db
class TestCredentialRequestRetrieveAPIView(TestRetrieveAPIView):
    __test__ = True
    path_base = "credential-request"
    test_pk = "1"
    path = f"{path_base}/{test_pk}"

    @pytest.fixture
    def setup(self, credential_request):
        return credential_request

    def test_retrieve(self, authenticate, credential_request):
        response = self.client.get(f"/credential-request/{credential_request.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        assert list(data.keys()) == ["code", "invitation_url"]
        assert data["code"] == "12345"
        assert response.get("ETag")


@pytest.mark.django_db
class TestCredentialRequestListCreateAPIView(TestListCreateAPIView):
    __test__ = True
    path = "credential-request"
    post_data = {
        "credential_definition": "testcredentialdefinition:1:2:3:test",
        "email": "test@mail.com",
        "credential_data": '{ "schema_key_1": "Silly String 1", "schema_key_2": "Silly String 2" }',
    }

    @pytest.fixture
    def setup(self, credential_request, mocker):
        mocker.patch(
            "manager.credential_workflow.connection_invitation_create",
            return_value=("invitation.url", "e30="),
        )
        return credential_request

    def test_list(self, authenticate, setup):
        assert CredentialRequest.objects.all().first()
        response = self.client.get(f"/{self.path}")
        assert response.status_code == status.HTTP_200_OK
        assert response.get("ETag")
        assert len(response.data.get("results")) == 1
        assert response.data["results"][0] == {
            "code": "12345",
            "invitation_url": "http://test.com/credential-obtain?code=12345",
        }

    @patch.object(mail, "send")
    def test_create(
        self, mock_send, authenticate, setup, credential_definition, invitation_template
    ):
        response = self.client.post(f"/{self.path}", self.post_data)
        assert response.status_code == status.HTTP_201_CREATED

        elements = CredentialRequest.objects.all()
        assert len(elements) == 2
        request = elements.first()
        code = request.code
        assert len(code) == 36  # is UUID
        assert code == response.data["code"]
        invitation_url = request.invitation_url
        assert invitation_url == response.data["invitation_url"]
        assert invitation_url == f"http://test.com/credential-obtain?code={code}"
        mock_send.assert_called()

    def test_create_two_same_data(self, authenticate, setup, credential_definition):
        assert not CredentialRequest.objects.filter(email="test@mail.com")

        response1 = self.client.post(f"/{self.path}", self.post_data)
        assert response1.status_code == status.HTTP_201_CREATED
        code1 = response1.data["code"]
        assert len(code1) == 36  # is UUID

        response2 = self.client.post(f"/{self.path}", self.post_data)
        assert response2.status_code == status.HTTP_201_CREATED
        code2 = response2.data["code"]
        assert len(code2) == 36  # is UUID

        assert code1 != code2

        elements = CredentialRequest.objects.filter(email="test@mail.com")
        assert len(elements) == 2

        assert CredentialRequest.objects.filter(code=code1)
        assert CredentialRequest.objects.filter(code=code2)


@pytest.mark.django_db
class TestCredentialObtainRetrieveAPIView:
    __test__ = True
    path_base = "credential-obtain"
    test_code = "1"
    path = f"{path_base}?code={test_code}"

    @pytest.fixture
    def setup(self, mocker, credential_request):
        mocker.patch(
            "manager.views.is_credential_request_ready",
            return_value=credential_request,
        )
        mocker.patch(
            "manager.views.connection_invitation_create",
            return_value=("invitation.url", "e30="),
        )
        return credential_request

    @override_settings(POLL_INTERVAL="1", POLL_MAX_TRIES="2")
    def test_get_invalid_code(self, api_client):
        response = api_client.get(f"/{self.path_base}?code=invalid_code")
        assert "Invalid code" in response.rendered_content

    @override_settings(POLL_INTERVAL="1", POLL_MAX_TRIES="2")
    def test_get_without_authentication(self, setup, api_client):
        response = api_client.get(f"/{self.path}")
        assert response.status_code == status.HTTP_200_OK
        assert response.get("ETag")
        assert response.template_name == "credential_obtain.html"
        data = response.context_data
        assert data.get("invitation_url") == "invitation.url"
        assert data.get("invitation_b64") == "e30="
        assert data.get("poll_interval") == "1"
        assert data.get("poll_max_tries") == "2"
        assert data.get("poll_connection_url") == "http://test.com/connection-check?code=12345"
        assert response.is_rendered is True


@pytest.mark.django_db
class TestCredentialDefinitionAPIView(TestListCreateAPIView):
    __test__ = True
    path = "credential-definition/"

    @pytest.fixture
    def setup(self, schema, credential_definition):
        self.post_data = {
            "name": "another_test_credential_definition",
            "credential_id": "anothertestcredentialdefinition:1:2:3:test",
            "schema": schema.schema_id,
            "support_revocation": "True",
        }
        return credential_definition

    def test_retrieve(self, authenticate, setup, get_response):
        response = self.client.get(
            path=f"/{self.path}",
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 1
        cred_def = results[0]
        assert cred_def["credential_id"] == "testcredentialdefinition:1:2:3:test"
        assert cred_def["name"] == "credential_definition"
        assert cred_def["enabled"] == True
        assert cred_def["schema"] == "testschema:1:id:1.0"
        assert cred_def["support_revocation"] == True
        assert cred_def["creator"] == 1

    def test_create_wrong_params(self, authenticate, setup, schema):
        post_data = {
            "name": "wrong_test_credential_definition",
            "credential_id": "wrongtestcredentialdefinition:1:2:3:test",
            "schema_id": schema.schema_id,
            "support_revocation": "False",
        }
        assert not CredentialDefinition.objects.filter(
            credential_id="wrongtestcredentialdefinition:1:2:3:test"
        ).first()
        response = self.client.post(
            path=f"/{self.path}",
            data=post_data,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This field is required" in str(response.data)
        assert "schema" in str(response.data)

    def test_create_already_exists(self, authenticate, setup, credential_definition):
        post_data = {
            "name": "another_test_credential_definition",
            "credential_id": credential_definition.credential_id,
            "schema": credential_definition.schema.schema_id,
            "support_revocation": "False",
        }
        assert CredentialDefinition.objects.filter(
            credential_id=credential_definition.credential_id
        ).first()
        response = self.client.post(
            path=f"/{self.path}",
            data=post_data,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data) == (
            "{'credential_id': [ErrorDetail(string='credential definition with this credential id already exists.', code='unique')]}"
        )
        assert not CredentialDefinition.objects.filter(
            name="another_test_credential_definition"
        ).first()

    def test_create(self, authenticate, setup):
        assert not CredentialDefinition.objects.filter(
            name="another_test_credential_definition"
        ).first()
        response = self.client.post(
            path=f"/{self.path}",
            data=self.post_data,
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        cred_def = response.data
        assert cred_def["name"] == "another_test_credential_definition"
        assert cred_def["credential_id"] == "anothertestcredentialdefinition:1:2:3:test"
        assert cred_def["support_revocation"] == True

        assert CredentialDefinition.objects.filter(
            name="another_test_credential_definition"
        ).first()
        get_from_db_by_id = CredentialDefinition.objects.filter(
            credential_id="anothertestcredentialdefinition:1:2:3:test"
        ).all()
        assert get_from_db_by_id
        assert len(get_from_db_by_id) == 1
        assert get_from_db_by_id.first().credential_json() == {
            "schema_id": "testschema:1:id:1.0",
            "tag": "another_test_credential_definition",
            "support_revocation": "true",
        }

    def test_create_when_schema_does_not_exist(self, authenticate, setup):
        post_data = {
            "name": "yet_another_test_credential_definition",
            "credential_id": "testcredentialdefinitionschemadoesnotexist:1:2:3:test",
            "schema": "nonexistentschema:1:2:3:test",
            "support_revocation": "False",
        }
        response = self.client.post(
            path=f"/{self.path}",
            data=post_data,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            str(response.data)
            == "{'schema': [ErrorDetail(string='A schema with schema_id \"nonexistentschema:1:2:3:test\" does not exist', code='does_not_exist')]}"
        )
        assert not CredentialDefinition.objects.filter(
            name="yet_another_test_credential_definition"
        ).first()

    def test_post_with_authentication_bad_request(self, authenticate, post_response):
        response = self.client.post(
            path=f"/{self.path}",
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
