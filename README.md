# Viridarium

> Self-hosted houseplant tracker: inventory, watering and feeding schedules that adjust for the season, and an open API so your home automation handles the reminders.

A *viridarium* was the green pleasure-garden of a Roman villa. Yours now lives in a container.

**Status: pre-alpha, under active development.** Not ready for use yet.

## Why another plant app?

The existing self-hosted options force user accounts, need a heavy database stack, or treat watering as a generic recurring task. This project is built around four ideas:

- **No login.** Single-user by design, for trusted networks (LAN, VPN, or behind your own reverse proxy auth). Open the page, water your plants.
- **Schedules are plant properties, not tasks.** Each plant has its own watering and feeding interval. Next-due is computed from when you actually last did it, with seasonal adjustment and a dormancy mode that pauses feeding in winter.
- **Open API first.** Everything the UI does goes through a documented REST API (`/api/v1`, OpenAPI). "What's due today" is one GET away for Home Assistant, Node-RED, n8n, or your own scripts. ICS calendar feeds and outbound webhooks are first-class features.
- **Trivial deploy.** One container, SQLite by default. PostgreSQL supported via a single `DATABASE_URL` if you prefer.

## Quickstart

One container, SQLite by default. Drop this `docker-compose.yml` next to where you want
your data and run `docker compose up -d`, then open `http://localhost:8000`.

```yaml
services:
  viridarium:
    image: ghcr.io/chaoskie/viridarium:latest
    # Or build from a checkout instead of pulling:
    # build: .
    container_name: viridarium
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - viridarium-data:/data
    environment:
      DATABASE_URL: sqlite:////data/app.db
    security_opt:
      - no-new-privileges:true

volumes:
  viridarium-data:
```

The repository ships a fuller [`docker-compose.yml`](docker-compose.yml) with a commented
PostgreSQL block and a healthcheck. PostgreSQL is opt-in via a single `DATABASE_URL` (see
that file).

Deploy on a trusted network or behind your own auth proxy: there is no authentication in
v1 by design. See [SECURITY.md](SECURITY.md) before exposing anything.

## Features

- [ ] Plant inventory: species, photos, location/room, pot size and material, light level, notes
- [ ] Per-plant watering schedule (interval + seasonal adjustment + dormancy)
- [ ] Per-plant feeding schedule with dormancy pause
- [ ] Care log: watering, feeding, repotting, observations, with photo history
- [ ] Due today / overdue dashboard
- [ ] REST API with OpenAPI docs
- [ ] ICS calendar feed per location
- [ ] Outbound webhooks on due/overdue (ntfy, Home Assistant, anything HTTP)
- [ ] Optional species lookup (pluggable, no hard dependency on any external API)

## Vision and scope

In scope: everything above, single user, beautiful responsive UI.

Out of scope, deliberately: user accounts and multi-tenancy, social features, AI care advice, cloud services. If you need collaboration, [HortusFox](https://github.com/danielbrendel/hortusfox-web) does that well.

## Security model

No authentication, on purpose. Deploy on a trusted network or behind your own auth proxy. See [SECURITY.md](SECURITY.md) before exposing anything.

## Stack

FastAPI + SQLAlchemy (Python 3.12), React + TypeScript + Tailwind, SQLite or PostgreSQL. Hexagonal architecture, enforced in CI.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). This project is developed in the open by a solo maintainer with AI assistance; every change is spec-driven, test-first, and passes deterministic quality gates before review. The full development rulebook is public in [`rules/`](rules/).

## License

[AGPL-3.0-or-later](LICENSE)
