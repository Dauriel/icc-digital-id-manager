#!/bin/bash
curl --location --request POST 'http://localhost:8082/credential-request' \
--header "Authorization: token $DEMO_TOKEN" \
--header 'Content-Type: application/json' \
--data-raw '{
    "credential_definition": "Th7MpTaRZVRYnPiabds81Y:3:CL:41577:idmanagerdemocreddef",
    "email": "your_email@mail.com",
    "credential_data": "{\"score\": \"10\" }"
}'