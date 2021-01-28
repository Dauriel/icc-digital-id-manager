import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.fields import empty

from manager.models import Schema, CredentialDefinition, CredentialRequest
from manager.utils import anonymize_values

LOGGER = logging.getLogger(__name__)


class SchemaJsonSerializer(serializers.Serializer):
    schema_name = serializers.CharField(required=True)
    schema_version = serializers.CharField(required=True)
    attributes = serializers.ListField(child=serializers.CharField(required=True))


class SchemaSerializer(serializers.ModelSerializer):
    schema_json = SchemaJsonSerializer(required=True, read_only=False)

    class Meta:
        model = Schema

        fields = "__all__"
        read_only_fields = ("creator",)


class CredentialDefinitionSerializer(serializers.ModelSerializer):
    schema = serializers.SlugRelatedField(
        slug_field="schema_id",
        read_only=False,
        queryset=Schema.objects.all(),
        error_messages={"does_not_exist": 'A schema with schema_id "{value}" does not exist'},
    )

    class Meta:
        model = CredentialDefinition

        fields = "__all__"
        read_only_fields = ("creator",)


class CredentialRequestSerializer(serializers.ModelSerializer):
    credential_definition = None

    def _validate_credential_definition(self, data):
        cred_def_id_or_name = data.get("credential_definition")
        try:
            self.credential_definition = CredentialDefinition.objects.get(
                credential_id=cred_def_id_or_name, enabled=True
            )
        except ObjectDoesNotExist:
            try:
                self.credential_definition = CredentialDefinition.objects.get(
                    name=cred_def_id_or_name, enabled=True
                )
            except Exception:
                LOGGER.error(f"CredentialRequest: credential definition not found: '{data}'")
                raise serializers.ValidationError(
                    {"credential_definition": "Credential definition does not exist"}
                )
        valid_data = data.copy()
        valid_data["credential_definition"] = self.credential_definition.id
        return valid_data

    def _validate_credential_data(self, data):
        schema = set(self.credential_definition.schema.schema_json.get("attributes"))
        try:
            credential_data = json.loads(data.get("credential_data", "{}"))
        except Exception:
            LOGGER.error(
                f"CredentialRequest: {self.credential_definition.credential_id}: "
                f"invalid data: {data.get('credential_data')}"
            )
            raise serializers.ValidationError({"credential_data": "Invalid credential data"})

        credential_data_keys = set(credential_data.keys())
        schema_data_diff = schema - credential_data_keys
        if schema_data_diff:
            LOGGER.error(
                f"CredentialRequest: {self.credential_definition.credential_id}: "
                f"attribute(s) not found in the data provided: {schema_data_diff} - "
                f"definition: '{self.credential_definition.credential_id}' - "
                f"data: {anonymize_values(credential_data)}"
            )
            raise serializers.ValidationError(
                {
                    "credential_data": f"Attribute(s) not found in the data provided: {schema_data_diff}"
                }
            )
        return data

    def run_validation(self, data=empty):
        if data in (empty, None):
            data = {}
        value = self._validate_credential_definition(data)
        value = super().run_validation(value)
        value = self._validate_credential_data(value)
        return value

    class Meta:
        model = CredentialRequest

        fields = (
            "credential_definition",
            "credential_data",
            "code",
            "email",
            "invitation_url",
        )
        read_only_fields = ("code", "invitation_url")
        extra_kwargs = {
            "credential_definition": {"write_only": True},
            "credential_data": {"write_only": True},
            "email": {"write_only": True},
        }
