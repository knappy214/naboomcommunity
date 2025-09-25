# Community Hub How-To

This guide explains how to install, configure, and operate the Community Hub
module that powers resident discussion channels, alerts, and events inside the
Naboom community platform.

## 1. Overview

The Community Hub is a Django app that exposes forum-style channels, moderation
policies, membership records, threaded discussions, alerts, event RSVPs, and
push-notification devices.【F:naboomcommunity/communityhub/models.py†L27-L201】【F:naboomcommunity/communityhub/models.py†L336-L520】
It ships with a REST API, realtime WebSocket updates, Celery-powered alert
fan-out, and Wagtail admin snippets for managing content and governance
settings.【F:naboomcommunity/communityhub/api/urls.py†L1-L39】【F:naboomcommunity/communityhub/routing.py†L1-L7】【F:naboomcommunity/communityhub/tasks.py†L1-L74】【F:naboomcommunity/communityhub/wagtail_hooks.py†L1-L77】

## 2. Prerequisites

* Django, Django REST Framework, Wagtail, and Django Channels must already be
  installed in your project (they are included in this repository's
  `requirements.txt`).
* PostgreSQL is recommended to unlock the search indexes defined on threads and
  posts, but the app will gracefully skip the search vector updates on other
  database engines.【F:naboomcommunity/communityhub/models.py†L384-L405】【F:naboomcommunity/communityhub/models.py†L430-L455】
* Redis (or another Celery broker) is required for background alert fan-out.
* Optional: `exponent-server-sdk` for Expo push notifications and `pywebpush`
  for Web Push notifications.【F:naboomcommunity/communityhub/tasks.py†L47-L73】

## 3. Installation Steps

1. **Add the app to `INSTALLED_APPS`.**
   ```python
   INSTALLED_APPS = [
       # ...
       "communityhub",
       "channels",  # required for WebSocket support
       "rest_framework",
       "wagtail",
       # ...
   ]
   ```
   The base settings file in this project already includes these entries for
   reference.【F:naboomcommunity/naboomcommunity/settings/base.py†L76-L119】

2. **Include the REST API routes.** Add the Community Hub API inside your main
   API router so that `/community/` endpoints become available.
   ```python
   from django.urls import include, path

   urlpatterns = [
       # ...
       path("community/", include("communityhub.api.urls")),
   ]
   ```
   【F:naboomcommunity/api/urls.py†L1-L66】

3. **Wire up WebSocket routing.** Append the hub's WebSocket URLs into your
   Channels `websocket_urlpatterns` so authenticated members can receive
   realtime thread and post events.
   ```python
   from communityhub.routing import websocket_urlpatterns as communityhub_ws

   websocket_urlpatterns = [
       *communityhub_ws,
   ]
   ```
   【F:naboomcommunity/naboomcommunity/routing.py†L1-L4】【F:naboomcommunity/communityhub/routing.py†L1-L7】

4. **Apply database migrations.**
   ```bash
   python manage.py migrate communityhub
   ```
   This seeds the schema for channels, memberships, posts, alerts, events, and
   audit logs.【F:naboomcommunity/communityhub/migrations/0001_initial.py†L293-L799】

5. **Start the background workers.** Configure Celery with a broker (Redis by
   default) and run a worker that listens to the `community-alerts` queue.
   ```bash
   celery -A naboomcommunity worker -Q community-alerts
   ```
   The default Celery settings and queue name live in `settings/base.py`.【F:naboomcommunity/communityhub/tasks.py†L1-L74】【F:naboomcommunity/naboomcommunity/settings/base.py†L474-L482】

6. **Expose push notification credentials.** Set the VAPID keys for web push
   and the Expo access token (if used) via environment variables.
   ```bash
   export WEBPUSH_VAPID_PUBLIC_KEY=...      # public key shared with clients
   export WEBPUSH_VAPID_PRIVATE_KEY=...     # keep secret on the server
   export WEBPUSH_VAPID_CLAIM_SUBJECT=mailto:ops@example.com
   export EXPO_ACCESS_TOKEN=...             # optional Expo service token
   ```
   【F:naboomcommunity/naboomcommunity/settings/base.py†L485-L488】

