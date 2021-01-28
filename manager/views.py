import json
import logging
import time

from django.conf import settings
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from manager.credential_workflow import (
    connection_invitation_accept,
    credential_offer_create,
    credential_offer_accept,
    is_credential_request_ready,
    connection_invitation_create,
)
from manager.models import (
    Schema,
    CredentialDefinition,
    CredentialRequest,
    ConnectionInvitation,
    CredentialOffer,
)
from manager.serializers import (
    SchemaSerializer,
    CredentialDefinitionSerializer,
    CredentialRequestSerializer,
)
from manager.utils import EmailHelper

LOGGER = logging.getLogger(__name__)


class SchemaViewSet(viewsets.ModelViewSet):
    serializer_class = SchemaSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Schema.objects.all()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CredentialDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = CredentialDefinitionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CredentialDefinition.objects.all()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CredentialRequestRetrieveAPIView(RetrieveAPIView):
    serializer_class = CredentialRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CredentialRequest.objects.all()


class CredentialRequestListCreateAPIView(ListCreateAPIView):
    serializer_class = CredentialRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CredentialRequest.objects.all()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
        invitation_url = serializer.instance.invitation_url
        LOGGER.debug(f"*** Obtain credential url: {invitation_url}")
        EmailHelper.send(
            serializer.instance.email,
            template="invitation",
            context={
                "credential_name": serializer.instance.credential_definition.name,
                "invitation_url": invitation_url,
            },
        )


class StepCheckAPIView(APIView):
    model_class = None
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, format=None):
        code = request.query_params.get("code")
        model = self.model_class.objects.filter(credential_request__code=code).order_by("-created").first()
        if not model:
            raise NotFound()

        if not model.accepted:
            raise ValidationError({"detail": "Not accepted yet"})

        return Response()


class ConnectionCheck(StepCheckAPIView):
    model_class = ConnectionInvitation


class CredentialCheck(StepCheckAPIView):
    model_class = CredentialOffer


def credential_obtain(request):
    template_name = "credential_obtain.html"

    code = request.GET.get("code")
    try:
        credential_request = is_credential_request_ready(code)
    except Exception as e:
        LOGGER.error(f"obtain_credential: code:{code} - error: {e}")
        return TemplateResponse(request, template_name, {"error": "Invalid code"})

    invitation_url, invitation_b64 = "", ""
    connection_invitations = credential_request.connection_invitations.order_by("-created")
    if not connection_invitations or not connection_invitations[0].accepted:
        invitation_url, invitation_b64 = connection_invitation_create(credential_request)

    return TemplateResponse(
        request,
        template_name,
        {
            "invitation_url": invitation_url,
            "invitation_b64": invitation_b64,
            "poll_interval": settings.POLL_INTERVAL,
            "poll_max_tries": settings.POLL_MAX_TRIES,
            "poll_connection_url": credential_request.connection_invitation_polling_url,
            "poll_credential_url": credential_request.credential_offer_polling_url,
        },
    )


@csrf_exempt
def webhooks(request, topic):
    # TODO: validate 'secret' key
    try:
        message = json.loads(request.body)

        state = message.get("state")

        LOGGER.info(f"webhook: received: topic: '{topic}' - state: '{state}' - message: {message}")

        if topic == "connections" and state == "response":
            connection_id = message.get("connection_id")
            try:
                connection_invitation = connection_invitation_accept(connection_id)
                if connection_invitation:
                    LOGGER.info(f"webhook: processing: connection accepted - connection_id: {connection_id}")
                    time.sleep(5)

                    credential_offer_create(connection_id, connection_invitation)
                else:
                    LOGGER.error(f"webhook: connection_invitation_accept: connection_id: {connection_id} not found")
            except Exception as e:
                LOGGER.error(f"webhook: connection_accepted: connection_id: {connection_id} - error: {e}")

        elif topic == "issue_credential" and state == "credential_issued":
            connection_id = message.get("connection_id")
            try:
                accepted_credential_offer = credential_offer_accept(connection_id)
                if accepted_credential_offer:
                    LOGGER.info(f"webhook: processing: credential accepted - connection_id: {connection_id}")

                else:
                    LOGGER.error(f"webhook: credential_offer_accept: connection_id: {connection_id} not found")

            except Exception as e:
                LOGGER.error(f"webhook: issue_credential: connection_id: {connection_id} - error: {e}")
        else:
            LOGGER.info(f"webhook: topic: {topic} and state: {state} is invalid")

    except Exception as e:
        LOGGER.info(f"webhook: {topic} : bad request: '{request.body}' - {e}")

    return HttpResponse()
