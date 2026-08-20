MESH - Multi-Agent Negotiation Engine
 0.1.0 
OAS 3.1
/openapi.json
AI-Driven Multi-Agent Decision Intelligence Engine for Hospital Digital Twin

default


GET
/
Root


Parameters
Cancel
No parameters

Execute
Clear
Responses
Curl

curl -X 'GET' \
  'http://127.0.0.1:8000/' \
  -H 'accept: application/json'
Request URL
http://127.0.0.1:8000/
Server response
Code	Details
200	
Response body
Download
{
  "app": "MESH",
  "status": "running",
  "env": "development"
}
Response headers
 content-length: 53 
 content-type: application/json 
 date: Thu,20 Aug 2026 14:09:20 GMT 
 server: uvicorn 
Responses
Code	Description	Links
200	
Successful Response

Media type

application/json
Controls Accept header.
Example Value
Schema
"string"
No links

GET
/health
Health Check


Parameters
Cancel
No parameters

Execute
Clear
Responses
Curl

curl -X 'GET' \
  'http://127.0.0.1:8000/health' \
  -H 'accept: application/json'
Request URL
http://127.0.0.1:8000/health
Server response
Code	Details
200	
Response body
Download
{
  "status": "ok"
}
Response headers
 content-length: 15 
 content-type: application/json 
 date: Thu,20 Aug 2026 14:09:29 GMT 
 server: uvicorn 
Responses
Code	Description	Links
200	
Successful Response

Media type

application/json
Controls Accept header.
Example Value
Schema
"string"
No links

GET
/twin/seed
Seed Twin


Seed the digital twin with sample hospital data — for testing only.

Parameters
Cancel
No parameters

Execute
Clear
Responses
Curl

curl -X 'GET' \
  'http://127.0.0.1:8000/twin/seed' \
  -H 'accept: application/json'
Request URL
http://127.0.0.1:8000/twin/seed
Server response
Code	Details
200	
Response body
Download
{
  "beds": {
    "ICU-1": {
      "bed_id": "ICU-1",
      "ward": "ICU",
      "status": "free",
      "patient_id": null
    },
    "ICU-2": {
      "bed_id": "ICU-2",
      "ward": "ICU",
      "status": "free",
      "patient_id": null
    },
    "WARD-C-1": {
      "bed_id": "WARD-C-1",
      "ward": "Ward-C",
      "status": "free",
      "patient_id": null
    }
  },
  "staff": {
    "N1": {
      "staff_id": "N1",
      "role": "nurse",
      "ward": "ICU",
      "available": true,
      "fatigue_score": 0
    }
  },
  "equipment": {
    "VENT-1": {
      "equipment_id": "VENT-1",
      "type": "ventilator",
      "ward": "ICU",
      "status": "available"
    }
  },
  "pharmacy": {
    "Paracetamol": {
      "name": "Paracetamol",
      "quantity": 100,
      "reorder_threshold": 20
    }
  }
}
Response headers
 content-length: 530 
 content-type: application/json 
 date: Thu,20 Aug 2026 14:09:38 GMT 
 server: uvicorn 
Responses
Code	Description	Links
200	
Successful Response

Media type

application/json
Controls Accept header.
Example Value
Schema
"string"
No links

POST
/scenario/trigger
Trigger Scenario


Trigger a simulated hospital event and see what the Emergency Agent proposes. This will later route through negotiation + verification too.

Parameters
Cancel
Reset
No parameters

Request body

application/json
Edit Value
Schema
{
  "scenario_type": "patient_surge",
  "ward": "ICU",
  "patient_count": 5
}
Execute
Clear
Responses
Curl

curl -X 'POST' \
  'http://127.0.0.1:8000/scenario/trigger' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "scenario_type": "patient_surge",
  "ward": "ICU",
  "patient_count": 5
}'
Request URL
http://127.0.0.1:8000/scenario/trigger
Server response
Code	Details
200	
Response body
Download
{
  "event": {
    "type": "patient_surge",
    "source": "simulation",
    "payload": {
      "scenario_type": "patient_surge",
      "ward": "ICU",
      "patient_count": 5,
      "details": null
    },
    "timestamp": "2026-08-20T14:12:12.629893"
  },
  "agent_observation": {
    "total_icu_beds": 2,
    "free_icu_beds": 2,
    "occupancy_rate": 0
  },
  "proposals": [
    {
      "agent": "emergency",
      "action": "request_overflow_capacity",
      "target_id": "ICU",
      "reason": "Incoming 5 patients but only 2 free ICU beds available. Short by 3 beds.",
      "confidence": 0.95,
      "cost": 30,
      "urgency": 0.8
    }
  ]
}
Response headers
 access-control-allow-credentials: true 
 access-control-allow-origin: * 
 content-length: 486 
 content-type: application/json 
 date: Thu,20 Aug 2026 14:12:12 GMT 
 server: uvicorn 
Responses
Code	Description	Links
200	
Successful Response

Media type

application/json
Controls Accept header.
Example Value
Schema
"string"
No links
422	
Validation Error

Media type

application/json
Example Value
Schema
{
  "detail": [
    {
      "loc": [
        "string",
        0
      ],
      "msg": "string",
      "type": "string"
    }
  ]
}
No links

Schemas
HTTPValidationErrorExpand allobject
ScenarioRequestExpand allobject
ValidationErrorExpand allobject