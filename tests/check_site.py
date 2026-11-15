#!/usr/bin/env python3
"""L2 (site contract) and L3 (contrast for this site's accent). Standard library only.

    python3 vendor/site-ui/tests/check_site.py style.css [--built dist/] [--site-ui DIR] [--allow p --allow x]

style.css   the site's own stylesheet (studio: src/styles/global.css)
--built     the built output folder: every var() in its .css files and <style> blocks must resolve
--site-ui   the package folder (default: the folder this file lives in, one level up)
--allow     a custom property set outside CSS (inline style or JS), e.g. --p

Exit 0 when everything passes, 1 otherwise; one FAIL line per problem.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cssutil import (BRAND, PACKAGE_CSS, contrast_failures, defined, read, strip_comments,  # noqa: E402
                     tokens, used)

ap = argparse.ArgumentParser()
ap.add_argument('style')
ap.add_argument('--built')
ap.add_argument('--site-ui', default=str(Path(__file__).resolve().parent.parent))
ap.add_argument('--allow', action='append', default=[])
args = ap.parse_args()

pkg = Path(args.site_ui)
fails = []


def fail(layer, msg):
    fails.append(f'FAIL {layer} {msg}')


site_css = read(args.style)
pkg_css = {f: read(pkg / f) for f in PACKAGE_CSS if (pkg / f).exists()}
pkg_text = '\n'.join(pkg_css.values())
allowed = {a if a.startswith('--') else '--' + a for a in args.allow}

# ---- L2: the four brand tokens, both themes ----------------------------------------------
light, dark = tokens(site_css, False), tokens(site_css, True)
for theme, got in (('light', light), ('dark', dark)):
    for name in BRAND:
        if name not in got:
            fail('L2', f'{args.style}: {name} is not defined for the {theme} theme')

# ---- L2: every var() in the site's CSS resolves ------------------------------------------
known = defined(site_css) | defined(pkg_text) | allowed
for name in sorted(used(site_css)):
    if name not in known:
        fail('L2', f'{args.style}: var({name}) is not defined in the site or in site-ui')

# ---- L2: the same, on the built output ---------------------------------------------------
if args.built:
    built = Path(args.built)
    if not built.is_dir():
        fail('L2', f'{args.built} is not a folder')
    else:
        texts, inline_defs = [], set()
        for f in built.rglob('*'):
            if f.suffix == '.css':
                texts.append((str(f), read(f)))
            elif f.suffix == '.html':
                html = read(f)
                for i, s in enumerate(re.findall(r'<style[^>]*>(.*?)</style>', html, flags=re.S)):
                    texts.append((f'{f}#style{i}', s))
                # custom properties set inline, e.g. style="--p:0.4"
                for attr in re.findall(r'style="([^"]*)"', html):
                    inline_defs |= set(re.findall(r'(--[\w-]+)\s*:', attr))
        built_defined = set(inline_defs)
        for _, t in texts:
            built_defined |= defined(t)
        known_built = built_defined | defined(pkg_text) | allowed
        seen = set()
        for where, t in texts:
            for name in sorted(used(t)):
                if name not in known_built and (name, where) not in seen:
                    seen.add((name, where))
                    fail('L2', f'built {where}: var({name}) is not defined')
        if not texts:
            fail('L2', f'{args.built}: no CSS found; was the site built?')

# ---- L3: contrast for this site's accent -------------------------------------------------
pk = pkg_css.get('tokens.css', '')
paper = {'light': tokens(pk, False).get('--paper'), 'dark': tokens(pk, True).get('--paper')}
for theme, got in (('light', light), ('dark', dark)):
    if all(n in got for n in BRAND):
        fails.extend('FAIL L3 ' + f for f in contrast_failures('site', theme, got, paper[theme]))

for f in fails:
    print(f)
print(f'check_site: {len(fails)} failure(s)' if fails else 'check_site: all checks passed')
sys.exit(1 if fails else 0)
