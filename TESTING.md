# Running the tests

How to run the checks described in [test-strategy.md](test-strategy.md).

## Status

| File | Layer | Status |
|---|---|---|
| `tests/check_package.py` | L1 static, L3 contrast | not written yet |
| `tests/check_site.py` | L2 site contract | not written yet |
| `tests/browser/` | L4 browser | not written yet |
| `tests/check_markup.py` | L5 markup drift | not written yet |
| L6 repo hygiene | | two commands, below |

Update this table as the files appear. The commands below are what each will do once written.

## Requirements

- Python 3.12 or newer. L1, L2, L3, L5 and L6 use the standard library only; L5 also needs
  `jinja2` (the sites already have it).
- L4 only: `pip install playwright pytest axe-playwright-python`, then
  `playwright install chromium`.

## In this repo (package)

```bash
python3 tests/check_package.py      # L1 + L3: tokens, fonts, contrast for the three accents
pytest tests/browser                # L4: demo.html at 1000/700/390/320px, per site
```

Run `pytest` with `-k garden` (or `bookshelf`, `studio`) to run one site. Add `--headed`
to watch the browser.

To look at the demo by hand:

```bash
python3 -m http.server 8000         # then open http://localhost:8000/demo.html
```

## In a site (garden, bookshelf, studio)

```bash
# L6: before the build (skip the tag check when SITE_UI_DIR points at a local clone)
test -f "${SITE_UI_DIR:-vendor/site-ui}/tokens.css" || { echo "site-ui not found"; exit 1; }
[ -n "$SITE_UI_DIR" ] || git -C vendor/site-ui describe --exact-match --tags

# L2 + L3 for this site's accent
python3 vendor/site-ui/tests/check_site.py style.css --built dist/
```

`check_site.py` takes the site's `style.css` and, optionally, the built output folder, to
check that every `var()` in the built CSS resolves. For the Jinja sites, call it from the end
of `build.py` so a broken site never gets published.

Studio only (L5): `python3 vendor/site-ui/tests/check_markup.py src/components/Nav.astro`.

## Exit codes and output

Every script exits `0` when all checks pass and `1` otherwise, and prints one line per
failure, for example:

```
FAIL L1 code.css: var(--pre-shadow) is not defined in tokens.css
FAIL L3 navy dark: --brand-text on --brand-tint is 3.9:1, needs 4.5:1
```

## When you change something

| Change | Run |
|---|---|
| Add or rename a token | L1, L2 in each site, and add it to the token list in `check_package.py` |
| Change an accent colour | L3, then `demo.html` |
| Change `nav.css` or `header.html` | L4, L5, and `demo.html` at 390px |
| Add or replace a font file | L1 |
| Tag a release | L1, L3, L4 |

## CI

```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python3 tests/check_package.py
      - run: pip install playwright pytest axe-playwright-python && playwright install --with-deps chromium
      - run: pytest tests/browser
```

In a site's CI, check out with submodules (`actions/checkout@v4` with `submodules: true`) and
run the L6 and L2 commands before the build.

## GitHub Pages

Serve the repo root from `main` (Settings, Pages). The demo is then at
`https://<owner>.github.io/site-ui/demo.html`, and it is the file the browser tests run.

## Troubleshooting

- **`vendor/site-ui/` is empty:** the submodule is not initialised. `git submodule update --init`.
- **`describe --exact-match` fails:** the checkout is not on a tag. Check out the release tag and commit the pointer.
- **Browser tests cannot find `demo.html`:** run `pytest` from the repo root.