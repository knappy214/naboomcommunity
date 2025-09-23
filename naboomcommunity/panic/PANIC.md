# PANIC Module API Usage Guide

## Overview
The `panic` application provides the APIs that power the community safety workflows across the Vue-based operations console and the Expo mobile panic button client. All endpoints are namespaced beneath `/panic/` for Django views and `/api/v2/panic/` for the Wagtail content API, and they share a common incident, responder, and patrol domain model.【F:naboomcommunity/panic/urls.py†L16-L32】【F:naboomcommunity/naboomcommunity/urls.py†L14-L33】【F:naboomcommunity/panic/api.py†L11-L103】

## Core domain objects
- **Incidents** carry priority, status, source, location, and contextual metadata. Status values progress through `open`, `acknowledged`, `resolved`, or `cancelled`, while priorities span `low` to `critical`. Each incident automatically receives a unique reference number.【F:naboomcommunity/panic/models.py†L140-L199】
- **Incident events** record lifecycle milestones such as creation, acknowledgements, resolutions, escalations, and inbound/outbound communications for traceability.【F:naboomcommunity/panic/models.py†L202-L233】
- **Responders, vehicles, patrol routes, waypoints, and alerts** supply situational awareness to the Vue console. Responders are filtered by province, vehicles continuously update last-known positions, and patrol alerts flag issues like missed checkpoints.【F:naboomcommunity/panic/models.py†L80-L405】【F:naboomcommunity/panic/models.py†L411-L477】
- **Push devices and emergency contacts** link Expo clients to notification channels and rapid responder outreach.【F:naboomcommunity/panic/models.py†L106-L138】【F:naboomcommunity/panic/models.py†L40-L79】

## Vue web console APIs
These endpoints back the operations dashboard. They assume an authenticated staff session (no explicit token logic is enforced in-view).

### List incidents
`GET /panic/api/incidents/?status=&province=&limit=` returns the most recent incidents with embedded client profiles and event history. The `status` and `province` query parameters filter results, and `limit` (default `50`, capped at `200`) constrains payload size.【F:naboomcommunity/panic/urls.py†L16-L28】【F:naboomcommunity/panic/views.py†L210-L239】 Responses use the `IncidentSerializer`, so every item includes identifiers, status, priority, client details, geographic context, and event timelines.【F:naboomcommunity/panic/serializers.py†L45-L68】

### Acknowledge or resolve an incident
`POST /panic/api/incidents/<id>/ack` and `POST /panic/api/incidents/<id>/resolve` transition an incident to the acknowledged or resolved state, updating timestamps and emitting an `IncidentEvent` that documents the change.【F:naboomcommunity/panic/urls.py†L26-L28】【F:naboomcommunity/panic/views_actions.py†L12-L48】 Repeat submissions are idempotent because the handlers ignore status changes that have already occurred.【F:naboomcommunity/panic/views_actions.py†L35-L47】

### Real-time monitoring stream
`GET /panic/api/stream?last_incident_id=&last_alert_id=` opens a server-sent events (SSE) feed (when `ENABLE_SSE` is enabled) that continuously pushes `incident` and `patrol_alert` events. Each event carries the same serialized payloads used in the REST list endpoints, and a heartbeat `: keepalive` comment keeps idle connections open. Clients should persist the highest received IDs and pass them back via the query parameters to avoid duplicates.【F:naboomcommunity/panic/urls.py†L24-L26】【F:naboomcommunity/panic/views_stream.py†L18-L65】

### Patrol waypoints
`GET /panic/api/waypoints?province=` lists the active patrol waypoints for map overlays. The optional `province` filter narrows the list, and responses supply IDs, coordinates, radius, and province code for each waypoint.【F:naboomcommunity/panic/urls.py†L23-L25】【F:naboomcommunity/panic/views_waypoints.py†L9-L27】

