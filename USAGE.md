# Using site-ui

For my own use: how the sites consume this repo and how a release works.

## What a site must define

In its own `style.css`, for both themes:

```css
:root                    { --brand: …; --brand-tint: …; --brand-text: …; --brand-hover: …; }
:root[data-theme='dark'] { --brand: …; --brand-tint: …; --brand-text: …; --brand-hover: …; }
```

| Token | Used for | Contrast needed |
|---|---|---|
| `--brand` | wordmark icon, focus ring, borders, bars | 3:1 on `--paper` |
| `--brand-tint` | tag and badge backgrounds (semi-transparent) | n/a |
| `--brand-text` | wordmark, links, small text on paper or tint | 4.5:1 on `--paper` and on the tint over paper |
| `--brand-hover` | hover fills with `--paper` text on top | 4.5:1 for `--paper` on it |

Also in `style.css`: `body { font-family; font-size }`, layout, and everything in the
header slot (garden's menu button, bookshelf's search). If garden's menu button is centred
with `position: absolute`, set `position: relative` on `.nav-inner`.

## Jinja sites (garden, bookshelf)

Add as a submodule, pinned to a tag:

```
git submodule add https://github.com/hugommartins/site-ui vendor/site-ui
git -C vendor/site-ui checkout v0.1.0
git add .gitmodules vendor/site-ui && git commit -m "Add site-ui v0.1.0"
```

`build.py`: take the package folder from `SITE_UI_DIR` if set (see Local development),
otherwise `vendor/site-ui`. Copy it to the output folder as `site-ui/` (skip `.git`, `docs`,
`tests`, `*.md`, `header.html`, `theme.js`), add it to the Jinja loader path, and pass
`theme_init = (UI / "theme.js").read_text()` to every render.

```python
UI = Path(os.environ.get("SITE_UI_DIR", "vendor/site-ui"))
print(f"site-ui: {UI}" + (" (LOCAL)" if "SITE_UI_DIR" in os.environ else ""))
```

`template.html`:

```jinja
{% from "header.html" import header %}
<head>
  <script>{{ theme_init|safe }}</script>
  <link rel="stylesheet" href="{{ root }}/site-ui/fonts.css">
  <link rel="stylesheet" href="{{ root }}/site-ui/tokens.css">
  <link rel="stylesheet" href="{{ root }}/site-ui/base.css">
  <link rel="stylesheet" href="{{ root }}/site-ui/nav.css">
  <link rel="stylesheet" href="{{ root }}/site-ui/code.css">
  <link rel="stylesheet" href="{{ root }}/style.css">
</head>
<body>
  {% call header(site_name, root) %}
    <!-- garden: menu button. bookshelf: search. -->
  {% endcall %}
```

Link the files separately (not concatenated) so the relative font URLs work. Order
matters: `fonts, tokens, base, nav, code`, then the site's `style.css`.

## Astro (studio)

```astro
---
import '@site-ui/fonts.css';
import '@site-ui/tokens.css';
import '@site-ui/base.css';
import '@site-ui/nav.css';
import '@site-ui/code.css';
import '../styles/site.css';
import themeInit from '@site-ui/theme.js?raw';
---
<script is:inline set:html={themeInit}></script>
```

`@site-ui` is a Vite alias, so the same imports work against the submodule or a local clone
(`astro.config.mjs`):

```js
import path from 'node:path';
export default defineConfig({
  vite: { resolve: { alias: { '@site-ui': path.resolve(process.env.SITE_UI_DIR ?? 'vendor/site-ui') } } },
});
```

Astro can't use the Jinja macro, so `Nav.astro` holds a copy of the header markup. Keep
it identical to `header.html` (a test compares them):

```html
<header class="nav">
  <div class="nav-inner">
    <a class="brand" href="/" aria-label="studio">
      <svg viewBox="0 0 28 28" aria-hidden="true"><rect width="28" height="28" rx="7"/></svg>
      <span class="brand-name">studio</span>
    </a>
    <div class="nav-slot"></div>
    <button class="theme" type="button" aria-label="Toggle theme">
      <span class="dot"></span><span class="theme-label">theme</span><span class="ico"></span>
    </button>
  </div>
</header>
```

## Favicon

Each site ships its own `favicon.svg`: the same rounded square as the mobile header icon,
filled with the site's `--brand`. The dark colour comes from a media query inside the SVG,
so it follows the browser, not the site's toggle.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28">
  <style>rect{fill:#3b5b7a}@media (prefers-color-scheme:dark){rect{fill:#8fb0d0}}</style>
  <rect width="28" height="28" rx="7"/>
</svg>
```

## Clone and CI

`git clone --recurse-submodules <site-repo>` (or `git submodule update --init`). Without
it `vendor/site-ui/` is empty and the build fails.

## Local development

You do not need to commit, tag or push `site-ui` to try a change. The submodule only
matters for what gets committed and deployed; locally, point each site at your working
copy.

1. Edit files in your normal `site-ui` clone, never under a site's `vendor/` folder.
2. See the package alone: `python3 -m http.server` in the clone, open `demo.html`, and run
   the checks ([testing.md](testing.md)).
3. See it in a site by setting `SITE_UI_DIR` to the clone:

   ```bash
   SITE_UI_DIR=../site-ui python3 build.py     # garden, bookshelf
   SITE_UI_DIR=../site-ui npm run dev          # studio
   ```

   All three sites can point at the same clone, so one edit shows in all of them.
4. When it looks right: commit, tag and push `site-ui`; then in each site fetch the tags,
   check out the new tag and commit the pointer (see Releasing). Build once without
   `SITE_UI_DIR` to confirm the site works from the pinned tag.

CI and production never set the variable, so they always use the pinned tag. If you forget
it locally, the site builds with the old pinned version, which is wrong but harmless; the
`site-ui:` line `build.py` prints says which one you built with.

Optional: rebuild on every change with `ls ../site-ui/*.css | entr python3 build.py`.

Quick experiments only: editing inside `vendor/site-ui` also works, since it is a real
checkout, but the site then shows `modified content`, the edit has to be copied back into
your clone by hand, and it is easy to commit a pointer to a commit that was never pushed.

## Releasing

1. Edit in a standalone clone of this repo, never inside a site's `vendor/` folder.
2. Run the tests ([testing.md](testing.md)) and open `demo.html` in both themes for all three sites.
3. `git commit`, `git tag vX.Y.Z`, `git push && git push --tags`.
4. Push this repo before any site commit that points at it.
5. In each site: `git -C vendor/site-ui fetch --tags && git -C vendor/site-ui checkout vX.Y.Z`,
   commit the pointer, rebuild, look at the pages.

| Change | Bump |
|---|---|
| Rename or remove a token or class, or change header markup | major |
| Add a token, file or class, or change a value | minor |
| Fix with no visible change | patch |

Below 1.0, treat minor bumps as possibly visible.

## Rules

- Never edit a file under `vendor/`. Change this repo, tag, upgrade.
- A site never defines neutrals, header rules or code colours; per-site overrides go in its `style.css`.
- This repo never defines `--brand*` and holds no site data or framework code.
- Add a token only when a second site needs it. Add a component only when three sites have the same one.

## Git quirks

- A detached HEAD inside `vendor/site-ui` is normal. Do not commit there.
- `git pull` does not move the submodule; run `git submodule update`, or `git config submodule.recurse true` once.
- `modified: vendor/site-ui (new commits)` means the checkout differs from the recorded pointer: commit the pointer or run `git submodule update`.
- `git subtree add --prefix=vendor/site-ui <url> v0.1.0 --squash` is the alternative if submodules feel fragile; upgrades become merges.