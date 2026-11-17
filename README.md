# site-ui

The shared look behind three personal sites: **studio**, **garden** and **bookshelf**.
Neutral colours, fonts, the header and code styling live here once; each site adds its
own accent and layout. Plain CSS and one small JS file, no build step.

**[Live demo](https://hugommartins.github.io/site-ui/)**: the three sites side by
side, light and dark, the header at phone width, favicons, and a live contrast check.

## Why it exists

Sites that start as copies of each other drift: colours, fonts and the header slowly
stop matching. This repo is the one place those pieces live. Each site pins a version
by tag, so a change never reaches a site until it upgrades.

## Why it's public

- Nothing in it is secret. It is CSS, a small script and open-licensed fonts, which
  every visitor of the sites downloads anyway.
- The sites pull it as a git submodule, and a public repo means CI and hosting need no
  token.
- It lets the demo be served from GitHub Pages, and lets anyone see how it is put together.

## What's inside

| | |
|---|---|
| `tokens.css`, `base.css` | Neutral colours, sizes, resets, focus ring |
| `fonts.css`, `fonts/` | Fraunces, Roboto Mono, JetBrains Mono, self-hosted |
| `nav.css`, `header.html`, `theme.js` | The header and the light/dark toggle |
| `code.css` | Code blocks and syntax highlighting |
| `demo.html` | All of the above, for the three sites |

## Testing a shared config

This repo is also a worked example of testing a design config that several sites share:
the strategy tests the contracts between the package and its sites (tokens resolve,
accents pass contrast, the header behaves at every width), not pixels.

- [docs/test-strategy.md](docs/test-strategy.md): risks, layers and what is left untested.
- [docs/testing.md](docs/testing.md): how to run the tests.

## Using it

[docs/usage.md](docs/usage.md): setup, wiring, versions and releases.

## Licence

Code: MIT. Fonts: SIL Open Font License 1.1, licences in `fonts/`.
