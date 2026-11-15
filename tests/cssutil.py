"""Small CSS helpers shared by the checks. Standard library only."""
import re
from pathlib import Path

BRAND = ('--brand', '--brand-tint', '--brand-text', '--brand-hover')
PACKAGE_CSS = ('tokens.css', 'base.css', 'nav.css', 'code.css', 'fonts.css')


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def rules(css):
    """Yield (selector, declarations) for every style rule, flattening @media and @supports.
    @font-face and @keyframes are skipped. declarations is a list of (property, value)."""
    css = strip_comments(css)
    out, i, n = [], 0, len(css)

    def block(start):
        depth, j = 1, start
        while j < n and depth:
            depth += {'{': 1, '}': -1}.get(css[j], 0)
            j += 1
        return j

    def walk(text):
        k = 0
        while k < len(text):
            o = text.find('{', k)
            if o < 0:
                break
            head = text[k:o].strip()
            depth, j = 1, o + 1
            while j < len(text) and depth:
                depth += {'{': 1, '}': -1}.get(text[j], 0)
                j += 1
            body = text[o + 1:j - 1]
            if head.startswith(('@media', '@supports', '@layer')):
                walk(body)
            elif head.startswith('@'):
                pass
            else:
                out.append((head, decls(body)))
            k = j

    walk(css)
    return out


def decls(body):
    res, depth, cur = [], 0, ''
    for ch in body:
        if ch in '({':
            depth += 1
        elif ch in ')}':
            depth -= 1
        if ch == ';' and depth == 0:
            res.append(cur)
            cur = ''
        else:
            cur += ch
    res.append(cur)
    pairs = []
    for d in res:
        if ':' in d:
            p, v = d.split(':', 1)
            pairs.append((p.strip(), v.strip()))
    return pairs


def is_dark(selector):
    return bool(re.search(r"data-theme\s*=\s*['\"]?dark", selector))


def defined(css):
    """Every custom property defined anywhere in css."""
    return {p for _, ds in rules(css) for p, _ in ds if p.startswith('--')}


def used(css):
    """Custom properties used with var(), without a fallback."""
    css = strip_comments(css)
    return set(re.findall(r'var\(\s*(--[\w-]+)\s*\)', css))


def tokens(css, dark):
    """Custom properties of the :root / html rules, for one theme. Later rules win."""
    res = {}
    for sel, ds in rules(css):
        for s in (x.strip() for x in sel.split(',')):
            if not re.match(r'^(:root|html)(:root)?(\[data-[\w-]+=[^\]]+\])*$', s):
                continue
            if is_dark(s) != dark:
                continue
            if dark is False and re.search(r'data-theme', s):
                continue
            for p, v in ds:
                if p.startswith('--'):
                    res[p] = v
    return res


# ---- colour ----
def parse_color(v):
    v = v.strip().lower()
    m = re.fullmatch(r'#([0-9a-f]{3,8})', v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = ''.join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return r, g, b, a
    m = re.fullmatch(r'rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)(?:[ ,/]+([\d.]+%?))?\s*\)', v)
    if m:
        a = m.group(4)
        a = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith('%') else float(a))
        return float(m.group(1)), float(m.group(2)), float(m.group(3)), a
    return None


def over(fg, bg):
    r, g, b, a = fg
    return tuple(a * f + (1 - a) * k for f, k in zip((r, g, b), bg[:3])) + (1.0,)


def lum(c):
    def ch(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def contrast_failures(label, theme, brand, paper):
    """The L3 rules for one accent in one theme. brand is a dict of the four tokens."""
    fails = []
    p = parse_color(paper)
    c = {k: parse_color(brand[k]) for k in BRAND if k in brand}
    if p is None or None in c.values() or len(c) < 4:
        return [f'{label} {theme}: could not read the colours (use hex or rgb/rgba literals)']
    tint = over(c['--brand-tint'], p)
    checks = [
        ('--brand-text on --paper', ratio(c['--brand-text'], p), 4.5),
        ('--brand-text on --brand-tint', ratio(c['--brand-text'], tint), 4.5),
        ('--brand on --paper', ratio(c['--brand'], p), 3.0),
        ('--paper on --brand-hover', ratio(p, c['--brand-hover']), 4.5),
    ]
    for name, r, need in checks:
        if r < need:
            fails.append(f'{label} {theme}: {name} is {r:.2f}:1, needs {need}:1')
    return fails


def read(path):
    return Path(path).read_text(encoding='utf-8')
