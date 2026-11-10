# Test strategy

How `site-ui` is kept from breaking the three sites that use it. For commands, see
[testing.md](testing.md).

## Scope and principles

- **Test the contracts, not pixels.** A shared config has no logic to unit-test. What
  breaks is the agreement between the package and each site: tokens that must exist, colours
  that must stay readable, markup that must match.
- **Fast and dependency-free first.** The cheapest checks (plain Python over the CSS) cover
  the failures already seen. Browser tests come second.
- **Fail loudly, at build time.** A missing submodule, an undefined token or an untagged
  pointer should stop the build, not show up as a subtle style bug.
- **`demo.html` is the fixture.** It links the real package files, so what the browser tests
  exercise is what the sites ship.

## Risks

Likelihood and impact are my own judgement for three personal sites with one maintainer.
"Seen" marks a failure that already happened.

| # | Risk | Likelihood | Impact | Mitigated by |
|---|---|---|---|---|
| R1 | A `var(--x)` has no definition, so a rule silently does nothing. Seen: garden's `--border` and `--muted`. | High | Medium | L1, L2 |
| R2 | A site lacks one of the four brand tokens in one theme; the wordmark, icon or hover fill loses its colour | Medium | High | L2 |
| R3 | An accent is unreadable on its paper, tint or hover fill. Seen: garden's green on its tint (4.37:1), navy on dark paper | High | High | L3 |
| R4 | The package defines `--brand*` and a site inherits the wrong accent | Low | High | L1 |
| R5 | The header breaks at a breakpoint: the 560px icon swap, garden's 860px menu, bookshelf's search squeezed at 320px | Medium | High | L4 |
| R6 | Theme flashes wrong on load, does not persist, or the toggle stops working | Medium | Medium | L4 |
| R7 | The header markup differs between `header.html` (Jinja) and `Nav.astro` | Medium | Medium | L5 |
| R8 | A font file is missing or misnamed, so text falls back to a system font | Medium | Medium | L1 |
| R9 | The icon-only brand or the compact toggle has no accessible name | Low | Medium | L4 |
| R10 | The submodule is not initialised in CI or hosting; the build runs on an empty folder | Medium | High | L6 |
| R11 | A site points at an unpushed or untagged `site-ui` commit; clones and deploys fail | Medium | High | L6 |
| R12 | An upgrade changes how a site looks and nobody notices | Medium | Medium | Semver, L2 and L3 on each build, looking at the pages |
| R13 | A visual regression the contract checks cannot see (spacing, alignment) | Medium | Low | Accepted. Look at `demo.html` before each release. |

## Layers

| Layer | Checks | Tool | Runs in | Speed |
|---|---|---|---|---|
| **L1 Static, package** | Every `var(--x)` in the package resolves; no `--brand*` is defined; every `font-family` token has an `@font-face`; every `url()` in `fonts.css` points at an existing file | Python, standard library | package CI | ms |
| **L2 Site contract** | The site's `style.css` defines all four brand tokens in both themes; every `var()` in the built CSS resolves | Python, standard library | each site's build | ms |
| **L3 Contrast** | `--brand-text` 4.5:1 on paper and on the tint over paper; `--brand` 3:1 on paper; paper on `--brand-hover` 4.5:1; light and dark, per site | Python, standard library | package CI (all three accents), each site's build (its own) | ms |
| **L4 Browser** | On `demo.html`, per site, at 1000, 700, 390 and 320px: no horizontal overflow; name above 560px and icon below; toggle flips, persists and is set before first paint; accessible names (axe); garden drawer opens, closes and closes on Esc; bookshelf search visible at every width | Playwright, pytest | package CI | seconds |
| **L5 Markup drift** | The `header.html` macro and `Nav.astro` produce the same normalised markup | Python plus Jinja | studio CI | ms |
| **L6 Repo hygiene** | `vendor/site-ui/tokens.css` exists before the build runs; the pointer is on a tag (`git describe --exact-match --tags`) | shell or Python | each site's build and CI | ms |

## Coverage

| Risk | L1 | L2 | L3 | L4 | L5 | L6 |
|---|---|---|---|---|---|---|
| R1 undefined var | ● | ● | | | | |
| R2 missing brand token | | ● | | | | |
| R3 contrast | | | ● | | | |
| R4 package leaks accent | ● | | | | | |
| R5 header breakpoints | | | | ● | | |
| R6 theme behaviour | | | | ● | | |
| R7 markup drift | | | | | ● | |
| R8 fonts | ● | | | | | |
| R9 accessible names | | | | ● | | |
| R10 empty submodule | | | | | | ● |
| R11 untagged pointer | | | | | | ● |
| R12 upgrade surprises | | ● | ● | | | |

## Not tested, on purpose

- **Pixel snapshots and before/after baselines.** Font rendering and antialiasing differ by
  machine, so they flake, and the contract checks above catch what matters. Revisit only if a
  visual regression slips through (R13).
- **Real font rendering.** The checks confirm that the files exist and are declared. How a
  font looks is judged by eye in the demo.
- **Per-site pages and e2e.** Each site tests its own content. This repo tests the package and
  the contract a site must meet.
- **The favicon.** It is a static file per site; `demo.html` shows all six variants.

## Order of work

1. **L1 and L3**: small, no dependencies, and they cover R1, R3, R4 and R8, which have
   already happened or are likely.
2. **L6**: two lines in each site's build.
3. **L4**: when `demo.html` links the real files.
4. **L2**: when the first site migrates.
5. **L5**: when studio adopts the package.

## Release gate

Before tagging a version: L1, L3 and L4 pass in CI, and `demo.html` has been looked at in
both themes for all three sites. After upgrading a site: its L2, L3 and L6 pass, and its pages
have been opened once in both themes.