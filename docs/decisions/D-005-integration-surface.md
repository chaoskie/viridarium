# D-005: Generic integration surface, no bespoke adapters

Status: ratified, 2026-06-07.

## Decision

The app exposes a generic integration surface that any self-hosted service can consume:

- a documented REST API (`/api/v1`, OpenAPI),
- a "due today / overdue" endpoint,
- ICS calendar feeds,
- outbound webhooks on due and overdue events.

The repository contains no adapter code for any specific home-automation or task system.

## Why

Reminders belong in whatever the user already runs (Home Assistant, Node-RED, n8n, a
script). A generic surface lets anyone wire their own setup, and keeps the repository
free of code that only fits one installation. Research confirmed that ICS feeds, webhooks
and automation-friendly JSON are exactly the gaps the existing apps leave open.

## Consequences

- Integrations are built by consumers: they poll the due endpoint or subscribe to
  webhooks, and that wiring lives outside this repository.
- Everything the UI does goes through the same public API.
