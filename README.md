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

## A note from the maintainer

Hello! I'm the creator of Viridarium.

I built this because the apps already out there didn't quite meet my expectations, and I wanted to make something nice of my own. I own a lot of plants, and some of them are wonderfully picky about water and moisture. I'm also forever forgetting when I last watered my cactus, because those things drink maybe once every three months.

The idea lived in my head for years. I just never got around to it: between work and life, hobby projects always fell to the back of the queue. I'm a software engineer and I genuinely love writing code, but I also love my garden, walks with my dogs, my motorcycle, and looking after all those plants. There's only so much time, and since I already write software all day for work, I tend not to do much of it in my free time.

Then AI came along, and suddenly the hundreds of ideas I'd been sitting on for years became things I could actually finish.

I know plenty of people in my field look at AI with distaste. The moment they see it, or suspect it, they object and condemn (I've watched someone literally spit at the mention of it, which was... weird). I understand the reaction. But I'd ask you to see it from my side too: I get to make this cool thing, and I'm happy with it. Even though it wasn't typed out by my own hands, I am very much the mind behind it: the functionality, the feel, the decisions. The rules and workflows that guided the build are all in this repo, for you to read and learn from. They're based on the software principles I try to follow.

Thanks for reading, and I hope you enjoy Viridarium. If you ever monetize it, I hope you're fair enough to at least buy me a coffee.

— chaoskie

## License

[AGPL-3.0-or-later](LICENSE)
