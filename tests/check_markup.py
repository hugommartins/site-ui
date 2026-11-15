#!/usr/bin/env python3
"""L5: the header.html macro and studio's Nav.astro must produce the same markup.

    python3 vendor/site-ui/tests/check_markup.py src/components/Nav.astro [--name studio]

Standard library only: a small renderer handles the few Jinja constructs header.html uses
(macro, if/else/endif on icon and caller, {{ site_name }}, {{ root or './' }}) and stops with an
error on anything else. The icon (<svg>) is the site's own, so it is compared as a placeholder.
Exit 0 when the markup matches, 1 otherwise.
"""
import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('nav')
ap.add_argument('--name', default='studio')
ap.add_argument('--site-ui', default=str(Path(__file__).resolve().parent.parent))
args = ap.parse_args()


class Events(HTMLParser):
    """Turns markup into a flat list of events, so whitespace and attribute order don't matter."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ev, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if self.skip:
            self.skip += tag == 'svg'
            return
        if tag == 'svg':
            self.ev.append('<svg/>')
            self.skip = 1
            return
        self.ev.append('<%s %s>' % (tag, ' '.join('%s=%r' % (k, v) for k, v in sorted(attrs))))

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= tag == 'svg'
            return
        self.ev.append('</%s>' % tag)

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.ev.append('text:' + ' '.join(data.split()))


def events(html):
    p = Events()
    p.feed(html)
    return p.ev


def render_header(path, name, root):
    """Render the header macro with icon=none and no caller (the shape studio's Nav.astro has)."""
    src = Path(path).read_text(encoding='utf-8')
    src = re.sub(r'{#.*?#}', '', src, flags=re.S)  # Jinja comments
    src = re.sub(r'{%-?\s*macro\b.*?-?%}', '', src, flags=re.S)
    src = re.sub(r'{%-?\s*endmacro\s*-?%}', '', src)
    truthy = {'icon': False, 'caller': False}

    def tokens(text):
        return re.split(r'({%-?.*?-?%})', text, flags=re.S)

    out, stack = [], []  # stack of (branch_is_live) for the open ifs
    for part in tokens(src):
        m = re.fullmatch(r'{%-?\s*(if|else|endif)\s*(\w+)?\s*-?%}', part, flags=re.S)
        if m:
            kw, var = m.group(1), m.group(2)
            if kw == 'if':
                if var not in truthy:
                    sys.exit(f'check_markup: unknown condition "{var}" in header.html; update this script')
                stack.append(truthy[var])
            elif kw == 'else':
                stack[-1] = not stack[-1]
            else:
                stack.pop()
            continue
        if part.startswith('{%'):
            sys.exit(f'check_markup: unsupported tag {part.strip()} in header.html; update this script')
        if all(stack):
            out.append(part)
    html = ''.join(out)
    html = html.replace("{{ root or './' }}", root).replace('{{ site_name }}', name)
    left = re.findall(r'{{.*?}}', html)
    if left:
        sys.exit(f'check_markup: unsupported expression {left[0]} in header.html; update this script')
    return html


macro = events(render_header(Path(args.site_ui) / 'header.html', args.name, '/'))

# the Astro component: markup after the frontmatter, before the first <script>
src = Path(args.nav).read_text(encoding='utf-8')
parts = src.split('---')
body = parts[2] if len(parts) >= 3 else src
body = body.split('<script')[0]
body = re.sub(r'\{`\$\{site\.title\} home`\}', '"%s home"' % args.name, body)
body = re.sub(r'\{site\.title\}', args.name, body)
astro = events(body)

if macro == astro:
    print('check_markup: header.html and %s match' % args.nav)
    sys.exit(0)
import difflib
print('FAIL L5 header.html and %s differ:' % args.nav)
for line in difflib.unified_diff(macro, astro, 'header.html', args.nav, lineterm='', n=1):
    print('  ' + line)
sys.exit(1)
