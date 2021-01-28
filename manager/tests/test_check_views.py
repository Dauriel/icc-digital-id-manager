import pytest
from rest_framework import status
from manager.tests.api_view_test_classes import (
    TestUnauthenticatedRetrieveAPIView,
)


@pytest.mark.django_db
class TestConnectionCheckRetrieveAPIView(TestUnauthenticatedRetrieveAPIView):
    __test__ = True
    path_base = "connection-check"
    credential_request_test_code = "12345"
    path = f"{path_base}?code={credential_request_test_code}"

    @pytest.fixture
    def setup(self, connection_invitation):
        connection_invitation.accepted = True
        connection_invitation.save()
        return connection_invitation

    def test_retrieve_not_accepted_invitation(self, connection_invitation, api_client):
        connection_invitation.accepted = False
        connection_invitation.save()
        response = api_client.get(f"/{self.path}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_without_authentication(self, setup, api_client):
        response = api_client.get(f"/{self.path}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_with_authentication(self, setup, api_client_admin):
        response = api_client_admin.get(f"/{self.path}")
        assert response.status_code == status.HTTP_200_OK

    def test_post_without_authentication(self, setup, api_client):
        response = api_client.post(f"/{self.path}", {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_invalid_code(self, api_client_admin):
        response = api_client_admin.get(f"/{self.path_base}?code=invalid_code")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCredentialCheckRetrieveAPIView(TestUnauthenticatedRetrieveAPIView):
    __test__ = True
    path_base = "credential-check"
    credential_request_test_code = "12345"
    path = f"{path_base}?code={credential_request_test_code}"

    @pytest.fixture
    def setup(self, credential_offer):
        credential_offer.accepted = True
        credential_offer.save()
        return credential_offer

    def test_retrieve_not_accepted_invitation(self, credential_offer, api_client):
        credential_offer.accepted = False
        credential_offer.save()
        response = api_client.get(f"/{self.path}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_without_authentication(self, setup, api_client):
        response = api_client.get(f"/{self.path}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_with_authentication(self, setup, api_client_admin):
        response = api_client_admin.get(f"/{self.path}")
        assert response.status_code == status.HTTP_200_OK

    def test_post_without_authentication(self, setup, api_client):
        response = api_client.post(f"/{self.path}", {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_invalid_code(self, api_client_admin):
        response = api_client_admin.get(f"/{self.path_base}?code=invalid_code")
        assert response.status_code == status.HTTP_404_NOT_FOUND
