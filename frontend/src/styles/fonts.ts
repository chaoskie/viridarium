/**
 * Self-hosted theme fonts (FE-001 lock), bundled by Vite and served same-origin
 * so the strict CSP (`style-src 'self'`, SEC-011) passes on the production path
 * and the app works fully offline (product-spec §7). Weights/styles mirror the
 * Google Fonts css2 request this replaces (VIRIDARIUM-37); static Fraunces
 * drops the `opsz` axis (accepted in the change proposal).
 *
 *   Roman + Dark -> Cinzel (display/label) + EB Garamond (body)
 *                   + Cormorant Garamond (italic accent / ledgers)
 *   Terracotta   -> Baloo 2 (display) + Atkinson Hyperlegible (body)
 *   Herbarium    -> Fraunces (display) + Spectral (body) + IBM Plex Mono
 */

import "@fontsource/cinzel/400.css";
import "@fontsource/cinzel/500.css";
import "@fontsource/cinzel/600.css";
import "@fontsource/cinzel/700.css";

import "@fontsource/eb-garamond/400.css";
import "@fontsource/eb-garamond/400-italic.css";
import "@fontsource/eb-garamond/500.css";
import "@fontsource/eb-garamond/600.css";

import "@fontsource/cormorant-garamond/500.css";
import "@fontsource/cormorant-garamond/500-italic.css";

import "@fontsource/baloo-2/500.css";
import "@fontsource/baloo-2/600.css";
import "@fontsource/baloo-2/700.css";
import "@fontsource/baloo-2/800.css";

import "@fontsource/atkinson-hyperlegible/400.css";
import "@fontsource/atkinson-hyperlegible/400-italic.css";
import "@fontsource/atkinson-hyperlegible/700.css";

import "@fontsource/fraunces/300.css";
import "@fontsource/fraunces/400.css";
import "@fontsource/fraunces/400-italic.css";
import "@fontsource/fraunces/600.css";
import "@fontsource/fraunces/900.css";

import "@fontsource/spectral/300.css";
import "@fontsource/spectral/400.css";
import "@fontsource/spectral/400-italic.css";
import "@fontsource/spectral/500.css";

import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
