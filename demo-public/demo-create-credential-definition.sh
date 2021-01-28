#!/bin/bash
curl -X POST "http://localhost:8082/credential-definition/" \
--header "Authorization: token $DEMO_TOKEN" \
-H "accept: application/json" -H "Content-Type: application/json" \
-d '{
    "name" : "idmanagerdemocreddef",
    "credential_id" : "Th7MpTaRZVRYnPiabds81Y:3:CL:41577:idmanagerdemocreddef",
    "schema" : "Th7MpTaRZVRYnPiabds81Y:2:prefs:1.0",
    "support_revocation" : "True"
}'