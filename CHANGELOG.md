# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2026-08-14)


### Features

* **about:** add About page and app-wide footer with support link ([#54](https://github.com/chaoskie/viridarium/issues/54)) ([72a4e0c](https://github.com/chaoskie/viridarium/commit/72a4e0c54d688a10b2991e0a35ed8e90214f447b))
* add CI workflows, multi-stage Docker image and compose quickstart ([c431983](https://github.com/chaoskie/viridarium/commit/c431983ef72fcdee41ac50f3b46d066905555dbb))
* **care:** log care events with quick actions and inline photo (US-3.2) ([#31](https://github.com/chaoskie/viridarium/issues/31)) ([c5b6cc1](https://github.com/chaoskie/viridarium/commit/c5b6cc16e6bd1d3a2d0a3935a6ec4ec4c1ec30a5))
* **care:** per-plant care history timeline (US-3.4) ([#42](https://github.com/chaoskie/viridarium/issues/42)) ([8115e2a](https://github.com/chaoskie/viridarium/commit/8115e2ae3d882e659a2406af1fd1d8a1dae39864))
* **care:** per-plant water/feed schedule config (US-3.1) ([#22](https://github.com/chaoskie/viridarium/issues/22)) ([34a7705](https://github.com/chaoskie/viridarium/commit/34a7705ea46b55298aaefa7c6466537bb5c5b688))
* **care:** per-schedule next-due/overdue on plant reads (US-3.3) ([#36](https://github.com/chaoskie/viridarium/issues/36)) ([eb226b2](https://github.com/chaoskie/viridarium/commit/eb226b200d22fb00bda66b7b1f8241562d66deea))
* **dashboard:** Today view - due/overdue by location, one-tap log (US-4.1) ([#43](https://github.com/chaoskie/viridarium/issues/43)) ([f041608](https://github.com/chaoskie/viridarium/commit/f041608c39c1c9ea4bb605f4ea216ebb5ef3ee95))
* implement Terracotta and Herbarium themes over the token layer ([f9d41e6](https://github.com/chaoskie/viridarium/commit/f9d41e62b5eb17b1be300bef8cb4e9ab76cd4c6a))
* **inventory:** archive/unarchive plants, default list excludes archived (US-2.4) ([#18](https://github.com/chaoskie/viridarium/issues/18)) ([dd1465c](https://github.com/chaoskie/viridarium/commit/dd1465cd92cc6310c4d3e1eeb6664f7892f6a270))
* **inventory:** location CRUD API + Rooms UI (US-2.2) ([#15](https://github.com/chaoskie/viridarium/issues/15)) ([b0b50a9](https://github.com/chaoskie/viridarium/commit/b0b50a91e401223a67eb064504409a8c2c4dad22))
* **inventory:** plant CRUD + search/filter, homeless plants (US-2.1) ([#17](https://github.com/chaoskie/viridarium/issues/17)) ([534487a](https://github.com/chaoskie/viridarium/commit/534487a9cef5b5cfdc3eb04fcbced7e5a45dd465))
* **inventory:** plant photo upload, gallery, and cover (US-2.3) ([#19](https://github.com/chaoskie/viridarium/issues/19)) ([1ce47a8](https://github.com/chaoskie/viridarium/commit/1ce47a878a2642c907518bfbad461847328dd2b4))
* **plants:** record decorative outer pot (cachepot) on a plant ([#49](https://github.com/chaoskie/viridarium/issues/49)) ([22889c6](https://github.com/chaoskie/viridarium/commit/22889c60147eec2cbf299ba46a3881aff5d329e8))
* **plants:** US-4.3 plant detail page - attributes, schedules, gallery, actions ([#61](https://github.com/chaoskie/viridarium/issues/61)) ([3a633bc](https://github.com/chaoskie/viridarium/commit/3a633bc7c199ddd2f043b81f1d6322a67f15c9cc))
* Roman default theme, dark theme, mobile-first responsive shell ([#13](https://github.com/chaoskie/viridarium/issues/13)) ([fcd8ae0](https://github.com/chaoskie/viridarium/commit/fcd8ae01763eb1602f1ec62a780f09a835076707))
* scaffold frontend with React, strict TS, Vite and theme tokens ([b857d65](https://github.com/chaoskie/viridarium/commit/b857d65c1aca5c4c495bc00e9198a6484853d6a0))
* scaffold hexagonal FastAPI backend with dual-engine persistence ([1a90387](https://github.com/chaoskie/viridarium/commit/1a90387732b851b356c9b504b55b80c16e9b9a1b))
* **settings:** seasonal toggle + editable winter window (US-3.5) ([#37](https://github.com/chaoskie/viridarium/issues/37)) ([b13eaf5](https://github.com/chaoskie/viridarium/commit/b13eaf544209472d2af16aa9c7729e22935505dc))
* **theme:** add Viridian glasshouse theme as a selectable candidate ([#30](https://github.com/chaoskie/viridarium/issues/30)) ([3c7b55d](https://github.com/chaoskie/viridarium/commit/3c7b55d02b05a38fe266c71a4f713369068275a7))


### Bug Fixes

* **care:** keep unsaved sibling values when saving a care schedule ([#50](https://github.com/chaoskie/viridarium/issues/50)) ([769e08b](https://github.com/chaoskie/viridarium/commit/769e08b54181e878267c43b1ab47b734e35a5239))
* **ci:** repair postgres leg, gitleaks initial-push scan, dependabot scope ([#10](https://github.com/chaoskie/viridarium/issues/10)) ([263f672](https://github.com/chaoskie/viridarium/commit/263f672d1bbd94f295448406d41a97634cd2dae2))
* **deps:** bump starlette to 1.3.1 via fastapi 0.137 to clear CVEs ([#45](https://github.com/chaoskie/viridarium/issues/45)) ([ad35bf9](https://github.com/chaoskie/viridarium/commit/ad35bf90ed7e97db95cd2b4c85de47e958fb7a96))
* **docker:** run alembic migrations in the entrypoint before uvicorn ([#68](https://github.com/chaoskie/viridarium/issues/68)) ([978019d](https://github.com/chaoskie/viridarium/commit/978019d9f4f03daa86396321bd5bc33ab3d630fc))
* **mobile:** S25+ soak layout fixes + Playwright acceptance layer ([#44](https://github.com/chaoskie/viridarium/issues/44)) ([01cbeee](https://github.com/chaoskie/viridarium/commit/01cbeee8b90a23bdfd486c03f98a69d9b6015d00))
* **photos:** open the full uncropped image from the gallery grid ([#51](https://github.com/chaoskie/viridarium/issues/51)) ([89d6c83](https://github.com/chaoskie/viridarium/commit/89d6c83eb3c9567036ca52f8764642dafc309fbc))
* **photos:** remove the saved file when the metadata insert fails ([#27](https://github.com/chaoskie/viridarium/issues/27)) ([1d7d225](https://github.com/chaoskie/viridarium/commit/1d7d225b923bdbd3b4f935ec074a8903802dae74))
* **photos:** serve 404 (not 500) when a photo's file is missing ([#21](https://github.com/chaoskie/viridarium/issues/21)) ([830dfb0](https://github.com/chaoskie/viridarium/commit/830dfb0248d47845842cd5def2f0d7f2dbb87fef))
* **plants:** validate pot size as a whole number in the form ([#26](https://github.com/chaoskie/viridarium/issues/26)) ([9a40652](https://github.com/chaoskie/viridarium/commit/9a40652a6953b680c9bbf7422e41d9b9a8b57a32))
* **schedules:** guard plant existence on schedule GET/DELETE ([#25](https://github.com/chaoskie/viridarium/issues/25)) ([5878a39](https://github.com/chaoskie/viridarium/commit/5878a3981be5201e6c7401a3d4ebfbb8b563064c))
* **theme:** self-host fonts and externalize the pre-paint script for CSP ([#28](https://github.com/chaoskie/viridarium/issues/28)) ([22cb84b](https://github.com/chaoskie/viridarium/commit/22cb84b685f71fd05a42cdf1ad2a1617b6082100))
* **timeline:** show portrait photos uncropped in the care timeline ([#52](https://github.com/chaoskie/viridarium/issues/52)) ([742c8f9](https://github.com/chaoskie/viridarium/commit/742c8f9a913e70183adf59ae71fb1ad87d221923))

## [Unreleased]

### Added

- Initial project scaffold: development workflow, rules library, quality gates.