7. **Optional:** Configure alert de-duplication thresholds and the name of the
   Celery queue via the `COMMUNITY_ALERT_DUPLICATE_*` and
   `COMMUNITY_ALERT_QUEUE` environment variables.【F:naboomcommunity/naboomcommunity/settings/base.py†L474-L494】

## 4. Wagtail Admin Usage

Once installed, Wagtail exposes a set of snippet screens for configuring the
hub. Administrators can manage channels, moderation and alert policies, invites
and join requests, canned report reasons, and per-channel configuration objects
without deploying code changes.【F:naboomcommunity/communityhub/wagtail_hooks.py†L1-L77】
Each snippet list view includes filters and search to help operators locate the
right records quickly.

## 5. REST API Highlights

The Community Hub API is namespaced under `/community/` and uses DRF viewsets.
Key endpoints include:

* `channels/` – list, create, and manage channels.
* `invites/` and `join-requests/` – manage onboarding flows.
* `threads/`, `posts/`, and `alerts/` – power asynchronous discussions and
  broadcast alerts.
* `events/` and `event-rsvps/` – attach event metadata and collect RSVP
  responses.
* `devices/` – register push-notification tokens.
* `reports/` and `audit-log/` – capture moderation signals.
* `search/threads/` – server-side search.
* `vapid-key/` – retrieve the public web push key for browser clients.【F:naboomcommunity/communityhub/api/urls.py†L1-L39】

All API endpoints require authentication and enforce object-level permissions
through custom DRF permission classes defined in the app.【F:naboomcommunity/communityhub/api/permissions.py†L1-L200】

## 6. Realtime Features

Authenticated channel members can open a WebSocket connection at
`ws/channels/<channel_id>/` to receive `new_thread` and `new_post` events as
soon as they are published. The `ChannelConsumer` ensures only active members
join the stream and broadcasts events using the shared channel layer.【F:naboomcommunity/communityhub/consumers.py†L1-L60】

## 7. Alerts and Notifications

When a post is marked as an alert, the `fan_out_alert` Celery task gathers all
registered devices for members of the channel and pushes notifications via Expo
or Web Push, tracking success and failure on each device record.【F:naboomcommunity/communityhub/tasks.py†L1-L74】【F:naboomcommunity/communityhub/models.py†L520-L620】
Use the deduplication settings in `settings/base.py` to guard against repeated
alerts in a short time window.【F:naboomcommunity/naboomcommunity/settings/base.py†L474-L494】

## 8. Working With Memberships

Residents join channels through invites or moderated join requests. Accepted
requests create or reactivate a `ChannelMembership` record that tracks the
member's role, notification preferences, and last-read timestamp. Moderators
can suspend members by toggling `is_active` and can tailor notification
preferences per user.【F:naboomcommunity/communityhub/models.py†L232-L379】

## 9. Testing the Installation

After wiring the app into your project, run the existing unit tests to confirm
behaviour:
```bash
python manage.py test communityhub
```
The bundled tests cover API flows, permissions, and model behaviours.【F:naboomcommunity/communityhub/tests/test_api.py†L1-L200】【F:naboomcommunity/communityhub/tests/test_models.py†L1-L200】

## 10. Next Steps

* Integrate the Community Hub views into your frontend to surface channel
  listings, discussions, and RSVP workflows using the documented API endpoints.
* Extend the Wagtail snippets to match your governance processes.
* Hook the websocket events into your UI to show live updates.
* Configure monitoring on the Celery queue and push-notification success rates
  to ensure reliable alert delivery.

With these steps complete, the Community Hub becomes a full-featured community
engagement layer that complements the rest of the Naboom platform.