### Vehicle telemetry
- `POST /panic/api/vehicle/ping` ingests telemetry from tracked vehicles. A valid `X-Vehicle-Token` header (or `token` field) authorises the request, while `lat`, `lng`, optional timestamp (`ts`), `speed_kph`, and `heading_deg` populate both the historical log and the vehicle’s live state.【F:naboomcommunity/panic/urls.py†L21-L22】【F:naboomcommunity/panic/views_vehicle.py†L30-L89】
- `GET /panic/api/vehicle/live` returns a GeoJSON feature collection of every active vehicle with a known last position, enabling Vue map layers to render patrol assets.【F:naboomcommunity/panic/urls.py†L21-L23】【F:naboomcommunity/panic/views_vehicle.py†L92-L114】
- `GET /panic/api/vehicle/tracks?minutes=&vehicle=` retrieves up to 1 000 recent track points (defaulting to the last 60 minutes) grouped by vehicle ID. Passing a `vehicle` query parameter limits the response to a single asset.【F:naboomcommunity/panic/urls.py†L21-L23】【F:naboomcommunity/panic/views_vehicle.py†L116-L142】

### Offline relay frames
`POST /panic/api/relay_submit` accepts a batch of offline incident frames (for example from LoRa or SMS relays) inside a `frames` array. Each frame is persisted as an `InboundMessage` and, when an `incident_reference` is supplied, produces an `IncidentEvent` flagged as an update for downstream monitoring.【F:naboomcommunity/panic/urls.py†L20-L21】【F:naboomcommunity/panic/views_relay.py†L12-L51】

### Wagtail JSON API (read-only)
Vue clients can also query the shared Wagtail API at `/api/v2/panic/…` for richer listings:
- `GET /api/v2/panic/incidents/?status=&province=&limit=` mirrors the custom list endpoint, returning incidents with serializer data and pagination metadata.【F:naboomcommunity/panic/api.py†L11-L38】
- `GET /api/v2/panic/incidents/<id>/` fetches a single incident record.【F:naboomcommunity/panic/api.py†L39-L43】
- `GET /api/v2/panic/responders/?province=` yields all active responders sorted by name, optionally filtered by province.【F:naboomcommunity/panic/api.py†L46-L63】
- `GET /api/v2/panic/alerts/?shift=&limit=` lists patrol alerts with embedded waypoint details, and `GET /api/v2/panic/alerts/<id>/` fetches a single alert.【F:naboomcommunity/panic/api.py†L71-L98】

## Expo mobile client APIs
Expo-based mobile apps call the same `/panic/api/` namespace to log incidents, manage contacts, and register for notifications.

### Submit a panic incident
`POST /panic/api/submit/` accepts JSON or form payloads with optional `client_id`, `lat`, `lng`, `description`, `source`, `address`, `priority`, `province`, and arbitrary `context`. When location coordinates are valid, they are stored as a GIS point; otherwise they are ignored. Successful submissions create both the incident and an accompanying `IncidentEvent` of kind `created`, defaulting the event description to “Panic button activation” unless `event_description` is supplied. The response returns the new incident ID, generated reference, status, and ISO-8601 creation timestamp, enabling the mobile client to track follow-up updates.【F:naboomcommunity/panic/urls.py†L16-L20】【F:naboomcommunity/panic/views.py†L32-L87】【F:naboomcommunity/panic/models.py†L140-L199】【F:naboomcommunity/panic/models.py†L202-L233】

### Bulk upsert emergency contacts
`POST /panic/api/contacts/bulk_upsert` syncs the device’s emergency contact list. The payload must include a `client_id` and a `contacts` array. Each entry should provide `phone_number` plus optional `full_name`, `relationship`, `priority`, and `is_active`; existing rows are updated in place and new ones are created. The response reports how many contacts were created versus updated so the Expo app can surface sync results.【F:naboomcommunity/panic/urls.py†L16-L20】【F:naboomcommunity/panic/views.py†L90-L132】 Contacts are exposed to staff through the incident serializer’s embedded `contacts` data for situational awareness.【F:naboomcommunity/panic/serializers.py†L21-L36】

