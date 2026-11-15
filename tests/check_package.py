#!/usr/bin/env python3
"""L1 (static, package) and L3 (contrast for the three accents). Standard library only.

Run from anywhere:  python3 tests/check_package.py
Exit 0 when everything passes, 1 otherwise; one FAIL line per problem.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cssutil import (BRAND, PACKAGE_CSS, contrast_failures, defined, read, rules,  # noqa: E402
                     strip_comments, tokens, used)

ROOT = Path(__file__).resolve().parent.parent
fails = []


def fail(layer, msg):
    fails.append(f'FAIL {layer} {msg}')


css = {f: read(ROOT / f) for f in PACKAGE_CSS if (ROOT / f).exists()}
for f in PACKAGE_CSS:
    if f not in css:
        fail('L1', f'{f} is missing')

# ---- L1: every var(--x) resolves --------------------------------------------------------
all_defined = set()
for text in css.values():
    all_defined |= defined(text)
site_provided = set(BRAND)  # defined by each site, never by the package
for f, text in css.items():
    for name in sorted(used(text)):
        if name not in all_defined and name not in site_provided:
            fail('L1', f'{f}: var({name}) is not defined in the package')

# ---- L1: the package never defines the brand tokens (R4) --------------------------------
for f, text in css.items():
    for name in sorted(defined(text) & site_provided):
        fail('L1', f'{f}: defines {name}; only a site may define the brand tokens')

# ---- L1: tokens every site relies on ----------------------------------------------------
tk = css.get('tokens.css', '')
light, dark = tokens(tk, False), tokens(tk, True)
REQUIRED = ['--paper', '--ink', '--mist', '--line', '--panel', '--bar', '--shadow-nav', '--markbg', '--markfg',
            '--code-bg', '--code-fg', '--pre-bg', '--pre-border', '--pre-shadow', '--t', '--nav-h', '--wrap',
            '--gutter', '--nav-gutter', '--font-serif', '--font-mono', '--font-code',
            '--fs-body', '--lh-body', '--fw-body', '--fs-small', '--lh-small', '--fs-ui', '--fs-tiny',
            '--fs-h1', '--fs-h2', '--fs-h3', '--fs-h4', '--fs-h5', '--fs-h6']
for name in REQUIRED:
    if name not in light:
        fail('L1', f'tokens.css: {name} is not defined in :root')
# colours that change with the theme must be redefined in the dark block
THEMED = ['--paper', '--ink', '--mist', '--line', '--bar', '--shadow-nav', '--markbg', '--markfg',
          '--code-bg', '--code-fg', '--pre-bg', '--pre-border', '--pre-shadow']
for name in THEMED:
    if name not in dark:
        fail('L1', f'tokens.css: {name} has no dark value')

# ---- L1: every font-family token has an @font-face ---------------------------------------
fonts_css = strip_comments(css.get('fonts.css', ''))
faces = {m.strip().strip('\'"') for m in re.findall(r'@font-face\s*{[^}]*font-family:\s*([^;]+);', fonts_css)}
GENERIC = {'serif', 'sans-serif', 'monospace', 'ui-monospace', 'system-ui'}
for tok in ('--font-serif', '--font-mono', '--font-code'):
    first = light.get(tok, '').split(',')[0].strip().strip('\'"')
    if first and first not in faces and first not in GENERIC:
        fail('L1', f'{tok}: first family "{first}" has no @font-face in fonts.css')

# ---- L1: every url() in fonts.css points at a file ---------------------------------------
for m in re.findall(r'url\(\s*[\'"]?([^)\'"]+)[\'"]?\s*\)', fonts_css):
    if m.startswith(('data:', 'http')):
        continue
    if not (ROOT / m).exists():
        fail('L1', f'fonts.css: {m} does not exist')

# ---- L3: contrast for the three accents (read from demo.html) ----------------------------
demo = read(ROOT / 'demo.html') if (ROOT / 'demo.html').exists() else ''
accents = {}
for sel, ds in rules('\n'.join(re.findall(r'<style>(.*?)</style>', demo, flags=re.S))):
    m = re.fullmatch(r":root\[data-accent=['\"](\w+)['\"]\](\[data-theme=['\"]dark['\"]\])?", sel)
    if m and any(p == '--brand' for p, _ in ds):
        accents.setdefault(m.group(1), {})['dark' if m.group(2) else 'light'] = dict(ds)
if not accents:
    fail('L3', 'demo.html: no accents found to check')
NAMES = {'green': 'garden', 'navy': 'bookshelf', 'ochre': 'studio'}
for acc, themes in accents.items():
    for theme in ('light', 'dark'):
        if theme not in themes:
            fail('L3', f'{NAMES.get(acc, acc)}: no {theme} accent in demo.html')
            continue
        paper = (light if theme == 'light' else dark).get('--paper')
        fails.extend('FAIL L3 ' + f for f in contrast_failures(NAMES.get(acc, acc), theme, themes[theme], paper))

for f in fails:
    print(f)
print(f'check_package: {len(fails)} failure(s)' if fails else 'check_package: all checks passed')
sys.exit(1 if fails else 0)
