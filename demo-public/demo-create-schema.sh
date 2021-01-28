#!/bin/bash
curl --location --request POST 'http://localhost:8082/schema/' \
--header "Authorization: token $DEMO_TOKEN" \
--header 'Content-Type: application/json' \
--data-raw '{
"name" : "idmanagerdemoschema",
"schema_id" : "Th7MpTaRZVRYnPiabds81Y:2:prefs:1.0",
"schema_json" : { "schema_version": "1.0", "schema_name": "prefs", "attributes": [ "score" ] }
}'