### Register Expo push tokens
`POST /panic/api/push/register` stores Expo (or APNS/FCM) push tokens for later notifications. Submitting a `token` is mandatory; optional `client_id`, `platform`, and `app_version` attributes associate the device with a client profile and platform enum (`android`, `ios`, `web`, or `unknown`). Tokens are upserted so repeated registrations simply refresh metadata.【F:naboomcommunity/panic/urls.py†L18-L20】【F:naboomcommunity/panic/views_push.py†L21-L49】【F:naboomcommunity/panic/models.py†L106-L138】

### Consuming incident updates
Mobile clients can poll the same `/api/v2/panic/incidents/` endpoint used by Vue to retrieve their own incident state, or subscribe to the SSE feed if the app supports background connections. Because incidents embed `events`, clients can detect acknowledgements, resolutions, and escalations without extra endpoints.【F:naboomcommunity/panic/api.py†L11-L38】【F:naboomcommunity/panic/serializers.py†L45-L68】【F:naboomcommunity/panic/views_stream.py†L34-L61】

## Monitoring incidents end-to-end
- **Vue console operators** typically maintain a live connection to `/panic/api/stream`, fall back to the paginated list API for historical browsing, and drive the acknowledgement/resolution endpoints to progress incidents through their lifecycle.【F:naboomcommunity/panic/views_stream.py†L18-L65】【F:naboomcommunity/panic/views.py†L210-L239】【F:naboomcommunity/panic/views_actions.py†L12-L48】
- **Expo users** submit new incidents and can monitor responses by polling the incident list for their reference, watching for new events such as escalations created by the escalation service, or receiving push notifications triggered via stored device tokens.【F:naboomcommunity/panic/views.py†L32-L87】【F:naboomcommunity/panic/services.py†L1-L71】【F:naboomcommunity/panic/views_push.py†L21-L49】
- **Automated channels** like Clickatell SMS webhooks and the USSD handler also create incidents or append messages, ensuring the incident stream remains the single source of truth regardless of entry point.【F:naboomcommunity/panic/urls.py†L16-L32】【F:naboomcommunity/panic/views.py†L153-L207】【F:naboomcommunity/panic/views_ussd.py†L9-L27】

## Logging incidents from Vue and Expo
- **Expo logging** is centred on the `/panic/api/submit/` endpoint described above; clients should set a distinctive `source` (e.g., `app` or `expo`) within the payload to assist operators in filtering.【F:naboomcommunity/panic/views.py†L62-L71】 Emergency contact uploads and push registration should happen immediately after account provisioning to ensure responders can be reached.【F:naboomcommunity/panic/views.py†L90-L132】【F:naboomcommunity/panic/views_push.py†L21-L49】
- **Vue logging** can reuse the same `/panic/api/submit/` endpoint for operator-initiated incidents by supplying a `source` such as `dashboard` and, where available, geocoded `lat`/`lng`. Subsequent acknowledgements and resolutions are handled through the dedicated endpoints, creating audit events that appear in the incident timeline for both clients and staff.【F:naboomcommunity/panic/urls.py†L16-L28】【F:naboomcommunity/panic/views.py†L32-L87】【F:naboomcommunity/panic/views_actions.py†L12-L48】【F:naboomcommunity/panic/serializers.py†L45-L68】
- **Supplementary channels** (USSD, SMS relay) fall back to the same incident/event model, so operators monitoring via Vue or Expo do not need separate workflows to stay informed.【F:naboomcommunity/panic/urls.py†L16-L32】【F:naboomcommunity/panic/views_relay.py†L12-L51】【F:naboomcommunity/panic/views_ussd.py†L9-L27】

## Escalations and messaging
The background escalation service walks open incidents after configurable delays, generates outbound messages, and records escalation events, guaranteeing that both Vue and Expo clients see these follow-ups in the shared event timeline.【F:naboomcommunity/panic/services.py†L1-L71】【F:naboomcommunity/panic/models.py†L202-L233】 Additionally, Clickatell delivery status callbacks update outbound message records so operators can confirm whether SMS alerts were accepted or failed.【F:naboomcommunity/panic/views.py†L188-L207】

